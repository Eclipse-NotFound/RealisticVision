"""D40: freeze D39; do not rebuild or overwrite historical experiments."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/overall-flow-output';GAME=MOD.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 assert sha(MOD/'release/RealisticVisionMod.swf')=='83d8e590c062e181b70bd5cabef2200084d5e81aaca081d1d1ebc347205c7e65'
 assert not OUT.exists();OUT.mkdir()
 src=MOD/'build/long-frame-output/production/src';shutil.copytree(src,OUT/'candidate-00/src')
 shutil.copy2(MOD/'release/RealisticVisionMod.swf',OUT/'candidate-00/RealisticVisionMod.swf')
 pins={str(p.relative_to(GAME)):sha(p) for p in [GAME/'pfe.swf',GAME/'application.xml',GAME/'mods/loader-manifest.txt',*sorted((GAME/'mods').glob('*/release/*.swf'))]}
 (OUT/'inputs.json').write_text(json.dumps({'installed':sha(MOD/'release/RealisticVisionMod.swf'),'sources':{p.relative_to(src).as_posix():sha(p) for p in src.rglob('*.as')},'production':pins},indent=2)+'\n',encoding='utf-8')
