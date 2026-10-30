#!/usr/bin/env python3
"""Prepare 25 query crops from a manually supplied public image URL."""
import argparse,io,urllib.request
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser()
p.add_argument("--image-url",required=True)
a=p.parse_args()
if not a.image_url.startswith(("https://github.com/user-attachments/assets/","https://raw.githubusercontent.com/")):
    raise SystemExit("Only GitHub-hosted image URLs are accepted")
req=urllib.request.Request(a.image_url,headers={"User-Agent":"CardRadar research/0.1"})
with urllib.request.urlopen(req,timeout=30) as response:
    data=response.read(10_000_001)
if len(data)>10_000_000:raise SystemExit("Image exceeds 10MB")
im=Image.open(io.BytesIO(data)).convert("RGB")
if im.width>400: 
    # The source composite has 4 columns of shop sheets.
    im=im.crop((0,0,round(im.width/4),round(im.height/4)))
if not (230<=im.width<=400 and 330<=im.height<=560):
    raise SystemExit(f"Unexpected shop-sheet dimensions: {im.size}; expected about 271x384")
im=im.resize((271,384),Image.Resampling.LANCZOS)
out=Path("matching-test/queries");out.mkdir(parents=True,exist_ok=True)
for row in range(5):
    for col in range(5):
        x0=9+col*51;y0=53+row*61
        im.crop((x0,y0,x0+47,y0+43)).resize((188,172)).save(out/f"card_{row+1}_{col+1}.png")
print("Prepared 25 query crops from",im.size)
