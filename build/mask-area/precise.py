"""D45: tighten only the proof of complete transparency; never crop a drawn mask."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output'
BASE=MOD/'build/combat-render-output/production-final2/src'
pins=json.loads((OUT/'inputs.json').read_text())
assert all(hashlib.sha256((BASE/p).read_bytes()).hexdigest()==sha for p,sha in pins['sources'].items())
dest=OUT/'candidates/precise/src';assert not dest.exists()
source=(BASE/'RealisticVisionMod.as').read_text(encoding='utf-8-sig')
old='''            // Keep bilinear neighbours, reusing one synchronous scratch rect.
            this.worldSupportRect.x=Math.max(0,supportX-1);
            this.worldSupportRect.y=Math.max(0,supportY-1);
            this.worldSupportRect.width=Math.min(supportData.width,supportX+(x1-x0+1)*MASK_SUB+1)-this.worldSupportRect.x;
            this.worldSupportRect.height=Math.min(supportData.height,supportY+(y1-y0+1)*MASK_SUB+1)-this.worldSupportRect.y;'''
new='''            // Prove transparency over the actual visual bounds, retaining
            // two low-resolution neighbours for bilinear and cached rendering.
            // Non-empty masks retain their original geometry and every pixel.
            var maskScale:Number=MASK_SUB/Tile.tileX;
            var maskOriginX:Number=Math.max(0,x0-MASK_PAD_X)*MASK_SUB;
            var maskOriginY:Number=Math.max(0,y0-MASK_PAD_TOP)*MASK_SUB;
            this.worldSupportRect.x=Math.max(0,Math.floor(bounds.left*maskScale)-maskOriginX-2);
            this.worldSupportRect.y=Math.max(0,Math.floor(bounds.top*maskScale)-maskOriginY-2);
            this.worldSupportRect.width=Math.min(supportData.width,Math.ceil(bounds.right*maskScale)-maskOriginX+2)-this.worldSupportRect.x;
            this.worldSupportRect.height=Math.min(supportData.height,Math.ceil(bounds.bottom*maskScale)-maskOriginY+2)-this.worldSupportRect.y;'''
assert source.count(old)==1
shutil.copytree(BASE,dest)
(dest/'RealisticVisionMod.as').write_text(source.replace(old,new),encoding='utf-8',newline='\n')
print('Prepared D44 + precise transparent-support proof')
