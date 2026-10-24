"""Reuse coverage only when the existing full mask-input equality check hits."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=MOD/'build/mask-lifecycle-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
def patch(source):
 old='if(maskDelta is uint && uint(maskDelta) == 0) return;'
 assert source.count(old)==1
 return source.replace(old,'''if(maskDelta is uint && uint(maskDelta) == 0)
            {
               // The complete raw field, bounds and filter are unchanged, so
               // its already computed blurred coverage is unchanged as well.
               if(rec.worldRaster === true && rec.coverageFov !== undefined)
                  rec.coverageFov=this.fovVersion;
               return;
            }''')
if __name__=='__main__':
 pins=json.loads((OUT/'inputs.json').read_text())['source']
 assert all(hashlib.sha256((BASE/p).read_bytes()).hexdigest()==h for p,h in pins.items())
 dest=OUT/'candidates/carry/src';assert not dest.exists();shutil.copytree(BASE,dest)
 p=dest/'RealisticVisionMod.as';p.write_text(patch(p.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
 print('Prepared exact-input coverage reuse; no rendering changes')
