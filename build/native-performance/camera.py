"""Repaint newly exposed camera pixels from the last samples without advancing logic."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('private var classicCornerDeltas:Array = [];','private var classicCornerDeltas:Array = [];\n      private var classicRenderedTiles:Rectangle;')
 s=s.replace('this.restoreWeaponVisuals();','this.classicRenderedTiles=null;\n         this.restoreWeaponVisuals();')
 start=s.index('      private function applyVisionClassic(');end=s.index('      private function joinClassicWalls(',start)
 part=s[start:end]
 a=part.index('         if(changed)\n         {');b=part.index('            // 在白底',a);z=part.index('            this.fovVersion++;',b)
 body=part[b:z]
 part=part[:a]+'''         if(changed){this.paintClassicDisplay(loc,paintTiles,logicOnly,separateLogic);this.fovVersion++;}
      }

      /** Raster-only refresh: camera moves never advance the last sampled light,
       * exploration, memory fade or logical sight. */
      private function paintClassicDisplay(loc:Location,paintTiles:Rectangle,logicOnly:Boolean,separateLogic:Boolean):void
      {
         var paint:Rectangle=paintTiles==null?this.fogRect:new Rectangle(FOG_PAD+paintTiles.x*FOG_SUB,FOG_PAD+paintTiles.y*FOG_SUB,paintTiles.width*FOG_SUB,paintTiles.height*FOG_SUB);
         if(paintTiles!=null){paint.inflate(16,16);paint=paint.intersection(this.fogRect);}
         var paintPoint:Point=new Point(paint.x,paint.y);
'''+body+'''         this.classicRenderedTiles=paintTiles==null?null:paintTiles.clone();
      }

      /** 墙保留原版基底，仅叠加中心遮挡；地板在墙外一格内接到同一边界值。 */
'''
 part=part.replace('''            if(this.cfgAutoTest) this.atClsS++;
            return;''','''            if(this.cfgAutoTest) this.atClsS++;
            if(this.classicRenderedTiles!=null && this.classicRaw!=null){
               var exposed:Rectangle=this.scenePaintBounds(),needed:Rectangle=exposed.clone();
               needed.inflate(-2,-2);
               if(!this.classicRenderedTiles.containsRect(needed))this.paintClassicDisplay(loc,exposed,logicOnly,true);
            }
            return;''')
 # The main routine only needs tile bounds; paint rectangles live in the renderer.
 part=part.replace('''         var paint:Rectangle=paintTiles==null?this.fogRect:new Rectangle(FOG_PAD+paintTiles.x*FOG_SUB,FOG_PAD+paintTiles.y*FOG_SUB,paintTiles.width*FOG_SUB,paintTiles.height*FOG_SUB);
         if(large){paint.inflate(16,16);paint=paint.intersection(this.fogRect);}
         var paintPoint:Point=new Point(paint.x,paint.y);
''','',1)
 return s[:start]+part+s[end:]
if __name__=='__main__':
 dest=OUT/'candidate-07/src';assert not dest.exists();shutil.copytree(OUT/'candidate-06/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
