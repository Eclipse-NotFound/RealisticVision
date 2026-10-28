"""Remove per-effect scratch allocations from the validated integer tile crop."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
BASE=MOD/'build/sustained-fire-output/candidates/integer/src'
OUT=MOD/'build/sustained-fire-output/candidates/integer-v2/src'
assert not OUT.exists()
s=(BASE/'RealisticVisionMod.as').read_text()
s=s.replace('private var worldMasks:Object = {};','private var worldMasks:Object = {};\n      private var worldPixelLattice:Dictionary = new Dictionary(true);')
s=s.replace('var drawClip:Rectangle=null;\n         var screenMatrix:Matrix=visual.parent.transform.concatenatedMatrix;','var crop:Boolean=false;\n         var clipLeft:int=0,clipTop:int=0,clipRight:int=0,clipBottom:int=0;')
s=s.replace('screenMatrix.a==1 && screenMatrix.d==1 && screenMatrix.b==0 && screenMatrix.c==0 && screenMatrix.tx==Math.floor(screenMatrix.tx) && screenMatrix.ty==Math.floor(screenMatrix.ty)', 'this.worldParentPixelAligned(visual.parent)')
s=s.replace('var clipLeft:int=Math.max(0,x0-1),clipTop:int=Math.max(0,y0-1);','clipLeft=Math.max(0,x0-1);clipTop=Math.max(0,y0-1);')
s=s.replace('var clipRight:int=Math.min(this.spaceX,x1+2),clipBottom:int=Math.min(this.spaceY,y1+2);','clipRight=Math.min(this.spaceX,x1+2);clipBottom=Math.min(this.spaceY,y1+2);')
s=s.replace('drawClip=new Rectangle(clipLeft*Tile.tileX,clipTop*Tile.tileY,(clipRight-clipLeft)*Tile.tileX,(clipBottom-clipTop)*Tile.tileY);','crop=true;')
s=s.replace('var clipChanged:Boolean=(drawClip==null)!=(record.drawClip==null) || (drawClip!=null && (record.drawClip==null || !drawClip.equals(record.drawClip)));','var clipChanged:Boolean=record.crop!==crop || (crop && (record.clipLeft!=clipLeft || record.clipTop!=clipTop || record.clipRight!=clipRight || record.clipBottom!=clipBottom));')
s=s.replace('else if(drawClip!=null){','else if(crop){')
s=s.replace('shape.graphics.drawRect(drawClip.x,drawClip.y,drawClip.width,drawClip.height);','shape.graphics.drawRect(clipLeft*Tile.tileX,clipTop*Tile.tileY,(clipRight-clipLeft)*Tile.tileX,(clipBottom-clipTop)*Tile.tileY);')
s=s.replace('record.drawClip=drawClip;','record.crop=crop;record.clipLeft=clipLeft;record.clipTop=clipTop;record.clipRight=clipRight;record.clipBottom=clipBottom;')
needle='      private function worldVisualHasFilters(visual:DisplayObject):Boolean'
helper='''      // All calls in one world pass are synchronous. Adding/removing a mask
      // does not change its parent's transform; resample on the next pass.
      private function worldParentPixelAligned(parent:DisplayObjectContainer):Boolean
      {
         var entry:Object=this.worldPixelLattice[parent];
         if(entry==null){entry={pass:-1,aligned:false};this.worldPixelLattice[parent]=entry;}
         if(entry.pass!=this.worldPass){
            var m:Matrix=parent.transform.concatenatedMatrix;
            entry.aligned=m.a==1 && m.d==1 && m.b==0 && m.c==0
               && m.tx==Math.floor(m.tx) && m.ty==Math.floor(m.ty);
            entry.pass=this.worldPass;
         }
         return entry.aligned;
      }

'''
assert s.count(needle)==1;s=s.replace(needle,helper+needle)
s=s.replace('this.worldMasks={};this.worldPass=0;','this.worldMasks={};this.worldPass=0;this.worldPixelLattice=new Dictionary(true);')
assert 'drawClip' not in s and 'screenMatrix' not in s
shutil.copytree(BASE,OUT)
(OUT/'RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
