"""Freeze D37 without touching its history or the installed bytes."""
from pathlib import Path
import shutil,json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/followup-performance-output';BASE=MOD/'build/native-performance-output/production/src'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if __name__=='__main__':
 assert sha(MOD/'release/RealisticVisionMod.swf')=='187d287b06fea10e6057c8e80287352062cff7577d075181261ddc0d04111272'
 assert not OUT.exists();OUT.mkdir()
 shutil.copytree(BASE,OUT/'candidate-00/src')
 (OUT/'inputs.json').write_text(json.dumps({'version':'v0.33.4-native-performance','installed':sha(MOD/'release/RealisticVisionMod.swf'),'sources':{p.relative_to(BASE).as_posix():sha(p) for p in BASE.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
