"""Test a narrower exact-domain hypothesis; non-full cones keep original path."""
from pathlib import Path
import hashlib,json,shutil,sys
from profile import once
from candidate import extract
from direct import optimize as direct_optimize
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output'
def optimize(base):
 s=direct_optimize(base)
 original=extract(base,'private function makeLight(').replace('private function makeLight(','private function maskedMakeLight(')
 s=once(s,'private function makeLight(light:Object):BitmapData {',
 '''private function makeLight(light:Object):BitmapData {
            if(Number(light.cone)<Math.PI*2-0.01)return maskedMakeLight(light);
            /* SHOT_DIRECT_FULL */''')
 end=s.rfind('    }');return s[:end]+'        '+original+'\n'+s[end:]

def hybrid(s,base,verify=False):
 s=once(s,'private var cache:Object = {};','private var cache:Object = {};public var rasterOptimized:Boolean=true;public var rasterChecks:int=0;public var directRasters:int=0;')
 s=once(s,'/* SHOT_DIRECT_FULL */','directRasters++;')
 s=once(s,'private function makeLight(light:Object):BitmapData {','private function directMakeLight(light:Object):BitmapData {')
 wrapper='''private function makeLight(light:Object):BitmapData {
            if(!rasterOptimized)return maskedMakeLight(light);
            var result:BitmapData=directMakeLight(light);
'''
 if verify:wrapper+='''            var reference:BitmapData=maskedMakeLight(light),difference:Object=result.compare(reference);
            if(!(difference is uint&&uint(difference)==0))throw new Error("SHOT_DIRECT_FULL_PIXELS "+light.id+" "+light.x+","+light.y+" radius="+light.radius);
            reference.dispose();rasterChecks++;
'''
 wrapper+='            return result;\n        }\n'
 end=s.rfind('    }');return s[:end]+'        '+wrapper+s[end:]

if __name__=='__main__':
 exact='--exact' in sys.argv
 root=OUT/('direct-circle-candidate/src' if exact else 'direct-full-candidate/src');assert not root.exists();shutil.copytree(OUT/'lighting-baseline/src',root)
 p=root/'lad/LadLightField.as';s=optimize(p.read_text('utf8'))
 if exact:s=once(s,'if(Number(light.cone)<Math.PI*2-0.01)','if(Number(light.cone)!==Math.PI*2)')
 p.write_text(s,'utf8',newline='\n')
 (root.parent/'sources.json').write_text(json.dumps({f.relative_to(root).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
 print('Created full-circle-only direct-gradient experiment')
