"""Freeze the deployed D41 baseline; all D42 experiments stay in a new root."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-visibility-output';GAME=MOD.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 assert sha(MOD/'release/RealisticVisionMod.swf')=='6dbbae60eb09ff8f42d34e31edc92fb9f83009ba918e9145980c6d289723d8ba'
 assert not OUT.exists();OUT.mkdir()
 src=MOD/'build/boundary-load-output/production/src'
 shutil.copytree(src,OUT/'baseline/src')
 shutil.copytree(src,OUT/'candidate/src')
 (OUT/'inputs.json').write_text(json.dumps({'installed':sha(MOD/'release/RealisticVisionMod.swf'),'host':sha(GAME/'pfe.swf'),'sources':{p.relative_to(src).as_posix():sha(p) for p in src.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
