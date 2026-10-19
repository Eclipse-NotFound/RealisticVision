"""D30 stair-shadow regression; isolated, pinned D29 baseline, no release writes."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, shutil, sys
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
OUT=MOD/'build/stair-shadow-output'
BASE=MOD/'build/wall-performance-output/candidate'
sys.path.insert(0,str(MOD/'build/wall-surface'))
spec=importlib.util.spec_from_file_location('surface_runner',MOD/'build/wall-surface/run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def candidate_text(p):
    text=p.read_text(encoding='utf-8-sig')
    if p.name=='RealisticVisionMod.as':text=text.replace('v0.32.1-wall-performance','v0.32.2-stair-candidate')
    if p.name=='RVWallSurface.as':
        old='         return heights[int(x/CELL)+1+(int(y/CELL)+1)*(cols+2)]>0?0:2;'
        new='''         // A partial tile can still be opaque (e.g. native C;F decoding).
         // Its cut-away top is open space, not a material notch. The contour
         // field's zero-valued filter halo must not replace that original fog.
         var h:int=heights[int(x/CELL)+1+(int(y/CELL)+1)*(cols+2)];
         return h>0 && y%CELL>=CELL-h?0:2;'''
        assert text.count(old)==1;text=text.replace(old,new)
    return text
def prepare():
    assert sha(BASE/'RealisticVisionMod.swf')=='2e7150cf415355c2d7b809689aac3c4ca0bacbb5f6d8770066a6e887d8907a10'
    OUT.mkdir(exist_ok=True)
    for variant in ['baseline','candidate']:
        for p in (BASE/'src').rglob('*.as'):
            q=OUT/variant/'src'/p.relative_to(BASE/'src')
            if variant=='candidate' and p.name in ['RealisticVisionMod.as','RVWallSurface.as']:
                text=candidate_text(p)
                if q.exists():assert q.read_text(encoding='utf-8-sig')==text,'Candidate drift: '+str(q)
                else:q.parent.mkdir(parents=True,exist_ok=True);q.write_text(text,encoding='utf-8')
            elif not q.exists():q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
            else:assert sha(p)==sha(q)
    pins={p.relative_to(BASE/'src').as_posix():sha(p) for p in (BASE/'src').rglob('*.as')}
    p=HERE/'inputs.json'
    if p.exists():assert json.loads(p.read_text())==pins
    else:p.write_text(json.dumps(pins,indent=2),encoding='utf-8')
def public_source(variant,dest):
    for p in (OUT/variant/'src').rglob('*.as'):
        q=dest/p.relative_to(OUT/variant/'src');q.parent.mkdir(parents=True,exist_ok=True)
        text=re.sub(r'\bprivate\b','public',p.read_text(encoding='utf-8-sig'))
        text=text.replace('File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt")','new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt")')
        q.write_text(text,encoding='utf-8')
def game(name,run=False):
    folder=OUT/name;folder.mkdir(exist_ok=True);(folder/'evidence').mkdir(exist_ok=True)
    if run:
        code,log=runner.run_air(folder,'pfe.swf',200)
        (folder/'game.log').write_text(log,encoding='utf-8');print('\n'.join(log.splitlines()[-40:]),flush=True)
        assert code==0 and 'SURFACE GAME COMPLETE' in log and 'FAIL ' not in log
        return
    frozen=MOD/'build/wall-restore-output/game-rock'
    for p in frozen.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):
            source=MOD/'build/wall-performance-output/runtime-inputs/pfe.swf' if p.name=='pfe.swf' else p
            target=folder/p.name
            if not target.exists():shutil.copyfile(source,target)
            assert sha(source)==sha(target)
    if not (folder/'Rooms').exists():shutil.copytree(frozen/'Rooms',folder/'Rooms')
    boot=folder/'mods/WallSurfaceProbe/release';boot.mkdir(parents=True,exist_ok=True)
    runner.compile(HERE/'WallSurfaceProbe.as',boot/'WallSurfaceProbe.swf',[HERE],definitions=['-define=CONFIG::rockFixture,false','-define=CONFIG::wallBench,false'])
    (folder/'mods/loader-manifest.txt').write_text('WallSurfaceProbe|WallSurfaceProbe|1|0|0\n',encoding='utf-8')
    for v in ['baseline','candidate']:
        src=folder/(v+'-src');public_source(v,src)
        runner.compile(src/'RealisticVisionMod.as',folder/(v+'.swf'),[src],stubs=True)
def checks(name,run=True):
    folder=OUT/name;src=folder/'src';public_source('candidate',src)
    for p in ['RVWallSurface.as','RealisticVisionMod.as']:
        text=(OUT/'baseline/src'/p).read_text(encoding='utf-8-sig')
        text=re.sub(r'\bprivate\b','public',text).replace('RealisticVisionMod','BaselineVision').replace('RVWallSurface','BaselineWallSurface')
        (src/('BaselineVision.as' if p=='RealisticVisionMod.as' else 'BaselineWallSurface.as')).write_text(text,encoding='utf-8')
    entry=HERE/'StairChecks.as'
    runner.compile(entry,folder/'StairChecks.swf',[src,HERE,MOD/'build/stubs'])
    if not run:return
    code,log=runner.run_air(folder,'StairChecks.swf')
    (folder/'checks.txt').write_text(log,encoding='utf-8');print(log,flush=True)
    assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
def regression(run=True):
    folder=OUT/'regression';src=folder/'src';public_source('candidate',src)
    text=(OUT/'baseline/src/RVWallSurface.as').read_text(encoding='utf-8-sig').replace('RVWallSurface','BaselineWallSurface')
    (src/'BaselineWallSurface.as').write_text(text,encoding='utf-8')
    # Planned behavior changes only in cut-away air of opaque partial tiles.
    # Keep the original dynamic-light/material suite with full-height geometry
    # for strict equality; StairChecks separately asserts the corrected geometry.
    text=(MOD/'build/wall-performance/EquivalenceChecks.as').read_text(encoding='utf-8')
    text=text.replace('tiles[2+2*10].zForm=frame%3;','tiles[2+2*10].zForm=0;')
    text=text.replace('changing light, partial wall, alpha and option','changing light, full wall, alpha and option')
    (src/'EquivalenceChecks.as').write_text(text,encoding='utf-8')
    shutil.copyfile(MOD/'build/wall-restore-output/checks-candidate/src/SettingsChecks.as',src/'SettingsChecks.as')
    results={}
    for name in ['EquivalenceChecks','RestoreChecks','SettingsChecks','SoftHarness','SharedExplorationHarness']:
        entry=next(p for p in [src/(name+'.as'),MOD/'build/wall-restore'/(name+'.as'),MOD/'build/motion-tests'/(name+'.as')] if p.exists())
        runner.compile(entry,folder/(name+'.swf'),[src,MOD/'build/wall-restore',MOD/'build/motion-tests',MOD/'build/stubs'])
        if not run:continue
        code,log=runner.run_air(folder,name+'.swf');(folder/(name+'.txt')).write_text(log,encoding='utf-8');print(log,flush=True)
        results[name]={'exit':code,'passed':len(re.findall(r'^PASS ',log,re.M)),'failed':len(re.findall(r'^FAIL ',log,re.M))}
        (folder/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        assert code==0 and 'COMPLETE' in log and not results[name]['failed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','compile-game','run-game','checks','compile-checks','regression','compile-regression','build']);p.add_argument('--name',default='diagnostic');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action in ['checks','compile-checks']:checks(a.name,a.action=='checks')
    elif a.action in ['regression','compile-regression']:regression(a.action=='regression')
    elif a.action=='build':
        src=OUT/'candidate/src';runner.compile(src/'RealisticVisionMod.as',src.parent/'RealisticVisionMod.swf',[src],stubs=True)
    else:game(a.name,a.action=='run-game')
