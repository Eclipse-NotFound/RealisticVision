"""Retest the exact source lattice after independently fixing stale bindings."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
BASE=OUT/'candidates/refresh/src'
dest=OUT/'candidates/grid_refresh/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
ref=(MOD/'build/sustained-fire-output/candidates/grid/src/RealisticVisionMod.as').read_text()
start='         var shape:Shape=record.shape as Shape;\n'
begin=s.index(start,s.index('private function applyWorldVisual('));end=s.index('         if(shape.parent!==visual.parent)',begin)
a=ref.index(start,ref.index('private function applyWorldVisual('));b=ref.index('         if(shape.parent!==visual.parent)',a)
part=ref[a:b].replace('// D54_TRAILING','// D56_REFRESH: crop uses the original sample lattice')
part=part.replace('record.raster!==raster || record.revision!=raster.maskRevision', 'record.raster!==raster || record.inputRevision!==raster.inputRevision || record.revision!=raster.maskRevision')
point='''         {
            if(drawDark)shape.graphics.clear();'''
assert part.count(point)==1
part=part.replace(point,'''         {
            if(visual.mask===shape)visual.mask=null;
            record.inputRevision=raster.inputRevision;
            if(drawDark)shape.graphics.clear();''')
s=s[:begin]+part+s[end:];p.write_text(s,encoding='utf-8',newline='\n')
