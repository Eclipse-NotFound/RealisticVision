"""Cache exact low-resolution classic samples and track solid topology separately."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('private var classicJoins:Array = [];','''private var classicJoins:Array = [];
      private var classicCells:Object;
      private var classicCellDim:Number=NaN;
      private var classicCellDark:Boolean;''')
 s=s.replace('this.classicJoins=[];','this.classicJoins=[];this.classicCells=null;')
 start=s.index('      private function applyVisionClassic(');end=s.index('      private function joinClassicWalls(',start)
 part=s[start:end]
 part=part.replace('for(var mi:int=0;mi<this.spaceX*this.spaceY;mi++) this.advanceMemory(loc,mi);','for(var mi:int=0;mi<this.spaceX*this.spaceY;mi++) this.advanceMemory(loc,mi);\n         this.prepareClassicCells(loc);')
 part=part.replace('            var a:int=this.tileFogAlpha(loc,tx,ty);','            if(!this.classicCells.dirty[i])continue;\n            var a:int=this.classicCells.alpha[i];')
 part=part.replace('if(this.refreshWallField(loc,needFov,false))changed=logicalChanged=true;','if(this.refreshWallField(loc,this.wallGeometryDirty,false))changed=logicalChanged=true;\n         this.wallGeometryDirty=false;')
 s=s[:start]+part+s[end:]
 return s.replace('      private function classicDifference(','''      /** Each native alpha, memory value and solid cell is still read this pass.
       * A changed cell invalidates its full 3x3 dependency neighbourhood. */
      private function prepareClassicCells(loc:Location):void
      {
         var n:int=this.spaceX*this.spaceY;
         var fresh:Boolean=this.classicCells==null || this.classicCells.alpha.length!=n;
         if(fresh){
            this.classicCells={alpha:new Vector.<int>(n,true),memory:new Vector.<Number>(n,true),
               known:new Vector.<Boolean>(n,true),solid:new Vector.<Boolean>(n,true),dirty:new Vector.<Boolean>(n,true)};
            this.wallGeometryDirty=true;
         }
         var cells:Object=this.classicCells;
         var all:Boolean=fresh || this.classicCellDim!=this.cfgDim || this.classicCellDark!=loc.retDark;
         this.classicCellDim=this.cfgDim;this.classicCellDark=loc.retDark;
         for(var i:int=0;i<n;i++)cells.dirty[i]=all;
         for(var y:int=0;y<this.spaceY;y++)for(var x:int=0;x<this.spaceX;x++){
            i=x+y*this.spaceX;
            var alpha:int=this.tileFogAlpha(loc,x,y),memory:Number=this.memCur[i];
            var known:Boolean=this.memoryExplored(i),solid:Boolean=loc.getTile(x,y).opac>=1;
            if(cells.solid[i]!=solid)this.wallGeometryDirty=true;
            if(!all && (cells.alpha[i]!=alpha || cells.memory[i]!=memory || cells.known[i]!=known || cells.solid[i]!=solid)){
               for(var yy:int=Math.max(0,y-1);yy<=Math.min(this.spaceY-1,y+1);yy++)
                  for(var xx:int=Math.max(0,x-1);xx<=Math.min(this.spaceX-1,x+1);xx++)cells.dirty[xx+yy*this.spaceX]=true;
            }
            cells.alpha[i]=alpha;cells.memory[i]=memory;cells.known[i]=known;cells.solid[i]=solid;
         }
      }

      private function classicDifference(''',1)
if __name__=='__main__':
 dest=OUT/'candidate-03/src';assert not dest.exists();shutil.copytree(OUT/'candidate-02/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
