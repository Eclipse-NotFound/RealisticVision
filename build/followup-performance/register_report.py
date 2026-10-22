"""Append the completed local report to the authorized global report ledger."""
from pathlib import Path
import json
MOD=Path(__file__).resolve().parents[2]
REPORT=MOD/'knowledge/experiments/2026-10-22-followup-performance.md'
LEDGER=Path('C:/Users/hello/.agents/测试报告台账.md')
if __name__=='__main__':
 receipt=json.loads((MOD/'build/followup-performance-output/deployment/receipt.json').read_text())
 assert receipt['result']=='PASS' and REPORT.exists()
 before=LEDGER.read_bytes();key=REPORT.as_posix()
 if key.encode('utf-8') in before:print('Report already registered')
 else:
  row=f'| 2026-10-22 | {key} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build / release-gate / swf-patching | 用户级及Remains工作区 | Remains/RealisticVision | D38精确采样与墙面补集复用：4987项/组、96严格图像及正式路径复验通过，v0.33.5已部署。同输入更新classic约20%～22%、current约9%降低；12原生战斗窗未见稳定整帧改善，保留长帧和继承测试编号分支纠正证据 | 待吸收 |\n'
  with LEDGER.open('ab') as f:f.write(('' if before.endswith(b'\n') else '\n').encode('utf-8')+row.encode('utf-8'))
  after=LEDGER.read_bytes();assert after.startswith(before) and after.count(key.encode('utf-8'))==1
  print('D38 report registered; prior bytes preserved')
