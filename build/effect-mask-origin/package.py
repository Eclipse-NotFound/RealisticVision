"""D56 production bytes, with no authority development or test counters."""
from pathlib import Path
import importlib.util,json,re,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/effect-mask-origin-output'
spec=importlib.util.spec_from_file_location('d56_package_runtime',MOD/'build/motion-performance/run.py');run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
PACKAGE=OUT/'production';VERSION='v0.33.11-effect-clip'
run.OUT=OUT

def build():
 assert json.loads((OUT/'current-final-pixels-26/validation.json').read_text())['passed']
 assert not PACKAGE.exists();shutil.copytree(OUT/'candidates/grid_current/src',PACKAGE/'src')
 p=PACKAGE/'src/RealisticVisionMod.as';s=p.read_text();assert s.count('v0.33.10-render-cache')==1
 p.write_text(s.replace('v0.33.10-render-cache',VERSION),encoding='utf-8',newline='\n')
 assert 'trailingHits' not in s and not list((PACKAGE/'src').rglob('*Authority*'))
 run.runner.compile(p,PACKAGE/'RealisticVisionMod.swf',[PACKAGE/'src'],stubs=True)
 probe=MOD/'build/vision-settings-output/options-final/CandidateOptionsProbe.as'
 run.runner.compile(probe,PACKAGE/'CandidateOptionsProbe.swf',[probe.parent],definitions=['-include-libraries='+str(MOD/'build/GameStubs.swc')])
 run.save(PACKAGE/'build.json',{'version':VERSION,'swf':run.sha(PACKAGE/'RealisticVisionMod.swf'),'bytes':(PACKAGE/'RealisticVisionMod.swf').stat().st_size,'sources':{p.relative_to(PACKAGE/'src').as_posix():run.sha(p) for p in (PACKAGE/'src').rglob('*.as')}})

def inspect():
 target=PACKAGE/'RealisticVisionMod.swf'
 proc=subprocess.run([str(run.runner.JAVA),'-jar',str(GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'),'-dumpAS3',str(target)],capture_output=True,timeout=60);assert proc.returncode==0
 output=proc.stdout.decode('utf-8',errors='replace');(PACKAGE/'classes.txt').write_text(output,encoding='utf-8')
 classes=set(re.findall(r'^([\w.]+) \d+$',output.replace('\r',''),re.M))
 assert classes=={'RealisticVisionMod','RVWallSurface','RVExplorationCarrier','RVKeybinds','modlocales.vision.RVLocale','modlocales.vision.RVLocaleMessages'},classes
 proof=json.loads((PACKAGE/'build.json').read_text());assert proof['swf']==run.sha(target);proof['classes']=sorted(classes);run.save(PACKAGE/'manifest.json',proof)
 print(json.dumps({'version':VERSION,'swf':proof['swf'],'bytes':proof['bytes'],'classes':proof['classes']}))

def check():
 proof=json.loads((PACKAGE/'manifest.json').read_text());assert run.sha(PACKAGE/'RealisticVisionMod.swf')==proof['swf']
 with run.Registration(owner='RealisticVision / D56 准确包设置',purpose=VERSION,run_dir=PACKAGE,evidence=PACKAGE/'settings.json',wait=900) as rec:
  previous=None;results=[]
  for name in ['first','restored']:
   folder=PACKAGE/name;folder.mkdir(exist_ok=False)
   shutil.copyfile(PACKAGE/'RealisticVisionMod.swf',folder/'candidate.swf');shutil.copyfile(PACKAGE/'CandidateOptionsProbe.swf',folder/'CandidateOptionsProbe.swf')
   code,log=run.air(folder,'CandidateOptionsProbe.swf',rec,90,previous)
   result=json.loads((folder/'last-run.json').read_text());result['passed']=len(re.findall(r'^PASS ',log,re.M));results.append(result);run.save(PACKAGE/'settings.json',results)
   assert code==0 and 'INSTALLED OPTIONS COMPLETE passed=18' in log and 'FAIL ' not in log
   assert ('restoring=true' if previous else 'restoring=false') in log
   runtime=(folder/'storage/RVision.log').read_text(encoding='utf-8-sig');assert 'init ok '+VERSION in runtime
   previous=folder/'storage'
  rec.outcome='passed';rec.note='准确生产包两进程36设置断言及tick181通过'
 print('Production settings PASS 36')

if __name__=='__main__':{'build':build,'inspect':inspect,'check':check}[sys.argv[1]]()
