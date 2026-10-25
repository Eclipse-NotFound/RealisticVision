"""D50: private classic interpolation reuse; public query extent unchanged."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/classic-inputs-output';BASE=MOD/'build/combat-render-output/production-final2/src'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(BASE/'RealisticVisionMod.as')=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
assert sha(MOD/'release/RealisticVisionMod.swf')=='638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710'
target=OUT/'candidates/raw/src';assert not target.exists();shutil.copytree(BASE,target)
p=target/'RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
def patch(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
patch('      private var classicLogicTiles:Vector.<int>;','      private var classicLogicTiles:Vector.<int>;\n      private var classicLogicInterpolated:Boolean=false;')
patch('            this.classicLogicTiles=new Vector.<int>(this.spaceX*this.spaceY,true);','            this.classicLogicTiles=new Vector.<int>(this.spaceX*this.spaceY,true);\n            this.classicLogicInterpolated=false;')
patch('         this.classicLogicDeltas=null;this.classicLogicTiles=null;','         this.classicLogicDeltas=null;this.classicLogicTiles=null;this.classicLogicInterpolated=false;')
old='''               var sample:Rectangle=region.clone();sample.inflate(16,16);sample=sample.intersection(this.fogRect);
               this.fogRaw.fillRect(sample,0xFFFFFFFF);
               this.fogRaw.draw(this.classicRaw,this.classicLightMatrix,null,null,sample,true);
               this.fogRaw.draw(this.classicLogicMemorySamples,this.classicMemoryMatrix,null,null,sample,true);
               this.fogRaw.colorTransform(sample,this.brightnessToFog);
               this.classicVisibilityField.fillRect(sample,0xFFFFFFFF);
               this.classicVisibilityField.draw(this.classicLogicVisibilitySamples,this.classicMemoryMatrix,null,null,sample,true);'''
new='''               var small:Boolean=this.spaceX<=48 && this.spaceY<=25;
               if(!small || !this.classicLogicInterpolated)
               {
                  // Only private interpolation inputs may be prepared early.
                  // Keep requested tiles, correction order, and fogCache writes
                  // identical; those affect native rendering and visibility.
                  var sample:Rectangle=small?this.fogRect:region.clone();
                  if(!small){sample.inflate(16,16);sample=sample.intersection(this.fogRect);}
                  this.fogRaw.fillRect(sample,0xFFFFFFFF);
                  this.fogRaw.draw(this.classicRaw,this.classicLightMatrix,null,null,sample,true);
                  this.fogRaw.draw(this.classicLogicMemorySamples,this.classicMemoryMatrix,null,null,sample,true);
                  this.fogRaw.colorTransform(sample,this.brightnessToFog);
                  this.classicVisibilityField.fillRect(sample,0xFFFFFFFF);
                  this.classicVisibilityField.draw(this.classicLogicVisibilitySamples,this.classicMemoryMatrix,null,null,sample,true);
                  this.classicLogicInterpolated=small;
               }'''
patch(old,new);p.write_text(s,encoding='utf-8',newline='\n')
(OUT/'inputs.json').write_text(json.dumps({'baseline':{p.relative_to(BASE).as_posix():sha(p) for p in BASE.rglob('*.as')},'candidate':{p.relative_to(target).as_posix():sha(p) for p in target.rglob('*.as')},'rule':'No D49 setters. Private raw/visibility preparation only; original public region, correction and publication order unchanged. Small rooms only.'},indent=2)+'\n',encoding='utf-8')
for name in ['group.py','perf.py','IdentityCombatProbe.as','runtime.py','verify-results.py']:
 text=(MOD/'build/fog-setters'/name).read_text(encoding='utf-8').replace('fog-setters-output','classic-inputs-output').replace('D49','D50').replace('d49','d50')
 if name=='verify-results.py':text=text.replace("('guard',)","('raw',)")
 (HERE/name).write_text(text,encoding='utf-8',newline='\n')
print('D50 private inputs candidate frozen; no production changes')
