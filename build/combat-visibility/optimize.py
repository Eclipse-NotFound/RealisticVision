from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-visibility-output'
def transform(s):
 s=s.replace('      private var weaponPass:int = 0;', '      private var weaponPass:int = 0;\n      private var maskAlphaMap:Array;\n      private var maskZeroMap:Array;')
 start=s.index('            var eligible:Vector.<uint> = bd.getVector(bd.rect);');end=s.index('\n         }',start)
 s=s[:start]+'            this.finishCurrentMask(bd,bdb);'+s[end:]
 at=s.index('      private function clearMask(')
 s=s[:at]+'''      /** Same alpha arithmetic as the pixel loop, without two temporary vectors. */
      private function finishCurrentMask(eligible:BitmapData, soft:BitmapData):void
      {
         if(this.maskAlphaMap == null)
         {
            this.maskAlphaMap=[];this.maskZeroMap=[];
            for(var i:int=0;i<256;i++)
            {
               var alpha:int=Math.max(0,2*i-255);
               this.maskAlphaMap[i]=alpha==0?0:uint((alpha<<24)|0xFFFFFF);
               this.maskZeroMap[i]=0;
            }
         }
         soft.paletteMap(soft,soft.rect,this.fogPoint,this.maskZeroMap,this.maskZeroMap,this.maskZeroMap,this.maskAlphaMap);
         soft.threshold(eligible,eligible.rect,this.fogPoint,"==",0,0,0xFFFFFFFF,false);
      }

'''+s[at:]
 return s

if __name__=='__main__':
 src=OUT/'candidate/src';shutil.copytree(src,OUT/'weapon-only/src')
 p=src/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
