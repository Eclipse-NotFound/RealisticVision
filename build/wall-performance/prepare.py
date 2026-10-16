"""D29: derive only from the frozen D28 production lineage."""
from pathlib import Path
import hashlib,json,shutil,subprocess
MOD=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=MOD/'build/wall-performance-output'
BASE=MOD/'build/wall-restore-output/candidate'
HELPER_PIN='62f22cc918368aeed59e70112d94dfcdab8de63c91a9249e888322513e47c895'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    assert sha(BASE/'RealisticVisionMod.swf')=='65b6bf90859cc78decef504ff7c912884d038e027e579bf0c51bebb046be7217'
    assert sha(BASE/'src/RVWallSurface.as')=='02d18cce5b9479a114fa70ae935d6d7f13b78a933e969868482979ae642271eb'
    assert sha(MOD/'src/RVWallSurface.as')==HELPER_PIN,'Helper changed: start another experiment'
    OUT.mkdir(exist_ok=True)
    for variant in ['baseline','candidate']:
        dest=OUT/variant/'src'
        for source in (BASE/'src').rglob('*.as'):
            data=source.read_bytes();name=source.relative_to(BASE/'src');target=dest/name
            if variant=='candidate':
                if source.name=='RVWallSurface.as':data=(MOD/'src/RVWallSurface.as').read_bytes()
                elif source.name=='RealisticVisionMod.as':data=data.replace(b'v0.32.0-wall-restore-candidate',b'v0.32.1-wall-performance')
            if target.exists():assert target.read_bytes()==data,'Frozen candidate drift: '+str(target)
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    if not (OUT/'wip-before.patch').exists():
        (OUT/'wip-before.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=MOD))
    pins={p.relative_to(BASE/'src').as_posix():sha(p) for p in (BASE/'src').rglob('*.as')}
    path=HERE/'inputs.json'
    if path.exists():assert json.loads(path.read_text())==pins
    else:path.write_text(json.dumps(pins,indent=2),encoding='utf-8')
    print('D28 source frozen; release untouched')
if __name__=='__main__':prepare()
