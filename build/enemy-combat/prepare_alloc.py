from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'enemy-combat-output'
target=OUT/'candidates/effect_alloc/src';assert not target.exists()
shutil.copytree(OUT/'candidates/world_aux/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text()
old='''            var pixels:Vector.<uint>=BitmapData(raster.m2e).getVector(new Rectangle(rx,ry,(x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB));
            var lit:Boolean=true;
            for each(var pixel:uint in pixels)if((pixel>>>24)!=255){lit=false;break;}'''
new='''            // A non-opaque first sample already disproves full visibility.
            // Avoid allocating the remaining samples in that exact case.
            var lit:Boolean=(BitmapData(raster.m2e).getPixel32(rx,ry)>>>24)==255;
            if(lit){
               var pixels:Vector.<uint>=BitmapData(raster.m2e).getVector(new Rectangle(rx,ry,(x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB));
               for each(var pixel:uint in pixels)if((pixel>>>24)!=255){lit=false;break;}
            }else { /* D57_VECTOR_SKIPPED */ }'''
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
t=(HERE/'aux_check.py').read_text()
t=t.replace('public var auxHits:int=0;', 'public var auxHits:int=0;public var vectorHits:int=0;')
t=t.replace(".replace('/* D57_AUX_OMITTED */','auxHits++;')", ".replace('/* D57_AUX_OMITTED */','auxHits++;').replace('/* D57_VECTOR_SKIPPED */','vectorHits++;')")
t=t.replace('trace("AUX HITS "+b.auxHits);', 'check(b.vectorHits>100,"early alpha rejection exercised");trace("VECTOR HITS "+b.vectorHits);trace("AUX HITS "+b.auxHits);')
(HERE/'alloc_check.py').write_text(t,encoding='utf-8')
print('Created effect_alloc, unchanged visible mask geometry')
