#!/usr/bin/env python3
"""Offline prototype: rank candidate card images; never claim identification is verified."""
import argparse, csv, html, json
from pathlib import Path
import cv2
import numpy as np

def signature(path):
    image=cv2.imread(str(path))
    if image is None: raise ValueError(f"Cannot read image: {path}")
    h,w=image.shape[:2]
    # Prefer central artwork: reduces borders, text, and price overlays.
    crop=image[int(h*.17):int(h*.66),int(w*.12):int(w*.88)]
    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
    gray=cv2.resize(gray,(32,32),interpolation=cv2.INTER_AREA).astype(np.float32)
    dct=cv2.dct(gray)[:8,:8]
    bits=(dct[1:,:]>np.median(dct[1:,:])).ravel()
    hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
    hist=cv2.calcHist([hsv],[0,1],None,[16,8],[0,180,0,256])
    cv2.normalize(hist,hist)
    return bits,hist

def score(a,b):
    hash_similarity=1.0-np.count_nonzero(a[0]!=b[0])/a[0].size
    color_similarity=max(0.,min(1.,float(cv2.compareHist(a[1],b[1],cv2.HISTCMP_CORREL)+1)/2))
    return round(.65*hash_similarity+.35*color_similarity,4)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queries",default="matching-test/queries")
    p.add_argument("--references",default="matching-test/references")
    p.add_argument("--manifest",default="matching-test/references.csv")
    p.add_argument("--output",default="matching-test/results")
    args=p.parse_args()
    query_files=sorted(x for x in Path(args.queries).glob("*") if x.suffix.lower() in (".png",".jpg",".jpeg"))
    reference_files=sorted(x for x in Path(args.references).glob("*") if x.suffix.lower() in (".png",".jpg",".jpeg"))
    if not query_files or not reference_files:
        raise SystemExit("NEED_INPUT: place card crops in queries/ and authorized reference images in references/. No accuracy measured.")
    labels={}
    if Path(args.manifest).exists():
        with open(args.manifest,encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                labels[row["filename"]]=row
    refs=[(r,signature(r)) for r in reference_files]
    rows=[]
    for q in query_files:
        sig=signature(q)
        ranked=sorted(((score(sig,s),r.name) for r,s in refs),reverse=True)[:3]
        for rank,(similarity,filename) in enumerate(ranked,1):
            meta=labels.get(filename,{})
            rows.append(dict(query=q.name,rank=rank,reference=filename,similarity=similarity,
                             card_name=meta.get("card_name",""),card_number=meta.get("card_number",""),
                             verified="NO"))
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    fields=["query","rank","reference","similarity","card_name","card_number","verified"]
    with open(output/"candidates.csv","w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    trs="".join("<tr>"+"".join(f"<td>{html.escape(str(row[k]))}</td>" for k in fields)+"</tr>" for row in rows)
    (output/"index.html").write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Card matching candidates</title><style>body{font:15px system-ui;margin:20px}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:7px}div{overflow-x:auto}</style><h1>Image matching: unverified candidates</h1><p>Similarity is not probability. Accuracy cannot be measured without independently labeled ground truth.</p><div><table><thead><tr>"+"".join(f"<th>{html.escape(k)}</th>" for k in fields)+"</tr></thead><tbody>"+trs+"</tbody></table></div>",encoding="utf-8")
    print(json.dumps({"queries":len(query_files),"references":len(refs),"candidate_rows":len(rows),"accuracy":"NOT_MEASURED"},ensure_ascii=False))

if __name__=="__main__":main()
