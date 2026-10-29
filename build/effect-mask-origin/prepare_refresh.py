"""D56: independently verify invalidation against fresh original masks."""
from pathlib import Path
import hashlib,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
dest=OUT/'candidates/refresh/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''         // 位图填充绘制进矢量 Shape'''
assert s.count(old)==1;s=s.replace(old,'         rec.inputRevision=int(rec.inputRevision)+1;\n'+old)
old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)
         {
            if(drawDark)shape.graphics.clear();'''
new='''         if(record.raster!==raster || record.inputRevision!==raster.inputRevision || record.revision!=raster.maskRevision || record.dark!==drawDark)
         {
            // D56_REFRESH: invalidate the target's cached mask association.
            if(visual.mask===shape)visual.mask=null;
            record.inputRevision=raster.inputRevision;
            if(drawDark)shape.graphics.clear();'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
