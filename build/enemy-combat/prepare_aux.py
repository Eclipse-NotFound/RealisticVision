"""Remove only an unattached duplicate Shape from independent effect rasters."""
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'enemy-combat-output'
target=OUT/'candidates/world_aux/src'
assert not target.exists()
shutil.copytree(OUT/'baseline/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text()
assert s.count('if(s3 == null)')==1
s=s.replace('if(s3 == null)', 'if(s3 == null && rec.worldRaster !== true)')
old='''         s3.graphics.clear();
         s3.graphics.copyFrom(g);'''
new='''         // Independent effect rasters never attach the HP-bar Shape.
         // Keep its duplicate graphics only for unit body/bar records.
         if(s3 != null){s3.graphics.clear();s3.graphics.copyFrom(g);}
         else { /* D57_AUX_OMITTED */ }'''
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
# Reuse the strict continuous two-tree visual test, without the rejected alpha
# bounds variant or its changed applyWorldVisual signature.
t=(HERE/'alpha_check.py').read_text()
start=t.index(" t=t.replace('b.applyWorldVisual(bb[i])','b.applyWorldVisual(bb[i],true)')",t.index(" if '--stable-v4'"))
end=t.index(" (folder/'EffectLoadChecks.as').write_text",start)
t=t[:start]+''' p=src/'RealisticVisionMod.as';code=p.read_text();code=code.replace('public var trailingHits:int=0;','public var trailingHits:int=0;public var auxHits:int=0;').replace('/* D57_AUX_OMITTED */','auxHits++;');p.write_text(code,encoding='utf-8')
 t=t.replace('trace("LOAD COMPLETE passed="+passed);','check(b.auxHits>100,"unused effect shape omitted");for each(var raster:Object in b.worldMasks)check(raster.m3==null,"effect raster has no unused HP shape");trace("AUX HITS "+b.auxHits);trace("LOAD COMPLETE passed="+passed);')
''' +t[end:]
(HERE/'aux_check.py').write_text(t,encoding='utf-8')
print('Created world_aux, baseline rendering and sampling unchanged')
