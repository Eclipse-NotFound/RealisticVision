"""Append one D55 report entry without rewriting the shared ledger."""
from pathlib import Path
p=Path('C:/Users/hello/.agents/测试报告台账.md')
report='D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/knowledge/experiments/2026-10-28-effect-replay.md'
row=f'| 2026-10-29 | {report} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build | 用户级；Remains工作区 | Remains/RealisticVision | D55同批原生特效与跨帧遮罩回放；stable-v4无整帧收益，identity/blit新增像素反例；24原生扫射窗，未采用/未部署 | 待吸收 |\n'
before=p.read_bytes()
if report.encode() not in before:
 with p.open('ab') as f:f.write(('' if before.endswith(b'\n') else '\n').encode()+row.encode('utf-8'))
 assert p.read_bytes().startswith(before)
 print('D55 report appended')
else:print('D55 report already registered')
