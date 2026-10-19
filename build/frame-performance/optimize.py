"""Apply exact D30 edits to a chosen development source; no release writes."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]

def replace_one(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)

def optimize(s):
    s=replace_one(s,'public class RealisticVisionMod extends Sprite\n   {','''public class RealisticVisionMod extends Sprite
   {
      // Lazily classify only tiles actually queried by units. A new immutable
      // sight snapshot invalidates all summaries, including stationary changes.
      private var classifiedSight:Vector.<uint>;
      private var sightClasses:Vector.<int>;''')
    s=replace_one(s,'         this.wallSurface.reset();\n         this.curLoc = null;','         this.wallSurface.reset();\n         this.curLoc = null;\n         this.classifiedSight = null; this.sightClasses = null;')
    s=replace_one(s,'         this.currentSightData = null;\n         this.wallGeometryDirty = true;','         this.currentSightData = null;\n         this.classifiedSight = null; this.sightClasses = null;\n         this.wallGeometryDirty = true;')
    begin=s.index('            var fg:BitmapData = this.fogCache;',s.index('private function applyMask('))
    end=s.index('\n         }\n         else',begin)
    s=s[:begin]+'''            // The old world -> tile -> subcell arithmetic resolves exactly
            // to this in-bounds integer rectangle (MASK_SUB == FOG_SUB).
            bd.threshold(this.fogCache,
               new Rectangle(FOG_PAD+x0*MASK_SUB,FOG_PAD+y0*MASK_SUB,totx,toty),
               this.fogPoint,"<",uint(MASK_LIT_A)<<24,0xFFFFFFFF,0xFF000000,false);'''+s[end:]
    # Keep current's original inward-feather loop: two measured native bulk
    # alternatives were pixel-equivalent but slower for these small masks.
    anchor='''         var blur:BlurFilter = this.cfgMode == "classic" ? this.maskBlurClassic : this.maskBlurCurrent;
         if(blur.blurX > 0)'''
    s=replace_one(s,anchor,'''         var blur:BlurFilter = this.cfgMode == "classic" ? this.maskBlurClassic : this.maskBlurCurrent;
         // Every eligible sample is still refreshed above. Reuse the rendered
         // mask only when its complete input, world rectangle and filter match.
         // Display attachment/restoration above always runs, even on a hit.
         var previousInput:BitmapData = rec.maskInput as BitmapData;
         if(rec.maskValid === true && previousInput != null
            && previousInput.width == bd.width && previousInput.height == bd.height
            && rec.maskBounds == sig && rec.maskMode == this.cfgMode
            && rec.maskBlurX == blur.blurX && rec.maskBlurY == blur.blurY && rec.maskQuality == blur.quality)
         {
            var maskDelta:Object = bd.compare(previousInput);
            if(maskDelta is uint && uint(maskDelta) == 0) return;
            if(maskDelta is BitmapData) BitmapData(maskDelta).dispose();
         }
         rec.maskValid = false;
         if(blur.blurX > 0)''')
    s=replace_one(s,'''         s3.graphics.copyFrom(g);
      }''','''         s3.graphics.copyFrom(g);
         if(previousInput == null || previousInput.width != bd.width || previousInput.height != bd.height)
         {
            if(previousInput != null) previousInput.dispose();
            previousInput = new BitmapData(bd.width,bd.height,true,0);
            rec.maskInput = previousInput;
         }
         previousInput.copyPixels(bd,bd.rect,this.fogPoint);
         rec.maskBounds = sig; rec.maskMode = this.cfgMode;
         rec.maskBlurX = blur.blurX; rec.maskBlurY = blur.blurY; rec.maskQuality = blur.quality;
         rec.maskValid = true;
      }''')
    anchor='''         for(var sy:int = 0; sy < FOG_SUB; sy++)
         {
            var fy:Number = (sy + 0.5) / FOG_SUB;'''
    s=replace_one(s,anchor,'''         // Uniform corners interpolate to the same integer for every sample.
         // Preserve the tracking path, including its old threshold comparison.
         if(!trackMask && a00 == a10 && a00 == a01 && a00 == a11
            && (this.cfgMode != "current" || this.currentSight == null
               || this.fov[tx+ty*this.spaceX] == FOV_NONE
               || (p00 == p10 && p00 == p01 && p00 == p11)))
         {
            this.fogCellRect.x = FOG_PAD + tx * FOG_SUB;
            this.fogCellRect.y = FOG_PAD + ty * FOG_SUB;
            this.fogCache.fillRect(this.fogCellRect,uint(Math.round(a00))<<24);
            if(this.cfgMode == "current" && this.currentSight != null)
               this.currentSight.fillRect(this.fogCellRect,
                  p00 < MASK_LIT_A && this.fov[tx+ty*this.spaceX] != FOV_NONE ? 0xFFFFFFFF : 0);
            return false;
         }
'''+anchor)
    anchor='''            // 格中心全亮时，单位边角仍可能被挡住；不能直接跳过子格掩膜。
            var first:int=-1;'''
    s=replace_one(s,anchor,'''            // Bounding boxes are tile aligned. Reusing each tile's exact
            // all-dark/all-visible/mixed summary avoids rescanning overlapping
            // unit bounds (including multiple units sharing a visual).
            if(bb[0]>=0 && bb[1]>=0 && bb[2]<this.spaceX && bb[3]<this.spaceY)
            {
               if(this.classifiedSight !== this.currentSightData)
               {
                  this.classifiedSight = this.currentSightData;
                  this.sightClasses = new Vector.<int>(this.spaceX*this.spaceY,true);
               }
               var combined:int = 0;
               var data:Vector.<uint> = this.currentSightData;
               var width:int = this.currentSight.width;
               for(var ty:int=bb[1];ty<=bb[3];ty++) for(var tx:int=bb[0];tx<=bb[2];tx++)
               {
                  var ti:int=tx+ty*this.spaceX;
                  var kind:int=this.sightClasses[ti];
                  if(kind==0)
                  {
                     var start:int=(FOG_PAD+ty*MASK_SUB)*width+FOG_PAD+tx*MASK_SUB;
                     kind=data[start]!=0?2:1;
                     for(var row:int=0;row<MASK_SUB && kind!=3;row++)
                        for(var col:int=0;col<MASK_SUB;col++)
                           if((data[start+row*width+col]!=0?2:1)!=kind){kind=3;break;}
                     this.sightClasses[ti]=kind;
                  }
                  if(kind==3 || (combined!=0 && kind!=combined))return 2;
                  combined=kind;
               }
               return combined==2?1:0;
            }
            // Preserve the original fallback for unusual out-of-room bounds.
            var first:int=-1;''')
    return s

if __name__=='__main__':
    target=Path(sys.argv[1]) if len(sys.argv)>1 else MOD/'build/frame-performance-output/candidate/src/RealisticVisionMod.as'
    source=MOD/'build/frame-performance-output/baseline/src/RealisticVisionMod.as' if len(sys.argv)==1 else target
    target.write_text(optimize(source.read_text(encoding='utf-8-sig')),encoding='utf-8')
