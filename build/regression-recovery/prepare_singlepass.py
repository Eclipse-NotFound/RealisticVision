"""One terrain traversal generates display and canonical brightness samples."""
import shutil
import prepare as p
import prepare_persistent

def change(s):
 s=prepare_persistent.change(s)
 start=s.index('         var separateLogic:Boolean = !logicOnly')
 end=s.index('\n         if(changed)\n',start)
 s=s[:start]+'''         var separateLogic:Boolean = this.cfgDim != 0.35;
         if(separateLogic && this.classicLogicMemorySamples == null)
         {
            this.classicLogicMemorySamples=new BitmapData(this.classicMemoryRaw.width,this.classicMemoryRaw.height,true,0xFF000000);
            this.classicLogicVisibilitySamples=new BitmapData(this.classicVisibilityRaw.width,this.classicVisibilityRaw.height,false,0xFFFFFF);
         }
         var changed:Boolean=needFov || separateLogic;
         var logicalChanged:Boolean=needFov;
         var displayGrey:int=Math.round(255*this.cfgDim);
         var canonicalGrey:int=Math.round(255*0.35);
         // Both fields share terrain, light and memory progress. Only their
         // grey values and deepest-neighbour choice may differ.
         for(var mi:int=0;mi<this.spaceX*this.spaceY;mi++) this.advanceMemory(loc,mi);
         for(var ty:int=0;ty<this.spaceY;ty++) for(var tx:int=0;tx<this.spaceX;tx++)
         {
            var i:int=tx+ty*this.spaceX;
            var a:int=this.tileFogAlpha(loc,tx,ty);
            if(a != this.lastA[i])
            {
               this.lastA[i]=a;this.classicRaw.setPixel32(tx,ty+1,a<<24);
               changed=logicalChanged=true;
            }
            var explored:Boolean=this.memoryExplored(i);
            var solid:Boolean=loc.getTile(tx,ty).opac>=1;
            var memory:Number=this.memCur[i], logicalMemory:Number=memory;
            var targetGrey:int=explored?displayGrey:0;
            var logicalTarget:int=explored?canonicalGrey:0;
            var grey:int=solid?Math.round((255-a)*this.cfgDim):targetGrey;
            var logicalGrey:int=solid?Math.round((255-a)*0.35):logicalTarget;
            if(!loc.retDark && solid)
            {
               var deepest:Number=0,logicalDeepest:Number=0;
               for(var dy:int=-1;dy<=1;dy++) for(var dx:int=-1;dx<=1;dx++)
               {
                  var nx:int=tx+dx,ny:int=ty+dy;
                  if(nx<=0 || ny<=0 || nx>=this.spaceX || ny>=this.spaceY || loc.getTile(nx,ny).opac>=1)continue;
                  var ni:int=nx+ny*this.spaceX;
                  var ne:Boolean=this.memoryExplored(ni);
                  var nm:Number=this.memCur[ni];
                  var ng:int=ne?displayGrey:0;
                  var depth:Number=nm*(255-ng);
                  if(depth>deepest){deepest=depth;memory=nm;grey=targetGrey=ng;}
                  if(separateLogic)
                  {
                     ng=ne?canonicalGrey:0;depth=nm*(255-ng);
                     if(depth>logicalDeepest){logicalDeepest=depth;logicalMemory=nm;logicalGrey=logicalTarget=ng;}
                  }
               }
            }
            var memoryAlpha:int=Math.round(memory*255);
            var pixel:uint=memoryAlpha==0?0:(memoryAlpha<<24)|(grey<<16)|(grey<<8)|grey;
            if(tx==0 || ty==0)pixel=0xFF000000;
            var visibility:int=Math.round(255-memory*(255-targetGrey));
            var visibilityPixel:uint=(visibility<<16)|(visibility<<8)|visibility;
            if(this.classicVisibilityRaw.getPixel(tx,ty+1)!=visibilityPixel)
            {this.classicVisibilityRaw.setPixel(tx,ty+1,visibilityPixel);changed=true;}
            if(this.classicMemoryRaw.getPixel32(tx,ty+1)!=pixel)
            {this.classicMemoryRaw.setPixel32(tx,ty+1,pixel);changed=true;}
            if(separateLogic)
            {
               memoryAlpha=Math.round(logicalMemory*255);
               pixel=memoryAlpha==0?0:(memoryAlpha<<24)|(logicalGrey<<16)|(logicalGrey<<8)|logicalGrey;
               if(tx==0 || ty==0)pixel=0xFF000000;
               visibility=Math.round(255-logicalMemory*(255-logicalTarget));
               visibilityPixel=(visibility<<16)|(visibility<<8)|visibility;
               if(this.classicLogicVisibilitySamples.getPixel(tx,ty+1)!=visibilityPixel)
               {this.classicLogicVisibilitySamples.setPixel(tx,ty+1,visibilityPixel);logicalChanged=true;}
               if(this.classicLogicMemorySamples.getPixel32(tx,ty+1)!=pixel)
               {this.classicLogicMemorySamples.setPixel32(tx,ty+1,pixel);logicalChanged=true;}
            }
         }
         if(this.refreshWallField(loc,needFov,false))changed=logicalChanged=true;
         if(separateLogic && (logicalChanged || this.classicLogicCache==null))
         {
            for(var ly:int=1;ly<=this.spaceY;ly++)
               this.classicLogicVisibilitySamples.setPixel(this.spaceX,ly,this.classicLogicVisibilitySamples.getPixel(this.spaceX-1,ly));
            for(var lx:int=0;lx<=this.spaceX;lx++)
            {
               this.classicLogicVisibilitySamples.setPixel(lx,0,this.classicLogicVisibilitySamples.getPixel(lx,1));
               this.classicLogicVisibilitySamples.setPixel(lx,this.spaceY+1,this.classicLogicVisibilitySamples.getPixel(lx,this.spaceY));
            }
            this.classicLogicCache=this.sizedScratch(this.classicLogicCache);
            this.classicLogicRaw=this.sizedScratch(this.classicLogicRaw);
            this.classicLogicVisibility=this.sizedScratch(this.classicLogicVisibility);
            this.classicLogicWalls=this.sizedScratch(this.classicLogicWalls);
            this.classicLogicCache.fillRect(this.fogRect,0xFF000000);
            this.classicLogicDeltas=new Array(this.spaceX*this.spaceY);
            this.classicLogicTiles=new Vector.<int>(this.spaceX*this.spaceY,true);
            if(logicalChanged)this.fovVersion++;
         }
''' + s[end:]
 return s

if __name__=='__main__':
 dest=p.OUT/'candidate-v6/src';assert not dest.exists();shutil.copytree(p.BASE,dest)
 file=dest/'RealisticVisionMod.as';file.write_text(change(file.read_text(encoding='utf-8-sig')),encoding='utf-8')
 print('prepared single traversal candidate')
