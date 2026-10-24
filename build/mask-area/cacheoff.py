"""Do not maintain a native bitmap cache while an RV-owned empty mask hides it."""
from pathlib import Path
import shutil,hashlib,json
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output'
BASE=MOD/'build/combat-render-output/production-final2/src';dest=OUT/'candidates/cacheoff/src'
pins=json.loads((OUT/'inputs.json').read_text())
assert all(hashlib.sha256((BASE/p).read_bytes()).hexdigest()==sha for p,sha in pins['sources'].items())
assert not dest.exists()
source=(BASE/'RealisticVisionMod.as').read_text(encoding='utf-8')
old='var useCache:Boolean=drawDark?record.cache:true;'
new='''// Empty geometric masks show no pixels. Native cache preference is
         // still restored by releaseWorldVisual when the visual becomes lit.
         var useCache:Boolean=!drawDark;'''
assert source.count(old)==1
shutil.copytree(BASE,dest)
(dest/'RealisticVisionMod.as').write_text(source.replace(old,new),encoding='utf-8',newline='\n')
print('Prepared exact D44 + no cache beneath an empty mask')
