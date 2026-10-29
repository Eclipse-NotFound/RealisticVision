"""Keep classic's installed render/cache behavior; adopt only current changes."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=OUT/'candidates/grid_refresh/src'
dest=OUT/'candidates/grid_current/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
s=s.replace('rec.inputRevision=int(rec.inputRevision)+1;','if(this.cfgMode=="current")rec.inputRevision=int(rec.inputRevision)+1;')
s=s.replace('record.inputRevision!==raster.inputRevision ||', '(this.cfgMode=="current" && record.inputRevision!==raster.inputRevision) ||')
old='''            if(visual.mask===shape)visual.mask=null;
            record.inputRevision=raster.inputRevision;'''
new='''            if(this.cfgMode=="current"){
               if(visual.mask===shape)visual.mask=null;
               record.inputRevision=raster.inputRevision;
            }'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
