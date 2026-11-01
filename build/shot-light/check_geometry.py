"""Exact makeLight bodies extracted from frozen baseline and candidate."""
from pathlib import Path
import importlib.util,json,re,sys
from candidate import extract
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output';HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('shot_geometry_checks',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
folder=OUT/sys.argv[1];assert not folder.exists();folder.mkdir()
with r.Registration(owner='RealisticVision / 灯光轮廓等价',purpose=folder.name,run_dir=folder,evidence=folder/'validation.json',wait=1800) as rec:
 selected='direct-circle-candidate' if '--direct-circle' in sys.argv else 'direct-full-candidate' if '--direct-full' in sys.argv else 'direct-candidate' if '--direct' in sys.argv else 'geometry-candidate'
 for variant,name in [('lighting-baseline','BaselineFan'),(selected,'CandidateFan')]:
  original=OUT/variant/'src/lad/LadLightField.as';s=original.read_text('utf8')
  functions=extract(s,'private function makeLight(')+'\n'+extract(s,'public function traceRay(')
  if 'private function maskedMakeLight(' in s:functions+='\n'+extract(s,'private function maskedMakeLight(')
  functions=functions.replace('private function makeLight(','public function makeLight(').replace('/* SHOT_GEOMETRY_REUSE */','reuses++;')
  functions=functions.replace('/* SHOT_DIRECT_FULL */','reuses++;')
  if variant.startswith('direct-'):functions=functions.replace('makeLight(light:Object):','makeLight(light:Object,previous:Object=null):')
  source='package {import flash.display.*;import flash.geom.*;public class '+name+' {public const cell:int=12;public var loc:*;public var reuses:int=0;\n'+functions+'\n}}'
  (folder/(name+'.as')).write_text(source,'utf8',newline='\n')
 checks=(HERE/'GeometryChecks.as').read_text('utf8')
 if selected.startswith('direct-'):checks=checks.replace('if(candidate.reuses<50)','if(false)')
 if '--circle-stress' in sys.argv:
  assert selected=='direct-circle-candidate'
  checks=checks.replace('f<900','f<1800').replace('room(int(f/300))','room(int(f/300)%3)')
  checks=checks.replace('var previous:BitmapData=entry.data,','light.cone=Math.PI*2;light.x=rnd()*2560;light.y=rnd()*1920;light.radius=[1,12,44.5,85,180,360,440][f%7]+(f%3==0?.125:0);var previous:BitmapData=entry.data,')
  checks=checks.replace('if(false)throw new Error("insufficient reuse "+candidate.reuses);','if(candidate.reuses!=1800)throw new Error("direct path coverage "+candidate.reuses);')
  if '--valid-projectile' in sys.argv:
   checks=checks.replace('f<1800','f<4800').replace('candidate.reuses!=1800','candidate.reuses!=4800')
   checks=checks.replace('var previous:BitmapData=entry.data,','light.transient=true;light.radius=Math.min(360,light.radius);loc.space[int(light.x/40)][int(light.y/40)].opac=0;var previous:BitmapData=entry.data,')
 (folder/'GeometryChecks.as').write_text(checks,'utf8',newline='\n')
 r.runner.compile(folder/'GeometryChecks.as',folder/'GeometryChecks.swf',[folder])
 r.save(folder/'build.json',{p.name:r.sha(p) for p in folder.iterdir() if p.is_file()})
 code,log=r.air(folder,'GeometryChecks.swf',rec,240)
 passed=code==0 and 'GEOMETRY COMPLETE' in log and 'FAIL ' not in log
 r.save(folder/'validation.json',{'passed':passed,'exit':code})
 print(log[-2500:]);assert passed
 rec.outcome='passed';rec.note='900张精确光场、轮廓命中、墙体改变与缓存清空对照；不作完整帧性能证明'
