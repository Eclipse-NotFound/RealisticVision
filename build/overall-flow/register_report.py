from pathlib import Path
MOD=Path(__file__).resolve().parents[2]
report=MOD/'knowledge/experiments/2026-10-23-overall-flow.md'
ledger=Path('C:/Users/hello/.agents/测试报告台账.md')
if __name__=='__main__':
 assert report.exists() and report.read_text(encoding='utf-8').startswith('被测技能：')
 before=ledger.read_bytes();path=report.as_posix()
 if path.encode('utf-8') not in before:
  row=f'| 2026-10-23 | {path} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build / mod-memory | 用户级及Remains工作区 | Remains/RealisticVision | D40六候选、132项/组及24原生跑动射击窗；整体收益未稳定，保持D39未部署。847ms中RV22ms；外部高频CPU观察器及诊断取图副作用纠正，长帧具体根因仍未完全定位 | 待吸收 |\n'
  with ledger.open('ab') as f:f.write((('' if before.endswith(b'\n') else '\n')+row).encode('utf-8'))
  assert ledger.read_bytes().startswith(before)
 print('D40 report registered once')
