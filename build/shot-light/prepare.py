"""Freeze the verified 0.7 lighting source in RV's isolated experiment only."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/shot-light-output'
OLD=MOD/'build/fire-cost-output';LAD=GAME/'mods/LightAndDarkness'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists()
freeze=json.loads((LAD/'build/out/brightness-v070-host3/freeze.json').read_text('utf8'))
assert sha(LAD/'release/LightAndDarknessMod.swf')==freeze['sha256']=='8adba6914df5aada4df12a646b6c22df4b95b9630a55dd05ca7f713621c7e3ef'
OUT.mkdir()
for rel,h in freeze['source'].items():
 p=LAD/'build/out/brightness-v070-host3/source'/rel
 assert sha(p)==h,rel
 q=OUT/'lighting-baseline/src'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
shutil.copytree(OLD/'baseline/src',OUT/'baseline/src')
# Reuse the last frozen host/package set, omitting historical backup SWFs.
shutil.copytree(OLD/'frozen',OUT/'frozen',ignore=shutil.ignore_patterns('*.before-*.swf','*.before.*.swf','*.bak'))
assert sha(OUT/'frozen/mods/LightAndDarkness/release/LightAndDarknessMod.swf')==freeze['sha256']
probe=(MOD/'build/fire-cost/SavedFireProbe.as').read_text('utf8').replace('build/fire-cost-output','build/shot-light-output')
(MOD/'build/shot-light/SavedFireProbe.as').write_text(probe,'utf8',newline='\n')
inputs={'files':{p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()},
        'nativeRunner':sha(MOD/'build/maximized-flow/run.py'),
        'lightingBuilder':sha(LAD/'build/build.ps1'),'lightingFreeze':freeze['sha256'],
        'note':'All writes in RV; LAD source, install and player settings untouched.'}
(OUT/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n','utf8',newline='\n')
print('Frozen lighting production source and prior matched host, excluded historical backup SWFs')
