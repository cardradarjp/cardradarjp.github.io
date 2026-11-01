#!/usr/bin/env python3
"""Experimental ORB reranking of visual candidates, independent of OCR.
Reports keypoint match evidence; does NOT assert identification accuracy.
"""
import csv,io,json,tarfile,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import cv2,numpy as np
base=Path("matching-test")
with (base/"results/candidates.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
byquery={}
for r in rows:byquery.setdefault(r["query"],[]).append(r)
req=urllib.request.Request("https://codeload.github.com/type-null/PTCG-database/tar.gz/refs/heads/main",headers={"User-Agent":"CardRadar research"})
with urllib.request.urlopen(req,timeout=90) as f:archive=f.read()
urls={}
with tarfile.open(fileobj=io.BytesIO(archive),mode="r:gz") as tar:
 for m in tar:
  if m.isfile() and "/data_jp/" in m.name and m.name.endswith(".json"):
   try:
    d=json.load(tar.extractfile(m))
    if d.get("img"):urls[m.name]=d["img"]
   except Exception:pass
orb=cv2.ORB_create(nfeatures=600,fastThreshold=8)
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
def desc(im):
 gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
 gray=cv2.resize(gray,(256,256),interpolation=cv2.INTER_CUBIC)
 return orb.detectAndCompute(gray,None)[1]
def compare(qd,ref):
 if qd is None or ref is None:return 0,0
 try:
  pairs=bf.knnMatch(qd,ref,k=2)
  good=[a for pair in pairs if len(pair)==2 for a,b in [pair] if a.distance<.75*b.distance]
  return len(good),round(len(good)/max(1,len(qd)),4)
 except cv2.error:return 0,0
# Fetch each distinct candidate once; cap per-query to control requests.
selected={}
for q,group in byquery.items():
 for row in group[:30]:
  if row["reference"] in urls:selected[row["reference"]]=urls[row["reference"]]
def fetch(item):
 key,url=item
 try:
  request=urllib.request.Request(url,headers={"User-Agent":"CardRadar research"})
  with urllib.request.urlopen(request,timeout=25) as f:data=f.read(3000000)
  im=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
  if im is None:return key,None
  h,w=im.shape[:2]
  return key,desc(im[int(h*.10):int(h*.65),int(w*.10):int(w*.90)])
 except Exception:return key,None
refs={}
with ThreadPoolExecutor(max_workers=8) as pool:
 for future in as_completed([pool.submit(fetch,item) for item in selected.items()]):
  k,v=future.result();refs[k]=v
results=[]
for q,group in byquery.items():
 im=cv2.imread(str(base/"queries"/q))
 if im is None:continue
 qd=desc(im)
 local=[]
 for row in group[:30]:
  count,ratio=compare(qd,refs.get(row["reference"]))
  r=dict(row);r["orb_good_matches"]=count;r["orb_match_ratio"]=ratio
  r["orb_available"]=refs.get(row["reference"]) is not None
  local.append(r)
 local.sort(key=lambda r:(r["orb_good_matches"],float(r["similarity"])),reverse=True)
 for rank,r in enumerate(local,1):r["orb_rank"]=rank;results.append(r)
out=base/"results/orb_candidates.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 writer=csv.DictWriter(f,fieldnames=list(results[0]) if results else ["query"])
 writer.writeheader();writer.writerows(results)
print(json.dumps({"queries":len(byquery),"reference_images_attempted":len(selected),"reference_descriptors_available":sum(x is not None for x in refs.values()),"results":len(results),"accuracy":"NOT_MEASURED"},ensure_ascii=False),flush=True)
