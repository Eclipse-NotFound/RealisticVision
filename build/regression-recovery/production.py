"""Freeze exact six-class D35 bytes and test the real settings entry points."""
import argparse, json, re, shutil, subprocess
import investigate
run=investigate.r
MOD,GAME,OUT=investigate.MOD,investigate.GAME,investigate.OUT
PACKAGE=OUT/'production-singlepass'
VERSION='v0.33.2-settings-performance'

def build():
 assert not PACKAGE.exists()
 with run.Registration(owner='RealisticVision / D35 正式包构建',purpose=VERSION,run_dir=PACKAGE,evidence=PACKAGE/'manifest.json',wait=300) as rec:
  shutil.copytree(investigate.SOURCES['fixed6'],PACKAGE/'src')
  target=PACKAGE/'RealisticVisionMod.swf';src=PACKAGE/'src'
  run.runner.compile(src/'RealisticVisionMod.as',target,[src],stubs=True)
  probe=MOD/'build/vision-settings-output/options-final/CandidateOptionsProbe.as'
  run.runner.compile(probe,PACKAGE/'CandidateOptionsProbe.swf',[probe.parent],definitions=['-include-libraries='+str(MOD/'build/GameStubs.swc')])
  cmd=[str(run.runner.JAVA),'-jar',str(GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'),'-dumpAS3',str(target)]
  result=subprocess.run(cmd,capture_output=True,timeout=60);assert result.returncode==0
  output=result.stdout.decode('utf-8',errors='replace');(PACKAGE/'classes.txt').write_text(output,encoding='utf-8')
  classes=set(re.findall(r'^([\w.]+) \d+$',output.replace('\r',''),re.M))
  assert classes=={'RealisticVisionMod','RVWallSurface','RVExplorationCarrier','RVKeybinds','modlocales.vision.RVLocale','modlocales.vision.RVLocaleMessages'},classes
  run.save(PACKAGE/'manifest.json',{'version':VERSION,'swf':run.sha(target),'bytes':target.stat().st_size,'sources':{p.relative_to(src).as_posix():run.sha(p) for p in src.rglob('*.as')},'classes':sorted(classes)})
  rec.outcome='passed'

def check():
 proof=json.loads((PACKAGE/'manifest.json').read_text());assert run.sha(PACKAGE/'RealisticVisionMod.swf')==proof['swf']
 with run.Registration(owner='RealisticVision / D35 准确包设置',purpose='真实生产字节、改键和参数跨进程保存',run_dir=PACKAGE,evidence=PACKAGE/'settings.json',wait=300) as rec:
  results=[];previous=None
  for name in ['first','restored']:
   folder=PACKAGE/name;folder.mkdir(exist_ok=False)
   shutil.copyfile(PACKAGE/'RealisticVisionMod.swf',folder/'candidate.swf');shutil.copyfile(PACKAGE/'CandidateOptionsProbe.swf',folder/'CandidateOptionsProbe.swf')
   code,log=run.air(folder,'CandidateOptionsProbe.swf',rec,90,previous)
   result=json.loads((folder/'last-run.json').read_text());result['passed']=len(re.findall(r'^PASS ',log,re.M));results.append(result);run.save(PACKAGE/'settings.json',results)
   print('\n'.join(log.splitlines()[-4:]),flush=True)
   assert code==0 and 'INSTALLED OPTIONS COMPLETE passed=18' in log and 'FAIL ' not in log
   assert ('restoring=true' if previous else 'restoring=false') in log
   previous=folder/'storage'
  rec.outcome='passed';rec.note='36项准确包设置入口与跨进程保存通过'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','check']);a=p.parse_args();build() if a.action=='build' else check()
