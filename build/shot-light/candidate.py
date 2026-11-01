"""Exact hot-loop candidate: no new temporal cache or skipped light samples."""
from pathlib import Path
import hashlib,json,shutil
from profile import once
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output'
def optimize(s):
 s=once(s,'private var epoch:uint=0;','''private var epoch:uint=0;
        private var rayTerrain:Array;
        private var rayWidth:int=0,rayHeight:int=0;''')
 s=once(s,'public function clear():void {colors.length=stamps.length=touched.length=0;epoch=0;}',
 '''public function clear():void {colors.length=stamps.length=touched.length=0;epoch=0;rayTerrain=null;rayWidth=rayHeight=0;}''')
 s=once(s,'visits=rays=painted=0;limited=false;touched.length=0;',
 '''visits=rays=painted=0;limited=false;touched.length=0;
            // Room arrays and dimensions are stable during this synchronous raster.
            // Tile opacity is still read live for every test; each render rebinds.
            rayTerrain=loc.space;rayWidth=loc.spaceX;rayHeight=loc.spaceY;''')
 s=once(s,'var t:Number=len2>0.001?Math.max(0,Math.min(1,((wx-ax)*dx+(wy-ay)*dy)/len2)):1;',
 '''var t:Number=len2>0.001?((wx-ax)*dx+(wy-ay)*dy)/len2:1;
                            if(t<0)t=0;else if(t>1)t=1;''')
 s=once(s,'var strength:Number=Math.min(1,q*q*longitudinal*light.power);',
 '''var strength:Number=q*q*longitudinal*light.power;
                            if(strength>1)strength=1;''')
 s=once(s,'''colors[index]=(Math.max(old>>16&255,int(red*strength))<<16)|
                                (Math.max(old>>8&255,int(green*strength))<<8)|Math.max(old&255,int(blue*strength));''',
 '''var rr:int=int(red*strength),gg:int=int(green*strength),bb:int=int(blue*strength);
                            var oldR:int=old>>16&255,oldG:int=old>>8&255,oldB:int=old&255;
                            if(oldR>rr)rr=oldR;if(oldG>gg)gg=oldG;if(oldB>bb)bb=oldB;
                            colors[index]=(rr<<16)|(gg<<8)|bb;''')
 start=s.index('        private function visible(')
 tail=s[start:].replace('loc.spaceX','rayWidth').replace('loc.spaceY','rayHeight').replace('loc.space[','rayTerrain[')
 tail=once(tail,'''if(Number(rayTerrain[cx][cy].opac)>=0.99 || Number(rayTerrain[ex][ey].opac)>=0.99)return false;
            if(cx==ex && cy==ey)return true;''',
 '''if(Number(rayTerrain[cx][cy].opac)>=0.99)return false;
            if(cx==ex && cy==ey){ /* SHOT_SAME_CELL */ return true; }
            if(Number(rayTerrain[ex][ey].opac)>=0.99)return false;''')
 marker='            var tx:Number=Math.abs(dx)<0.00001?1e20:Math.abs(40/dx),ty:Number=Math.abs(dy)<0.00001?1e20:Math.abs(40/dy),opacity:Number=0;'
 tail=once(tail,marker,'''            // Preserve the original corner tolerance, including endpoints on
            // grid lines. Only return when the original next step reaches the
            // already-checked destination without touching a corner.
            if(Math.abs(nx-ny)>=0.000001 &&
                ((cy==ey && cx+stepX==ex && nx<ny) || (cx==ex && cy+stepY==ey && ny<nx))) {
                /* SHOT_ADJACENT */ return true;
            }
'''+marker)
 return s[:start]+tail
def extract(s,label):
 start=s.index(label);brace=s.index('{',start);depth=1;i=brace+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[start:i]
def hybrid(candidate,baseline):
 s=once(candidate,'public static const MAX_VISITS:int=65536;','public static const MAX_VISITS:int=65536;public var optimized:Boolean=true;')
 marker='public function render(target:BitmapData,bounds:Rectangle,cell:int,loc:*,lights:Array):void {'
 s=once(s,marker,marker+'\n            if(!optimized){baselineRender(target,bounds,cell,loc,lights);return;}')
 render=extract(baseline,'public function render(').replace('public function render(','private function baselineRender(').replace('!visible(','!baselineVisible(')
 visible=extract(baseline,'private function visible(').replace('private function visible(','private function baselineVisible(')
 end=s.rfind('    }')
 return s[:end]+'        '+render+'\n        '+visible+'\n'+s[end:]
if __name__=='__main__':
 root=OUT/'candidate/src';assert not root.exists();shutil.copytree(OUT/'lighting-baseline/src',root)
 p=root/'lad/LadTrailRaster.as';p.write_text(optimize(p.read_text('utf8')),'utf8',newline='\n')
 (root.parent/'sources.json').write_text(json.dumps({f.relative_to(root).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
 print('Created hot-loop candidate; original sample order, coverage and budget retained')
