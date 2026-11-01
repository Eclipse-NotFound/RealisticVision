"""Experimental single gradient-filled polygon. Requires strict pixel oracle."""
from pathlib import Path
import hashlib,json,shutil
from profile import once
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output'
def optimize(s):
 s=once(s,'var root:Sprite=new Sprite(),glow:Sprite=new Sprite(),mask:Sprite=new Sprite();',
        'var root:Sprite=new Sprite(),glow:Sprite=root,mask:Sprite=root;')
 s=once(s,'glow.graphics.drawRect(0,0,side,side);glow.graphics.endFill();\n            mask.graphics.beginFill(0xFFFFFF);','')
 s=once(s,'mask.graphics.endFill();root.addChild(glow);root.addChild(mask);glow.mask=mask;','mask.graphics.endFill();')
 return s
if __name__=='__main__':
 root=OUT/'direct-candidate/src';assert not root.exists();shutil.copytree(OUT/'lighting-baseline/src',root)
 p=root/'lad/LadLightField.as';p.write_text(optimize(p.read_text('utf8')),'utf8',newline='\n')
 (root.parent/'sources.json').write_text(json.dumps({f.relative_to(root).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
 print('Created direct-gradient experiment; not accepted without pixel equality')
