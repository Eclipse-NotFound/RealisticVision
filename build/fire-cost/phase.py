"""Candidate: retain bitmap origin; crop only at integer screen-pixel offsets."""
from pathlib import Path
import hashlib,json,shutil,sys
from instrument import once
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/fire-cost-output';target=OUT/'candidates'/('phase2' if '--both-edges' in sys.argv else 'phase')/'src'
assert not target.exists();shutil.copytree(OUT/'baseline/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text('utf8')
marker='         var clipChanged:Boolean='
new='''         // FIRE_PHASE: retain both the original bitmap origin and its screen
         // sampling phase. Only rational positive scales with an exact small
         // integer period are candidates; rotated/skewed/filter cases fall back.
         if(drawClip==null && this.cfgMode=="current" && !drawDark && screenMatrix.b==0 && screenMatrix.c==0
            && screenMatrix.a>0 && screenMatrix.d>0 && (screenMatrix.a!=1 || screenMatrix.d!=1)
            && !this.worldVisualHasFilters(visual)){
            var periodX:int=this.worldPixelPeriod(screenMatrix.a),periodY:int=this.worldPixelPeriod(screenMatrix.d);
            if(periodX>0 && periodY>0){
               var padX:int=Math.ceil(2/(screenMatrix.a*periodX))*periodX;
               var padY:int=Math.ceil(2/(screenMatrix.d*periodY))*periodY;
               var phaseLeft:Number=Math.max(drawX,drawX+Math.floor((bounds.left-drawX)/periodX)*periodX-padX);
               var phaseTop:Number=Math.max(drawY,drawY+Math.floor((bounds.top-drawY)/periodY)*periodY-padY);
               var phaseRight:Number=Math.min(drawX+BitmapData(raster.m2e).width*drawScale,drawX+Math.ceil((bounds.right-drawX)/periodX)*periodX+padX);
               var phaseBottom:Number=Math.min(drawY+BitmapData(raster.m2e).height*drawScale,drawY+Math.ceil((bounds.bottom-drawY)/periodY)*periodY+padY);
               drawClip=new Rectangle(phaseLeft,phaseTop,phaseRight-phaseLeft,phaseBottom-phaseTop);
               // FIRE_PHASE_HIT
            }
         }
'''+marker
if '--both-edges' in sys.argv:
 new=once(new,'drawX+Math.ceil((bounds.right-drawX)/periodX)*periodX+padX','drawX+BitmapData(raster.m2e).width*drawScale-Math.floor((drawX+BitmapData(raster.m2e).width*drawScale-bounds.right)/periodX)*periodX+padX')
 new=once(new,'drawY+Math.ceil((bounds.bottom-drawY)/periodY)*periodY+padY','drawY+BitmapData(raster.m2e).height*drawScale-Math.floor((drawY+BitmapData(raster.m2e).height*drawScale-bounds.bottom)/periodY)*periodY+padY')
s=once(s,marker,new)
s=once(s,'      private function worldVisualHasFilters(','''      private function worldPixelPeriod(scale:Number):int
      {
         for(var period:int=1;period<=12;period++)
            if(scale*period>=1 && Math.abs(scale*period-Math.round(scale*period))<0.000000001)return period;
         return 0;
      }

      private function worldVisualHasFilters(''')
p.write_text(s,'utf8',newline='\n')
(target.parent/'sources.json').write_text(json.dumps({q.relative_to(target).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in target.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
print('Created independent screen-phase crop candidate')
