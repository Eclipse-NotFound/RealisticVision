"""Reuse exact foreground copy rectangles, without reusing terrain pixel content."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def surface(s):
 s=s.replace('private var contourUpdates:int = 0;','private var contourUpdates:int = 0;\n      private var contourSourceLayout:Array;\n      private var contourSourceVersion:int=0;')
 s=s.replace('contourDirty=contourLayoutDirty=true;mode=-1;','contourDirty=contourLayoutDirty=true;mode=-1;contourSourceLayout=null;contourSourceVersion++;')
 s=s.replace('         var sources:Array=foregroundSources(front);\n         for each(patch in contourPieces){','''         var sources:Array=foregroundSources(front);
         var sameSources:Boolean=sources!=null && contourSourceLayout!=null && sources.length==contourSourceLayout.length;
         if(sameSources)for(var si:int=0;si<sources.length;si++){
            var oldSource:Object=contourSourceLayout[si],newSource:Object=sources[si];
            if(oldSource.data!==newSource.data || oldSource.x!=newSource.x || oldSource.y!=newSource.y || !Rectangle(oldSource.rect).equals(newSource.rect)){sameSources=false;break;}
         }
         if(!sameSources){contourSourceVersion++;contourSourceLayout=sources;}
         for each(patch in contourPieces){''')
 a=s.index('         var contourScratch:BitmapData=patch.scratch;');b=s.index('         var delta:Object=contourScratch.compare',a)
 s=s[:a]+'''         var contourScratch:BitmapData=patch.scratch;
         if(sources!=null){
            if(patch.copyVersion!==contourSourceVersion){
               var plan:Array=[];
               for each(var source:Object in sources){
                  var region:Rectangle=patch.rect.intersection(source.rect);if(region.isEmpty())continue;
                  var dest:Point=new Point(region.x-patch.rect.x,region.y-patch.rect.y);region.offset(-source.x,-source.y);
                  plan.push({data:source.data,region:region,dest:dest});
               }
               patch.copyPlan=plan;patch.copyVersion=contourSourceVersion;
            }
            plan=patch.copyPlan;
            var full:Boolean=plan.length==1 && plan[0].dest.x==0 && plan[0].dest.y==0 && plan[0].region.width==contourScratch.width && plan[0].region.height==contourScratch.height;
            if(!full)contourScratch.fillRect(contourScratch.rect,0);
            for each(var command:Object in plan)contourScratch.copyPixels(command.data,command.region,command.dest,null,null,!full);
         }else{
            contourScratch.fillRect(contourScratch.rect,0);
            var m:Matrix=front.transform.matrix;m.tx-=left*CELL+patch.rect.x;m.ty-=top*CELL+patch.rect.y;
            contourScratch.draw(front,m,front.transform.colorTransform,null,null,true);
         }
'''+s[b:]
 return s
def cells(s):
 # Keep the low-sample dependency scan from the verified C04; omit its separate
 # whole-image join cache because the viewport path already bounds that work.
 ref=(OUT/'candidate-04/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
 methods=ref[ref.index('      private function prepareClassicCells('):ref.index('      private function classicDifference(')]
 s=s.replace('private var classicCornerDeltas:Array = [];','''private var classicCornerDeltas:Array = [];
      private var classicCells:Object;
      private var classicCellDim:Number=NaN;
      private var classicCellDark:Boolean;
      private var classicInputRegion:Rectangle;''')
 s=s.replace('this.restoreWeaponVisuals();','this.classicCells=null;\n         this.restoreWeaponVisuals();')
 start=s.index('      private function applyVisionClassic(');end=s.index('      private function paintClassicDisplay(',start)
 part=s[start:end].replace('for(var mi:int=0;mi<this.spaceX*this.spaceY;mi++) this.advanceMemory(loc,mi);','for(var mi:int=0;mi<this.spaceX*this.spaceY;mi++) this.advanceMemory(loc,mi);\n         this.prepareClassicCells(loc);')
 part=part.replace('            var a:int=this.tileFogAlpha(loc,tx,ty);','            if(!this.classicCells.dirty[i])continue;\n            var a:int=this.classicCells.alpha[i];')
 part=part.replace('if(this.refreshWallField(loc,needFov,false))changed=logicalChanged=true;','if(this.refreshWallField(loc,this.wallGeometryDirty,false))changed=logicalChanged=true;\n         this.wallGeometryDirty=false;')
 s=s[:start]+part+s[end:]
 return s.replace('      private function paintClassicDisplay(',methods+'      private function paintClassicDisplay(',1)
if __name__=='__main__':
 dest=OUT/'candidate-09/src';assert not dest.exists();shutil.copytree(OUT/'candidate-07/src',dest)
 p=dest/'RVWallSurface.as';p.write_text(surface(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
 p=dest/'RealisticVisionMod.as';p.write_text(cells(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
