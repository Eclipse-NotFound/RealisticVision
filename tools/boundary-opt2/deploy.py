"""Install only the verified RV SWF; keep configuration, host and player state."""
from datetime import datetime
import json, os, shutil, uuid
from run import MOD, OUT, PIN, r

candidate=OUT/'production/RealisticVisionMod.swf'
build=json.loads((OUT/'production/build.json').read_text('utf8'))
smoke=json.loads((OUT/'production-smoke-01/validation.json').read_text('utf8'))
assert smoke['passed'] and r.sha(candidate)==smoke['production']==build['swf']
exact=json.loads((OUT/'pad-exact-03/evidence/result.json').read_text('utf8'))
assert exact['checks']>0 and 'error' not in exact
for name in ['pad-perf-01','pad-perf-02','pad-aa-01']:
    assert json.loads((OUT/name/'summary.json').read_text('utf8'))['environment']['performanceEligible']
release=MOD/'release/RealisticVisionMod.swf'
assert release.resolve().parent==(MOD/'release').resolve()
assert r.sha(release)==PIN,'Installed version changed; stop instead of overwriting concurrent work'
config=MOD/'release/config.txt';config_hash=r.sha(config)
backup=MOD/'build/backups'/('before-clip-pad-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
backup.mkdir(parents=True,exist_ok=False)
shutil.copy2(release,backup/release.name);shutil.copy2(config,backup/config.name)
assert r.sha(backup/release.name)==PIN
temporary=release.parent/(release.name+'.new-'+uuid.uuid4().hex)
shutil.copyfile(candidate,temporary)
assert r.sha(temporary)==build['swf'] and r.sha(release)==PIN
os.replace(temporary,release)
assert r.sha(release)==build['swf'] and r.sha(config)==config_hash
receipt=dict(version=build['version'],time=datetime.now().isoformat(),previous=PIN,
    installed=r.sha(release),bytes=release.stat().st_size,config=config_hash,
    backup=str(backup),source=str(OUT/'production/src'),smoke='production-smoke-01',
    scope='RV SWF only; restart to load; no host, config, save or player-process changes')
r.save(OUT/'deployment.json',receipt)
print(json.dumps(receipt,indent=2))
