#!/usr/bin/env python3
"""Rank cropped queries against all locally available feature-index shards."""
import csv,html,json
from pathlib import Path
import cv2,numpy as np
from test_matching import signature
base=Path("matching-test")
files=sorted((base/"feature-index").glob("batch_*.npz"))
queries=sorted((base/"queries").glob("*.png"))
if not files or not queries:raise SystemExit("Missing indexed shards or queries")
refs=[]
for f in files:
    with np.load(f) as d:
        for i in range(len(d["ids"])):
            refs.append((str(d["ids"][i]),str(d["names"][i]),str(d["numbers"][i]),d["bits"][i],d["hist"][i]))
rows=[]
for q in queries:
    bits,hist=signature(q);h=hist.flatten()
    scored=[]
    for rid,name,number,rb,rh in refs:
        hs=1.0-np.count_nonzero(bits!=rb)/bits.size
        cs=max(0.,min(1.,(float(cv2.compareHist(h.astype(np.float32),rh.astype(np.float32),cv2.HISTCMP_CORREL))+1)/2))
        scored.append((round(.65*hs+.35*cs,4),rid,name,number))
    for rank,(s,rid,name,number) in enumerate(sorted(scored,reverse=True)[:10],1):
        rows.append({"query":q.name,"rank":rank,"reference":rid,"similarity":s,"card_name":name,"card_number":number,"verified":"NO"})
out=base/"results";out.mkdir(exist_ok=True)
fields=list(rows[0])
with (out/"candidates.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
summary={"queries":len(queries),"references":len(refs),"candidate_rows":len(rows),"shards":len(files),"accuracy":"NOT_MEASURED"}
(out/"index_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
