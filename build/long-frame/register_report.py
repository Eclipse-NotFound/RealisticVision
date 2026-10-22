"""Append this report once; never rewrite pre-existing ledger bytes."""
from pathlib import Path
MOD=Path(__file__).resolve().parents[2]
report=MOD/'knowledge/experiments/2026-10-22-long-frame-triggers.md'
ledger=Path('C:/Users/hello/.agents/测试报告台账.md')
if __name__=='__main__':
 assert report.exists() and report.read_text(encoding='utf-8').startswith('被测技能：')
 before=ledger.read_bytes();path=report.as_posix()
 if path.encode('utf-8') not in before:
  row=f'| 2026-10-22 | {path} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build / release-gate / swf-patching | 用户级及Remains工作区 | Remains/RealisticVision | D39定位镜头跨墙面缓存边界的集中重建；414项/组与96严格图像通过，v0.33.6已部署。跨边界RV更新current约58→30ms、classic57→38ms，完整组合整帧未稳定改善；纠正EXIT_FRAME阶段错配，经验KB-000107 | 待吸收 |\n'
  with ledger.open('ab') as f:f.write((('' if before.endswith(b'\n') else '\n')+row).encode('utf-8'))
  assert ledger.read_bytes().startswith(before)
 print('D39 report registered once')
