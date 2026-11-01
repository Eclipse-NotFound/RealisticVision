"""Reuse the off-stage vector tree used by makeLight; preserve its draw call."""
from pathlib import Path
import hashlib,json,shutil
from profile import once
from candidate import extract
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output'

def optimize(s):
 s=once(s,'private var cache:Object = {};','''private var cache:Object = {};
        private var lightRoot:Sprite,lightGlow:Sprite,lightMask:Sprite;
        private var lightRadius:Number=NaN;''')
 s=once(s,'trailRaster.clear();','''trailRaster.clear();
            if(lightGlow)lightGlow.mask=null;
            lightRoot=lightGlow=lightMask=null;lightRadius=NaN;''')
 s=once(s,'var root:Sprite=new Sprite(),glow:Sprite=new Sprite(),mask:Sprite=new Sprite();','''// The tree is never attached to the game's display list. Reuse the
            // same native mask relationship, resetting all variable graphics.
            if(!lightRoot) {
                lightRoot=new Sprite();lightGlow=new Sprite();lightMask=new Sprite();
                lightRoot.addChild(lightGlow);lightRoot.addChild(lightMask);lightGlow.mask=lightMask;
            }
            var root:Sprite=lightRoot,glow:Sprite=lightGlow,mask:Sprite=lightMask;
            if(lightRadius!=radius) {
            glow.graphics.clear();''')
 s=once(s,'glow.graphics.drawRect(0,0,side,side);glow.graphics.endFill();',
 '''glow.graphics.drawRect(0,0,side,side);glow.graphics.endFill();
            lightRadius=radius;
            }
            mask.graphics.clear();''')
 s=once(s,'mask.graphics.endFill();root.addChild(glow);root.addChild(mask);glow.mask=mask;',
 'mask.graphics.endFill();')
 return s

def hybrid(s,base,verify=False):
 marker='private function makeLight(light:Object):BitmapData {'
 original=extract(base,marker).replace(marker,'private function originalMakeLight(light:Object):BitmapData {')
 s=once(s,marker,marker+'\n            if(!rasterOptimized)return originalMakeLight(light);')
 s=once(s,'private var cache:Object = {};','private var cache:Object = {};public var rasterOptimized:Boolean=true;public var rasterChecks:int=0;')
 if verify:
  # Runs immediately on the same stable native tile arrays. This is evidence,
  # not a timing candidate or a production class.
  s=once(s,'result.draw(root);return result;','''result.draw(root);
            var reference:BitmapData=originalMakeLight(light),difference:Object=result.compare(reference);
            if(!(difference is uint && uint(difference)==0))throw new Error("SHOT_RASTER_PIXELS "+light.id+" "+light.x+","+light.y+" radius="+radius);
            reference.dispose();rasterChecks++;
            return result;''')
 end=s.rfind('    }');return s[:end]+'        '+original+'\n'+s[end:]

if __name__=='__main__':
 root=OUT/'raster-candidate/src';assert not root.exists();shutil.copytree(OUT/'lighting-baseline/src',root)
 p=root/'lad/LadLightField.as';p.write_text(optimize(p.read_text('utf8')),'utf8',newline='\n')
 (root.parent/'sources.json').write_text(json.dumps({f.relative_to(root).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
 print('Created reusable vector-tree candidate; ray order and bitmap draw unchanged')
