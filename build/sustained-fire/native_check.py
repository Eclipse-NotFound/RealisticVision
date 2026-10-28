"""Native effect, griffon, filter and ownership checks on the D54 candidate."""
from pathlib import Path
import importlib.util,shutil,sys,re,json
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/sustained-fire-output'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v=load('d54_native_validation',MOD/'build/combat-render/validate.py')
v.OUT=OUT;r=v.r
media=load('d54_native_media',MOD/'build/candidate-comparison/runtime.py');media.bind(r)
BASE=MOD/'build/combat-render-output/production-final2/src'
def freeze():
 dest=OUT/'baseline/src'
 if not dest.exists():shutil.copytree(BASE,dest)
 assert {p.name:r.sha(p) for p in dest.rglob('*.as')}=={p.name:r.sha(p) for p in BASE.rglob('*.as')}
v.freeze=freeze
compile_original=r.runner.compile
def compile_probe(entry,*a,**k):
 if entry.name=='EffectVisibilityProbeMod.as':
  s=entry.read_text().replace('/RealisticVision/build/combat-render-output/','/RealisticVision/build/sustained-fire-output/')
  s=s.replace('package {','package {\nimport flash.media.SoundMixer;import flash.media.SoundTransform;')
  s=s.replace('if(main==null)return;','if(main==null)return;SoundMixer.soundTransform=new SoundTransform(0);')
  s=s.replace('private function tick(e:Event):void{','private function tick(e:Event):void{SoundMixer.soundTransform=new SoundTransform(0);')
  entry.write_text(s,encoding='utf-8')
 return compile_original(entry,*a,**k)
r.runner.compile=compile_probe
name=sys.argv[1];folder=OUT/name;assert not folder.exists()
with r.Registration(owner='RealisticVision / D54 原生视觉',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 v.native_build(name,'direct-cache' if '--direct-cache' in sys.argv else 'pixel-cache' if '--pixel-cache' in sys.argv else 'integer-v2' if '--integer-v2' in sys.argv else 'integer' if '--integer' in sys.argv else 'trailing-current' if '--current-only' in sys.argv else 'trailing-v2')
 code,log=r.air(folder,'pfe.swf',rec,300)
 (folder/'result.txt').write_text(log,encoding='utf-8')
 ok=code==0 and 'FRAME COMPLETE' in log and not re.search(r'^FAIL ',log,re.M)
 r.save(folder/'validation.json',{'passed':ok,'exit':code,'checks':len(re.findall(r'^PASS ',log,re.M))})
 print(log[-1500:]);assert ok;rec.outcome='passed';rec.note='原生动画、滤镜、遮挡与恢复的严格功能检查'
