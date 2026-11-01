"""Append the required report index entry; never rewrite existing ledger lines."""
from pathlib import Path
ledger=Path('C:/Users/hello/.agents/测试报告台账.md')
report='D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/knowledge/experiments/2026-11-01-combo-audit.md'
before=ledger.read_bytes()
if report.encode() not in before:
    line='| 2026-11-01 | '+report+' | code-review；diagnosing-bugs；remains-runtime-debug / auto-testing | 用户级；Remains工作区 | Remains/RealisticVision | combo-v4审核：40窗7160间隔；确认外框缓存与渐入恢复缺陷；零敌人扫射仍慢、特效计算削减无稳定整帧收益、阴影显示仅解释部分成本；5394ms后段停顿未全解，未部署 | 待吸收 |\n'
    with ledger.open('ab') as f:f.write(('' if before.endswith(b'\n') else '\n').encode()+line.encode())
    assert ledger.read_bytes().startswith(before)
print('Report indexed (deduplicated)')
