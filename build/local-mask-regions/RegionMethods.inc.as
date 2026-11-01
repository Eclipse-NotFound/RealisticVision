      // Exact 8x8 binary inputs, not samples or hashes. A monotonically increasing
      // stamp changes only when one of the 64 logical pixels changes.
      private var regionSource:BitmapData;
      private var regionMode:String;
      private var regionLo:Vector.<uint>,regionHi:Vector.<uint>;
      private var regionStamp:Vector.<Number>,regionRead:Vector.<Number>;
      private var regionClock:Number=0;

      private function ensureRegions(source:BitmapData):void
      {
         var n:int=this.spaceX*this.spaceY;
         if(this.regionSource===source && this.regionMode==this.cfgMode && this.regionLo!=null && this.regionLo.length==n)return;
         this.regionSource=source;this.regionMode=this.cfgMode;this.regionClock=0;
         this.regionLo=new Vector.<uint>(n,true);this.regionHi=new Vector.<uint>(n,true);
         this.regionStamp=new Vector.<Number>(n,true);this.regionRead=new Vector.<Number>(n,true);
         for(var i:int=0;i<n;i++)this.regionRead[i]=-1;
      }

      private function putRegion(tx:int,ty:int,lo:uint,hi:uint):void
      {
         var i:int=tx+ty*this.spaceX;
         if(this.regionLo[i]!=lo || this.regionHi[i]!=hi){
            this.regionLo[i]=lo;this.regionHi[i]=hi;this.regionStamp[i]=++this.regionClock;
         }
         this.regionRead[i]=this.fovVersion;
      }

      // The bitmap clear precedes the tile writers. Do not publish intermediate
      // zeros for overlapping tiles: those writers commit their complete result.
      private function clearRegionsOutside(next:Rectangle):void
      {
         var old:Rectangle=this.currentSightWritten;
         var x0:int=old==null?0:int((old.x-FOG_PAD)/FOG_SUB);
         var y0:int=old==null?0:int((old.y-FOG_PAD)/FOG_SUB);
         var x1:int=old==null?this.spaceX:int((old.right-FOG_PAD)/FOG_SUB);
         var y1:int=old==null?this.spaceY:int((old.bottom-FOG_PAD)/FOG_SUB);
         for(var y:int=y0;y<y1;y++)for(var x:int=x0;x<x1;x++)
            if(x<next.left || x>=next.right || y<next.top || y>=next.bottom)this.putRegion(x,y,0,0);
      }

      private function regionVersion(x0:int,y0:int,x1:int,y1:int):Number
      {
         var source:BitmapData=this.cfgMode=="current"?this.currentSight:this.fogCache;
         this.ensureRegions(source);
         if(this.cfgMode=="classic")this.classicLogicRegion(new Rectangle(x0,y0,x1-x0+1,y1-y0+1));
         var stamp:Number=0;
         for(var y:int=y0;y<=y1;y++)for(var x:int=x0;x<=x1;x++){
            var i:int=x+y*this.spaceX;
            // Current's writers already commit exact bits. Classic materializes
            // canonical pixels on demand, so read each requested tile once per
            // field generation, after the canonical generator has published it.
            if(this.regionRead[i]<0 || (this.cfgMode=="classic" && this.regionRead[i]!=this.fovVersion)){
               var data:Vector.<uint>=source.getVector(new Rectangle(FOG_PAD+x*FOG_SUB,FOG_PAD+y*FOG_SUB,FOG_SUB,FOG_SUB));
               var lo:uint=0,hi:uint=0;
               for(var b:int=0;b<64;b++)if(this.cfgMode=="current"?data[b]!=0:(data[b]>>>24)<MASK_LIT_A){
                  if(b<32)lo|=uint(1)<<b;else hi|=uint(1)<<(b-32);
               }
               this.putRegion(x,y,lo,hi);
            }
            if(this.regionStamp[i]>stamp)stamp=this.regionStamp[i];
         }
         return stamp;
      }

      private function regionMaskUnchanged(rec:Object,bb:Array,x0:int,y0:int,x1:int,y1:int):Boolean
      {
         if((this.cfgMode!="current" && this.cfgMode!="classic") ||
            (this.cfgMode=="current"?this.currentSight==null:this.fogCache==null))return false;
         var stamp:Number=this.regionVersion(x0,y0,x1,y1);
         var blur:BlurFilter=this.cfgMode=="classic"?this.maskBlurClassic:this.maskBlurCurrent;
         var same:Boolean=rec.regionReady===true && rec.regionToken===this.regionLo && rec.regionVersion===stamp
            && rec.regionX0===x0 && rec.regionY0===y0 && rec.regionX1===x1 && rec.regionY1===y1
            && rec.regionB0===bb[0] && rec.regionB1===bb[1] && rec.regionB2===bb[2] && rec.regionB3===bb[3]
            && rec.regionBlurX===blur.blurX && rec.regionBlurY===blur.blurY && rec.regionQuality===blur.quality;
         if(same)return true;
         rec.regionReady=false;rec.regionToken=this.regionLo;rec.regionVersion=stamp;
         rec.regionX0=x0;rec.regionY0=y0;rec.regionX1=x1;rec.regionY1=y1;
         rec.regionB0=bb[0];rec.regionB1=bb[1];rec.regionB2=bb[2];rec.regionB3=bb[3];
         rec.regionBlurX=blur.blurX;rec.regionBlurY=blur.blurY;rec.regionQuality=blur.quality;
         return false;
      }
