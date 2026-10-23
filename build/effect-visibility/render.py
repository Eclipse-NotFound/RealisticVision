from pathlib import Path
import run as r0,re,argparse,shutil
r=r0.r;MOD=r0.MOD;OUT=r0.OUT
def build(name):
 folder=OUT/name;assert not folder.exists();src=folder/'src'
 with r.Registration(owner='RealisticVision / D42 身体遮罩回归',purpose='unchanged native mask raster and render',run_dir=folder,evidence=folder/'build.json',wait=300) as rec:
  r.public(OUT/'candidate/src',src)
  s=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig');s=re.sub(r'\bprivate\b','public',s).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
  shutil.copyfile(MOD/'build/boundary-load/MaskRenderChecks.as',folder/'MaskRenderChecks.as')
  r.runner.compile(folder/'MaskRenderChecks.as',folder/'MaskRenderChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs']);rec.outcome='passed'
def execute(name):
 folder=OUT/name
 with r.Registration(owner='RealisticVision / D42 身体遮罩回归',purpose=name,run_dir=folder,evidence=folder/'result.json',wait=300) as rec:
  code,log=r.air(folder,'MaskRenderChecks.swf',rec,100);(folder/'result.txt').write_text(log,encoding='utf-8');r.save(folder/'result.json',{'exit':code,'summary':log.splitlines()[-4:]});print(log[-1800:]);assert code==0 and 'RENDER COMPLETE' in log and 'FAIL ' not in log;rec.outcome='passed'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');a=p.parse_args();build(a.name) if a.action=='build' else execute(a.name)
