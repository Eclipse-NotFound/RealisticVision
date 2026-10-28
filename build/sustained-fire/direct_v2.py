"""D54: test Bitmap sampling without implicit pixel snapping."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/sustained-fire-output/candidates/direct-cache/src'
OUT=MOD/'build/sustained-fire-output/candidates/direct-v2/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
old='var bitmap:Bitmap=shape as Bitmap;'
new='var bitmap:Bitmap=shape as Bitmap;bitmap.smoothing=true;bitmap.pixelSnapping="never";'
assert s.count(old)==1
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s.replace(old,new),encoding='utf-8',newline='\n')
