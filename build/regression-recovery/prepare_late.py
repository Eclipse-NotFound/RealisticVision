"""Second candidate: defer native raster work as well as per-pixel wall joins."""
import shutil
import prepare as p

def change(s):
 s=p.change(s)
 s=s.replace('private var classicLogicRaw:BitmapData;', '''private var classicLogicMemorySamples:BitmapData;
      private var classicLogicVisibilitySamples:BitmapData;
      private var classicLogicRaw:BitmapData;''')
 s=s.replace('''            this.classicLogicCache=this.sizedScratch(this.classicLogicCache);
            this.classicLogicCache.copyPixels(this.fogCache,this.fogRect,this.fogPoint);
''','')
 start=s.index('            this.joinClassicWalls(loc,logicOnly ? new Rectangle() : null);')
 end=s.index('            // 部分敌人',start)
 s=s[:start]+'            this.joinClassicWalls(loc);\n'+s[end:]
 start=s.index('         if(!separateLogic && this.refreshWallField(loc,needFov,false)) changed = true;')
 end=start+len('         if(!separateLogic && this.refreshWallField(loc,needFov,false)) changed = true;')
 s=s[:end]+'''
         if(logicOnly)
         {
               // Always snapshot: a live brightness change can enter this
               // path before any canonical cache exists, even if samples match.
               // Keep the exact low-resolution inputs of this generation.
               // Mask queries will rasterize only their padded tile bounds.
               for(var ly:int=1;ly<=this.spaceY;ly++)
                  this.classicVisibilityRaw.setPixel(this.spaceX,ly,this.classicVisibilityRaw.getPixel(this.spaceX-1,ly));
               for(var lx:int=0;lx<=this.spaceX;lx++)
               {
                  this.classicVisibilityRaw.setPixel(lx,0,this.classicVisibilityRaw.getPixel(lx,1));
                  this.classicVisibilityRaw.setPixel(lx,this.spaceY+1,this.classicVisibilityRaw.getPixel(lx,this.spaceY));
               }
               if(this.classicLogicMemorySamples == null)
               {
                  this.classicLogicMemorySamples=this.classicMemoryRaw.clone();
                  this.classicLogicVisibilitySamples=this.classicVisibilityRaw.clone();
               }
               else
               {
                  this.classicLogicMemorySamples.copyPixels(this.classicMemoryRaw,this.classicMemoryRaw.rect,this.fogPoint);
                  this.classicLogicVisibilitySamples.copyPixels(this.classicVisibilityRaw,this.classicVisibilityRaw.rect,this.fogPoint);
               }
               this.classicLogicCache=this.sizedScratch(this.classicLogicCache);
               this.classicLogicRaw=this.sizedScratch(this.classicLogicRaw);
               this.classicLogicVisibility=this.sizedScratch(this.classicLogicVisibility);
               this.classicLogicWalls=this.sizedScratch(this.classicLogicWalls);
               this.classicLogicCache.fillRect(this.fogRect,0xFF000000);
               this.classicLogicDeltas=new Array(this.spaceX*this.spaceY);
               this.classicLogicTiles=new Vector.<int>(this.spaceX*this.spaceY,true);
               if(changed) this.fovVersion++;
            return;
         }
'''+s[end:]
 start=s.index('      private function classicLogicRegion(');end=s.index('      private function releaseClassicLogic(',start)
 s=s[:start]+'''      private function classicLogicRegion(bounds:Rectangle):void
      {
         if(this.cfgMode != "classic" || this.cfgDim == 0.35 || this.classicLogicTiles == null) return;
         var region:Rectangle=new Rectangle(FOG_PAD+bounds.x*FOG_SUB,FOG_PAD+bounds.y*FOG_SUB,bounds.width*FOG_SUB,bounds.height*FOG_SUB);
         var fresh:Boolean=false;
         var tx:int,ty:int;
         for(ty=bounds.y;ty<bounds.bottom && !fresh;ty++) for(tx=bounds.x;tx<bounds.right;tx++)
            if(!this.classicLogicTiles[tx+ty*this.spaceX]){fresh=true;break;}
         if(fresh)
         {
            var raw:BitmapData=this.fogRaw,bmp:BitmapData=this.fogBmp,cache:BitmapData=this.fogCache;
            var visibility:BitmapData=this.classicVisibilityField;
            var deltas:Array=this.classicCornerDeltas;
            try
            {
               this.fogRaw=this.classicLogicRaw;this.fogBmp=this.classicLogicCache;this.fogCache=this.classicLogicWalls;
               this.classicVisibilityField=this.classicLogicVisibility;this.classicCornerDeltas=this.classicLogicDeltas;
               // AIR's clipped smooth raster adds edge rounding with a one-pixel
               // gutter. Two tiles of support match the full raster exactly.
               var sample:Rectangle=region.clone();sample.inflate(16,16);sample=sample.intersection(this.fogRect);
               this.fogRaw.fillRect(sample,0xFFFFFFFF);
               this.fogRaw.draw(this.classicRaw,this.classicLightMatrix,null,null,sample,true);
               this.fogRaw.draw(this.classicLogicMemorySamples,this.classicMemoryMatrix,null,null,sample,true);
               this.fogRaw.colorTransform(sample,this.brightnessToFog);
               this.classicVisibilityField.fillRect(sample,0xFFFFFFFF);
               this.classicVisibilityField.draw(this.classicLogicVisibilitySamples,this.classicMemoryMatrix,null,null,sample,true);
               this.fogCache.fillRect(region,0xFFFFFFFF);
               this.fogCache.draw(this.wallRaw,this.classicLightMatrix,null,null,region,true);
               this.fogCache.draw(this.classicVisibilityField,null,null,"multiply",region);
               this.fogCache.colorTransform(region,this.brightnessToFog);
               var cell:Rectangle=new Rectangle(0,0,FOG_SUB,FOG_SUB),point:Point=new Point();
               for(ty=bounds.y;ty<bounds.bottom;ty++) for(tx=bounds.x;tx<bounds.right;tx++)
               {
                  if(this.classicLogicTiles[tx+ty*this.spaceX]) continue;
                  cell.x=point.x=FOG_PAD+tx*FOG_SUB;cell.y=point.y=FOG_PAD+ty*FOG_SUB;
                  this.fogBmp.fillRect(cell,0);
                  this.fogBmp.copyChannel(this.fogRaw,cell,point,BitmapDataChannel.RED,BitmapDataChannel.ALPHA);
               }
               for(ty=bounds.y;ty<=bounds.bottom && ty<this.spaceY;ty++) for(tx=bounds.x;tx<=bounds.right && tx<this.spaceX;tx++)
               {
                  var ci:int=tx+ty*this.spaceX;
                  if(this.classicCornerDeltas[ci] !== undefined) continue;
                  this.classicCornerDeltas[ci]=this.wallA[ci] === undefined ? 0 :
                     this.classicWallDelta(this.wallA[ci],FOG_PAD+tx*FOG_SUB-0.5,FOG_PAD+ty*FOG_SUB-0.5);
               }
               this.joinClassicWalls(this.curLoc,bounds,true,this.classicLogicTiles);
            }
            finally
            {
               this.fogRaw=raw;this.fogBmp=bmp;this.fogCache=cache;
               this.classicVisibilityField=visibility;this.classicCornerDeltas=deltas;
            }
         }
         this.fogCache.copyPixels(this.classicLogicCache,region,new Point(region.x,region.y));
      }

'''+s[end:]
 s=s.replace('''         if(this.classicLogicCache != null) this.classicLogicCache.dispose();''','''         if(this.classicLogicMemorySamples != null) this.classicLogicMemorySamples.dispose();
         if(this.classicLogicVisibilitySamples != null) this.classicLogicVisibilitySamples.dispose();
         this.classicLogicMemorySamples=this.classicLogicVisibilitySamples=null;
         if(this.classicLogicCache != null) this.classicLogicCache.dispose();''')
 return s

if __name__=='__main__':
 dest=p.OUT/'candidate-v4/src';assert not dest.exists();shutil.copytree(p.BASE,dest)
 file=dest/'RealisticVisionMod.as';file.write_text(change(file.read_text(encoding='utf-8-sig')),encoding='utf-8')
 print('prepared regional raster candidate')
