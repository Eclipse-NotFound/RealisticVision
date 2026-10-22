"""Replace full raster comparisons by exact low-sample dependency invalidation."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('private var classicCells:Object;','private var classicCells:Object;\n      private var classicInputRegion:Rectangle;\n      private var classicGeneration:uint=0;')
 start=s.index('      private function prepareClassicCells(');end=s.index('      private function classicDifference(',start)
 part=s[start:end]
 part=part.replace('         var cells:Object=this.classicCells;','''         var cells:Object=this.classicCells;
         var alphas:Vector.<int>=cells.alpha,memories:Vector.<Number>=cells.memory;
         var knowns:Vector.<Boolean>=cells.known,solids:Vector.<Boolean>=cells.solid,dirtyCells:Vector.<Boolean>=cells.dirty;''')
 for a,b in [('cells.alpha[','alphas['),('cells.memory[','memories['),('cells.known[','knowns['),('cells.solid[','solids['),('cells.dirty[','dirtyCells[')]:part=part.replace(a,b)
 at=part.rfind('      }')
 part=part[:at]+'''         var x0:int=this.spaceX,y0:int=this.spaceY,x1:int=0,y1:int=0;
         for(y=0;y<this.spaceY;y++)for(x=0;x<this.spaceX;x++)if(dirtyCells[x+y*this.spaceX]){
            if(x<x0)x0=x;if(y<y0)y0=y;if(x+1>x1)x1=x+1;if(y+1>y1)y1=y+1;
         }
         this.classicInputRegion=x1>x0?new Rectangle(FOG_PAD+x0*FOG_SUB,FOG_PAD+y0*FOG_SUB,(x1-x0)*FOG_SUB,(y1-y0)*FOG_SUB):new Rectangle();
'''+part[at:]
 s=s[:start]+part+s[end:]
 start=s.index('      private function applyVisionClassic(');end=s.index('      private function joinClassicWalls(',start)
 part=s[start:end].replace('         if(changed)\n         {','         if(changed)\n         {\n            this.classicGeneration++;')
 s=s[:start]+part+s[end:]
 start=s.index('      private function prepareClassicJoin(');end=s.index('      private function disposeClassicJoin(',start)
 part=s[start:end].replace('item.raw.width!=this.fogRaw.width || item.raw.height!=this.fogRaw.height','item.output.width!=this.fogRaw.width || item.output.height!=this.fogRaw.height')
 part=part.replace('item={raw:this.fogRaw.clone(),visibility:this.classicVisibilityField.clone(),wall:this.wallRaw.clone(),','item={generation:this.classicGeneration,soft:this.cfgSoftClassic,wall:this.wallRaw.clone(),')
 a=part.index('         var dirty:Rectangle=');b=part.index('         if(!change.isEmpty())\n         {',a)
 part=part[:a]+'''         var dirty:Rectangle=this.classicInputRegion==null?this.fogRect.clone():this.classicInputRegion.clone();
         if(item.generation!=this.classicGeneration-1 || (slot==1 && item.soft!=this.cfgSoftClassic))dirty=this.fogRect.clone();
         item.generation=this.classicGeneration;item.soft=this.cfgSoftClassic;
         // Low samples influence bilinear output and up to q2/8px softening.
         // Additional support is conservative; no changed sample is discarded.
         if(slot==1 && !dirty.isEmpty())dirty.inflate(16,16);
         var change:Rectangle=this.classicDifference(this.wallRaw,item.wall);
'''+part[b:]
 part=part.replace('         item.raw.copyPixels(this.fogRaw,this.fogRect,this.fogPoint);\n         item.visibility.copyPixels(this.classicVisibilityField,this.fogRect,this.fogPoint);\n','')
 s=s[:start]+part+s[end:]
 s=s.replace('item.raw.dispose();item.visibility.dispose();item.wall.dispose();','item.wall.dispose();')
 return s
if __name__=='__main__':
 dest=OUT/'candidate-04/src';assert not dest.exists();shutil.copytree(OUT/'candidate-03/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
