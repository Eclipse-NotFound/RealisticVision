"""Single-variable candidate: cache the result for unchanged mask pixels."""
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combat-split-output'
target=OUT/'candidates/support/src';assert not target.exists()
shutil.copytree(OUT/'baseline/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text()
start=s.index('            var supportData:BitmapData=raster.m2e as BitmapData;')
end=s.index('\n         }\n         if(record==null)',start)
old=s[start:end]
block=old[:old.index('            // Reading filters')]
replacement='''            // The key fixes this region. Reuse its zero-alpha result only
            // until refreshMask actually rewrites the blurred pixels.
            if(raster.supportEmptyValid !== true)
            {
'''+''.join('   '+line+'\n' for line in block.splitlines())+'''               /* D58_SUPPORT_TEST */
               raster.supportEmpty=!supportData.hitTest(this.fogPoint,1,this.worldSupportRect);
               raster.supportEmptyValid=true;
            }
            else { /* D58_SUPPORT_HIT */ }
            // Filter state still belongs to each current animation tree.
            if(raster.supportEmpty && !this.worldVisualHasFilters(visual))drawDark=true;'''
s=s[:start]+replacement+s[end:]
marker='         rec.maskValid = false;\n         if(blur.blurX > 0)'
assert s.count(marker)==1
s=s.replace(marker,'         rec.maskValid = false;\n         if(rec.worldRaster === true)rec.supportEmptyValid=false;\n         if(blur.blurX > 0)')
p.write_text(s,encoding='utf-8',newline='\n')
print('Prepared support-result-only candidate; original integer crop guard retained')
