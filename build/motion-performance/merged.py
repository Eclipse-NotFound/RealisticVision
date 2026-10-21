"""Rebase the selected D33 optimization onto the deployed D34 source snapshot."""
import argparse, json, re, shutil
import run
import optimize
import analyze

ROOT=run.MOD/'build/motion-performance-output'
run.OUT=ROOT/'merged-settings'
BASE=run.MOD/'build/vision-settings-output'
OLD='8d4a19634770acca0b66c8c684955855ef4725e80fbdff329451d69710c55bf1'

def freeze():
    assert not run.OUT.exists()
    proof=json.loads((BASE/'build.json').read_text())
    assert run.sha(run.MOD/'release/RealisticVisionMod.swf')==proof['swf']==OLD
    src=BASE/'candidate/src'
    assert all(run.sha(src/p)==h for p,h in proof['sources'].items())
    assert run.sha(src/'RVWallSurface.as')==run.sha(ROOT/'baseline/src/RVWallSurface.as')
    for name in ['baseline','candidate']:shutil.copytree(src,run.OUT/name/'src')
    optimize.prepare(packed=True)
    run.save(run.OUT/'inputs.json',{'installed':OLD,'base':str(BASE.relative_to(run.MOD)),'sources':proof['sources']})

def extra_checks(build):
    folder=run.OUT/'settings-checks';src=folder/'src'
    with run.Registration(owner='RealisticVision / D33+D34 回归',purpose='设置、共享探索与柔化'+(' 编译' if build else ' 验收'),run_dir=folder,evidence=folder/'checks.json',wait=300) as rec:
        if build:
            assert not folder.exists();run.public(run.OUT/'candidate/src',src)
            text=(run.OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
            text=re.sub(r'\bprivate\b','public',text).replace('RealisticVisionMod','BaselineVision')
            (src/'BaselineVision.as').write_text(text,encoding='utf-8')
            for name in ['SettingsChecks','SoftHarness','SharedExplorationHarness']:
                origin=run.MOD/('build/vision-settings' if name=='SettingsChecks' else 'build/motion-tests')/(name+'.as')
                text=origin.read_text(encoding='utf-8-sig').replace('p.m.curBlur.blurX=p.m.curBlur.blurY=6','p.m.cfgSoftCurrent=30')
                entry=src/(name+'.as');entry.write_text(text,encoding='utf-8')
                run.runner.compile(entry,folder/(name+'.swf'),[src,run.MOD/'build/motion-tests',run.MOD/'build/stubs'])
            rec.outcome='passed';rec.note='设置与逻辑夹具编译通过';return
        results=[]
        for name in ['SettingsChecks','SoftHarness','SharedExplorationHarness']:
            code,log=run.air(folder,name+'.swf',rec,150)
            (folder/(name+'.txt')).write_text(log,encoding='utf-8')
            result=json.loads((folder/'last-run.json').read_text());result.update(name=name,passed=len(re.findall(r'^PASS ',log,re.M)))
            results.append(result);run.save(folder/'checks.json',results)
            print('\n'.join(log.splitlines()[-4:]),flush=True)
            assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
        rec.outcome='passed';rec.note='设置、柔化、共享探索回归通过'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','build','run','analyze','analyze-live','checks-build','checks-run','settings-build','settings-run']);p.add_argument('--name');p.add_argument('--verify',action='store_true');p.add_argument('--profile',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='build':run.build(a.name,a.profile,a.verify,True,a.live)
    elif a.action=='run':run.run(a.name)
    elif a.action=='analyze':analyze.analyze(a.name)
    elif a.action=='analyze-live':analyze.analyze_live(a.name)
    elif a.action.startswith('checks-'):run.checks(a.name,a.action=='checks-build')
    elif a.action.startswith('settings-'):extra_checks(a.action=='settings-build')
