#!/usr/bin/env python3
"""OCR card names from the always-visible top edge, then rerank visual candidates.
Research only; never treat OCR guesses as verified identities.
"""
import csv,json,re,unicodedata
from pathlib import Path
import cv2,numpy as np
from difflib import SequenceMatcher
try:
 import pytesseract
except ImportError:
 raise SystemExit("Install pytesseract")
base=Path("matching-test")
source=base/"results/candidates.csv"
if not source.exists():raise SystemExit("Run image matcher first")
with source.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
byquery={}
for row in rows:byquery.setdefault(row["query"],[]).append(row)
def norm(s):
 return re.sub(r"[^0-9a-zA-Zぁ-んァ-ヶ一-龥]+","",unicodedata.normalize("NFKC",s)).lower()
ocr_rows=[]
for q,group in byquery.items():
 img=cv2.imread(str(base/"queries"/q))
 if img is None:continue
 # Crop the uppermost name line, preserving the full top of the card.
 strip=img[:max(12,round(img.shape[0]*.23)),:]
 gray=cv2.cvtColor(strip,cv2.COLOR_BGR2GRAY)
 enlarged=cv2.resize(gray,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
 variants=(enlarged,cv2.threshold(enlarged,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1])
 readings=[]
 for v in variants:
  for mode in (6,7):
   readings.append(pytesseract.image_to_string(v,lang="jpn+eng",config=f"--psm {mode}").strip())
 readings=[r for r in readings if norm(r)]
 # Rank only candidates from visual top-10; a weak OCR match cannot identify arbitrary cards.
 for row in group:
  name=norm(row["card_name"])
  ocr_sim=max((SequenceMatcher(None,norm(t),name).ratio() for t in readings),default=0)
  visual=float(row["similarity"])
  row["ocr_score"]=round(ocr_sim,4)
  row["combined_score"]=round(.5*visual+.5*ocr_sim,4)
  row["ocr_readings"]=" | ".join(readings)
 group.sort(key=lambda x:x["combined_score"],reverse=True)
 for rank,row in enumerate(group,1):
  row["rank"]=rank
  ocr_rows.append(row)
out=base/"results/ocr_candidates.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(ocr_rows[0]) if ocr_rows else ["query"]);w.writeheader();w.writerows(ocr_rows)
print(json.dumps({"queries":len(byquery),"candidates":len(ocr_rows),"output":str(out),"verified_accuracy":"NOT_MEASURED"},ensure_ascii=False))
