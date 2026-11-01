#!/usr/bin/env python3
"""Independent Japanese OCR name search across the entire indexed card database.
OCR is a hypothesis, not a verified identification.
"""
import csv,json,re,unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import cv2,numpy as np,pytesseract
base=Path("matching-test")
source=base/"results/candidates.csv"
if not source.exists():raise SystemExit("Run image matcher first")
with source.open(encoding="utf-8-sig",newline="") as f:visual=list(csv.DictReader(f))
byquery={}
for row in visual:byquery.setdefault(row["query"],[]).append(row)
def norm(s):
 return re.sub(r"[^0-9a-zA-Zぁ-んァ-ヶ一-龥]+","",unicodedata.normalize("NFKC",s)).lower()
# All 24k names, NOT merely the visual top-10.
cards={}
for shard in sorted((base/"feature-index").glob("batch_*.npz")):
 with np.load(shard) as d:
  for key,name,num in zip(d["ids"],d["names"],d["numbers"]):
   cards[str(key)]=(str(name),str(num))
if not cards:raise SystemExit("No reference names found")
output=[];debug=[]
for query,group in sorted(byquery.items()):
 img=cv2.imread(str(base/"queries"/query))
 if img is None:continue
 h,w=img.shape[:2]
 # Card names normally appear at the TOP of a Pokemon card.
 # Also test the lower edge as a diagnostic, never assume it is the name.
 strips={"top":img[:max(12,round(h*.22)),:],
         "lower_diagnostic":img[round(h*.76):,:]}
 readings=[]
 for region,strip in strips.items():
  gray=cv2.cvtColor(strip,cv2.COLOR_BGR2GRAY)
  up=cv2.resize(gray,None,fx=5,fy=5,interpolation=cv2.INTER_CUBIC)
  binary=cv2.threshold(up,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
  for v in (up,binary):
   for psm in (6,7):
    value=pytesseract.image_to_string(v,lang="jpn+eng",config=f"--psm {psm}").strip()
    if norm(value):readings.append((region,value))
 debug.append({"query":query,"ocr_readings":" | ".join(f"{r}:{t}" for r,t in readings)})
 # OCR independently retrieves names from the FULL database.
 # Keep visual candidates too, even if OCR is unreadable.
 ranked=[]
 for key,(name,num) in cards.items():
  n=norm(name)
  score=max((SequenceMatcher(None,norm(t),n).ratio() for region,t in readings if region=="top"),default=0.)
  if score>=.45:ranked.append((score,key,name,num))
 ranked.sort(reverse=True)
 selected={key:(score,name,num,"ocr_full_database") for score,key,name,num in ranked[:30]}
 for v in group:
  key=v["reference"]
  if key not in selected:selected[key]=(0.,v["card_name"],v["card_number"],"visual_top10")
 for key,(ocr_score,name,num,origin) in selected.items():
  v=next((r for r in group if r["reference"]==key),None)
  visual_score=float(v["similarity"]) if v else 0.
  combined=(.65*ocr_score+.35*visual_score) if ocr_score else .35*visual_score
  output.append({"query":query,"reference":key,"card_name":name,"card_number":num,
   "ocr_score":round(ocr_score,4),"visual_score":round(visual_score,4),
   "combined_score":round(combined,4),"source":origin,"verified":"NO"})
out=base/"results";out.mkdir(exist_ok=True)
for name,rows in (("ocr_candidates.csv",output),("ocr_readings.csv",debug)):
 with (out/name).open("w",encoding="utf-8-sig",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ["query"])
  writer.writeheader();writer.writerows(rows)
print(json.dumps({"queries":len(byquery),"database_cards":len(cards),"candidates":len(output),"accuracy":"NOT_MEASURED"},ensure_ascii=False),flush=True)
