"""D53: skip allocating/copying an already transparent current support region."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/combat-render-output/production-final2/src'
OUT=MOD/'build/solo-fire-output'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
dest=OUT/'candidates/early-dark/src';assert not dest.exists()
shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
needle='''         var bd:BitmapData = rec.m2d as BitmapData;   // 子格二值场'''
replacement='''         // The source already contains the exact binary current sight field.
         // Prove the entire old support rectangle transparent before allocating
         // or copying a private raster. Mixed regions retain the original path.
         if(rec.worldRaster===true && this.cfgMode=="current" && this.currentSight!=null)
         {
            this.worldSupportRect.setTo(FOG_PAD+x0*MASK_SUB,FOG_PAD+y0*MASK_SUB,totx,toty);
            if(!this.currentSight.hitTest(this.fogPoint,1,this.worldSupportRect))
            {
               rec.fullyDark=true;rec.fullyLit=false;rec.coverageFov=this.fovVersion;
               rec.maskValid=false;
               // D53_EARLY_DARK
               return;
            }
         }
'''+needle
assert s.count(needle)==1;s=s.replace(needle,replacement)
p.write_text(s,encoding='utf-8',newline='\n')
(dest.parent/'manifest.json').write_text(json.dumps({p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*.as')},indent=2)+'\n',encoding='utf-8')
print('Prepared early-dark, exact D44 + one allocation shortcut; not installed')
