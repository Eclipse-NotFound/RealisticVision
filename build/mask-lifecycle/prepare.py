"""D46: measure actual stale-raster releases before changing their schedule."""
from pathlib import Path
import hashlib,json
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=MOD/'build/mask-lifecycle-output';BASE=MOD/'build/combat-render-output/production-final2/src'
OUT.mkdir(exist_ok=True)
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
pins={p.relative_to(BASE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.rglob('*.as')}
target=OUT/'inputs.json';assert not target.exists(),'Do not replace frozen inputs'
target.write_text(json.dumps({'baseline':'D44','source':pins},indent=2)+'\n',encoding='utf-8',newline='\n')
source=(MOD/'build/mask-area/run.py').read_text(encoding='utf-8').replace('mask-area','mask-lifecycle').replace('d45','d46').replace('D45','D46')
needle='        r.public(BASE,folder/\'rv-src\')'
assert source.count(needle)==1
source=source.replace(needle,needle+'''\n        from instrument import patch
        source=folder/'rv-src/RealisticVisionMod.as'
        source.write_text(patch(source.read_text(encoding='utf-8')),encoding='utf-8',newline='\\n')''')
(HERE/'run.py').write_text(source,encoding='utf-8',newline='\n')
probe=(MOD/'build/mask-area/CombatRenderProbeMod.as').read_text(encoding='utf-8').replace('mask-area','mask-lifecycle').replace('D45','D46')
start=probe.index('   for each(var n:int in ');end=probe.index('\n',start)
probe=probe[:start]+"   for each(var mode:String in ['current','classic']) for(var round:int=0;round<2;round++)plan.push({n:6,mode:mode,variant:'normal'});"+probe[end:]
needle='previousFrame={age:age,rv:ms,'
assert probe.count(needle)==1
probe=probe.replace(needle,'previousFrame={releasedRasters:rv.diagReleasedRasters,releasedPixels:rv.diagReleasedPixels,releasedBuffers:rv.diagReleasedBuffers,sweepMs:rv.diagSweepMs,createdRasters:rv.diagCreatedRasters,sweep:rv.diagSweep,age:age,rv:ms,')
(HERE/'CombatRenderProbeMod.as').write_text(probe,encoding='utf-8',newline='\n')
group=(MOD/'build/mask-area/group.py').read_text(encoding='utf-8').replace('mask-area','mask-lifecycle').replace('D45','D46')
(HERE/'group.py').write_text(group,encoding='utf-8',newline='\n')
steps=[['run.py','build','release-observe-01','--full','--controlled','--frames','540','--warmup','60'],['run.py','run','release-observe-01']]
(HERE/'observe-steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8',newline='\n')
print('D46 diagnostic prepared; no production changes')
