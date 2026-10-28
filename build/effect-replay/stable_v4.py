"""Restrict support reuse to exactly the same field generation and filter."""
from pathlib import Path
import shutil
MOD=Path(__file__).resolve().parents[2]
src=MOD/'build/effect-replay-output/candidates/stable-v2/src'
dst=src.parents[1]/'stable-v4/src';assert not dst.exists()
shutil.copytree(src,dst)
p=dst/'RealisticVisionMod.as';s=p.read_text()
s=s.replace('record.stableBb!=null && this.worldParentPixelAligned',
'''record.stableBb!=null && record.stableFov===this.fovVersion
            && record.stableBlurX===this.maskBlurCurrent.blurX && record.stableBlurY===this.maskBlurCurrent.blurY && record.stableQuality===this.maskBlurCurrent.quality
            && this.worldParentPixelAligned''')
s=s.replace('record.stableBb=[mx0,my0,mx1,my1];','''record.stableBb=[mx0,my0,mx1,my1];record.stableFov=this.fovVersion;
         record.stableBlurX=this.maskBlurCurrent.blurX;record.stableBlurY=this.maskBlurCurrent.blurY;record.stableQuality=this.maskBlurCurrent.quality;''')
p.write_text(s,encoding='utf-8',newline='\n')
