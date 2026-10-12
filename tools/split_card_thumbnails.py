from pathlib import Path
import re
from PIL import Image

SPRITE = Path("assets/review/card-sprite.jpg")
OUT = Path("assets/review/card-crops")
OUT.mkdir(parents=True, exist_ok=True)

img = Image.open(SPRITE).convert("RGB")
cell_w, cell_h, cols = 56, 78, 10
expected = (560, 1092)
if img.size != expected:
    raise SystemExit(f"Unexpected sprite size: {img.size}, expected {expected}")

numbers = list(range(113, 236)) + [237] + list(range(238, 248))
if len(numbers) != 134:
    raise SystemExit("Unexpected number mapping")

for i, no in enumerate(numbers):
    x = (i % cols) * cell_w
    y = (i // cols) * cell_h
    crop = img.crop((x, y, x + cell_w, y + cell_h))
    crop.save(OUT / f"{no}.webp", "WEBP", quality=78, method=6)

css = """.photo{width:56px;height:78px;display:block;flex:none;border-radius:9px;border:1px solid var(--line);background:var(--chip);object-fit:cover;box-shadow:0 1px 4px rgba(0,0,0,.10)}"""

photo_js = """function photoHtml(z){
  const n=+z[0];
  if(!((n>=113&&n<=235)||(n>=237&&n<=247)))return '';
  return '<div class="photoWrap"><img class="photo" loading="lazy" decoding="async" src="/assets/review/card-crops/'+n+'.webp?v=20261012-1800" alt="'+x(z[1])+' 実物写真"><div class="photoLabel">実物</div></div>';
}"""

for name in ("buyback-list.html", "buyback-list-clean.html"):
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    s, n1 = re.subn(r"\.photo\{[^}]*\}", css, s, count=1)
    s, n2 = re.subn(
        r"function photoIndex\(z\)\{.*?\n\}\nfunction photoHtml\(z\)\{.*?\n\}",
        photo_js,
        s,
        count=1,
        flags=re.S,
    )
    s = re.sub(r"buyback-current\.json\?v=[0-9-]+", "buyback-current.json?v=20261012-1800", s)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"Could not update {name}: css={n1}, js={n2}")
    p.write_text(s, encoding="utf-8")

print(f"Created {len(numbers)} independent thumbnails.")
