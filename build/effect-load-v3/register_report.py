"""Append this completed report once; never rewrite older ledger entries."""
from pathlib import Path
MOD=Path(__file__).resolve().parents[2]
report=MOD/'knowledge/experiments/2026-10-24-effect-load.md'
assert report.read_text(encoding='utf-8').splitlines()[0].startswith('被测技能：')
ledger=Path('C:/Users/hello/.agents/测试报告台账.md')
raw=ledger.read_bytes();path=report.as_posix()
if path.encode('utf-8') not in raw:
    row=f'| 2026-10-24 | {path} | diagnosing-bugs；remains-runtime-debug / auto-testing / mod-build / release-gate / swf-patching / mod-memory | 用户级及Remains工作区 | Remains/RealisticVision | D43密集特效单次采样优化；1131项/组、36原生战斗窗及正式启动通过，v0.33.9已部署。受控更新current约-20%、classic约-6%，整帧基本持平，默认条件有波动且长帧未解；测试调度策略未部署 | 待吸收 |\n'
    with ledger.open('ab') as stream:stream.write((b'' if raw.endswith(b'\n') else b'\n')+b'\n'+row.encode('utf-8'))
    assert ledger.read_bytes().startswith(raw)
print('Report ledger registered')
