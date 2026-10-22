"""D37 alternative: paint only the camera plus support, keep sight lazy and exact."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
BASE=MOD/'build/combat-visibility-output/production/src'
def transform(s):
 start=s.index('      private function applyVisionClassic(');end=s.index('      private function joinClassicWalls(',start)
 part=s[start:end]
 part=part.replace('var separateLogic:Boolean = this.cfgDim != 0.35;','''var large:Boolean=this.spaceX>48 || this.spaceY>25;
         var paintTiles:Rectangle=large?this.scenePaintBounds():null;
         var paint:Rectangle=paintTiles==null?this.fogRect:new Rectangle(FOG_PAD+paintTiles.x*FOG_SUB,FOG_PAD+paintTiles.y*FOG_SUB,paintTiles.width*FOG_SUB,paintTiles.height*FOG_SUB);
         if(large){paint.inflate(16,16);paint=paint.intersection(this.fogRect);}
         var paintPoint:Point=new Point(paint.x,paint.y);
         var separateLogic:Boolean = this.cfgDim != 0.35 || large;''')
 a=part.index('         if(changed)\n');body=part[a:]
 body=body.replace('this.fogRect','paint').replace('this.fogPoint','paintPoint')
 body=body.replace('this.classicLightMatrix,null,null,null,true','this.classicLightMatrix,null,null,paint,true')
 body=body.replace('this.classicMemoryMatrix,null,null,null,true','this.classicMemoryMatrix,null,null,paint,true')
 body=body.replace('this.joinClassicWalls(loc);','this.joinClassicWalls(loc,paintTiles);')
 # The logical field keeps its previous whole-room allocation; queries fill it.
 body=body.replace('if(separateLogic) this.fogCache.copyPixels(this.classicLogicCache,paint,paintPoint);','if(separateLogic) this.fogCache.copyPixels(this.classicLogicCache,this.fogRect,this.fogPoint);')
 part=part[:a]+body;s=s[:start]+part+s[end:]
 start=s.index('      private function joinClassicWalls(');end=s.index('         var x0:int=bounds',start)
 part=s[start:end]
 part=part.replace('         if(!prepared)','''         var paint:Rectangle=bounds==null?this.fogRect:new Rectangle(FOG_PAD+bounds.x*FOG_SUB,FOG_PAD+bounds.y*FOG_SUB,bounds.width*FOG_SUB,bounds.height*FOG_SUB);
         if(bounds!=null){paint.inflate(16,16);paint=paint.intersection(this.fogRect);}
         var paintPoint:Point=new Point(paint.x,paint.y);
         if(!prepared)''',1)
 part=part.replace('this.classicWallShade.fillRect(this.fogRect','this.classicWallShade.fillRect(paint')
 part=part.replace('this.classicVisibilityField,this.fogRect,this.fogPoint','this.classicVisibilityField,paint,paintPoint')
 part=part.replace('this.fogCache.colorTransform(this.fogRect','this.fogCache.colorTransform(paint')
 part=part.replace('this.fogCache,this.fogRect,this.fogPoint','this.fogCache,paint,paintPoint')
 part=part.replace('this.fogCache.fillRect(this.fogRect','this.fogCache.fillRect(paint')
 part=part.replace('this.classicLightMatrix,null,null,null,true','this.classicLightMatrix,null,null,paint,true')
 part=part.replace('this.classicVisibilityField,null,null,"multiply"','this.classicVisibilityField,null,null,"multiply",paint')
 part=part.replace('         for each(var ci:int in this.wallCorners)\n         {','''         for each(var ci:int in this.wallCorners)
         {
            if(bounds!=null && (ci%this.spaceX<bounds.x || ci%this.spaceX>bounds.right || int(ci/this.spaceX)<bounds.y || int(ci/this.spaceX)>bounds.bottom))continue;''')
 s=s[:start]+part+s[end:]
 s=s.replace('this.cfgMode != "classic" || this.cfgDim == 0.35 || this.classicLogicTiles == null','this.cfgMode != "classic" || this.classicLogicTiles == null')
 # Native wall support is at most 32 world pixels. Keep 2 tiles outside the
 # camera, plus the existing 2-tile moving gutter, rather than 4+2 tiles.
 start=s.index('      private function updateWallSurface(');end=s.index('      /** Read light',start)
 part=s[start:end].replace('         var view:Rectangle = this.scenePaintBounds();','''         var view:Rectangle = this.scenePaintBounds();
         if(this.spaceX>48 || this.spaceY>25){
            var camera:*=Object(w).cam;var scale:Number=camera.scaleV>0?camera.scaleV:1;
            var vx:int=Math.max(0,Math.floor(-camera.vx/scale/Tile.tileX)-2);
            var vy:int=Math.max(0,Math.floor(-camera.vy/scale/Tile.tileY)-2);
            var vr:int=Math.min(this.spaceX,Math.ceil((-camera.vx+camera.screenX)/scale/Tile.tileX)+2);
            var vb:int=Math.min(this.spaceY,Math.ceil((-camera.vy+camera.screenY)/scale/Tile.tileY)+2);
            if(!this.cfgWallBright)view=new Rectangle(vx,vy,vr-vx,vb-vy);
         }''')
 s=s[:start]+part+s[end:]
 return s
if __name__=='__main__':
 dest=OUT/'candidate-06/src';assert not dest.exists();shutil.copytree(BASE,dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
