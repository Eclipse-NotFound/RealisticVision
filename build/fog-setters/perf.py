"""D49P isolated rendering attribution. Diagnostic omissions never ship."""
from pathlib import Path
import argparse,importlib.util,json,re,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/fog-setters-output'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
r=module('d49p_runtime',MOD/'build/motion-performance/run.py')
policy=module('d49p_policy',MOD/'build/effect-load-v3/policy_capture.py')
r.HiddenProcess=policy.wrap(r.HiddenProcess,True)
from runtime import bind
bind(r)
BASE=MOD/'build/combat-render-output/production-final2/src'
def build(name,full=False,large=False,frames=90,warmup=30,candidate=None,controlled=False,profile=False,split=False):
    if candidate:assert not (OUT/'candidates'/candidate/'not-adopted.json').exists(),'Rejected candidate; start a new evidence-backed variant'
    assert 1<=frames<=600 and 0<=warmup<=600,'Bound the diagnostic duration'
    folder=OUT/name;assert not folder.exists(),'Use a fresh name'
    folder.mkdir(parents=True)
    with r.Registration(owner='RealisticVision / D49P 绘制归因构建',purpose=name,run_dir=folder,evidence=folder/'build.json',resource='offline') as rec:
        r.runtime(folder)
        s=(HERE/'IdentityCombatProbe.as').read_text(encoding='utf-8').replace('SAMPLE_COUNT=90','SAMPLE_COUNT='+str(frames)).replace('WARMUP_COUNT=30','WARMUP_COUNT='+str(warmup)).replace('LARGE=false','LARGE='+str(large).lower()).replace('EXPERIMENT=false','EXPERIMENT='+str(candidate is not None).lower())
        s=s.replace('CONTROLLED=false','CONTROLLED='+str(controlled).lower())
        s=s.replace('PROFILE=false','PROFILE='+str(profile).lower())
        s=s.replace('SPLIT=false','SPLIT='+str(split).lower())
        (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8',newline='\n')
        r.runner.compile(folder/'CombatRenderProbeMod.as',folder/'mods/CombatRenderProbe/release/CombatRenderProbeMod.swf',[folder])
        r.public(BASE,folder/'rv-src')
        if split:
            diagnostic=module('d49p_diagnostic',HERE/'diagnostic.py')
            diagnostic_source=folder/'rv-src/RealisticVisionMod.as'
            diagnostic_source.write_text(diagnostic.patch(diagnostic_source.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
        r.runner.compile(folder/'rv-src/RealisticVisionMod.as',folder/'rv.swf',[folder/'rv-src'],stubs=True)
        if candidate:
            r.public(OUT/'candidates'/candidate/'src',folder/'candidate-src')
            if profile:
                source=folder/'candidate-src/RealisticVisionMod.as'
                source.write_text(r.fp.instrument(source.read_text(encoding='utf-8'),['prepareOcclusion','computeFov','applyVision','applyVisionClassic','updateWallSurface','hideEnemies','applyMask','refreshMask','enemyState','fillFogCache','refreshWallField','applyWorldVisuals','applyWorldVisual']),encoding='utf-8')
            r.runner.compile(folder/'candidate-src/RealisticVisionMod.as',folder/'candidate.swf',[folder/'candidate-src'],stubs=True)
        selected=['CombatRenderProbeMod']
        for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
            c=line.split('|')
            if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1]!='RealisticVisionMod' and (full or large and c[1]=='ContinuousSceneMod'):
                selected.append(c[1]);shutil.copytree(GAME/'mods'/c[0]/'release',folder/'mods'/c[0]/'release',dirs_exist_ok=True)
        catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
        (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nCombatRenderProbe|CombatRenderProbeMod|1|0|0\n',encoding='utf-8')
        scan=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--list','--json','--no-ui'],capture_output=True,text=True,encoding='utf-8',timeout=60)
        (folder/'installed-inventory.json').write_text(scan.stdout,encoding='utf-8');assert scan.returncode==0
        scan=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8',timeout=60)
        (folder/'selection.log').write_text(scan.stdout+scan.stderr,encoding='utf-8');assert scan.returncode==0
        r.save(folder/'build.json',{'baseline':'D44','candidate':candidate,'controlled':controlled,'profile':profile,'split':split,'installed':r.sha(MOD/'release/RealisticVisionMod.swf'),'full':full,'large':large,'samples':frames,'warmup':warmup,'selected':selected,'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.as','.swf','.xml','.txt','.json')}})
        rec.outcome='passed';rec.note='隔离诊断构建；尚未运行'
def run(name):
    assert not (OUT/'TESTS-PAUSED.json').exists(),'User paused game tests; resume only after explicit user steering'
    folder=OUT/name;assert not (folder/'last-run.json').exists()
    assert not (folder/'invalidated.json').exists(),'Retired diagnostic fixture; build a fresh name'
    for rel,digest in json.loads((folder/'build.json').read_text())['files'].items():assert r.sha(folder/rel)==digest,rel
    with r.Registration(owner='RealisticVision / D49P 绘制归因',purpose=name,run_dir=folder,evidence=folder/'evidence/result.json',wait=900) as rec:
        import psutil
        env={'time':time.time(),'available':psutil.virtual_memory().available,'processes':[],'hostCpu':psutil.cpu_percent(interval=2)}
        for p in psutil.process_iter(['pid','name','cmdline','exe']):
            if (p.info['name'] or '').lower() in ('adl64.exe','adl.exe','java.exe','javaw.exe'):env['processes'].append(p.info)
        r.save(folder/('environment-attempt-'+str(time.time_ns())+'.json'),env)
        if not (folder/'environment-start.json').exists():r.save(folder/'environment-start.json',env)
        assert not [p for p in env['processes'] if (p['name'] or '').lower() in ('adl64.exe','adl.exe')],'Other AIR active; no trial launched'
        assert env['available']>5*1024**3,'Less than 5 GiB available'
        r.save(folder/'environment-active.json',env)
        build=json.loads((folder/'build.json').read_text())
        timeout=max(650,120+42*(build.get('samples',90)+build.get('warmup',30))//10)
        code,log=r.air(folder,'pfe.swf',rec,timeout=timeout)
        print('\n'.join(x[:700] for x in log.splitlines() if x.startswith(('D49P','FAIL')))[-7000:],flush=True)
        assert code==0 and 'D49P COMPLETE' in log and 'FAIL ' not in log
        rec.outcome='passed';rec.note='完整战斗对照完成；性能采用结论另看报告'
    report(name)
def report(name):
    d=json.loads((OUT/name/'evidence/result.json').read_text())
    for c in d['cases']:
        frames=[f for f in c.get('frames',[]) if 'nextInterval' in f]
        a=sorted(f['nextInterval'] for f in frames) if frames else sorted(c['intervals']);u=[f['rv'] for f in frames] if frames else c['updates']
        print(json.dumps({'n':c['crowd'],'mode':c['mode'],'variant':c['variant'],'pairedFrames':len(frames),'mean':round(sum(a)/len(a),2),'p95':a[int(.95*(len(a)-1))],'max':a[-1],'>100':sum(x>100 for x in a),'rv':round(sum(u)/len(u),2),'masks':max(c['masks']),'bullets':c['maxProjectiles'],'particles':c.get('maxParticles'),'units':c['units'],'objects':c['maxObjects'],'retained':c.get('retained')},ensure_ascii=False),flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run','report']);a.add_argument('name');a.add_argument('--full',action='store_true');a.add_argument('--large',action='store_true');a.add_argument('--frames',type=int,default=90);a.add_argument('--warmup',type=int,default=30);a.add_argument('--candidate');a.add_argument('--controlled',action='store_true');a.add_argument('--profile',action='store_true');a.add_argument('--split',action='store_true');x=a.parse_args()
    if x.action=='build':build(x.name,x.full,x.large,x.frames,x.warmup,x.candidate,x.controlled,x.profile,x.split)
    elif x.action=='run':run(x.name)
    else:report(x.name)
