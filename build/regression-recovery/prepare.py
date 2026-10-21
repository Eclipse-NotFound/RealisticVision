"""Surgical D35 fix from the exact D33+D34 production snapshot."""
from pathlib import Path
import shutil, re
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/regression-recovery-output'
BASE=MOD/'build/motion-performance-output/merged-settings/production/src'
VERSION='v0.33.2-settings-performance'

def change(s):
    assert s.count('v0.33.1-motion-performance')==1
    s=s.replace('v0.33.1-motion-performance',VERSION)
    s=s.replace('private var classicLogicCache:BitmapData;','''private var classicLogicCache:BitmapData;
      // D35: preserve the canonical field, but finish wall seams only in mask
      // regions that are actually queried. Display brightness never grants sight.
      private var classicLogicRaw:BitmapData;
      private var classicLogicVisibility:BitmapData;
      private var classicLogicWalls:BitmapData;
      private var classicLogicDeltas:Array;
      private var classicLogicTiles:Vector.<int>;''')
    s=s.replace('this.joinClassicWalls(loc);\n            // 部分敌人', '''this.joinClassicWalls(loc,logicOnly ? new Rectangle() : null);
            if(logicOnly)
            {
               this.classicLogicRaw=this.sizedScratch(this.classicLogicRaw);
               this.classicLogicVisibility=this.sizedScratch(this.classicLogicVisibility);
               this.classicLogicWalls=this.sizedScratch(this.classicLogicWalls);
               this.classicLogicRaw.copyPixels(this.fogRaw,this.fogRect,this.fogPoint);
               this.classicLogicVisibility.copyPixels(this.classicVisibilityField,this.fogRect,this.fogPoint);
               this.classicLogicWalls.copyPixels(this.fogCache,this.fogRect,this.fogPoint);
               this.classicLogicDeltas=this.classicCornerDeltas;
               this.classicLogicTiles=new Vector.<int>(this.spaceX*this.spaceY,true);
            }
            // 部分敌人''')
    start=s.index('      private function joinClassicWalls(')
    end=s.index('      private function sizedScratch(',start)
    part=s[start:end]
    part=part.replace('joinClassicWalls(loc:Location):void','joinClassicWalls(loc:Location, bounds:Rectangle = null, prepared:Boolean = false, visited:Vector.<int> = null):void')
    part=part.replace('         this.classicWallShade.fillRect','         if(!prepared)\n         {\n         this.classicWallShade.fillRect',1)
    part=part.replace('         var wallPoint:Point = new Point();','''         }
         var x0:int=bounds == null ? 0 : Math.max(0,int(bounds.x));
         var y0:int=bounds == null ? 0 : Math.max(0,int(bounds.y));
         var x1:int=bounds == null ? this.spaceX : Math.min(this.spaceX,int(bounds.right));
         var y1:int=bounds == null ? this.spaceY : Math.min(this.spaceY,int(bounds.bottom));
         if(x1<=x0 || y1<=y0) return;
         var wallPoint:Point = new Point();''')
    part=part.replace('''         for each(var wi:int in this.wallTiles)
         {
            wallPoint.x =''','''         var copyCount:int=bounds == null ? this.wallTiles.length : (x1-x0)*(y1-y0);
         for(var copyIndex:int=0;copyIndex<copyCount;copyIndex++)
         {
            var wi:int=bounds == null ? this.wallTiles[copyIndex] : x0+copyIndex%(x1-x0)+(y0+int(copyIndex/(x1-x0)))*this.spaceX;
            if(visited != null && visited[wi]) continue;
            if(bounds != null && loc.getTile(wi%this.spaceX,int(wi/this.spaceX)).opac<1) continue;
            wallPoint.x =''',1)
    part=part.replace('for(var ty:int = 0; ty < this.spaceY; ty++) for(var tx:int = 0; tx < this.spaceX; tx++)','for(var ty:int = y0; ty < y1; ty++) for(var tx:int = x0; tx < x1; tx++)')
    part=part.replace('''            if(loc.getTile(tx,ty).opac >= 1) continue;''','''            if(visited != null)
            {
               var vi:int=tx+ty*this.spaceX;
               if(visited[vi]) continue;
               visited[vi]=1;
            }
            if(loc.getTile(tx,ty).opac >= 1) continue;''',1)
    s=s[:start]+part+'''      /** Materialize each requested canonical tile once per refreshed field.
       * New units and changed bounds can query additional tiles in the same frame.
       * All arithmetic and raster inputs are those of the original full pass. */
      private function classicLogicRegion(bounds:Rectangle):void
      {
         if(this.cfgMode != "classic" || this.cfgDim == 0.35 || this.classicLogicTiles == null) return;
         var raw:BitmapData=this.fogRaw, bmp:BitmapData=this.fogBmp, cache:BitmapData=this.fogCache;
         var visibility:BitmapData=this.classicVisibilityField;
         var deltas:Array=this.classicCornerDeltas;
         try
         {
            this.fogRaw=this.classicLogicRaw;
            this.fogBmp=this.classicLogicCache;
            this.fogCache=this.classicLogicWalls;
            this.classicVisibilityField=this.classicLogicVisibility;
            this.classicCornerDeltas=this.classicLogicDeltas;
            this.joinClassicWalls(this.curLoc,bounds,true,this.classicLogicTiles);
         }
         finally
         {
            this.fogRaw=raw;this.fogBmp=bmp;this.fogCache=cache;
            this.classicVisibilityField=visibility;this.classicCornerDeltas=deltas;
         }
         var region:Rectangle=new Rectangle(FOG_PAD+bounds.x*FOG_SUB,FOG_PAD+bounds.y*FOG_SUB,bounds.width*FOG_SUB,bounds.height*FOG_SUB);
         this.fogCache.copyPixels(this.classicLogicCache,region,new Point(region.x,region.y));
      }

'''+s[end:]
    s=s.replace('''            bd.threshold(this.fogCache,''','''            this.classicLogicRegion(new Rectangle(x0,y0,x1-x0+1,y1-y0+1));
            bd.threshold(this.fogCache,''')
    s=s.replace('if(this.refreshWallField(loc,needFov,false)) changed = true;',
                'if(!separateLogic && this.refreshWallField(loc,needFov,false)) changed = true;')
    s=s.replace('''      private function resetOff():void
      {''','''      private function resetOff():void
      {
         this.releaseClassicLogic();''')
    s=s.replace('''      private function resetRoom(w:World, loc:Location):void
      {''','''      private function resetRoom(w:World, loc:Location):void
      {
         this.releaseClassicLogic();''')
    s=s.replace('''      private function sizedScratch(b:BitmapData):BitmapData''','''      private function releaseClassicLogic():void
      {
         if(this.classicLogicCache != null) this.classicLogicCache.dispose();
         if(this.classicLogicRaw != null) this.classicLogicRaw.dispose();
         if(this.classicLogicVisibility != null) this.classicLogicVisibility.dispose();
         if(this.classicLogicWalls != null) this.classicLogicWalls.dispose();
         this.classicLogicCache=this.classicLogicRaw=this.classicLogicVisibility=this.classicLogicWalls=null;
         this.classicLogicDeltas=null;this.classicLogicTiles=null;
      }

      private function sizedScratch(b:BitmapData):BitmapData''')
    # Reuse the falloff already needed for display. Do not recompute sqrt just
    # to preserve the fixed logical threshold when the display dim changes.
    s=s.replace('var br:Number = lit * this.distFalloff(sdx * sdx + sdy * sdy);','var br:Number = lit * this.distFalloff(sdx * sdx + sdy * sdy);\n                  var logicalBrightness:Number=br;')
    s=s.replace('''                  br = lit * this.distFalloff(sdx * sdx + sdy * sdy);
                  if(br < floorF)''','''                  br = lit * this.distFalloff(sdx * sdx + sdy * sdy);
                  logicalBrightness=br;
                  if(br < floorF)''')
    s=s.replace('''               var logicalA:int=Math.round((1-Math.max(lit*this.distFalloff(sdx*sdx+sdy*sdy),doorView?floorF:0.35))*255);
               if(lit > 0.0001 && logicalA < MASK_LIT_A && sdx*sdx+sdy*sdy <= this.locDist2*this.locDist2)
                  this.currentSight.setPixel32(FOG_PAD+tx*FOG_SUB+sx,FOG_PAD+ty*FOG_SUB+sy,0xFFFFFFFF);''','''               if(lit > 0.0001)
               {
                  var logicalA:int=Math.round((1-Math.max(logicalBrightness,doorView?floorF:0.35))*255);
                  if(logicalA < MASK_LIT_A && sdx*sdx+sdy*sdy <= this.locDist2*this.locDist2)
                     this.currentSight.setPixel32(FOG_PAD+tx*FOG_SUB+sx,FOG_PAD+ty*FOG_SUB+sy,0xFFFFFFFF);
               }''')
    return s

if __name__=='__main__':
    dest=OUT/'candidate/src';assert not dest.exists();shutil.copytree(BASE,dest)
    p=dest/'RealisticVisionMod.as';p.write_text(change(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
    print('prepared '+VERSION)
