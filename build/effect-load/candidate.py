from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/effect-load-output'
s=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
s=s.replace('      private var worldPass:int = 0;','''      private var worldPass:int = 0;
      private var worldCellEpoch:int = -1;
      private var worldCellKinds:Object = {};
      private var worldCellPixels:BitmapData;
      private var worldDark:Object = {fullyDark:true,maskRevision:0};''')
marker='         var key:String=x0+","+y0+","+x1+","+y1;'
assert s.count(marker)==1
s=s.replace(marker,'''         var uniform:int=this.worldUniform(x0,y0,x1,y1);
         if(uniform==2){if(record!=null)this.releaseWorldVisual(visual,record);return;}
'''+marker)
s=s.replace('var raster:Object=this.worldMasks[key];\n         if(raster==null)', 'var raster:Object=uniform==1?this.worldDark:this.worldMasks[key];\n         if(raster==null)')
s=s.replace('         this.refreshMask(raster,[x0,y0,x1,y1]);','         if(uniform!=1)this.refreshMask(raster,[x0,y0,x1,y1]);')
s=s.replace('if(raster.coverageFov!==this.fovVersion)','if(uniform!=1 && raster.coverageFov!==this.fovVersion)')
s=s.replace('         this.worldMasks={};this.worldPass=0;','''         this.worldMasks={};this.worldPass=0;
         this.worldCellKinds={};this.worldCellEpoch=-1;
         if(this.worldCellPixels){this.worldCellPixels.dispose();this.worldCellPixels=null;}''')
methods='''      /** Uniform raw support needs no filtered per-visual bitmap. Mixed support
       * always uses the original path; never approximate the moving boundary. */
      private function worldUniform(bx0:int,by0:int,bx1:int,by1:int):int
      {
         if((this.cfgMode=="current" && this.currentSight==null) || (this.cfgMode=="classic" && this.fogCache==null))return 3;
         if(this.worldCellEpoch!=this.fovVersion){this.worldCellEpoch=this.fovVersion;this.worldCellKinds={};}
         if(this.worldCellPixels==null)this.worldCellPixels=new BitmapData(MASK_SUB,MASK_SUB,true,0);
         var x0:int=Math.max(0,bx0-MASK_PAD_X),y0:int=Math.max(0,by0-MASK_PAD_TOP);
         var x1:int=Math.min(this.spaceX-1,bx1+MASK_PAD_X),y1:int=Math.min(this.spaceY-1,by1+MASK_PAD_BOTTOM);
         var combined:int=0;
         for(var y:int=y0;y<=y1;y++)for(var x:int=x0;x<=x1;x++)
         {
            var index:int=x+y*this.spaceX,kind:int=int(this.worldCellKinds[index]);
            if(kind==0)
            {
               var source:Rectangle=new Rectangle(FOG_PAD+x*MASK_SUB,FOG_PAD+y*MASK_SUB,MASK_SUB,MASK_SUB);
               if(this.cfgMode=="current")this.worldCellPixels.copyPixels(this.currentSight,source,this.fogPoint);
               else {
                  this.classicLogicRegion(new Rectangle(x,y,1,1));
                  this.worldCellPixels.fillRect(this.worldCellPixels.rect,0);
                  this.worldCellPixels.threshold(this.fogCache,source,this.fogPoint,"<",uint(MASK_LIT_A)<<24,0xffffffff,0xff000000,false);
               }
               kind=this.worldCellPixels.getColorBoundsRect(0xff000000,0,false).isEmpty()?1:
                  this.worldCellPixels.getColorBoundsRect(0xff000000,0xff000000,false).isEmpty()?2:3;
               this.worldCellKinds[index]=kind;
            }
            if(kind==3 || (combined!=0 && combined!=kind))return 3;
            combined=kind;
         }
         if(combined==2){
            var blur:BlurFilter=this.cfgMode=="classic"?this.maskBlurClassic:this.maskBlurCurrent;
            // Retain the original filter if room clipping or a wide setting
            // can bring a transparent bitmap border into the visual's bounds.
            if(bx0-x0<MASK_PAD_X || by0-y0<MASK_PAD_TOP || x1-bx1<MASK_PAD_X || y1-by1<MASK_PAD_BOTTOM
               || blur.blurX*blur.quality/2+2>MASK_PAD_X*MASK_SUB
               || blur.blurY*blur.quality/2+2>MASK_PAD_BOTTOM*MASK_SUB)return 3;
         }
         return combined;
      }

'''
s=s.replace('      private function applyWorldVisual(visual:DisplayObject):void',methods+'      private function applyWorldVisual(visual:DisplayObject):void')
(OUT/'candidate/src/RealisticVisionMod.as').write_text(s,encoding='utf-8',newline='\n')
