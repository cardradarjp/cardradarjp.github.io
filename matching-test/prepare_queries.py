#!/usr/bin/env python3
"""Extract the 5x5 cards by detecting yellow price banners as row anchors."""
import argparse,io,urllib.request
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
p=argparse.ArgumentParser()
p.add_argument("--image-url",required=True)
a=p.parse_args()
if not a.image_url.startswith(("https://github.com/user-attachments/assets/","https://raw.githubusercontent.com/")):
    raise SystemExit("Only GitHub-hosted image URLs are accepted")
req=urllib.request.Request(a.image_url,headers={"User-Agent":"CardRadar research/0.1"})
with urllib.request.urlopen(req,timeout=30) as response:data=response.read(10_000_001)
if len(data)>10_000_000:raise SystemExit("Image exceeds 10MB")
im=Image.open(io.BytesIO(data)).convert("RGB")
if im.width>400:im=im.crop((0,0,round(im.width/4),round(im.height/4)))
if not (230<=im.width<=400 and 330<=im.height<=560):
    raise SystemExit(f"Unexpected shop-sheet dimensions: {im.size}")
# Detect horizontal yellow price bands on the source resolution, not on an enlarged crop.
arr=np.asarray(im)
hsv=cv2.cvtColor(arr,cv2.COLOR_RGB2HSV)
yellow=cv2.inRange(hsv,np.array((15,100,110)),np.array((40,255,255)))
coverage=np.count_nonzero(yellow,axis=1)/im.width
active=coverage>.33
runs=[];start=None
for y,on in enumerate(active):
    if on and start is None:start=y
    if start is not None and (not on or y==im.height-1):
        end=y if not on else y+1
        if end-start>=5:runs.append((start,end))
        start=None
if len(runs)!=5:
    raise SystemExit(f"Expected 5 yellow price bands, found {runs}; review source before matching")
tops=[x[0] for x in runs]
spacings=np.diff(tops)
if np.max(spacings)-np.min(spacings)>5:
    raise SystemExit(f"Inconsistent price row spacing: {tops}")
row_pitch=int(round(float(np.median(spacings))))
# Each banner spans a card column; use its regular five-column grid.
left=int(round(im.width*.036))
right=int(round(im.width*.969))
pitch=(right-left)/5
out=Path("matching-test/queries");out.mkdir(parents=True,exist_ok=True)
audit=im.copy();draw=ImageDraw.Draw(audit)
for row,price_y in enumerate(tops):
    card_top=max(0,price_y-row_pitch+1) if row==0 else runs[row-1][1]+2
    if card_top>=price_y:raise SystemExit(f'Invalid card region at row {row+1}')
    # A card starts AFTER the previous row's price band and ends BEFORE its own price band.
    for col in range(5):
        x0=int(round(left+col*pitch));x1=int(round(left+(col+1)*pitch))
        crop=im.crop((x0,card_top,x1,price_y))
        crop.resize((188,172),Image.Resampling.LANCZOS).save(out/f"card_{row+1}_{col+1}.png")
        draw.rectangle((x0,card_top,x1-1,price_y-1),outline="#00ff66",width=1)
audit.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(out/"crop_audit.png")
print(f"Detected yellow price bands: {runs}; card row pitch={row_pitch}; prepared 25 crops",flush=True)
