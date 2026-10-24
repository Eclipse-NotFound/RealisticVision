from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-load-output'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 src=MOD/'build/effect-visibility-output/production-final/src'
 assert sha(MOD/'release/RealisticVisionMod.swf')=='0dbe0d7a95b8e496fb393d7fcd75f88d60c34a1d0fabb33266b122e3fa04f2bf'
 assert not OUT.exists();OUT.mkdir()
 for v in ['baseline','candidate']:shutil.copytree(src,OUT/v/'src')
 (OUT/'inputs.json').write_text(json.dumps({'installed':sha(MOD/'release/RealisticVisionMod.swf'),'host':sha(MOD.parents[1]/'pfe.swf'),'sources':{p.relative_to(src).as_posix():sha(p) for p in src.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
