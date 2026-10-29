"""D57 second hypothesis: trim empty native blit margins, retain D56 raster."""
from pathlib import Path
import shutil
M=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;O=M/'build/enemy-combat-output';D=O/'candidates/alpha_clip/src'
if not D.exists():shutil.copytree(O/'baseline/src',D)
p=D/'RealisticVisionMod.as';s=(O/'baseline/src/RealisticVisionMod.as').read_text()
old='kind=name=="fe.graph::Part" || name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet";'
new='kind=name=="fe.graph::Part" ? 2 : (name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet");'
assert s.count(old)==1;s=s.replace(old,new)
old='if(kind && obj.vis != null)this.applyWorldVisual(obj.vis);'
new='if(kind && obj.vis != null)this.applyWorldVisual(obj.vis,kind===2 && Object(obj)["blitData"]!=null);'
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('private function applyWorldVisual(visual:DisplayObject):void','private function applyWorldVisual(visual:DisplayObject,nativeBlit:Boolean=false):void')
at='''            var clipLeft:int=Math.max(drawX,(Math.floor(bounds.left/drawScale)-2)*drawScale);'''
new='''            // Native Part.initBlit owns a single bitmap with no vector art.
            // Keep the full sampling field and original world-space fill;
            // omit only transparent sprite-sheet margins from the draw shape.
            var clipBounds:Rectangle=bounds;
            var container:DisplayObjectContainer=visual as DisplayObjectContainer;
            var vm:Matrix=visual.transform.matrix;
            if(nativeBlit && container!=null && container.numChildren==1
               && container.getChildAt(0) is Bitmap && vm.b==0 && vm.c==0 && Math.abs(vm.a)==1 && Math.abs(vm.d)==1){
               var child:Bitmap=container.getChildAt(0) as Bitmap;
               var cm:Matrix=child.transform.matrix;
               if(child.bitmapData!=null && cm.a==1 && cm.d==1 && cm.b==0 && cm.c==0){
                  var occupied:Rectangle=child.bitmapData.getColorBoundsRect(0xff000000,0,false);
                  if(!occupied.isEmpty()){
                     occupied.inflate(1,1); // include native bilinear neighbours
                     var ax:Number=(occupied.left+cm.tx)*vm.a+vm.tx;
                     var ay:Number=(occupied.top+cm.ty)*vm.d+vm.ty;
                     var bx:Number=(occupied.right+cm.tx)*vm.a+vm.tx;
                     var by:Number=(occupied.bottom+cm.ty)*vm.d+vm.ty;
                     clipBounds=new Rectangle(Math.min(ax,bx),Math.min(ay,by),Math.abs(bx-ax),Math.abs(by-ay)).intersection(bounds); // D57_ALPHA_CLIP
                  }
               }
            }
            var clipLeft:int=Math.max(drawX,(Math.floor(clipBounds.left/drawScale)-2)*drawScale);'''
assert s.count(at)==1;s=s.replace(at,new)
s=s.replace('Math.floor(bounds.top/drawScale)','Math.floor(clipBounds.top/drawScale)').replace('Math.ceil(bounds.right/drawScale)','Math.ceil(clipBounds.right/drawScale)').replace('Math.ceil(bounds.bottom/drawScale)','Math.ceil(clipBounds.bottom/drawScale)')
p.write_text(s,encoding='utf-8')
# Reuse D56's continuous independent objects, with actual 120x120 transparent
# animation buffers. The original baseline remains D56, never D44.
s=(M/'build/effect-mask-origin/check.py').read_text().replace('effect-mask-origin-output','enemy-combat-output').replace('RealisticVision / D56','RealisticVision / D57')
a=s.index("r.public(OUT/'candidates'/");b=s.index('\n p=src/',a)
s=s[:a]+"r.public(OUT/'candidates'/chosen/'src',src)"+s[b:]
s=s.replace("MOD/'build/combat-render-output/production-final2/src/RealisticVisionMod.as'","OUT/'baseline/src/RealisticVisionMod.as'")
at=" (folder/'EffectLoadChecks.as').write_text(t,encoding='utf-8')"
extra='''
 t=t.replace('b.applyWorldVisual(bb[i])','b.applyWorldVisual(bb[i],true)')
 old='var data:BitmapData=new BitmapData([3,6,12][i%3],[3,6,12][i%3],true,0xff12fd88+i);data.setPixel32(0,0,0);'
 new='var data:BitmapData=new BitmapData(120,120,true,0);data.fillRect(new Rectangle(48,49,3+i%17,4+i%13),0xff12fd88+i);data.setPixel32(50,50,0);'
 assert t.count(old)==1;t=t.replace(old,new)
 t=t.replace('va.rotation=vb.rotation=(i+age)%19;', 'va.rotation=vb.rotation=i%2==0?0:(i+age)%19;')
 t=t.replace('Bitmap(va.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);Bitmap(vb.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);', 'for each(var animated:Sprite in [va,vb]){var data:BitmapData=Bitmap(animated.getChildAt(0)).bitmapData;data.fillRect(data.rect,0);data.fillRect(new Rectangle(48+age%5,49,3+i%17,4+i%13),age%2?0xff80f030:0x802080f0);Bitmap(animated.getChildAt(0)).x=-60;Bitmap(animated.getChildAt(0)).y=-60;}')
 p=src/'RealisticVisionMod.as';code=p.read_text();code=code.replace('public var trailingHits:int=0;','public var trailingHits:int=0;public var alphaHits:int=0;').replace('// D57_ALPHA_CLIP','alphaHits++; // D57_ALPHA_CLIP');p.write_text(code,encoding='utf-8')
 t=t.replace('trace("LOAD COMPLETE passed="+passed);','check(b.alphaHits>100,"native alpha bounds exercised");trace("ALPHA HITS "+b.alphaHits);trace("LOAD COMPLETE passed="+passed);')
'''
assert s.count(at)==1;s=s.replace(at,extra+at)
(H/'alpha_check.py').write_text(s,encoding='utf-8')
print('alpha_clip prepared separately from rejected body candidate')
