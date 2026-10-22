"""Freeze the installed D38 production source, without touching prior runs."""
from pathlib import Path
import shutil,json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/long-frame-output'
BASE=MOD/'build/followup-performance-output/production/src'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if __name__=='__main__':
 assert sha(MOD/'release/RealisticVisionMod.swf')=='6593ee35008a898bd2d2b1189693a17bd0767c387697bcbee73a387f8fd6ec06'
 assert not OUT.exists();OUT.mkdir();shutil.copytree(BASE,OUT/'candidate-00/src')
 (OUT/'inputs.json').write_text(json.dumps({'version':'v0.33.5-followup-performance','installed':sha(MOD/'release/RealisticVisionMod.swf'),'sources':{p.relative_to(BASE).as_posix():sha(p) for p in BASE.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
