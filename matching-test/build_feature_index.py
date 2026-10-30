#!/usr/bin/env python3
"""Incremental card-reference feature index. Fetch metadata snapshot once; process a shard per run.
Images are never stored in the index or uploaded to artifacts.
"""
import argparse,csv,io,json,os,tarfile,time,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import cv2,numpy as np
from test_matching import signature

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CardRadar image matching research"})
    with urllib.request.urlopen(req,timeout=50) as r:return r.read()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--batch",type=int,default=0)
    p.add_argument("--all",action="store_true",help="Index all database cards in one run")
    p.add_argument("--batch-size",type=int,default=1500)
    p.add_argument("--workers",type=int,default=6)
    a=p.parse_args()
    if a.batch<0 or not 100<=a.batch_size<=3000:raise SystemExit("Invalid batch settings")
    base=Path("matching-test");out=base/"feature-index";out.mkdir(parents=True,exist_ok=True)
    archive=get("https://codeload.github.com/type-null/PTCG-database/tar.gz/refs/heads/main")
    cards=[]
    with tarfile.open(fileobj=io.BytesIO(archive),mode="r:gz") as tar:
        for member in tar:
            if member.isfile() and "/data_jp/" in member.name and member.name.endswith(".json"):
                try:
                    d=json.load(tar.extractfile(member))
                    if d.get("img"):cards.append((member.name,d))
                except Exception:pass
    cards.sort(key=lambda x:x[0])
    def process(item):
        path,d=item
        try:
            raw=get(d["img"])
            img=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
            if img is None:raise ValueError("image decode")
            # Match existing signature() behavior without writing the original image.
            h,w=img.shape[:2]
            crop=img[int(h*.17):int(h*.66),int(w*.12):int(w*.88)]
            gray=cv2.resize(cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY),(32,32),interpolation=cv2.INTER_AREA).astype(np.float32)
            dct=cv2.dct(gray)[:8,:8]
            bits=(dct[1:,:]>np.median(dct[1:,:])).ravel()
            hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
            hist=cv2.calcHist([hsv],[0,1],None,[16,8],[0,180,0,256])
            cv2.normalize(hist,hist)
            return (path,d.get("name",""),str(d.get("jp_id","")),bits,hist.flatten()),None
        except Exception as e:return None,{"path":path,"error":str(e)[:120]}
    batches=range((len(cards)+a.batch_size-1)//a.batch_size) if a.all else [a.batch]
    totals={"total_metadata":len(cards),"indexed":0,"failed":0,"completed_batches":[]}
    for batch in batches:
        start=batch*a.batch_size
        selected=cards[start:start+a.batch_size]
        if not selected:raise SystemExit(f"No cards in batch {batch}; total={len(cards)}")
        shard=out/f"batch_{batch:03d}.npz"
        if shard.exists():
            with np.load(shard) as existing:
                n=len(existing["ids"])
            print(f"SKIP batch={batch} existing={n}",flush=True)
            totals["indexed"]+=n;totals["completed_batches"].append(batch)
            continue
        rows=[];fail=[]
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            for future in as_completed([pool.submit(process,item) for item in selected]):
                row,error=future.result()
                if row:rows.append(row)
                else:fail.append(error)
        rows.sort(key=lambda x:x[0])
        if rows:
            np.savez_compressed(shard,
                ids=np.array([x[0] for x in rows]),names=np.array([x[1] for x in rows]),
                numbers=np.array([x[2] for x in rows]),bits=np.stack([x[3] for x in rows]),
                hist=np.stack([x[4] for x in rows]))
        summary={"batch":batch,"batch_size":a.batch_size,"total_metadata":len(cards),
            "requested":len(selected),"indexed":len(rows),"failed":len(fail),"errors":fail[:10]}
        (out/f"batch_{batch:03d}.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        print(json.dumps(summary,ensure_ascii=False),flush=True)
        totals["indexed"]+=len(rows);totals["failed"]+=len(fail);totals["completed_batches"].append(batch)
        if not rows:raise SystemExit("No images indexed in batch "+str(batch))
    (out/"full_index_summary.json").write_text(json.dumps(totals,ensure_ascii=False,indent=2))
    print(json.dumps(totals,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
