#!/usr/bin/env python3
"""Download a bounded sample of reference cards for a reproducible image-match trial.
No reference image files are committed or included in artifacts.
"""
import argparse,csv,json,time,urllib.request
from pathlib import Path
import cv2,numpy as np

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (CardRadar research trial)"})
    with urllib.request.urlopen(req,timeout=25) as response:return response.read()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--set",default="20th",help="PTCG-database set directory")
    p.add_argument("--limit",type=int,default=50)
    a=p.parse_args()
    if not (1<=a.limit<=300):raise SystemExit("limit must be 1..300")
    base="https://api.github.com/repos/type-null/PTCG-database/contents/data_jp/"+a.set
    items=json.loads(get(base))
    files=[x for x in items if x.get("name","").endswith(".json") and x.get("download_url")]
    out=Path("matching-test/references");out.mkdir(parents=True,exist_ok=True)
    rows=[];failures=[]
    for item in files[:a.limit]:
        try:
            info=json.loads(get(item["download_url"]))
            url=info.get("img")
            if not url:continue
            body=get(url)
            img=cv2.imdecode(np.frombuffer(body,dtype=np.uint8),cv2.IMREAD_COLOR)
            if img is None:raise ValueError("image decode failed")
            filename=item["name"].removesuffix(".json")+".jpg"
            (out/filename).write_bytes(body)
            rows.append({"filename":filename,"card_name":info.get("name",""),"card_number":info.get("jp_id",""),"source_url":url})
        except Exception as exc:
            failures.append({"file":item["name"],"error":str(exc)[:160]})
    with open("matching-test/references.csv","w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["filename","card_name","card_number","source_url"]);writer.writeheader();writer.writerows(rows)
    result={"set":a.set,"requested":min(a.limit,len(files)),"downloaded":len(rows),"failures":failures[:10],"note":"Sample only, not full database or measured identification accuracy"}
    Path("matching-test/results").mkdir(parents=True,exist_ok=True)
    Path("matching-test/results/reference_batch.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if not rows:raise SystemExit("No reference images downloaded")

if __name__=="__main__":main()
