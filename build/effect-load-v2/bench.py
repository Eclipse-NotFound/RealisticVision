from pathlib import Path
import importlib.util,re,sys,argparse
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/effect-load-v2-output'
spec=importlib.util.spec_from_file_location('d43_run',MOD/'build/effect-visibility/run.py');r0=importlib.util.module_from_spec(spec);spec.loader.exec_module(r0);r=r0.r;r.OUT=OUT
def main(action,name,edges=False):
 folder=OUT/name
 with r.Registration(owner='RealisticVision / D43 密集视觉',purpose=action+' '+name,run_dir=folder,evidence=folder/'result.txt',wait=300) as rec:
  if action=='build':
   assert not folder.exists();folder.mkdir(parents=True);src=folder/'src';r.public(OUT/'candidate/src',src)
   s=re.sub(r'\bprivate\b','public',(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
   test=(HERE/'EffectLoadChecks.as').read_text(encoding='utf-8')
   if edges:
    test=test.replace('count:int=group%2?500:100','count:int=100')
    test=test.replace('m.fovVersion++;m.worldPass++;','var blur:Number=[0,1,2,4,6,9][age%6];m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.fovVersion++;m.worldPass++;')
    test=test.replace('100+(i*61+age*17)%730+.3','(i*61+age*17)%920+.3').replace('140+(i*37)%500+.7','(i*37+age*5)%710+.7')
   test=test.replace('trace("LOAD COMPLETE passed="+passed);NativeApplication','removeEventListener(Event.ENTER_FRAME,step);trace("LOAD COMPLETE passed="+passed);NativeApplication')
   (folder/'EffectLoadChecks.as').write_text(test,encoding='utf-8')
   r.runner.compile(folder/'EffectLoadChecks.as',folder/'EffectLoadChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
  else:
   code,log=r.air(folder,'EffectLoadChecks.swf',rec,180);(folder/'result.txt').write_text(log,encoding='utf-8');print(log[-4000:]);assert code==0 and 'LOAD COMPLETE' in log and 'FAIL ' not in log
  rec.outcome='passed'
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action');a.add_argument('name');a.add_argument('--edges',action='store_true');x=a.parse_args();main(x.action,x.name,x.edges)
