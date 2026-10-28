"""Test whether retained graphics caches miss bitmap content invalidation."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
src=MOD/'build/effect-replay-output/candidates/stable-v2/src'
dst=src.parents[1]/'stable-v3/src';assert not dst.exists()
shutil.copytree(src,dst)
p=dst/'RealisticVisionMod.as';s=p.read_text()
needle='         // 位图填充绘制进矢量 Shape'
assert s.count(needle)==1
s=s.replace(needle,'         if(rec.worldRaster)rec.contentRevision=int(rec.contentRevision)+1;\n'+needle)
s=s.replace('if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark)','if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==drawDark || record.contentRevision!==raster.contentRevision)')
s=s.replace('record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;','record.raster=raster;record.revision=raster.maskRevision;record.dark=drawDark;record.contentRevision=raster.contentRevision;')
p.write_text(s,encoding='utf-8',newline='\n')
