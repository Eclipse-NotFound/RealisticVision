"""Build exact production bytes and validate settings without test exports."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
import run

run.OUT=run.MOD/'build/motion-performance-output/merged-settings'
VERSION='v0.33.1-motion-performance'
PACKAGE=run.OUT/'production'

def build():
    assert not PACKAGE.exists()
    with run.Registration(owner='RealisticVision / D33 正式候选编译',purpose=VERSION+' 构建与类清点',run_dir=PACKAGE,evidence=PACKAGE/'manifest.json',wait=300) as rec:
        shutil.copytree(run.OUT/'candidate/src',PACKAGE/'src')
        p=PACKAGE/'src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig');assert s.count('v0.33.0-vision-settings')==1
        p.write_text(s.replace('v0.33.0-vision-settings',VERSION),encoding='utf-8')
        target=PACKAGE/'RealisticVisionMod.swf'
        run.runner.compile(p,target,[p.parent],stubs=True)
        probe=run.MOD/'build/vision-settings-output/options-final/CandidateOptionsProbe.as'
        run.runner.compile(probe,PACKAGE/'CandidateOptionsProbe.swf',[probe.parent],definitions=['-include-libraries='+str(run.MOD/'build/GameStubs.swc')])
        ffdec=run.GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'
        result=subprocess.run([str(run.runner.JAVA),'-jar',str(ffdec),'-dumpAS3',str(target)],capture_output=True,timeout=60)
        text=result.stdout.decode('utf-8',errors='replace');(PACKAGE/'classes.txt').write_text(text,encoding='utf-8');(PACKAGE/'class-audit.stderr.txt').write_text(result.stderr.decode('utf-8',errors='replace'),encoding='utf-8')
        assert result.returncode==0
        run.save(PACKAGE/'manifest.json',{'version':VERSION,'swf':run.sha(target),'bytes':target.stat().st_size,'sources':{p.relative_to(PACKAGE/'src').as_posix():run.sha(p) for p in (PACKAGE/'src').rglob('*.as')},'test_sources':{p.relative_to(run.OUT/'candidate/src').as_posix():run.sha(p) for p in (run.OUT/'candidate/src').rglob('*.as')}})
        rec.outcome='passed';rec.note='准确候选编译与字节码导出完成；类清单需复核，功能另验'

def check():
    proof=json.loads((PACKAGE/'manifest.json').read_text());assert run.sha(PACKAGE/'RealisticVisionMod.swf')==proof['swf']
    with run.Registration(owner='RealisticVision / D33 准确包验收',purpose='设置、改键、两进程保存恢复',run_dir=PACKAGE,evidence=PACKAGE/'settings.json',wait=300) as rec:
        assert run.environment()['available_bytes']>=6*1024**3
        results=[];previous=None
        for name in ['first','restored']:
            folder=PACKAGE/name;folder.mkdir(exist_ok=False)
            shutil.copyfile(PACKAGE/'RealisticVisionMod.swf',folder/'candidate.swf');shutil.copyfile(PACKAGE/'CandidateOptionsProbe.swf',folder/'CandidateOptionsProbe.swf')
            code,log=run.air(folder,'CandidateOptionsProbe.swf',rec,90,previous)
            result=json.loads((folder/'last-run.json').read_text());result['passed']=len(re.findall(r'^PASS ',log,re.M));results.append(result);run.save(PACKAGE/'settings.json',results)
            print('\n'.join(log.splitlines()[-6:]),flush=True)
            assert code==0 and 'INSTALLED OPTIONS COMPLETE passed=18' in log and 'FAIL ' not in log
            assert ('restoring=true' if previous else 'restoring=false') in log
            previous=folder/'storage'
        rec.outcome='passed';rec.note='准确生产字节36项设置与跨进程恢复通过'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','check']);a=p.parse_args();build() if a.action=='build' else check()
