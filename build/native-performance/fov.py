"""Exact radius bounds: zero the old field, then visit only possible contributors."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 start=s.index('      private function computeFov(');end=s.index('   private function castRay(',start)
 part=s[start:end]
 part=part.replace('            var r2:Number = r * r;','''            var r2:Number = r * r;
            var fx0:int=Math.max(0,Math.floor((ex-r)/Tile.tileX-0.5));
            var fy0:int=Math.max(0,Math.floor((ey-r)/Tile.tileY-0.5));
            var fx1:int=Math.min(this.spaceX,Math.ceil((ex+r)/Tile.tileX+0.5));
            var fy1:int=Math.min(this.spaceY,Math.ceil((ey+r)/Tile.tileY+0.5));
            for(var clearIndex:int=0;clearIndex<this.spaceX*this.spaceY;clearIndex++)this.fov[clearIndex]=FOV_NONE;''')
 part=part.replace('for(tx = 0; tx < this.spaceX; tx++)','for(tx = fx0; tx < fx1; tx++)',1)
 part=part.replace('for(ty = 0; ty < this.spaceY; ty++)','for(ty = fy0; ty < fy1; ty++)',1)
 marker='            // 墙可见性：'
 idx=part.index(marker)
 part=part[:idx]+'''            // Only an immediate neighbour of a visible non-wall can be lit.
            fx0=Math.max(0,fx0-1);fy0=Math.max(0,fy0-1);
            fx1=Math.min(this.spaceX,fx1+1);fy1=Math.min(this.spaceY,fy1+1);
'''+part[idx:]
 part=part.replace('for(tx = 0; tx < this.spaceX; tx++)','for(tx = fx0; tx < fx1; tx++)',1)
 part=part.replace('for(ty = 0; ty < this.spaceY; ty++)','for(ty = fy0; ty < fy1; ty++)',1)
 return s[:start]+part+s[end:]
if __name__=='__main__':
 dest=OUT/'candidate-10/src';assert not dest.exists();shutil.copytree(OUT/'candidate-09/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
