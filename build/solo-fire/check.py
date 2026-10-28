"""D53 exact rendered comparisons including proof that the new path executes."""
from pathlib import Path
import importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/solo-fire-output'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load('d53_check_runtime',MOD/'build/motion-performance/run.py')
name=sys.argv[1];folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
with r.Registration(owner='RealisticVision / D53 严格画面对照',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 src=folder/'src';r.public(OUT/'candidates/early-dark/src',src)
 p=src/'RealisticVisionMod.as';s=p.read_text();s=s.replace('public var worldPass:int = 0;','public var worldPass:int = 0;public var earlyDarkHits:int=0;');s=s.replace('// D53_EARLY_DARK','earlyDarkHits++;');p.write_text(s,encoding='utf-8')
 s=re.sub(r'\bprivate\b','public',(MOD/'build/combat-render-output/production-final2/src/RealisticVisionMod.as').read_text()).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
 t=(MOD/'build/effect-load-v3/EffectLoadChecks.as').read_text()
 t=t.replace('m.fovVersion++;m.worldPass++;','var blur:Number=[0,1,2,4,6,9][age%6];m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.fovVersion++;m.worldPass++;')
 t=t.replace('100+(i*61+age*17)%730+.3','(i*61+age*17)%920+.3').replace('140+(i*37)%500+.7','(i*37+age*5)%710+.7')
 t=t.replace('out.draw(layer);return out;','var zoom:Number=[.5,.75,1,1.5,2][f%5];out.draw(layer,new Matrix(zoom,0,0,zoom,.35,.65),null,null,null,true);return out;')
 t=t.replace('if(++f>=360){','if(++f>=360){check(b.earlyDarkHits>0,"early dark is exercised");trace("EARLY DARK hits="+b.earlyDarkHits);removeEventListener(Event.ENTER_FRAME,step);')
 (folder/'EffectLoadChecks.as').write_text(t,encoding='utf-8')
 r.runner.compile(folder/'EffectLoadChecks.as',folder/'EffectLoadChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
 r.save(folder/'build.json',{'files':{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()}})
 code,log=r.air(folder,'EffectLoadChecks.swf',rec,300);(folder/'result.txt').write_text(log,encoding='utf-8')
 ok=code==0 and 'LOAD COMPLETE' in log and 'FAIL ' not in log
 r.save(folder/'validation.json',{'passed':ok,'exit':code,'checks':int(re.search(r'LOAD COMPLETE passed=(\d+)',log)[1]) if ok else 0})
 print(log[-1200:]);assert ok;rec.outcome='passed';rec.note='严格像素比较，仅功能证据'
