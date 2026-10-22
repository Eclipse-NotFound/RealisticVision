"""Remember only the local seen-subcell classification; every local write invalidates it."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('private var explorationBits:Array;', 'private var explorationBits:Array;\n      private var memoryTileState:Array;')
 s=s.replace('this.explorationBits = null;', 'this.explorationBits = null;this.memoryTileState=null;')
 s=s.replace('this.explorationBits = new Array(n);', 'this.explorationBits = new Array(n);this.memoryTileState=new Array(n);')
 s=s.replace('this.explorationBits[tx + ty * this.spaceX] = null;', 'this.explorationBits[tx + ty * this.spaceX] = null;this.memoryTileState[tx+ty*this.spaceX]=null;')
 start=s.index('      private function fillMemoryTile(');end=s.index('      /** classic',start)
 part=s[start:end]
 part=part.replace('         var idxBase:int', '''         // Shared exploration is merged independently. Keep its existing scan;
         // local-only tiles reuse a classification until a seenSub write.
         var tileIndex:int=tx+ty*this.spaceX;
         var cached:*=this.sharedSeen==null && this.memoryTileState!=null?this.memoryTileState[tileIndex]:null;
         if(cached===0 || cached===2){
            this.fogCellRect.x=FOG_PAD+tx*FOG_SUB;this.fogCellRect.y=FOG_PAD+ty*FOG_SUB;
            this.fogCache.fillRect(this.fogCellRect,cached===0?0xFF000000:uint(dimA)<<24);return;
         }
         var idxBase:int''',1)
 part=part.replace('         for(sx = 0; sx < FOG_SUB; sx++)','         if(cached!==1) for(sx = 0; sx < FOG_SUB; sx++)',1)
 part=part.replace('         this.fogCellRect.x = FOG_PAD + tx * FOG_SUB;', '''         if(cached===1){seenAll=false;seenAny=true;}
         else if(this.sharedSeen==null && this.memoryTileState!=null)this.memoryTileState[tileIndex]=seenAll?2:(seenAny?1:0);
         this.fogCellRect.x = FOG_PAD + tx * FOG_SUB;''',1)
 return s[:start]+part+s[end:]
if __name__=='__main__':
 dest=OUT/'candidate-12/src';assert not dest.exists();shutil.copytree(OUT/'candidate-11/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
