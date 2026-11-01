from pathlib import Path
import importlib.util,subprocess,shutil,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/eye-boundary-output'
spec=importlib.util.spec_from_file_location('eye_smoke_helpers',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
folder=OUT/sys.argv[1];assert not folder.exists();r.runtime(folder)
probe=folder/'mods/SmokeProbe/release';probe.mkdir(parents=True)
r.runner.compile(HERE/'SmokeProbeMod.as',probe/'SmokeProbeMod.swf',[HERE])
release=folder/'mods/RealisticVision/release';release.mkdir(parents=True)
shutil.copyfile(OUT/'candidate/RealisticVisionMod.swf',release/'RealisticVisionMod.swf');shutil.copyfile(MOD/'release/config.txt',release/'config.txt')
catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True)
(catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text('utf-8-sig')+'\nSmokeProbe|SmokeProbeMod|1|0|0\n','utf8')
p=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only','RealisticVisionMod,SmokeProbeMod','--no-ui','--report',str(folder/'selection.json')],capture_output=True);assert p.returncode==0,p.stdout+p.stderr
with r.Registration(owner='RealisticVision / 正式候选冒烟',purpose=sys.argv[1],resource='game-coexist',run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 code,log=r.air(folder,'pfe.swf',rec,180)
 rvlog=(folder/'storage/RVision.log').read_text('utf8');print(log[-1200:]);print(rvlog[-1200:])
 assert code==0 and 'PRODUCTION SMOKE COMPLETE' in log and 'FAIL ' not in log
 assert 'init ok v0.34.3-eye-boundary' in rvlog and 'onFrame error' not in rvlog
 assert all('ModLoader[ok_'+n+']' in log for n in ['RealisticVisionMod','SmokeProbeMod'])
 r.save(folder/'validation.json',{'passed':True,'production':r.sha(release/'RealisticVisionMod.swf'),'config':r.sha(release/'config.txt'),'host':r.sha(folder/'pfe.swf')})
 rec.outcome='passed';rec.note='正式未插桩候选与当前加载器启动、原生游戏75采样窗无错误；静音独立存档'
