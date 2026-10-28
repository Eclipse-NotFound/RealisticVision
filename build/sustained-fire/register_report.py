"""Append this report once; do not rewrite the cross-workspace ledger."""
from pathlib import Path
path=Path('C:/Users/hello/.agents/测试报告台账.md')
report='D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/knowledge/experiments/2026-10-28-sustained-fire.md'
line=f'| 2026-10-28 | {report} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build / release-gate / swf-patching | 用户级；Remains工作区 | Remains/RealisticVision | D54最大化存档原生轻机枪持续射击；纠正输入、超容量补弹、visible回读和零触发；安全候选画面通过但整帧无稳定收益，仍未修复/未部署；经验KB-000123 | 待吸收 |\n'
raw=path.read_bytes()
if report.encode() not in raw:
 with path.open('ab') as f:f.write(('' if raw.endswith(b'\n') else '\n').encode()+line.encode('utf-8'))
 assert path.read_bytes().startswith(raw)
 print('D54 report appended')
else:print('D54 report already registered')
