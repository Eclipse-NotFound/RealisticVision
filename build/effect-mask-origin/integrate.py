"""Merge only validated render edits into the authority development source."""
from pathlib import Path
import importlib.util,json
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
old=(MOD/'build/combat-render-output/production-final2/src/RealisticVisionMod.as').read_text()
new=(OUT/'production/src/RealisticVisionMod.as').read_text();path=MOD/'src/RealisticVisionMod.as';live=path.read_text()
assert json.loads((OUT/'deployment/receipt.json').read_text())['result']=='PASS'
assert 'v0.33.11-effect-clip' not in live
begin='      private function applyWorldVisual(visual:DisplayObject):void'
end='      private function worldVisualHasFilters(visual:DisplayObject):Boolean'
before=old[old.index(begin):old.index(end,old.index(begin))]
after=new[new.index(begin):new.index(end,new.index(begin))]
def development(block):
 block=block.replace('if(visual.cacheAsBitmap!==useCache)visual.cacheAsBitmap=useCache;', 'if(this.authorityView.active || visual.cacheAsBitmap!==useCache)this.authorityView.write(visual,"cacheAsBitmap",useCache);')
 block=block.replace('if(visual.mask!==shape)visual.mask=shape;', 'if(this.authorityView.active || visual.mask!==shape)this.authorityView.write(visual,"mask",shape);')
 block=block.replace('if(visual.mask===shape)visual.mask=null;', 'if(this.authorityView.active || visual.mask===shape)this.authorityView.write(visual,"mask",null);')
 return block
before=development(before);after=development(after)
assert live.count(before)==1;live=live.replace(before,after)
anchor='         // 位图填充绘制进矢量 Shape'
assert live.count(anchor)==1;live=live.replace(anchor,'         if(this.cfgMode=="current")rec.inputRevision=int(rec.inputRevision)+1;\n'+anchor)
assert live.count('v0.33.10-render-cache')==1;live=live.replace('v0.33.10-render-cache','v0.33.11-effect-clip')
live=live.replace('// Keep the old sampling lattice; test whether unused outer tiles\n         // can be omitted without changing Flash\'s cached alpha rendering.', '// Omit unused outer samples while retaining the original sampling\n         // lattice and updating the target\'s cached mask association.')
live=live.replace('bitmap sampling phase. Retain two pixels beyond native bounds;', 'bitmap sampling phase. Retain two original samples beyond bounds;')
path.write_text(live,encoding='utf-8',newline='\n')
spec=importlib.util.spec_from_file_location('d56_integrate_runtime',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.runner.compile(path,OUT/'development-syntax.swf',[MOD/'src'],stubs=True)
r.save(OUT/'integration.json',{'mainSource':r.sha(path),'developmentSyntax':r.sha(OUT/'development-syntax.swf'),'authorityChangesExcludedFromProduction':True})
