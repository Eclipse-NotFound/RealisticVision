"""Rebind existing proven drivers without altering old experiments."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
for name in ['group.py','perf.py','IdentityCombatProbe.as','verify-results.py']:
 text=(MOD/'build/shared-mask'/name).read_text(encoding='utf-8').replace('shared-mask-output','fog-setters-output').replace('D48','D49').replace('d48','d49')
 if name=='perf.py':text=text.replace("BASE=MOD/",'from runtime import bind\nbind(r)\nBASE=MOD/')
 if name=='verify-results.py':text=text.replace("('shared','shared-v2','reference','reference-v2')","('guard',)")
 if name=='IdentityCombatProbe.as':
  start=text.index('    retained.sharedBlocks=0;');end=text.index('    row.retained=retained;',start);text=text[:start]+text[end:]
 (HERE/name).write_text(text,encoding='utf-8',newline='\n')
print('D49 isolated drivers prepared')
