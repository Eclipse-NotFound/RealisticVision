"""Freeze the unwrapped D45 combat comparison for D47 identity candidate."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
for filename,outname in [('run.py','perf.py'),('CombatRenderProbeMod.as','IdentityCombatProbe.as')]:
    target=HERE/outname
    assert not target.exists(),target
    source=(MOD/'build/mask-area'/filename).read_text(encoding='utf-8')
    source=source.replace('build/mask-area-output','build/frame-attribution-output')
    source=source.replace('D45','D47P').replace('d45_','d47p_')
    if filename=='run.py':
        source=source.replace("(HERE/'CombatRenderProbeMod.as')","(HERE/'IdentityCombatProbe.as')")
        source=source.replace("rec.note='归因窗口完成；诊断性显示差异，非生产验收'","rec.note='完整战斗对照完成；性能采用结论另看报告'")
    target.write_text(source,encoding='utf-8',newline='\n')
(HERE/'identity-perf-steps.json').write_text(json.dumps([
    ['perf.py','build','identity-combat-01','--full','--candidate','identity','--controlled','--warmup','210','--frames','180'],
    ['perf.py','run','identity-combat-01']
],indent=2)+'\n',encoding='utf-8',newline='\n')
print('Unwrapped 12-window combat comparison prepared')
