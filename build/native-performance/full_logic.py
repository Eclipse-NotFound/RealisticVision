"""Full default-brightness rendering already provides the canonical field."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('         if(classicZoom!=1)this.classicFullRaster=true;', '''         if(classicZoom!=1)this.classicFullRaster=true;
         var separateLogic:Boolean=this.cfgDim!=0.35 || (!this.classicFullRaster && (this.spaceX>48 || this.spaceY>25));
         if(!separateLogic && this.classicLogicTiles!=null)this.releaseClassicLogic();''')
 s=s.replace('logicOnly,this.cfgDim!=0.35 || this.spaceX>48 || this.spaceY>25);','logicOnly,separateLogic);')
 s=s.replace('         var separateLogic:Boolean = this.cfgDim != 0.35 || bigScene;\n','')
 s=s.replace('      private var classicInputRegion:Rectangle;\n','')
 a=s.index('         var x0:int=this.spaceX,y0:int=this.spaceY,x1:int=0,y1:int=0;',s.index('      private function prepareClassicCells('))
 b=s.index('      private function paintClassicDisplay(',a)
 s=s[:a]+'      }\n\n'+s[b:]
 return s
if __name__=='__main__':
 dest=OUT/'candidate-17/src';assert not dest.exists();shutil.copytree(OUT/'candidate-16/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
