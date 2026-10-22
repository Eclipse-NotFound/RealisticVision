"""D36 reuse of the settings/logic checks, kept out of frozen D35 folders."""
from pathlib import Path
import sys,importlib.util,argparse
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
sys.path.insert(0,str(MOD/'build/regression-recovery'))
import checks
checks.OUT=MOD/'build/combat-visibility-output';checks.r.OUT=checks.OUT
checks.inv.SOURCES['d36']=checks.OUT/'candidate/src'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('name');a=p.parse_args()
 if a.action=='build':
  checks.build(a.name,'d36')
  folder=checks.OUT/a.name
  with checks.r.Registration(owner='RealisticVision / D36 批量遮罩编译',purpose=a.name,run_dir=folder,evidence=folder/'batch.json',wait=300) as rec:
   checks.r.runner.compile(HERE/'MaskBatchChecks.as',folder/'MaskBatchChecks.swf',[folder/'src',MOD/'build/stubs'])
   rec.outcome='passed'
 else:
  checks.run(a.name)
  folder=checks.OUT/a.name
  with checks.r.Registration(owner='RealisticVision / D36 批量遮罩像素',purpose=a.name,run_dir=folder,evidence=folder/'batch.json',wait=300) as rec:
   code,log=checks.r.air(folder,'MaskBatchChecks.swf',rec,60)
   (folder/'batch.txt').write_text(log,encoding='utf-8');assert code==0 and 'BATCH COMPLETE 65' in log and 'FAIL ' not in log
   checks.r.save(folder/'batch.json',{'checks':65,'exit':code});rec.outcome='passed';print(log)
