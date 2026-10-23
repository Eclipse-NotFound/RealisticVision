"""D42 native effects and mercenary render regression; private AIR/registry."""
from pathlib import Path
import sys,json,shutil,subprocess,argparse,importlib.util
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/effect-visibility-output'
sys.path.insert(0,str(MOD/'build/motion-performance'))
spec=importlib.util.spec_from_file_location('d42_motion_runtime',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.OUT=OUT

def build(name,full=False):
 folder=OUT/name;assert not folder.exists()
 with r.Registration(owner='RealisticVision / D42 特效与狮鹫',purpose=name+' build',run_dir=folder,evidence=folder/'build.json',wait=300) as rec:
  r.runtime(folder)
  s=(MOD/'build/frame-performance/FrameProbe.as').read_text(encoding='utf-8-sig').replace('FrameProbe','EffectVisibilityProbeMod').replace('/RealisticVision/build/frame-performance-output/','/RealisticVision/build/effect-visibility-output/')
  s=s.replace('makeUnits(w);canvas=', 'inspectEffects(w);return;makeUnits(w);canvas=')
  probe=(HERE/'inspect.as.inc').read_text(encoding='utf-8')
  probe=probe.replace('               arm.visible=false;', (HERE/'extra.as.inc').read_text(encoding='utf-8')+'\n               arm.visible=false;')
  s=s.replace('      private function makeUnits(w:*):void{',probe+'\n      private function makeUnits(w:*):void{')
  entry=folder/'EffectVisibilityProbeMod.as';entry.write_text(s,encoding='utf-8')
  r.runner.compile(entry,folder/'mods/EffectVisibilityProbe/release/EffectVisibilityProbeMod.swf',[folder],definitions=['-define=CONFIG::largeScene,false','-define=CONFIG::verifyPixels,false','-define=CONFIG::liveFrames,false'])
  inv=json.loads(subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--list','--json','--no-ui'],capture_output=True,text=True,encoding='utf-8-sig',timeout=45).stdout);r.save(folder/'inventory.json',inv)
  selected=[]
  if full:
   for item in inv['mods']:
    if item['enabled'] and item['entry']!='RealisticVisionMod':
     shutil.copytree(GAME/'mods'/item['directory']/'release',folder/'mods'/item['directory']/'release');selected.append(item['entry'])
  selected.append('EffectVisibilityProbeMod')
  catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
  (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nEffectVisibilityProbe|EffectVisibilityProbeMod|1|0|0\n',encoding='utf-8')
  p=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8-sig',timeout=45);assert p.returncode==0,p.stdout+p.stderr
  for v in ['baseline','candidate']:
   r.public(OUT/v/'src',folder/(v+'-src'));r.runner.compile(folder/(v+'-src/RealisticVisionMod.as'),folder/(v+'.swf'),[folder/(v+'-src')],stubs=True)
  r.save(folder/'build.json',{'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ['.swf','.as','.txt','.xml']}});rec.outcome='passed'

def execute(name):
 folder=OUT/name;assert not (folder/'last-run.json').exists()
 pins=json.loads((folder/'build.json').read_text())['files'];assert all(r.sha(folder/k)==v for k,v in pins.items())
 with r.Registration(owner='RealisticVision / D42 原生显示验证',purpose=name,run_dir=folder,evidence=folder/'evidence/result.json',wait=300) as rec:
  r.save(folder/'launch-state.json',r.environment());code,log=r.air(folder,'pfe.swf',rec,210)
  print('\n'.join([line for line in log.splitlines() if not line.startswith('D42 EFFECT')][-20:]))
  assert code==0 and 'FRAME COMPLETE' in log and 'FAIL ' not in log;rec.outcome='passed'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--full',action='store_true');a=p.parse_args();build(a.name,a.full) if a.action=='build' else execute(a.name)
