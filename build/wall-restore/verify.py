from pathlib import Path
import sys,importlib.util,re,json,shutil,argparse,os,hashlib
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1];OUT=MOD/'build/wall-restore-output'
sys.path.append(str(MOD/'build/wall-surface'))
spec=importlib.util.spec_from_file_location('wall_runner',MOD/'build/wall-surface/run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
runner.HERE=HERE;runner.OUT=OUT

def public_source(variant,folder):
    for path in (OUT/variant/'src').rglob('*.as'):
        dest=folder/path.relative_to(OUT/variant/'src');dest.parent.mkdir(parents=True,exist_ok=True)
        text=re.sub(r'\bprivate\b','public',path.read_text(encoding='utf-8-sig'))
        if path.name=='RealisticVisionMod.as':
            text=text.replace('File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt")',
                              'new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt")')
        dest.write_text(text,encoding='utf-8')

def checks(variant,compile_only=False):
    folder=OUT/('checks-'+variant);source=folder/'src';public_source(variant,source)
    names=['RestoreChecks'] if variant=='baseline' else ['RestoreChecks','ContourCacheChecks','SettingsChecks','SoftHarness','SharedExplorationHarness']
    reference=(HERE/'reference/RVWallSurface.as').read_text(encoding='utf-8')
    (source/'FullScanWallSurface.as').write_text(reference.replace('RVWallSurface','FullScanWallSurface'),encoding='utf-8')
    settings=(MOD/'build/wall-options/SettingsChecks.as').read_text(encoding='utf-8')
    settings=settings.replace('item.def===true&&item.get()===true','item.def===false&&item.get()===false').replace('default-on','default-off')
    settings=settings.replace('item.set(false);','item.set(true);item.set(false);')
    settings=settings.replace('next.cfgWallBright===true,"old configs','next.cfgWallBright===false,"old configs')
    settings=settings.replace('next.cfgWallBright===true,"invalid config','next.cfgWallBright===false,"invalid config')
    (source/'SettingsChecks.as').write_text(settings,encoding='utf-8')
    results={}
    for name in names:
        entry=next(p for p in [HERE/(name+'.as'),source/(name+'.as'),MOD/'build/motion-tests'/(name+'.as')] if p.exists())
        runner.compile(entry,folder/(name+'.swf'),[source,HERE,MOD/'build/motion-tests',MOD/'build/stubs'])
        if compile_only:continue
        code,log=runner.run_air(folder,name+'.swf');(folder/(name+'.txt')).write_text(log,encoding='utf-8');print(log,flush=True)
        results[name]={'exit':code,'passed':len(re.findall(r'^PASS ',log,re.M)),'failed':len(re.findall(r'^FAIL ',log,re.M))}
        (folder/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        if variant=='baseline':
            assert code==1 and 'FAIL OFF every material pixel preserves' in log,'Must detect old rim repaint'
        elif code or 'COMPLETE' not in log or results[name]['failed']:raise RuntimeError(name+' failed')

def game(rock=False,bench=False):
    folder=OUT/('bench' if bench else 'game-rock' if rock else 'game');folder.mkdir(exist_ok=True)
    (folder/'evidence').mkdir(exist_ok=True)
    for path in runner.GAME.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',path.name):
            dest=folder/path.name
            if not dest.exists():
                frozen=OUT/'game-rock'/path.name
                if not frozen.exists():frozen=OUT/'game-rock-full-alpha'/path.name
                if frozen.exists() and frozen!=dest and hashlib.sha256(frozen.read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest():
                    os.link(frozen,dest)
                else:shutil.copy2(path,dest)
    shutil.copytree(runner.GAME/'Rooms',folder/'Rooms',dirs_exist_ok=True)
    boot=folder/'mods/WallSurfaceProbe/release';boot.mkdir(parents=True,exist_ok=True)
    runner.compile(HERE/'WallSurfaceProbe.as',boot/'WallSurfaceProbe.swf',[HERE],definitions=['-define=CONFIG::rockFixture,'+str(rock).lower(),'-define=CONFIG::wallBench,'+str(bench).lower()])
    (folder/'mods/loader-manifest.txt').write_text('WallSurfaceProbe|WallSurfaceProbe|1|0|0\n',encoding='utf-8')
    for variant in ['baseline','legacy','candidate']:
        source=folder/(variant+'-src');public_source(variant,source)
        runner.compile(source/'RealisticVisionMod.as',folder/(variant+'.swf'),[source],stubs=True)
    code,log=runner.run_air(folder,'pfe.swf',300)
    (folder/'game.log').write_text(log,encoding='utf-8');print('\n'.join(log.splitlines()[-45:]),flush=True)
    if code or 'SURFACE GAME COMPLETE' not in log or 'FAIL ' in log:raise RuntimeError('Full game capture failed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','compile-checks','red','checks','game','game-rock','bench']);args=p.parse_args()
    if args.action=='build':
        for variant in ['baseline','legacy','candidate']:
            src=OUT/variant/'src';runner.compile(src/'RealisticVisionMod.as',src.parent/'RealisticVisionMod.swf',[src],stubs=True)
    elif args.action=='compile-checks':checks('baseline',True);checks('candidate',True)
    elif args.action in ['red','checks']:checks('baseline' if args.action=='red' else 'candidate')
    else:game(rock=args.action=='game-rock',bench=args.action=='bench')
