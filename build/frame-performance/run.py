"""D31: frozen installed baseline, full-pipeline profiling and exact A/B checks.

Only writes this mod's experimental output. AIR uses unique IDs and hidden windows.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, shutil, sys
from datetime import datetime, timezone
import psutil
import threading

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
OUT = MOD / 'build/frame-performance-output'
sys.path.insert(0, str(MOD / 'build/wall-surface'))
spec = importlib.util.spec_from_file_location('surface_runner', MOD / 'build/wall-surface/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def freeze():
    old = MOD / 'build/wall-performance-output/candidate'
    assert sha(MOD / 'release/RealisticVisionMod.swf') == '2e7150cf415355c2d7b809689aac3c4ca0bacbb5f6d8770066a6e887d8907a10'
    assert sha(old / 'src/RealisticVisionMod.as') == '62085fefc016119b3eeb7c5520e2a8d8d0f6215b92fdd7efbaA8c5a922c5ef81'.lower()
    OUT.mkdir(exist_ok=True)
    for variant in ['baseline', 'candidate']:
        dest = OUT / variant
        if not dest.exists():
            shutil.copytree(old / 'src', dest / 'src')
    if not (OUT/'inputs.json').exists():
        (OUT/'inputs.json').write_text(json.dumps({str(p.relative_to(MOD)): sha(p) for p in [MOD/'release/RealisticVisionMod.swf', *sorted((old/'src').rglob('*.as'))]}, indent=2), encoding='utf-8')

def instrument(s, names):
    # Wrappers are exclusively for attribution, never used for final A/B timings.
    if 'import flash.utils.getTimer;' not in s:
        s=s.replace('import flash.display.Bitmap;', 'import flash.display.Bitmap;\n import flash.utils.getTimer;')
    pos = s.index('{', s.index('public class ')) + 1
    s = s[:pos] + '\n public var profile:Object = {}; public var calls:Object = {};\n' + s[pos:]
    for name in names:
        pat = r'public function ' + name + r'\(([^)]*)\)\s*:\s*(\w+)\s*\{'
        found = re.search(pat, s)
        assert found, name
        args, ret = found.group(1), found.group(2)
        params = ','.join(x.strip().split(':')[0] for x in args.split(',') if x.strip())
        wrapper = f'''public function {name}({args}):{ret} {{
var pstart:int=getTimer(); {'var presult:'+ret+';' if ret != 'void' else ''}
try {{ {'presult=' if ret != 'void' else ''}this.profiled_{name}({params}); }}
finally {{profile["{name}"]=Number(profile["{name}"]||0)+getTimer()-pstart; calls["{name}"]=int(calls["{name}"])+1;}}
{'return presult;' if ret != 'void' else ''}
}}
public function profiled_{name}({args}):{ret} {{'''
        s = s[:found.start()] + wrapper + s[found.end():]
    return s

def public_source(variant, dest, profile=False):
    for p in (OUT/variant/'src').rglob('*.as'):
        q=dest/p.relative_to(OUT/variant/'src');q.parent.mkdir(parents=True,exist_ok=True)
        s=re.sub(r'\bprivate\b','public',p.read_text(encoding='utf-8-sig'))
        if profile and p.name=='RealisticVisionMod.as':
            s=instrument(s,['prepareOcclusion','computeFov','applyVision','applyVisionClassic','updateWallSurface','hideEnemies','applyMask','enemyState','fillFogCache','refreshWallField'])
        if profile and p.name=='RVWallSurface.as':
            s=instrument(s,['updateContour','buildContourClip','rebuildFaces','rebuildSamples','rebuildSupport'])
        q.write_text(s,encoding='utf-8')

def runtime(folder):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'evidence').mkdir(exist_ok=True)
    frozen=MOD/'build/wall-restore-output/game-rock'
    for p in frozen.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):
            q=folder/p.name
            source=MOD/'build/wall-performance-output/runtime-inputs/pfe.swf' if p.name=='pfe.swf' else p
            if not q.exists():shutil.copyfile(source,q)
            assert sha(q)==sha(source)
    if not (folder/'Rooms').exists():shutil.copytree(frozen/'Rooms',folder/'Rooms')
    (folder/'mods').mkdir(exist_ok=True)
    (folder/'mods/loader-manifest.txt').write_text('FrameProbe|FrameProbe|1|0|0\n',encoding='utf-8')

def build(name, profile=False, large=False, verify=False, live=False, baseline='baseline'):
    folder=OUT/name;runtime(folder)
    if large:
        cs=MOD.parent/'ContinuousScene/release';dest=folder/'mods/ContinuousScene/release';dest.mkdir(parents=True,exist_ok=True)
        for source in [cs/'ContinuousSceneMod.swf',cs/'scene.xml']:
            shutil.copyfile(source,dest/source.name)
        (folder/'mods/loader-manifest.txt').write_text('ContinuousScene|ContinuousSceneMod|1|0|0\nFrameProbe|FrameProbe|1|0|0\n',encoding='utf-8')
    runner.compile(HERE/'FrameProbe.as',folder/'mods/FrameProbe/release/FrameProbe.swf',[HERE],definitions=['-define=CONFIG::largeScene,'+str(large).lower(),'-define=CONFIG::verifyPixels,'+str(verify).lower(),'-define=CONFIG::liveFrames,'+str(live).lower()])
    for variant, source in [('baseline',baseline),('candidate','candidate')]:
        src=folder/(variant+'-src');public_source(source,src,profile)
        runner.compile(src/'RealisticVisionMod.as',folder/(variant+'.swf'),[src],stubs=True)
    (folder/'build-inputs.json').write_text(json.dumps({'baseline':baseline,'profile':profile,'large':large,'verify':verify,'live':live,
        'runtime':{str(p.relative_to(folder)):sha(p) for p in [folder/'pfe.swf',folder/'mods/ContinuousScene/release/ContinuousSceneMod.swf',folder/'mods/ContinuousScene/release/scene.xml'] if p.exists()},
        'sources':{str(p.relative_to(OUT)):sha(p) for source in [baseline,'candidate'] for p in sorted((OUT/source/'src').rglob('*.as'))}},indent=2),encoding='utf-8')

def run(name):
    folder=OUT/name
    available=psutil.virtual_memory().available
    processes=[{'pid':p.info['pid'],'name':p.info['name']} for p in psutil.process_iter(['pid','name'])
               if (p.info['name'] or '').lower() in ['adl.exe','adl64.exe','java.exe','javaw.exe']]
    (folder/'launch-state.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
        'available_bytes':available,'minimum_available_bytes':6*1024**3,'processes':processes},indent=2),encoding='utf-8')
    if available<6*1024**3:raise RuntimeError('Less than 6 GiB available; no AIR was started')
    # Observe other AIR/Java activity throughout the window, not only before it.
    # No instrumentation is inserted into either measured SWF.
    stop=threading.Event();samples=[]
    def observe():
        while not stop.is_set():
            samples.append({'utc':datetime.now(timezone.utc).isoformat(),'available_bytes':psutil.virtual_memory().available,
                'processes':[{'pid':p.info['pid'],'name':p.info['name']} for p in psutil.process_iter(['pid','name'])
                    if (p.info['name'] or '').lower() in ['adl.exe','adl64.exe','java.exe','javaw.exe']]})
            stop.wait(10)
    watcher=threading.Thread(target=observe,daemon=True);watcher.start()
    try:code,log=runner.run_air(folder,'pfe.swf',300)
    finally:
        stop.set();watcher.join(timeout=2)
        (folder/'environment.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    (folder/'game.log').write_text(log,encoding='utf-8')
    print('\n'.join(log.splitlines()[-35:]),flush=True)
    assert code==0 and 'FRAME COMPLETE' in log and 'FAIL ' not in log

def checks(name, build_only=False):
    folder=OUT/name;src=folder/'src';public_source('candidate',src)
    baseline=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
    (src/'BaselineVision.as').write_text(re.sub(r'\bprivate\b','public',baseline.replace('RealisticVisionMod','BaselineVision')),encoding='utf-8')
    for name in ['MaskChecks','SightChecks','SoftHarness','SharedExplorationHarness']:
        entry=HERE/(name+'.as') if name in ['MaskChecks','SightChecks'] else MOD/'build/motion-tests'/(name+'.as')
        runner.compile(entry,folder/(name+'.swf'),[src,HERE,MOD/'build/motion-tests',MOD/'build/stubs'])
        if build_only:continue
        code,log=runner.run_air(folder,name+'.swf',150)
        (folder/(name+'.txt')).write_text(log,encoding='utf-8');print(log,flush=True)
        assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log and 'MOTION RED' not in log

def run_checks(name):
    folder=OUT/name
    for harness in ['MaskChecks','SightChecks','SoftHarness','SharedExplorationHarness']:
        code,log=runner.run_air(folder,harness+'.swf',150)
        (folder/(harness+'.txt')).write_text(log,encoding='utf-8');print(log,flush=True)
        assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log and 'MOTION RED' not in log

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','build','run','checks','check-build','check-run','campaign']);p.add_argument('--name',default='profile-01');p.add_argument('--profile',action='store_true');p.add_argument('--large',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--live',action='store_true');p.add_argument('--baseline',default='baseline');a=p.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='checks':checks(a.name)
    elif a.action=='check-build':checks(a.name,True)
    elif a.action=='check-run':run_checks(a.name)
    elif a.action=='build':build(a.name,a.profile,a.large,a.verify,a.live,a.baseline)
    elif a.action=='campaign':
        for name in a.name.split(','):run(name)
    else:run(a.name)
