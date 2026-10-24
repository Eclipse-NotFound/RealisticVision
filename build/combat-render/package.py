"""D44 exact six-class package; source excludes unpublished authority work."""
from pathlib import Path
import importlib.util,json,re,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
spec=importlib.util.spec_from_file_location('d44_package_runtime',HERE/'run.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
run=d.r;OUT=d.OUT;GAME=d.GAME;PACKAGE=OUT/'production-final2';VERSION='v0.33.10-render-cache'
run.OUT=OUT

def build():
 assert not PACKAGE.exists()
 with run.Registration(owner='RealisticVision / D44 正式包构建',purpose=VERSION,run_dir=PACKAGE,evidence=PACKAGE/'manifest.json',resource='offline') as rec:
  shutil.copytree(OUT/'candidates/bindings/src',PACKAGE/'src')
  source=PACKAGE/'src/RealisticVisionMod.as';text=source.read_text(encoding='utf-8');assert 'v0.33.9-effect-load' in text
  source.write_text(text.replace('v0.33.9-effect-load',VERSION),encoding='utf-8',newline='\n')
  run.runner.compile(source,PACKAGE/'RealisticVisionMod.swf',[PACKAGE/'src'],stubs=True)
  probe=MOD/'build/vision-settings-output/options-final/CandidateOptionsProbe.as'
  run.runner.compile(probe,PACKAGE/'CandidateOptionsProbe.swf',[probe.parent],definitions=['-include-libraries='+str(MOD/'build/GameStubs.swc')])
  run.save(PACKAGE/'build.json',{'version':VERSION,'swf':run.sha(PACKAGE/'RealisticVisionMod.swf'),'bytes':(PACKAGE/'RealisticVisionMod.swf').stat().st_size,'sources':{p.relative_to(PACKAGE/'src').as_posix():run.sha(p) for p in (PACKAGE/'src').rglob('*.as')}});rec.outcome='passed'

def inspect():
 target=PACKAGE/'RealisticVisionMod.swf'
 p=subprocess.run([str(run.runner.JAVA),'-jar',str(GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'),'-dumpAS3',str(target)],capture_output=True,timeout=60);assert p.returncode==0
 output=p.stdout.decode('utf-8',errors='replace');(PACKAGE/'classes.txt').write_text(output,encoding='utf-8')
 classes=set(re.findall(r'^([\w.]+) \d+$',output.replace('\r',''),re.M))
 assert classes=={'RealisticVisionMod','RVWallSurface','RVExplorationCarrier','RVKeybinds','modlocales.vision.RVLocale','modlocales.vision.RVLocaleMessages'},classes
 proof=json.loads((PACKAGE/'build.json').read_text());assert proof['swf']==run.sha(target);proof['classes']=sorted(classes);run.save(PACKAGE/'manifest.json',proof);print(proof)

def check():
 proof=json.loads((PACKAGE/'manifest.json').read_text());assert run.sha(PACKAGE/'RealisticVisionMod.swf')==proof['swf']
 with run.Registration(owner='RealisticVision / D44 准确包设置',purpose=VERSION,run_dir=PACKAGE,evidence=PACKAGE/'settings.json',wait=900) as rec:
  results=[];previous=None
  for name in ['first','restored']:
   folder=PACKAGE/name;folder.mkdir(exist_ok=False)
   shutil.copyfile(PACKAGE/'RealisticVisionMod.swf',folder/'candidate.swf');shutil.copyfile(PACKAGE/'CandidateOptionsProbe.swf',folder/'CandidateOptionsProbe.swf')
   code,log=run.air(folder,'CandidateOptionsProbe.swf',rec,90,previous)
   result=json.loads((folder/'last-run.json').read_text());result['passed']=len(re.findall(r'^PASS ',log,re.M));results.append(result);run.save(PACKAGE/'settings.json',results)
   print('\n'.join(log.splitlines()[-4:]));assert code==0 and 'INSTALLED OPTIONS COMPLETE passed=18' in log and 'FAIL ' not in log
   assert ('restoring=true' if previous else 'restoring=false') in log
   previous=folder/'storage'
  rec.outcome='passed'

if __name__=='__main__':{'build':build,'inspect':inspect,'check':check}[sys.argv[1]]()
