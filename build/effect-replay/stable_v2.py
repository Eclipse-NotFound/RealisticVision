"""Preserve uniform-support early exits; freeze a separate candidate."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
src=MOD/'build/effect-replay-output/candidates/stable/src'
dst=src.parents[1]/'stable-v2/src'
assert not dst.exists()
shutil.copytree(src,dst)
p=dst/'RealisticVisionMod.as';s=p.read_text()
old='if(raster.coverageFov!==this.fovVersion || raster.coverageBb!==coverage)'
assert s.count(old)==1
s=s.replace(old,'if(raster.coverageFov!==this.fovVersion || (raster.maskValid!==false && raster.coverageBb!==coverage))')
p.write_text(s,encoding='utf-8',newline='\n')
