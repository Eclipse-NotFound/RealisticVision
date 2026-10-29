"""A bounded diagnostic: explicitly rebuild both native bitmap caches."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
dest=OUT/'candidates/raster-reset/src';assert not dest.exists();shutil.copytree(OUT/'candidates/raster-rebind/src',dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''            if(visual.mask===shape)visual.mask=null;
            if(drawDark)shape.graphics.clear();'''
new='''            if(visual.mask===shape)visual.mask=null;
            if(visual.cacheAsBitmap)visual.cacheAsBitmap=false;
            if(shape.cacheAsBitmap)shape.cacheAsBitmap=false;
            if(drawDark)shape.graphics.clear();'''
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
