"""Isolated AIR checks for the optional bright wall and unconditional edge repair."""
from pathlib import Path
import argparse,importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
OUT=MOD/'build/wall-options-output'
sys.path.insert(0,str(MOD/'build/wall-surface'))
spec=importlib.util.spec_from_file_location('old_wall_runner',MOD/'build/wall-surface/run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
run_air=runner.run_air
# Six complete captures plus final-stage PNGs exceed the old four-case budget.
runner.run_air=lambda folder,entry,timeout=55:run_air(folder,entry,300 if entry=='pfe.swf' else timeout)

def checks():
    folder=OUT/'checks';source=folder/'src';source.mkdir(parents=True,exist_ok=True)
    for path in (OUT/'candidate/src').rglob('*.as'):
        target=source/path.relative_to(OUT/'candidate/src');target.parent.mkdir(parents=True,exist_ok=True)
        text=re.sub(r'\bprivate\b','public',path.read_text(encoding='utf-8-sig'))
        if path.name=='RealisticVisionMod.as':
            original='File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt")'
            assert text.count(original)==2
            text=text.replace(original,'new File(File.applicationDirectory.nativePath).resolvePath("config-under-test.txt")')
        target.write_text(text,encoding='utf-8')
    # Frozen pre-optimization renderer: compare actual AIR pixels, not a second
    # copy of the optimized formula. It never enters the production SWF.
    reference=(HERE/'reference/RVWallSurface.as').read_text(encoding='utf-8')
    (source/'RepeatedWallSurface.as').write_text(reference.replace('RVWallSurface','RepeatedWallSurface'),encoding='utf-8')
    result={}
    for name in ['BoundaryChecks','DrawOnceChecks','SettingsChecks','SoftHarness','SharedExplorationHarness']:
        entry=HERE/(name+'.as') if (HERE/(name+'.as')).exists() else MOD/'build/motion-tests'/(name+'.as')
        runner.compile(entry,folder/(name+'.swf'),[source,HERE,MOD/'build/motion-tests',MOD/'build/stubs'])
        code,log=runner.run_air(folder,name+'.swf');(folder/(name+'.txt')).write_text(log,encoding='utf-8');print(log,flush=True)
        result[name]={'exit':code,'passed':len(re.findall(r'^PASS ',log,re.M)),'failed':len(re.findall(r'^FAIL ',log,re.M))}
        (folder/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        if code or 'COMPLETE' not in log or result[name]['failed']:raise RuntimeError(name+' failed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['checks','build','game','game-rock','bench']);args=p.parse_args()
    if args.action=='checks':checks()
    elif args.action=='build':
        for variant in ['baseline','candidate']:
            folder=OUT/variant;runner.compile(folder/'src/RealisticVisionMod.as',folder/'RealisticVisionMod.swf',[folder/'src'],stubs=True)
    else:
        runner.OUT=OUT;runner.HERE=HERE
        runner.game(rock=args.action=='game-rock',bench=args.action=='bench')
