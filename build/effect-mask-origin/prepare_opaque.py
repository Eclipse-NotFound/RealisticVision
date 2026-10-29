"""Keep the original pipeline for opacity/color transforms and vector timelines."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output'
dest=OUT/'candidates/raster-crop-opaque/src';assert not dest.exists();shutil.copytree(OUT/'candidates/raster-crop/src',dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='this.worldParentPixelAligned(visual.parent) && !this.worldVisualHasFilters(visual)'
assert s.count(old)==1;s=s.replace(old,'this.worldParentPixelAligned(visual.parent) && this.worldOpaqueBitmap(visual) && !this.worldVisualHasFilters(visual)')
where='      private function worldScreenMask('
method='''      private function worldOpaqueBitmap(visual:DisplayObject):Boolean
      {
         var container:DisplayObjectContainer=visual as DisplayObjectContainer;
         if(container==null || container.numChildren!=1 || !(container.getChildAt(0) is Bitmap))return false;
         var ct:ColorTransform=container.getChildAt(0).transform.concatenatedColorTransform;
         return ct.alphaMultiplier==1 && ct.alphaOffset==0 && ct.redMultiplier==1 && ct.greenMultiplier==1 && ct.blueMultiplier==1
            && ct.redOffset==0 && ct.greenOffset==0 && ct.blueOffset==0;
      }

'''
assert s.count(where)==1;s=s.replace(where,method+where)
p.write_text(s,encoding='utf-8',newline='\n')
