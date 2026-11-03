"""C-Bul-2: narrow the world-visual (projectile/arm) mask support padding.

refreshMask keeps its defaults for unit masks (enemy blood bars need the
generous top pad); applyWorldVisual passes a tight 1/1/1 pad so projectile
rasters allocate ~half the subcells. All coordinate mappings inside
applyWorldVisual move to the same tight pad. Line-anchored replacements keep
working across the lineage's irregular indentation.
"""
from pathlib import Path
import argparse
import difflib, shutil
from run import OUT, prepare

prepare()
p=argparse.ArgumentParser();p.add_argument('--name',default='clip-pad');args=p.parse_args()
target = OUT/args.name/'src'
assert not target.exists(), 'Keep candidate snapshots immutable'
shutil.copytree(OUT/'baseline/src', target)
path = target/'RealisticVisionMod.as'
before = path.read_text('utf8')
after = before

def swap(old, new, note):
    global after
    assert after.count(old)==1, note+' :: '+repr(old[:70])
    after = after.replace(old,new)

# 1) refreshMask signature gains explicit pads (defaults unchanged for units).
swap('private function refreshMask(rec:Object,bb:Array):void',
     'private function refreshMask(rec:Object,bb:Array,padX:int = MASK_PAD_X,padTop:int = MASK_PAD_TOP,padBottom:int = MASK_PAD_BOTTOM):void',
     'signature')
swap('         var x0:int = bb[0] - MASK_PAD_X;','         var x0:int = bb[0] - padX;','x0')
swap('         var y0:int = bb[1] - MASK_PAD_TOP;','         var y0:int = bb[1] - padTop;','y0')
swap('         var x1:int = bb[2] + MASK_PAD_X;','         var x1:int = bb[2] + padX;','x1')
swap('         var y1:int = bb[3] + MASK_PAD_BOTTOM;','         var y1:int = bb[3] + padBottom;','y1')

# 2) uniformLit guard uses the effective pads.
swap('bb[0]-x0<MASK_PAD_X || bb[1]-y0<MASK_PAD_TOP || x1-bb[2]<MASK_PAD_X || y1-bb[3]<MASK_PAD_BOTTOM',
     'bb[0]-x0<padX || bb[1]-y0<padTop || x1-bb[2]<padX || y1-bb[3]<padBottom','uniform band')
swap('blur.blurX*blur.quality/2+2>MASK_PAD_X*this.fogSub',
     'blur.blurX*blur.quality/2+2>padX*this.fogSub','uniform blurX')
swap('blur.blurY*blur.quality/2+2>MASK_PAD_BOTTOM*this.fogSub',
     'blur.blurY*blur.quality/2+2>padBottom*this.fogSub','uniform blurY')

# 3) applyWorldVisual passes the tight pad.
swap('this.refreshMask(raster,[x0,y0,x1,y1]);',
     '// v0.34.8 C-Bul-2：弹体/手臂栅格支持区收窄（2/3/1→1/1/1）；几何已含于\n            // bounds，模糊半径需求远小于 1 瓦片；敌人单位掩膜走默认 pad 不变。\n            this.refreshMask(raster,[x0,y0,x1,y1],1,1,1);','raster call')

# 4) Coordinate mappings inside applyWorldVisual switch to the tight pad.
swap('var rx:int=(x0-Math.max(0,x0-MASK_PAD_X))*this.fogSub;','var rx:int=(x0-Math.max(0,x0-1))*this.fogSub;','rx')
swap('var ry:int=(y0-Math.max(0,y0-MASK_PAD_TOP))*this.fogSub;','var ry:int=(y0-Math.max(0,y0-1))*this.fogSub;','ry')
swap('var supportX:int=(x0-Math.max(0,x0-MASK_PAD_X))*this.fogSub;','var supportX:int=(x0-Math.max(0,x0-1))*this.fogSub;','supportX')
swap('var supportY:int=(y0-Math.max(0,y0-MASK_PAD_TOP))*this.fogSub;','var supportY:int=(y0-Math.max(0,y0-1))*this.fogSub;','supportY')
swap('var drawX:Number=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;','var drawX:Number=Math.max(0,x0-1)*Tile.tileX;','drawX')
swap('var drawY:Number=Math.max(0,y0-MASK_PAD_TOP)*Tile.tileY;','var drawY:Number=Math.max(0,y0-1)*Tile.tileY;','drawY')

# Only the three constant definitions may still reference MASK_PAD_*.
leftover = [l for l in after.splitlines() if 'MASK_PAD_' in l and 'private static const' not in l and 'padX:int' not in l]
assert not leftover, 'unhandled MASK_PAD references: '+repr(leftover)

path.write_text(after,'utf8')
patch = ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
    fromfile='a/RealisticVisionMod.as',tofile='b/RealisticVisionMod.as'))
(Path(__file__).parent/'production-pad.patch').write_text(patch,'utf8')
print(target)
