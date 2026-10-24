"""Append the task's report to the authorized cross-workspace index once."""
from pathlib import Path
path=Path('C:/Users/hello/.agents/测试报告台账.md')
report='D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/knowledge/experiments/2026-10-25-mask-area.md'
line=f'| 2026-10-25 | {report} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build | 用户级；Remains工作区 | Remains/RealisticVision | D45三候选未采用，完整组合64窗含受限诊断；严格图像和尾部性能分别判断，纠正mask计数与拆装干扰，清理帧关联待验证；正式仍D44 | 待吸收 |\n'
raw=path.read_bytes()
if report.encode() not in raw:
 with path.open('ab') as f:f.write(('' if raw.endswith(b'\n') else '\n').encode()+line.encode('utf-8'))
 assert path.read_bytes().startswith(raw)
 print('D45 report appended')
else:print('D45 report already registered')
