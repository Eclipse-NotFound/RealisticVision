"""Isolate cache invalidation when the cropped mask geometry changes."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
dest=OUT/'candidates/raster-rebind/src';assert not dest.exists();shutil.copytree(OUT/'candidates/raster-crop/src',dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark || clipChanged)
         {
            if(drawDark)shape.graphics.clear();'''
new='''         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark || clipChanged)
         {
            if(visual.mask===shape)visual.mask=null;
            if(drawDark)shape.graphics.clear();'''
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
