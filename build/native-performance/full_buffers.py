"""Keep native raster buffer extents; restrict only costly wall/floor correction loops."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 a=s.index('      private function paintClassicDisplay(');b=s.index('         var x0:int=bounds',a)
 part=s[a:b]
 start='var paint:Rectangle=paintTiles==null?this.fogRect:new Rectangle(FOG_PAD+paintTiles.x*FOG_SUB,FOG_PAD+paintTiles.y*FOG_SUB,paintTiles.width*FOG_SUB,paintTiles.height*FOG_SUB);\n         if(paintTiles!=null){paint.inflate(16,16);paint=paint.intersection(this.fogRect);}'
 assert start in part;part=part.replace(start,'var paint:Rectangle=this.fogRect;')
 start='var paint:Rectangle=bounds==null?this.fogRect:new Rectangle(FOG_PAD+bounds.x*FOG_SUB,FOG_PAD+bounds.y*FOG_SUB,bounds.width*FOG_SUB,bounds.height*FOG_SUB);\n         if(bounds!=null){paint.inflate(16,16);paint=paint.intersection(this.fogRect);}'
 assert start in part;part=part.replace(start,'var paint:Rectangle=this.fogRect;')
 s=s[:a]+part+s[b:]
 s=s.replace('      private var classicInputRegion:Rectangle;\n','')
 a=s.index('         var x0:int=this.spaceX,y0:int=this.spaceY,x1:int=0,y1:int=0;',s.index('      private function prepareClassicCells('))
 b=s.index('      private function paintClassicDisplay(',a);s=s[:a]+'      }\n\n'+s[b:]
 return s
if __name__=='__main__':
 dest=OUT/'candidate-18/src';assert not dest.exists();shutil.copytree(OUT/'candidate-12/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
