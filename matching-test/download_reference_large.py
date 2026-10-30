#!/usr/bin/env python3
"""Fetch card metadata from multiple Japanese PTCG-database sets and build reference images.
Downloaded images are ephemeral CI inputs, never uploaded as artifacts.
"""
import argparse,csv,json,os,random,time,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import cv2,numpy as np

HEADERS={"User-Agent":"CardRadar research image matching (GitHub Actions)","Accept":"application/vnd.github+json"}
if os.environ.get("GITHUB_TOKEN"): HEADERS["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
def get(url,retries=2):
    for attempt in range(retries+1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=22) as r:return r.read()
        except Exception:
            if attempt==retries:raise
            time.sleep(1.5*(attempt+1))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--limit",type=int,default=1200)
    p.add_argument("--workers",type=int,default=8)
    a=p.parse_args()
    if not 1<=a.limit<=4000:raise SystemExit("limit 1..4000")
    api="https://api.github.com/repos/type-null/PTCG-database/contents/data_jp"
    sets=[x for x in json.loads(get(api)) if x["type"]=="dir"]
    # Newest era folders are not necessarily in chronological order; prioritize modern sets.
    sets.sort(key=lambda x:x["name"],reverse=True)
    entries=[]
    for folder in sets:
        if len(entries)>=a.limit:break
        try:
            items=json.loads(get(folder["url"]))
            entries.extend(x for x in items if x.get("name","").endswith(".json") and x.get("download_url"))
        except Exception as e:print("SET_ERROR",folder["name"],str(e)[:100])
    entries=entries[:a.limit]
    out=Path("matching-test/references");out.mkdir(parents=True,exist_ok=True)
    def fetch(entry):
        try:
            data=json.loads(get(entry["download_url"]))
            url=data.get("img")
            if not url:return None,"no image URL"
            raw=get(url,retries=1)
            img=cv2.imdecode(np.frombuffer(raw,dtype=np.uint8),cv2.IMREAD_COLOR)
            if img is None:return None,"invalid image"
            filename=str(data.get("jp_id",entry["name"].replace(".json","")))+".jpg"
            (out/filename).write_bytes(raw)
            return {"filename":filename,"card_name":data.get("name",""),"card_number":data.get("jp_id",""),"source_url":url},None
        except Exception as e:return None,str(e)[:120]
    rows=[];fail=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(fetch,item):item for item in entries}
        for future in as_completed(futures):
            row,error=future.result()
            if row:rows.append(row)
            else:fail.append({"file":futures[future]["name"],"error":error})
    rows.sort(key=lambda x:x["filename"])
    with open("matching-test/references.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["filename","card_name","card_number","source_url"]);w.writeheader();w.writerows(rows)
    Path("matching-test/results").mkdir(parents=True,exist_ok=True)
    summary={"requested":a.limit,"metadata_candidates":len(entries),"downloaded":len(rows),"failed":len(fail),"sample_errors":fail[:15],"sets_considered":len(sets)}
    Path("matching-test/results/reference_batch.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))
    if len(rows)<50:raise SystemExit("Too few reference images downloaded")
if __name__=="__main__":main()
