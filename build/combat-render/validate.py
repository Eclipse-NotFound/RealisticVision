"""D44 pixel checks reuse known fixtures with explicitly rebound frozen inputs."""
from pathlib import Path
import importlib.util,json,re,shutil,sys,argparse
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combat-render-output'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=load('d44_driver',HERE/'run.py');r=d.r

def freeze():
 for name,source in [('baseline',d.BASE),('candidate',OUT/'candidates/guard/src')]:
  dest=OUT/name/'src'
  if not dest.exists():shutil.copytree(source,dest)
  assert {p.relative_to(dest).as_posix():r.sha(p) for p in dest.rglob('*.as')}=={p.relative_to(source).as_posix():r.sha(p) for p in source.rglob('*.as')}

def dense_build(name,candidate='guard'):
 freeze();folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with r.Registration(owner='RealisticVision / D44 像素构建',purpose=name,run_dir=folder,evidence=folder/'build.json',resource='offline') as rec:
  src=folder/'src';r.public(OUT/'candidates'/candidate/'src',src)
  s=re.sub(r'\bprivate\b','public',(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
  test=(MOD/'build/effect-load-v3/EffectLoadChecks.as').read_text(encoding='utf-8')
  test=test.replace('m.fovVersion++;m.worldPass++;','var blur:Number=[0,1,2,4,6,9][age%6];m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.fovVersion++;m.worldPass++;')
  test=test.replace('100+(i*61+age*17)%730+.3','(i*61+age*17)%920+.3').replace('140+(i*37)%500+.7','(i*37+age*5)%710+.7')
  test=test.replace('out.draw(layer);return out;', 'var zoom:Number=[.5,.75,1,1.5,2][f%5];out.draw(layer,new Matrix(zoom,0,0,zoom,.35,.65),null,null,null,true);return out;')
  test=test.replace('trace("LOAD COMPLETE passed="+passed);NativeApplication','removeEventListener(Event.ENTER_FRAME,step);trace("LOAD COMPLETE passed="+passed);NativeApplication')
  if candidate=='tileclip':
   test=test.replace('package {','package {\n import flash.filesystem.*;')
   needle='check(d is uint&&uint(d)==0,"exact dense moving visuals");'
   capture='''if(d is BitmapData){
    var evidence:File=File.applicationDirectory.resolvePath("evidence");evidence.createDirectory();
    var snapshots:Array=[ca,cb,d],labels:Array=["baseline","candidate","difference"];
    for(var di:int=0;di<snapshots.length;di++){
     var fs:FileStream=new FileStream();fs.open(evidence.resolvePath(labels[di]+"-"+f+".png"),FileMode.WRITE);
     fs.writeBytes(BitmapData(snapshots[di]).encode(BitmapData(snapshots[di]).rect,new PNGEncoderOptions()));fs.close();
    }
    trace("DIFFERENCE bounds="+BitmapData(d).getColorBoundsRect(0xffffffff,0,false));
   }'''
   assert test.count(needle)==1
   test=test.replace(needle,capture+needle)
  (folder/'EffectLoadChecks.as').write_text(test,encoding='utf-8')
  r.runner.compile(folder/'EffectLoadChecks.as',folder/'EffectLoadChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
  r.save(folder/'build.json',{'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file()}});rec.outcome='passed'

def native_build(name,candidate='guard'):
 freeze()
 # Keep the native host fixture; add exact baseline/candidate captures after
 # the existing visibility, independent arm, weapon and lifecycle assertions.
 helper=OUT/'native-check-source';helper.mkdir(exist_ok=True)
 source=(MOD/'build/effect-load-v3/inspect.as.inc').read_text(encoding='utf-8')
 source=source.replace('         save();trace("D42 EFFECT ',(HERE/'native-identity.as.inc').read_text(encoding='utf-8')+'\n         save();trace("D42 EFFECT ')
 (helper/'inspect.as.inc').write_text(source,encoding='utf-8')
 shutil.copyfile(MOD/'build/effect-load-v3/extra.as.inc',helper/'extra.as.inc')
 f=load('d44_native',MOD/'build/effect-visibility/run.py');f.OUT=OUT;f.HERE=helper;f.r=r
 original_compile=r.runner.compile
 def compile_local(entry,*args,**kwargs):
  if entry.name=='EffectVisibilityProbeMod.as':
   text=entry.read_text(encoding='utf-8')
   assert '/RealisticVision/build/effect-visibility-output/' in text
   text=text.replace('package {','package {\nimport flash.filters.GlowFilter;')
   entry.write_text(text.replace('/RealisticVision/build/effect-visibility-output/','/RealisticVision/build/combat-render-output/'),encoding='utf-8')
  return original_compile(entry,*args,**kwargs)
 r.runner.compile=compile_local
 original_public=r.public
 def public_local(source,dest,*args,**kwargs):
  if source==OUT/'candidate/src':source=OUT/'candidates'/candidate/'src'
  return original_public(source,dest,*args,**kwargs)
 r.public=public_local
 original_registration=r.Registration
 def offline_registration(**kwargs):
  kwargs['resource']='offline';kwargs['owner']='RealisticVision / D44 原生视觉构建';return original_registration(**kwargs)
 r.Registration=offline_registration
 try:f.build(name,True)
 finally:r.runner.compile=original_compile;r.Registration=original_registration;r.public=original_public

def execute(name,dense=False):
 folder=OUT/name;assert not(folder/'last-run.json').exists()
 pins=json.loads((folder/'build.json').read_text())['files'];assert all(r.sha(folder/k)==v for k,v in pins.items())
 with r.Registration(owner='RealisticVision / D44 视觉回归',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
  env=r.environment();r.save(folder/'launch-state.json',env)
  assert not [p for p in env['processes'] if p['name'].lower() in ('adl64.exe','adl.exe')]
  assert env['available_bytes']>5*1024**3
  code,log=r.air(folder,'EffectLoadChecks.swf' if dense else 'pfe.swf',rec,300)
  (folder/'result.txt').write_text(log,encoding='utf-8')
  count=int(re.search(r'LOAD COMPLETE passed=(\d+)',log)[1]) if dense and 'LOAD COMPLETE' in log else len(re.findall(r'^PASS ',log,re.M))
  ok=code==0 and ('LOAD COMPLETE' if dense else 'FRAME COMPLETE') in log and not re.search(r'^FAIL ',log,re.M)
  r.save(folder/'validation.json',{'pass':ok,'checks':count,'exit':code,'log':r.sha(folder/'result.txt')});print(log[-1800:]);assert ok;rec.outcome='passed'

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--candidate',default='guard');a=p.parse_args()
 {'dense-build':lambda n:dense_build(n,a.candidate),'native-build':lambda n:native_build(n,a.candidate),'dense-run':lambda n:execute(n,True),'native-run':execute}[a.action](a.name)
