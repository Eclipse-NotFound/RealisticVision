"""Append D46 to the user's report index once; existing bytes stay intact."""
from pathlib import Path
path=Path('C:/Users/hello/.agents/测试报告台账.md')
report='D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/knowledge/experiments/2026-10-25-mask-lifecycle.md'
line=f'| 2026-10-25 | {report} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build | 用户级；Remains工作区 | Remains/RealisticVision | D46清理观察2156配对帧反证集中释放主因；carry 361+888检查通过但12完整战斗窗无稳定收益，未部署；正式D44不变，长帧仍未尽归因 | 待吸收 |\n'
raw=path.read_bytes()
if report.encode() not in raw:
 with path.open('ab') as f:f.write(('' if raw.endswith(b'\n') else '\n').encode()+line.encode('utf-8'))
 assert path.read_bytes().startswith(raw);print('D46 report appended')
else:print('D46 report already registered')
