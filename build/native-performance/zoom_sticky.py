from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/native-performance-output'
def transform(s):
 s=s.replace('private var classicRasterScale:Number=NaN;', 'private var classicRasterScale:Number=NaN;\n      private var classicFullRaster:Boolean=false;')
 s=s.replace('this.classicRasterScale=NaN;', 'this.classicRasterScale=NaN;this.classicFullRaster=false;')
 s=s.replace('         // 交替渲染帧或 FOV 变化帧更新；实际频率取决于宿主帧率。', '         if(classicZoom!=1)this.classicFullRaster=true;\n         // 交替渲染帧或 FOV 变化帧更新；实际频率取决于宿主帧率。')
 s=s.replace('classicZoom==1?exposed:null', '!this.classicFullRaster?exposed:null')
 s=s.replace('bigScene && classicZoom==1', 'bigScene && !this.classicFullRaster')
 return s
if __name__=='__main__':
 dest=OUT/'candidate-15/src';assert not dest.exists();shutil.copytree(OUT/'candidate-14/src',dest)
 p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
