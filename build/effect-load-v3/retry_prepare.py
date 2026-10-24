from pathlib import Path
import shutil
OUT=Path(__file__).resolve().parents[2]/'build/effect-load-v3-output'
p=OUT/'native-01/launch-state.json';q=p.with_name('preflight-memory-abort.json')
assert p.exists() and not q.exists();shutil.copyfile(p,q)
# The first benchmark completed every comparison but reached its process limit
# during system-wide memory pressure. Preserve it and rerun with a bounded grace.
src=OUT/'candidate-02';dst=OUT/'candidate-03';assert not dst.exists()
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('storage','*.log','last-run.json','running.json','result.txt','test.xml'))
print('aborted preflight and timed-out evidence preserved')
