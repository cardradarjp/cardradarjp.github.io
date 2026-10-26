#!/usr/bin/env python3
"""Check whether GitHub Actions can fetch and decode one reference card image."""
import json
import urllib.request
from pathlib import Path
import cv2
import numpy as np

CARD_JSON="https://raw.githubusercontent.com/type-null/PTCG-database/main/data_jp/20th/31651.json"
OUT=Path("matching-test/results")
OUT.mkdir(parents=True,exist_ok=True)
result={"source":CARD_JSON,"download_ok":False,"opencv_decode_ok":False}
try:
    req=urllib.request.Request(CARD_JSON,headers={"User-Agent":"CardRadar-image-matching-test/0.1"})
    with urllib.request.urlopen(req,timeout=25) as response:
        record=json.load(response)
    result.update({"card_name":record.get("name"),"card_number":record.get("number"),"image_url":record["img"]})
    req=urllib.request.Request(record["img"],headers={"User-Agent":"Mozilla/5.0 (compatible; CardRadar-research/0.1)"})
    with urllib.request.urlopen(req,timeout=25) as response:
        body=response.read(8*1024*1024)
        content_type=response.headers.get("Content-Type","")
    result["content_type"]=content_type
    result["download_bytes"]=len(body)
    result["download_ok"]=content_type.startswith("image/") and len(body)>1000
    image=cv2.imdecode(np.frombuffer(body,dtype=np.uint8),cv2.IMREAD_COLOR)
    result["opencv_decode_ok"]=image is not None
    if image is not None:
        result["image_size"]=[int(image.shape[1]),int(image.shape[0])]
        # Do not redistribute source image in public repository or CI artifacts.
except Exception as exc:
    result["error"]=f"{type(exc).__name__}: {exc}"
(OUT/"reference_download_check.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False))
if not result["opencv_decode_ok"]:
    raise SystemExit(1)
