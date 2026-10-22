"""Keep full native raster extent during zoom; retain viewport work at 1:1."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('         // 交替渲染帧或 FOV 变化帧更新；实际频率取决于宿主帧率。','         var classicZoom:Number=(this.spaceX>48 || this.spaceY>25)?Object(w).cam.scaleV:1;\n         // 交替渲染帧或 FOV 变化帧更新；实际频率取决于宿主帧率。')
 s=s.replace('private var classicRenderedTiles:Rectangle;', 'private var classicRenderedTiles:Rectangle;\n      private var classicRasterScale:Number=NaN;')
 s=s.replace('this.classicRenderedTiles=null;', 'this.classicRenderedTiles=null;this.classicRasterScale=NaN;')
 s=s.replace('if(this.classicRenderedTiles!=null && this.classicRaw!=null){','if(this.classicRaw!=null && (this.classicRenderedTiles!=null || this.classicRasterScale!=classicZoom)){')
 s=s.replace('if(!this.classicRenderedTiles.containsRect(needed))this.paintClassicDisplay(loc,exposed,logicOnly,true);','if(this.classicRasterScale!=classicZoom || this.classicRenderedTiles==null || !this.classicRenderedTiles.containsRect(needed))this.paintClassicDisplay(loc,classicZoom==1?exposed:null,logicOnly,this.cfgDim!=0.35 || this.spaceX>48 || this.spaceY>25);')
 s=s.replace('var large:Boolean=this.spaceX>48 || this.spaceY>25;', 'var bigScene:Boolean=this.spaceX>48 || this.spaceY>25;\n         var large:Boolean=bigScene && classicZoom==1;')
 s=s.replace('this.cfgDim != 0.35 || large;', 'this.cfgDim != 0.35 || bigScene;')
 s=s.replace('this.classicRenderedTiles=paintTiles==null?null:paintTiles.clone();', 'this.classicRenderedTiles=paintTiles==null?null:paintTiles.clone();this.classicRasterScale=(this.spaceX>48 || this.spaceY>25)?Object(World.w).cam.scaleV:1;')
 return s
if __name__=='__main__':
 dest=OUT/'candidate-14/src';assert not dest.exists();shutil.copytree(OUT/'candidate-12/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
