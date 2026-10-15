"""The old compositor must reproduce the wall-shadow leak into a transparent notch."""
from pathlib import Path
import importlib.util,sys,subprocess,re
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
OUT=MOD/'build/wall-options-output'
sys.path.insert(0,str(MOD/'build/wall-surface'))
spec=importlib.util.spec_from_file_location('surface_runner',MOD/'build/wall-surface/run.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
legacy='--repaired' not in sys.argv
folder=OUT/('legacy-repro' if legacy else 'repaired-repro');folder.mkdir(parents=True,exist_ok=True)
text=subprocess.check_output(['git','show','f72c25f:src/RVWallSurface.as'],cwd=MOD).decode('utf-8') if legacy else (MOD/'src/RVWallSurface.as').read_text(encoding='utf-8')
(folder/'RVWallSurface.as').write_text(re.sub(r'\bprivate\b','public',text),encoding='utf-8')
runner.compile(HERE/'BoundaryRepro.as',folder/'BoundaryRepro.swf',[folder,HERE],definitions=[f'-define=CONFIG::legacy,{str(legacy).lower()}',f'-define=CONFIG::repaired,{str(not legacy).lower()}'])
code,log=runner.run_air(folder,'BoundaryRepro.swf');(folder/'repro.txt').write_text(log,encoding='utf-8');print(log)
assert code==(1 if legacy else 0) and 'REPRO COMPLETE' in log,(code,log)
