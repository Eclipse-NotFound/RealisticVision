from pathlib import Path
import importlib.util,sys,subprocess,shutil,json
HERE=Path(__file__).resolve().parent; MOD=HERE.parents[1]; GAME=MOD.parents[1]; OUT=MOD/'build/eye-boundary-output'
spec=importlib.util.spec_from_file_location('eye_helpers',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
name=sys.argv[1]; folder=OUT/name; assert not folder.exists(); folder.mkdir()
for v in ('baseline','candidate'):
 r.public(OUT/v/'src',folder/(v+'-src'))
 r.runner.compile(folder/(v+'-src/RealisticVisionMod.as'),folder/(v+'.swf'),[folder/(v+'-src')],stubs=True)
r.runner.compile(OUT/'candidate/src/RealisticVisionMod.as',OUT/'candidate/RealisticVisionMod.swf',[OUT/'candidate/src'],stubs=True)
r.runtime(folder)
probe=folder/'mods/EyeBoundaryProbe/release';probe.mkdir(parents=True)
r.runner.compile(HERE/'EyeBoundaryProbeMod.as',probe/'EyeBoundaryProbeMod.swf',[HERE])
catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True)
(catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text('utf-8-sig')+'\nEyeBoundaryProbe|EyeBoundaryProbeMod|1|0|0\n','utf8')
a=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only','EyeBoundaryProbeMod','--no-ui','--report',str(folder/'selection.json')],capture_output=True)
assert a.returncode==0,a.stdout+a.stderr
r.save(folder/'inputs.json',{'production':r.sha(OUT/'candidate/RealisticVisionMod.swf'),'host':r.sha(folder/'pfe.swf')})
with r.Registration(owner='RealisticVision / 眼部与弹道边界修复',purpose=name,resource='game-coexist',run_dir=folder,evidence=folder/'evidence/result.json',wait=900) as rec:
 code,log=r.air(folder,'pfe.swf',rec,180)
 print(log[-4000:]);assert code==0 and 'BOUNDARY COMPLETE' in log and 'FAIL ' not in log
 assert 'ModLoader[ok_EyeBoundaryProbeMod]' in log
 rec.outcome='passed';rec.note='原生玩家眼部姿态、视野刷新与弹体跨边界渲染断言通过；非性能基准'
