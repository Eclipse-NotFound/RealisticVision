"""Deploy only the verified local exploration cache, with automatic smoke rollback."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys, uuid
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];RC=GAME/'mods/RConnect'
sys.path.insert(0,str(RC/'tools/validation'))
from validation_baseline import verify_runtime_inputs
ap=argparse.ArgumentParser();ap.add_argument('folder');ap.add_argument('integration');a=ap.parse_args()
out=(MOD/a.folder).resolve();integration=(RC/a.integration).resolve()
assert out.parent==MOD/'build' and out.name.startswith('exploration-cache-')
assert integration.parent==RC/'build/m51' and integration.name.startswith('probe-vision-installed22-')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
m=read(out/'inputs.json');candidate=out/'RealisticVisionMod.swf';target=MOD/'release/RealisticVisionMod.swf'
assert sha(candidate)==m['candidate_sha256'] and not (out/'deployment.json').exists()
for n,h in m['source'].items():assert sha(out/n)==sha(MOD/n)==h,n
for n,h in m['protected'].items():assert sha(GAME/n)==h,n
checks=read(out/'checks.json')
for name,count in [('SoftHarness',16),('SharedExplorationHarness',21),('ExplorationCacheHarness',9)]:
    row=checks[name];log=out/'checks'/(name+'.log')
    assert row['passed']==count and sha(log)==row['log_sha256']
    text=log.read_text(encoding='utf-8');assert 'failures=0' in text and 'FAIL ' not in text
baseline=read(RC/'build/m51/integration-baseline-0.2.22-external1/inputs.json')
for n,h in baseline['protected'].items():assert sha(GAME/n)==h,n
expected=json.loads(json.dumps(baseline))
rvkey=next(n for n in expected['runtime_modules'] if n.lower()=='mods/realisticvision/release/realisticvisionmod.swf')
expected['runtime_modules'][rvkey]=sha(candidate)
proof={}
for entry in ('VisionApiTestDoc','RoomCooperationTestDoc','MirrorMaskRestoreTestDoc'):
    r=read(integration/(entry+'-result.json'));assert r['exit']==0 and r['vision_override']['sha256']==sha(candidate)
    assert r['sha256']==baseline['release_sha256']
    run=RC/'build/cooperation'/r['run'];verify_runtime_inputs(expected,read(run/'run.json'))
    for role in ('host','join'):assert r[role]['done'] and r[role]['failed']==0 and r[role]['passed']>0
    proof[entry]=dict(run=r['run'],result_sha256=sha(integration/(entry+'-result.json')))
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
backup=MOD/'build/backups'/('before-exploration-cache-'+stamp);backup.mkdir(parents=True,exist_ok=False)
shutil.copy2(target,backup/'RealisticVisionMod.before.swf')
old=sha(target);assert sha(backup/'RealisticVisionMod.before.swf')==old
record=dict(status='deployed-awaiting-smoke',version='v0.30.2-candidate',sha256=sha(candidate),previous_sha256=old,
    backup=(backup/'RealisticVisionMod.before.swf').relative_to(MOD).as_posix(),integration=proof,
    authorization='RConnect user explicitly approved local exploration API testing, changes, deployment and RV coordination on 2026-10-10')
temp=target.with_name('RealisticVisionMod.'+uuid.uuid4().hex+'.tmp')
shutil.copy2(candidate,temp);os.replace(temp,target);save(out/'deployment.json',record)
try:
    command=[sys.executable,'-X','utf8',str(RC/'tools/run_coop_regression.py'),'--candidate',str(RC/'release/RConnectMod.swf'),
        '--smoke','--all-mods','--responsive','--visible-windows','--seconds','180','--expected-version','0.2.22-dev',
        '--vision-smoke-version',record['version']]
    r=subprocess.run(command,cwd=RC,capture_output=True,text=True,encoding='utf-8',errors='replace')
    log=r.stdout+'\n'+r.stderr;(out/'normal-smoke.log').write_text(log,encoding='utf-8')
    match=re.search(r'OUTPUT .*?([0-9a-f]{10})\s*$',r.stdout,re.M)
    assert r.returncode==0 and match,log[-3000:]
    runid=match.group(1);run=RC/'build/cooperation'/runid
    verify_runtime_inputs(expected,read(run/'run.json'))
    for role in ('host','join'):
        text=(run/(role+'-vision.log')).read_text(encoding='utf-8-sig')
        assert 'init ok '+record['version'] in text and 'tick 181' in text and 'ERROR' not in text and 'error:' not in text
    for n,h in baseline['protected'].items():
        assert sha(GAME/n)==(record['sha256'] if n.lower()=='mods/realisticvision/release/realisticvisionmod.swf' else h),n
    record.update(status='deployed-smoke-passed',smoke=runid,pids=read(run/'run.json')['pids'])
except BaseException as error:
    assert sha(backup/'RealisticVisionMod.before.swf')==old
    shutil.copy2(backup/'RealisticVisionMod.before.swf',temp);os.replace(temp,target)
    record.update(status='rolled-back-after-smoke-failed',error=str(error));save(out/'deployment.json',record);raise
save(out/'deployment.json',record);print(json.dumps(record,ensure_ascii=False),flush=True)
