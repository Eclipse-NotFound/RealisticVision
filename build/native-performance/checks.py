from pathlib import Path
import sys,argparse,re,json
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/native-performance-output'
sys.path.insert(0,str(MOD/'build/regression-recovery'))
import checks as old
old.OUT=OUT;old.r.OUT=OUT;old.inv.OUT=OUT
def build(name,candidate):
 old.inv.SOURCES['d37']=OUT/candidate/'src';old.build(name,'d37')
 folder=OUT/name;src=folder/'src'
 with old.r.Registration(owner='RealisticVision / D37 缓存回归构建',purpose=name,run_dir=folder,evidence=folder/'extra.json',wait=300) as rec:
  base=MOD/'build/combat-visibility-output/production/src/RVWallSurface.as'
  (src/'BaselineWallSurface.as').write_text(re.sub(r'\bprivate\b','public',base.read_text(encoding='utf-8-sig')).replace('RVWallSurface','BaselineWallSurface'),encoding='utf-8')
  old.r.runner.compile(MOD/'build/wall-performance/EquivalenceChecks.as',folder/'EquivalenceChecks.swf',[src,MOD/'build/wall-performance'])
  s=(src/'LazyClassicChecks.as').read_text(encoding='utf-8').replace('LazyClassicChecks','DirtyClassicChecks').replace('frame<12','frame<24')
  s=s.replace('a.loc.gg.X=b.loc.gg.X=200+frame*43;', '''a.loc.gg.X=b.loc.gg.X=200+int(frame/3)*43;
     if(frame==13){a.m.cfgSoftClassic=b.m.cfgSoftClassic=40;}
     if(frame==18){a.m.cfgSoftClassic=b.m.cfgSoftClassic=0;}
     if(frame==20){a.loc.getTile(10,8).opac=b.loc.getTile(10,8).opac=1;}''')
  (src/'DirtyClassicChecks.as').write_text(s,encoding='utf-8')
  old.r.runner.compile(src/'DirtyClassicChecks.as',folder/'DirtyClassicChecks.swf',[src,MOD/'build/motion-tests',MOD/'build/stubs'])
  if candidate=='candidate-10':
   original=MOD/'build/combat-visibility-output/production/src/RealisticVisionMod.as'
   (src/'FovBaselineVision.as').write_text(re.sub(r'\bprivate\b','public',original.read_text(encoding='utf-8-sig')).replace('RealisticVisionMod','FovBaselineVision'),encoding='utf-8')
   old.r.runner.compile(HERE/'FovBoundsChecks.as',folder/'FovBoundsChecks.swf',[src,HERE,MOD/'build/motion-tests',MOD/'build/stubs'])
  rec.outcome='passed'
def run(name):
 old.run(name);folder=OUT/name;results=[]
 with old.r.Registration(owner='RealisticVision / D37 缓存回归',purpose=name,run_dir=folder,evidence=folder/'extra.json',wait=300) as rec:
  for test in ['EquivalenceChecks','DirtyClassicChecks']+(['FovBoundsChecks'] if (folder/'FovBoundsChecks.swf').exists() else []):
   code,log=old.r.air(folder,test+'.swf',rec,180)
   (folder/(test+'.txt')).write_text(log,encoding='utf-8')
   print('\n'.join(log.splitlines()[-5:]),flush=True)
   results.append({'name':test,'exit':code,'summary':log.splitlines()[-5:]});old.r.save(folder/'extra.json',results)
   assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
  rec.outcome='passed'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('name');p.add_argument('--candidate',default='candidate-02');a=p.parse_args()
 build(a.name,a.candidate) if a.action=='build' else run(a.name)
