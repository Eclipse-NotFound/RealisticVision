"""Second D50 candidate: also reuse the private wall interpolation input."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/classic-inputs-output'
source=OUT/'candidates/raw/src';target=OUT/'candidates/all/src';assert not target.exists();shutil.copytree(source,target)
p=target/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
old='''               this.fogCache.fillRect(region,0xFFFFFFFF);
               this.fogCache.draw(this.wallRaw,this.classicLightMatrix,null,null,region,true);
               this.fogCache.draw(this.classicVisibilityField,null,null,"multiply",region);
               this.fogCache.colorTransform(region,this.brightnessToFog);'''
assert s.count(old)==1
marker='                  this.classicLogicInterpolated=small;'
assert s.count(marker)==1
s=s.replace(old,'''               if(!small)
               {
'''+old+'''
               }''')
s=s.replace(marker,'''                  if(small)
                  {
                     this.fogCache.fillRect(this.fogRect,0xFFFFFFFF);
                     this.fogCache.draw(this.wallRaw,this.classicLightMatrix,null,null,this.fogRect,true);
                     this.fogCache.draw(this.classicVisibilityField,null,null,"multiply",this.fogRect);
                     this.fogCache.colorTransform(this.fogRect,this.brightnessToFog);
                  }
'''+marker)
p.write_text(s,encoding='utf-8',newline='\n')
(target.parent/'inputs.json').write_text(json.dumps({p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*.as')},indent=2)+'\n',encoding='utf-8')
print('Frozen all candidate; old raw unchanged')
