from pathlib import Path
import os,shutil,json,hashlib
OUT=Path(__file__).resolve().parents[1]/'effect-load-v3-output'
src=OUT/'safe-01-parent';dst=OUT/'safe-02-parent'
assert json.loads((src/'last-run.json').read_text())['exit']==124
assert not dst.exists()
assert 'safe-01-parent' not in (src/'RecoveryFrameProbeMod.as').read_text(encoding='utf-8')
def copy(source,target):
    if Path(source).suffix in ['.swf','.as','.xml','.png','.jpg']:os.link(source,target);return target
    return shutil.copy2(source,target)
shutil.copytree(src,dst,copy_function=copy,ignore=shutil.ignore_patterns('evidence','storage','*.log','last-run.json','running.json','launch-state.json','environment.json','test.xml'))
pins=json.loads((dst/'build.json').read_text())['files']
for rel,d in pins.items():assert hashlib.sha256((dst/rel).read_bytes()).hexdigest()==d,rel
(dst/'retry-of.json').write_text(json.dumps({'source':'safe-01-parent','reason':'exit124 at 300 seconds; keep identical SWFs, allow 600 seconds','files_verified':len(pins)},indent=2),encoding='utf-8')
print('Parent retry, identical frozen bytes',len(pins))
