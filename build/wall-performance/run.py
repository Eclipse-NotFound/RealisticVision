"""Pixel equivalence and paired timing, isolated from historical experiments."""
from pathlib import Path
import sys,importlib.util,re,json,shutil,argparse,os,hashlib
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/wall-performance-output'
sys.path.append(str(MOD/'build/wall-surface'))
spec=importlib.util.spec_from_file_location('wall_runner',MOD/'build/wall-surface/run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
runner.HERE=HERE;runner.OUT=OUT
def profile(s):
    s=s.replace('import flash.display.Bitmap;','import flash.utils.getTimer;\n   import flash.display.Bitmap;')
    s=s.replace('private var owner:*;','public var profile:Array=[0,0,0,0,0,0];\n      private var owner:*;')
    anchors=[('var requested:int=alwaysBright?1:0;','var pt:int=getTimer();\n         var requested:int=alwaysBright?1:0;'),
      ('var count:int=0;','profile[0]+=getTimer()-pt;pt=getTimer();\n         var count:int=0;'),
      ('var fieldChanged:Boolean=fieldShapeDirty;','profile[1]+=getTimer()-pt;pt=getTimer();\n         var fieldChanged:Boolean=fieldShapeDirty;'),
      ('wallPixels.visible=count>0;','profile[2]+=getTimer()-pt;\n         wallPixels.visible=count>0;'),
      ('baseLight.fillRect(baseLight.rect,0xffffff);','pt=getTimer();\n         baseLight.fillRect(baseLight.rect,0xffffff);'),
      ('for each(var piece:Object in pieces){','profile[3]+=getTimer()-pt;pt=getTimer();\n         for each(var piece:Object in pieces){'),
      ('if(updated)terrainUpdates++;','profile[4]+=getTimer()-pt;\n         if(updated)terrainUpdates++;'),
      ('if(contourFog==null||contourFog.width','var ct:int=getTimer();\n         if(contourFog==null||contourFog.width'),
      ('}else base.mask=baseClip;','}else base.mask=baseClip;\n         profile[5]+=getTimer()-ct;')]
    for a,b in anchors:
        assert s.count(a)==1,a;s=s.replace(a,b)
    return s
def public_source(variant,folder,instrument=False):
    for p in (OUT/variant/'src').rglob('*.as'):
        dest=folder/p.relative_to(OUT/variant/'src');dest.parent.mkdir(parents=True,exist_ok=True)
        text=p.read_text(encoding='utf-8-sig')
        if instrument and p.name=='RVWallSurface.as':text=profile(text)
        text=re.sub(r'\bprivate\b','public',text)
        text=text.replace('File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt")','new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt")')
        dest.write_text(text,encoding='utf-8')
def compile_game(name,rock=False,bench=False,instrument=False):
    folder=OUT/name;folder.mkdir(exist_ok=True);(folder/'evidence').mkdir(exist_ok=True)
    frozen=MOD/'build/wall-restore-output/game-rock'
    for p in frozen.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):
            dest=folder/p.name
            source=OUT/'runtime-inputs/pfe.swf' if p.name=='pfe.swf' else p
            if not dest.exists():shutil.copyfile(source,dest)
            assert hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest(),str(dest)
    if not (folder/'Rooms').exists():shutil.copytree(frozen/'Rooms',folder/'Rooms')
    boot=folder/'mods/WallSurfaceProbe/release';boot.mkdir(parents=True,exist_ok=True)
    runner.compile(HERE/'WallSurfaceProbe.as',boot/'WallSurfaceProbe.swf',[HERE],definitions=['-define=CONFIG::rockFixture,'+str(rock).lower(),'-define=CONFIG::wallBench,'+str(bench).lower()])
    (folder/'mods/loader-manifest.txt').write_text('WallSurfaceProbe|WallSurfaceProbe|1|0|0\n',encoding='utf-8')
    for v in ['baseline','candidate']:
        src=folder/(v+'-src');public_source(v,src,instrument)
        runner.compile(src/'RealisticVisionMod.as',folder/(v+'.swf'),[src],stubs=True)
def run_game(name):
    folder=OUT/name;code,log=runner.run_air(folder,'pfe.swf',300)
    (folder/'game.log').write_text(log,encoding='utf-8');print('\n'.join(log.splitlines()[-35:]),flush=True)
    assert code==0 and 'SURFACE GAME COMPLETE' in log and 'FAIL ' not in log
def checks(run=True):
    folder=OUT/'checks';src=folder/'src';public_source('candidate',src)
    baseline=(OUT/'baseline/src/RVWallSurface.as').read_text(encoding='utf-8')
    (src/'BaselineWallSurface.as').write_text(baseline.replace('RVWallSurface','BaselineWallSurface'),encoding='utf-8')
    # Reuse the already validated settings defaults and logical regressions.
    shutil.copyfile(MOD/'build/wall-restore-output/checks-candidate/src/SettingsChecks.as',src/'SettingsChecks.as')
    results={}
    for name in ['EquivalenceChecks','RestoreChecks','SettingsChecks','SoftHarness','SharedExplorationHarness']:
        entry=next(p for p in [HERE/(name+'.as'),src/(name+'.as'),MOD/'build/wall-restore'/(name+'.as'),MOD/'build/motion-tests'/(name+'.as')] if p.exists())
        runner.compile(entry,folder/(name+'.swf'),[src,HERE,MOD/'build/wall-restore',MOD/'build/motion-tests',MOD/'build/stubs'])
        if not run:continue
        code,log=runner.run_air(folder,name+'.swf');(folder/(name+'.txt')).write_text(log,encoding='utf-8');print(log,flush=True)
        results[name]={'exit':code,'passed':len(re.findall(r'^PASS ',log,re.M)),'failed':len(re.findall(r'^FAIL ',log,re.M))}
        (folder/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        assert code==0 and 'COMPLETE' in log and not results[name]['failed']
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['compile-game','run-game','checks','compile-checks','build']);p.add_argument('--name',default='profile');p.add_argument('--rock',action='store_true');p.add_argument('--bench',action='store_true');p.add_argument('--profile',action='store_true');a=p.parse_args()
    if a.action=='compile-game':compile_game(a.name,a.rock,a.bench,a.profile)
    elif a.action=='run-game':run_game(a.name)
    elif a.action in ['checks','compile-checks']:checks(a.action=='checks')
    else:
        src=OUT/'candidate/src';runner.compile(src/'RealisticVisionMod.as',src.parent/'RealisticVisionMod.swf',[src],stubs=True)
