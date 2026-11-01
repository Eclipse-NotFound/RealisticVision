"""Skip rasterization only when every shadow polygon coordinate is identical.

All native rays are still evaluated on every original cache miss. This does not
extend the existing position/angle quantization or assume terrain stayed fixed.
"""
from pathlib import Path
import hashlib,json,shutil
from profile import once
from candidate import extract
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output'

def optimize(s):
 s=once(s,'''                if(entry)entry.data.dispose();
                entry={key:signature,data:makeLight(light)};cache[identity]=entry;rebuilds++;''',
 '''                var oldRaster:BitmapData=entry?entry.data:null;
                if(!entry)entry={};
                var nextRaster:BitmapData=makeLight(light,entry);
                if(oldRaster && oldRaster!==nextRaster)oldRaster.dispose();
                entry.key=signature;entry.data=nextRaster;cache[identity]=entry;rebuilds++;''')
 old=extract(s,'private function makeLight(')
 new='''private function makeLight(light:Object,previous:Object=null):BitmapData {
            var radius:Number=Number(light.radius);
            var side:int=Math.ceil(radius*2/cell)+1;
            var cone:Number=Number(light.cone),center:Number=Number(light.angle);
            var full:Boolean=cone>=Math.PI*2-0.01;
            var start:Number=full?0:center-cone/2;
            var count:int=light.transient?64:Math.max(24,Math.ceil(cone/(Math.PI/90)));
            var points:Vector.<Number>=new Vector.<Number>((count+1)*2,true);
            var oldPoints:Vector.<Number>=previous?previous.fanPoints as Vector.<Number>:null;
            var same:Boolean=oldPoints!=null && previous.data!=null && oldPoints.length==points.length
                && previous.fanRadius===radius && previous.fanFull===full;
            for(var i:int=0;i<=count;i++) {
                var angle:Number=start+cone*i/count;
                var distance:Number=traceRay(light.x,light.y,Math.cos(angle),Math.sin(angle),radius);
                var px:Number=(radius+Math.cos(angle)*distance)/cell;
                var py:Number=(radius+Math.sin(angle)*distance)/cell;
                points[i*2]=px;points[i*2+1]=py;
                if(same && (oldPoints[i*2]!==px || oldPoints[i*2+1]!==py))same=false;
            }
            // Same radius, path type, vertex order and coordinates produce the
            // exact same local raster. World position/colour/brightness remain
            // applied by the original drawLight call on every render.
            if(same){ /* SHOT_GEOMETRY_REUSE */ return previous.data; }
            if(previous){previous.fanPoints=points;previous.fanRadius=radius;previous.fanFull=full;}
            var root:Sprite=new Sprite(),glow:Sprite=new Sprite(),mask:Sprite=new Sprite();
            var matrix:Matrix=new Matrix();matrix.createGradientBox(radius*2/cell,radius*2/cell);
            glow.graphics.beginGradientFill(GradientType.RADIAL,[0xFFFFFF,0xFFFFFF,0],[1,1,1],[0,45,255],matrix);
            glow.graphics.drawRect(0,0,side,side);glow.graphics.endFill();
            mask.graphics.beginFill(0xFFFFFF);
            if(!full)mask.graphics.moveTo(radius/cell,radius/cell);
            for(i=0;i<=count;i++) {
                px=points[i*2];py=points[i*2+1];
                if(i==0 && full)mask.graphics.moveTo(px,py);else mask.graphics.lineTo(px,py);
            }
            if(!full)mask.graphics.lineTo(radius/cell,radius/cell);
            mask.graphics.endFill();root.addChild(glow);root.addChild(mask);glow.mask=mask;
            var result:BitmapData=new BitmapData(side,side,false,0);
            result.draw(root);return result;
        }'''
 return once(s,old,new)

def hybrid(s,base,verify=False):
 marker='private function makeLight(light:Object,previous:Object=null):BitmapData {'
 original=extract(base,'private function makeLight(').replace('private function makeLight(','private function originalMakeLight(')
 s=once(s,marker,marker+'''\n            if(!rasterOptimized){if(previous)delete previous.fanPoints;return originalMakeLight(light);}''')
 s=once(s,'private var cache:Object = {};','private var cache:Object = {};public var rasterOptimized:Boolean=true;public var rasterChecks:int=0;public var geometryReuses:int=0;')
 s=once(s,'/* SHOT_GEOMETRY_REUSE */','geometryReuses++;')
 if verify:
  s=once(s,'return previous.data;','verifyRaster(previous.data,light);return previous.data;')
  s=once(s,'result.draw(root);return result;','result.draw(root);verifyRaster(result,light);return result;')
  original+='''
        private function verifyRaster(result:BitmapData,light:Object):void {
            var reference:BitmapData=originalMakeLight(light),difference:Object=result.compare(reference);
            if(!(difference is uint && uint(difference)==0))throw new Error("SHOT_GEOMETRY_PIXELS "+light.id+" "+light.x+","+light.y+" radius="+light.radius);
            reference.dispose();rasterChecks++;
        }
'''
 end=s.rfind('    }');return s[:end]+'        '+original+'\n'+s[end:]

if __name__=='__main__':
 root=OUT/'geometry-candidate/src';assert not root.exists();shutil.copytree(OUT/'lighting-baseline/src',root)
 p=root/'lad/LadLightField.as';p.write_text(optimize(p.read_text('utf8')),'utf8',newline='\n')
 (root.parent/'sources.json').write_text(json.dumps({f.relative_to(root).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
 print('Created exact polygon reuse candidate; every original ray is retained')
