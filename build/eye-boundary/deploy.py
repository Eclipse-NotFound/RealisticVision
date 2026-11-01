from pathlib import Path
import hashlib,json,shutil,difflib,datetime
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/eye-boundary-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((OUT/'inputs.json').read_text('utf8'))
check=json.loads((OUT/'checks-07/evidence/result.json').read_text('utf8'))
smoke=json.loads((OUT/'smoke-01/validation.json').read_text('utf8'))
target=MOD/'release/RealisticVisionMod.swf';candidate=OUT/'candidate/RealisticVisionMod.swf'
assert all(c['ok'] for c in check['checks']) and len(check['checks'])>750 and 'error' not in check
assert smoke['passed'] and smoke['production']==sha(candidate)
assert sha(target)==pins['installed'] and sha(MOD/'release/config.txt')==pins['config']==smoke['config']
backup=MOD/'build/backups'/('before-eye-boundary-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir()
shutil.copy2(target,backup/target.name);shutil.copy2(MOD/'release/config.txt',backup/'config.txt')
# Check again immediately before the authorized local installation.
assert sha(target)==pins['installed']
shutil.copyfile(candidate,target)
assert sha(target)==smoke['production'] and sha(MOD/'release/config.txt')==pins['config']
receipt={'version':'v0.34.3-eye-boundary','bytes':target.stat().st_size,'sha256':sha(target),'previous':pins['installed'],'config':pins['config'],'backup':str(backup),'checks':len(check['checks']),'productionSmoke':'smoke-01','source':{p.relative_to(OUT/'candidate/src').as_posix():sha(p) for p in (OUT/'candidate/src').rglob('*.as')}}
(OUT/'deployment.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf8')
base=(OUT/'baseline/src/RealisticVisionMod.as').read_text('utf8').splitlines(True)
updated=(OUT/'candidate/src/RealisticVisionMod.as').read_text('utf8').splitlines(True)
(HERE/'production.patch').write_text(''.join(difflib.unified_diff(base,updated,fromfile='v0.34.2/RealisticVisionMod.as',tofile='v0.34.3/RealisticVisionMod.as')),'utf8')
(HERE/'baseline-source.json').write_text(json.dumps(pins,indent=2)+'\n','utf8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
