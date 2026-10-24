"""Separate local-filter and shared-field rasters even for identical bounds."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shared-mask-output'
for base,name in [('shared','shared-v2'),('reference','reference-v2')]:
 source=OUT/'candidates'/base/'src';target=OUT/'candidates'/name/'src';assert not target.exists()
 pins=json.loads((source.parent/'manifest.json').read_text());assert all(hashlib.sha256((source/p).read_bytes()).hexdigest()==h for p,h in pins.items())
 shutil.copytree(source,target);path=target/'RealisticVisionMod.as';s=path.read_text(encoding='utf-8')
 old='''         var key:String=x0+","+y0+","+x1+","+y1;
         var raster:Object=this.worldMasks[key];'''
 new='''         var shareAllowed:Boolean=!this.worldVisualHasFilters(visual);
         // Filtered and unfiltered overlapping visuals must not mutate one
         // another's retained bitmap through an identical bounds cache key.
         var key:String=x0+","+y0+","+x1+","+y1+(shareAllowed?",shared":",local");
         var raster:Object=this.worldMasks[key];'''
 assert s.count(old)==1;s=s.replace(old,new)
 old='''         // Filter support can extend outside getBounds: preserve local masks.
         var shareAllowed:Boolean=!this.worldVisualHasFilters(visual);
'''
 assert s.count(old)==1;s=s.replace(old,'')
 path.write_text(s,encoding='utf-8',newline='\n')
 (target.parent/'manifest.json').write_text(json.dumps({p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*.as')},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Separated raster keys in new variants; old failed inputs retained')
