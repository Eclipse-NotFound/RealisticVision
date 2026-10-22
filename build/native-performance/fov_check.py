from pathlib import Path
import argparse,re,json
import measure
r=measure.inv.r;OUT=measure.OUT;MOD=measure.MOD;HERE=measure.HERE
def build(name,candidate):
 folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with r.Registration(owner='RealisticVision / D37 FOV bounds',purpose=name+' build',run_dir=folder,evidence=folder/'inputs.json') as rec:
  src=folder/'src';r.public(OUT/candidate/'src',src)
  base=MOD/'build/combat-visibility-output/production/src/RealisticVisionMod.as'
  (src/'FovBaselineVision.as').write_text(re.sub(r'\bprivate\b','public',base.read_text(encoding='utf-8-sig')).replace('RealisticVisionMod','FovBaselineVision'),encoding='utf-8')
  (src/'FovBoundsChecks.as').write_bytes((HERE/'FovBoundsChecks.as').read_bytes())
  r.runner.compile(src/'FovBoundsChecks.as',folder/'FovBoundsChecks.swf',[src,MOD/'build/motion-tests',MOD/'build/stubs'])
  r.save(folder/'inputs.json',{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()})
  rec.outcome='passed'
def run(name):
 folder=OUT/name
 assert all(r.sha(folder/k)==v for k,v in json.loads((folder/'inputs.json').read_text()).items())
 with r.Registration(owner='RealisticVision / D37 FOV bounds',purpose=name,run_dir=folder,evidence=folder/'result.json') as rec:
  code,log=r.air(folder,'FovBoundsChecks.swf',rec,180)
  count=re.search(r'FOV BOUNDS COMPLETE passed=(\d+)',log)
  r.save(folder/'result.json',{'exit':code,'passed':int(count[1]) if count else 0})
  print(log[-2000:]);assert code==0 and count and 'FAIL ' not in log;rec.outcome='passed'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('name');p.add_argument('--candidate',default='candidate-10');a=p.parse_args()
 build(a.name,a.candidate) if a.action=='build' else run(a.name)
