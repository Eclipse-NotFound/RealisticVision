import package as p
import re
from pathlib import Path
if __name__=='__main__':
 import sys
 folder=p.OUT/(sys.argv[1] if len(sys.argv)>1 else 'display-matrix');assert not folder.exists();folder.mkdir()
 with p.run.Registration(owner='RealisticVision / D37 取图坐标验证',purpose='父层实际绘制与包含根节点变换的直接绘制一致',run_dir=folder,evidence=folder/'result.json') as rec:
  source=Path(__file__).parent/'DisplayMatrixChecks.as'
  p.run.runner.compile(source,folder/'DisplayMatrixChecks.swf',[source.parent])
  code,log=p.run.air(folder,'DisplayMatrixChecks.swf',rec,60)
  match=re.search(r'DISPLAY MATRIX COMPLETE passed=(\d+)',log)
  p.run.save(folder/'result.json',{'exit':code,'passed':int(match[1]) if match else 0,'source':p.run.sha(source)})
  print(log[-1500:]);assert code==0 and match and int(match[1])==36 and 'FAIL' not in log;rec.outcome='passed'
