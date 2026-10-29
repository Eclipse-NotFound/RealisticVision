from pathlib import Path
import shutil
M=Path(__file__).resolve().parents[2];O=M/'build/enemy-combat-output';D=O/'candidates/unit_clip_refresh/src'
assert not D.exists();shutil.copytree(O/'candidates/unit_clip_v2/src',D)
p=D/'RealisticVisionMod.as';s=p.read_text()
old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || changed){
            shape.graphics.clear();'''
new='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.inputRevision!=raster.inputRevision || changed){
            if(visual.mask===shape)visual.mask=null;
            record.inputRevision=raster.inputRevision;
            shape.graphics.clear();'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
