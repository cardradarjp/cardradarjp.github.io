#!/usr/bin/env python3
"""Fast vectorized matching across cached reference feature shards."""
import csv,json,time
from pathlib import Path
import numpy as np
from partial_features import features
import cv2
base=Path("matching-test")
files=sorted((base/"feature-index").glob("batch_*.npz"))
queries=sorted((base/"queries").glob("*.png"))
if not files or not queries:raise SystemExit("Missing indexed shards or queries; check cache restore")
ids=[];names=[];numbers=[];bits=[];hists=[]
for f in files:
    with np.load(f) as d:
        ids.extend(d["ids"].tolist());names.extend(d["names"].tolist())
        numbers.extend(d["numbers"].tolist())
        bits.append(d["bits"]);hists.append(d["hist"])
B=np.concatenate(bits).astype(bool)
H=np.concatenate(hists).astype(np.float32)
# OpenCV HISTCMP_CORREL computes centered cosine similarity.
H=H-H.mean(axis=2,keepdims=True)
H/=np.maximum(np.linalg.norm(H,axis=2,keepdims=True),1e-10)
rows=[]
for q in queries:
    img=cv2.imread(str(q))
    qb,qh=features(img)
    qb=np.asarray(qb,dtype=bool)
    qh=np.asarray(qh,dtype=np.float32)
    qh=qh-qh.mean(axis=1,keepdims=True)
    qh/=np.maximum(np.linalg.norm(qh,axis=1,keepdims=True),1e-10)
    # Compare matching visible artwork regions, not hidden lower card.
    hash_score=1.0-np.count_nonzero(B!=qb[None,:,:],axis=2)/B.shape[2]
    color_score=np.clip((np.einsum("nrd,rd->nr",H,qh)+1.0)/2.0,0.0,1.0)
    scores=np.max(.65*hash_score+.35*color_score,axis=1)
    best=np.argsort(scores)[-10:][::-1]
    for rank,i in enumerate(best,1):
        rows.append(dict(query=q.name,rank=rank,reference=ids[i],similarity=round(float(scores[i]),4),
            card_name=names[i],card_number=numbers[i],verified="NO"))
out=base/"results";out.mkdir(exist_ok=True)
fields=["query","rank","reference","similarity","card_name","card_number","verified"]
with (out/"candidates.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
summary={"queries":len(queries),"references":len(ids),"candidate_rows":len(rows),"shards":len(files),"accuracy":"NOT_MEASURED"}
(out/"index_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False),flush=True)
