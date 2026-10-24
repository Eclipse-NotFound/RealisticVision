from pathlib import Path
MOD=Path(__file__).resolve().parents[2];p=MOD/'build/effect-load-v2-output/candidate/src/RealisticVisionMod.as'
s=p.read_text(encoding='utf-8')
s=s.replace('      private var worldCellEpoch:int = -1;\n      private var worldCellKinds:Object = {};\n','')
s=s.replace('         this.worldCellKinds={};this.worldCellEpoch=-1;\n','')
start=s.index('         if(this.worldCellEpoch!=this.fovVersion)')
end=s.index('         if(combined==2)',start)
s=s[:start]+'''         var x0:int=Math.max(0,bx0-MASK_PAD_X),y0:int=Math.max(0,by0-MASK_PAD_TOP);
         var x1:int=Math.min(this.spaceX-1,bx1+MASK_PAD_X),y1:int=Math.min(this.spaceY-1,by1+MASK_PAD_BOTTOM);
         var area:Rectangle=new Rectangle(FOG_PAD+x0*MASK_SUB,FOG_PAD+y0*MASK_SUB,(x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB);
         if(this.cfgMode=="current" && !this.currentSight.hitTest(this.fogPoint,1,area))return 1;
         // threshold returns the exact match count. One reusable scratch bitmap
         // lets the runtime classify a rectangle without per-tile AS loops,
         // filters, temporary vectors or per-region raster allocations.
         if(this.worldCellPixels==null || this.worldCellPixels.width<area.width || this.worldCellPixels.height<area.height){
            var width:int=this.worldCellPixels?Math.max(this.worldCellPixels.width,area.width):area.width;
            var height:int=this.worldCellPixels?Math.max(this.worldCellPixels.height,area.height):area.height;
            if(this.worldCellPixels)this.worldCellPixels.dispose();
            this.worldCellPixels=new BitmapData(width,height,true,0);
         }
         var matches:uint;
         if(this.cfgMode=="classic"){
            this.classicLogicRegion(new Rectangle(x0,y0,x1-x0+1,y1-y0+1));
            matches=this.worldCellPixels.threshold(this.fogCache,area,this.fogPoint,"<",uint(MASK_LIT_A)<<24,0xffffffff,0xff000000,false);
            if(matches==0)return 1;
         } else matches=this.worldCellPixels.threshold(this.currentSight,area,this.fogPoint,"==",0xff000000,0xffffffff,0xff000000,false);
         var combined:int=matches==area.width*area.height?2:3;
'''+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
print('native match-count classification ready')
