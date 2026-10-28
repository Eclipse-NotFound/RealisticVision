"""Reuse the validated D54 native driver, with new source and output roots."""
from pathlib import Path
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
assert not (HERE/'native_run.py').exists()
s=(MOD/'build/sustained-fire/SavedProbe.as').read_text().replace('sustained-fire-output','effect-replay-output').replace('D54','D55')
(HERE/'SavedFireProbe.as').write_text(s,encoding='utf-8',newline='\n')
s=(MOD/'build/sustained-fire/run.py').read_text().replace("OUT=MOD/'build/sustained-fire-output'","OUT=MOD/'build/effect-replay-output'").replace("SEED=OUT/'player-seed'","SEED=MOD/'build/sustained-fire-output/player-seed'").replace("HERE/'SavedProbe.as'","HERE/'SavedFireProbe.as'").replace('D54','D55')
a=s.index(' if candidate:sources.append');b=s.index('\n for variant,source in sources:',a)
s=s[:a]+" if candidate:sources.append(('candidate',OUT/'candidates/stable-v4/src'))"+s[b:]
s=s.replace("s=s.replace('// D55_TRAILING','trailingHits++;')","s=s.replace('// D55_STABLE','if(mx0!=x0 || my0!=y0 || mx1!=x1 || my1!=y1)trailingHits++;')")
(HERE/'native_run.py').write_text(s,encoding='utf-8',newline='\n')
s=(MOD/'build/sustained-fire/native_check.py').read_text().replace('sustained-fire-output','effect-replay-output').replace('D54','D55').replace('d54','d55')
a=s.index(' v.native_build(name,');b=s.index('\n code,log=',a)
s=s[:a]+" v.native_build(name,'stable-v4')"+s[b:]
(HERE/'native_check.py').write_text(s,encoding='utf-8',newline='\n')
