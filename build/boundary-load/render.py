from pathlib import Path
import re,argparse
import measure as m
r=m.inv.r;MOD=m.MOD;OUT=r.OUT
def build(name,candidate='candidate-01'):
 folder=OUT/name;assert not folder.exists();src=folder/'src'
 with r.Registration(owner='RealisticVision / D41 遮罩绘制',purpose='编译逐帧动态像素和复用图形检查',run_dir=folder,evidence=folder/'build.json',wait=300) as rec:
  r.public(OUT/candidate/'src',src)
  s=(OUT/'candidate-00/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig');s=re.sub(r'\bprivate\b','public',s).replace('RealisticVisionMod','BaselineVision')
  (src/'BaselineVision.as').write_text(s,encoding='utf-8')
  import shutil
  shutil.copyfile(Path(__file__).parent/'MaskRenderChecks.as',folder/'MaskRenderChecks.as')
  r.runner.compile(folder/'MaskRenderChecks.as',folder/'MaskRenderChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
  r.save(folder/'build.json',{'swf':r.sha(folder/'MaskRenderChecks.swf'),'sources':{str(p.relative_to(src)):r.sha(p) for p in src.rglob('*.as')}});rec.outcome='passed'
def run(name):
 folder=OUT/name
 with r.Registration(owner='RealisticVision / D41 遮罩绘制',purpose='逐帧身体/血条/武器图形像素对照',run_dir=folder,evidence=folder/'result.json',wait=300) as rec:
  code,log=r.air(folder,'MaskRenderChecks.swf',rec,100);(folder/'result.txt').write_text(log,encoding='utf-8');r.save(folder/'result.json',{'exit':code,'summary':log.splitlines()[-4:]});print(log[-2500:]);assert code==0 and 'RENDER COMPLETE' in log and 'FAIL ' not in log;rec.outcome='passed'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--candidate',default='candidate-03');a=p.parse_args();build(a.name,a.candidate) if a.action=='build' else run(a.name)
