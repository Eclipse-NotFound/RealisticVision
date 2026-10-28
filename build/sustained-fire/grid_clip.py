"""D54: preserve five-pixel bitmap boundaries while cropping empty support."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/sustained-fire-output/candidates/tight/src'
OUT=MOD/'build/sustained-fire-output/candidates/grid/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
for before,after in [('Math.floor(bounds.left)-2','(Math.floor(bounds.left/drawScale)-2)*drawScale'),('Math.floor(bounds.top)-2','(Math.floor(bounds.top/drawScale)-2)*drawScale'),('Math.ceil(bounds.right)+2','(Math.ceil(bounds.right/drawScale)+2)*drawScale'),('Math.ceil(bounds.bottom)+2','(Math.ceil(bounds.bottom/drawScale)+2)*drawScale')]:
 assert s.count(before)==1;s=s.replace(before,after)
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
