"""C-Bul-1 + C-Ene-1: projectile clip masks and enemy-state hysteresis.

Both edits are applied to the frozen v0.34.5 baseline; anchors are asserted to
occur exactly once so concurrent source drift cannot pass silently.
"""
from pathlib import Path
import argparse
import difflib, shutil
from run import OUT, prepare

prepare()
p=argparse.ArgumentParser();p.add_argument('--name',default='clip-hyst');args=p.parse_args()
target = OUT/args.name/'src'
assert not target.exists(), 'Keep candidate snapshots immutable'
shutil.copytree(OUT/'baseline/src', target)
path = target/'RealisticVisionMod.as'
before = path.read_text('utf8')

# ---- C-Bul-1: projectiles (dynamicBounds) use vector clip masks.
# Rotating, fast-moving bullets invalidate the alpha-mask bitmap cache every
# frame; clip semantics needs no cached surfaces on either side.
old = '''         if(shape.parent!==visual.parent)visual.parent.addChild(shape);
         if(shape.cacheAsBitmap!==!drawDark)shape.cacheAsBitmap=!drawDark;
         var useCache:Boolean=drawDark?record.cache:true;
         if(visual.cacheAsBitmap!==useCache)visual.cacheAsBitmap=useCache;
         if(visual.mask!==shape)visual.mask=shape;'''
new = '''         if(shape.parent!==visual.parent)visual.parent.addChild(shape);
         // v0.34.6 C-Bul-1：高速弹体（dynamicBounds）改矢量裁剪遮罩。旋转/位移
         // 弹体在 alpha 遮罩（双侧 cacheAsBitmap）下每帧位图缓存击穿重栅格化；
         // 裁剪语义无需位图表面，两侧缓存恢复原值。代价：跨界弹体边界由 alpha
         // 渐变变为遮罩场 alpha>0 硬边（亮区尾迹与暗区隐藏语义不变）。
         if(dynamicBounds)
         {
            if(shape.cacheAsBitmap)shape.cacheAsBitmap=false;
            if(visual.cacheAsBitmap!==record.cache)visual.cacheAsBitmap=record.cache;
         }
         else
         {
            if(shape.cacheAsBitmap!==!drawDark)shape.cacheAsBitmap=!drawDark;
            var useCache:Boolean=drawDark?record.cache:true;
            if(visual.cacheAsBitmap!==useCache)visual.cacheAsBitmap=useCache;
         }
         if(visual.mask!==shape)visual.mask=shape;'''
assert before.count(old)==1, 'C-Bul-1 anchor'
after = before.replace(old,new)

# ---- C-Ene-1: fix the missing middle-band classification and add hysteresis.
old = '''               if(mixed && this.cfgEnemyFast == 1)
               {
                  // v0.34.1：透光门/水泄漏区（FOV_DIM）必须保留门景暗化软遮罩——
                  // 混合区按比例提升为全可见会把门后单位（如炮塔）亮显。
                  var gateRatio:Number=litWeight/tileCount;
                  if(gateRatio>=0.8 && dimTiles==0) return 1;
                  if(gateRatio<=0.15) return 0;
               }
               return !mixed && combined==2 ? 1 : 0;'''
new = '''               if(mixed && this.cfgEnemyFast == 1)
               {
                  // v0.34.1：透光门/水泄漏区（FOV_DIM）必须保留门景暗化软遮罩——
                  // 混合区按比例提升为全可见会把门后单位（如炮塔）亮显。
                  // v0.34.6 C-Ene-1：修复 0.15<比例<0.8 临界区漏判（原跌落返回 0，
                  // 边界微晃引发 0/1 高频翻转与显隐/渐入抖动）；中间带明确走软遮罩，
                  // 并按上一稳定状态加迟滞带（升显 0.85、离显 0.80、离隐 0.25、
                  // 降隐 0.10；带内保持），0 与 1 之间必经软遮罩过渡。
                  var gateRatio:Number=litWeight/tileCount;
                  var prevRec:Object=this.unitVis[u];
                  var prevSt:int=prevRec!=null?int(prevRec.state):-1;
                  if(gateRatio>=0.85 && dimTiles==0) return 1;
                  if(gateRatio>=0.8) return dimTiles==0 && prevSt==1 ? 1 : 2;
                  if(gateRatio>=0.25) return 2;
                  if(gateRatio>=0.15) return prevSt==0 ? 0 : 2;
                  if(gateRatio>=0.1) return prevSt==2 ? 2 : 0;
                  return 0;
               }
               return !mixed && combined==2 ? 1 : 0;'''
assert after.count(old)==1, 'C-Ene-1 anchor'
after = after.replace(old,new)

path.write_text(after,'utf8')
patch = ''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
    fromfile='a/RealisticVisionMod.as',tofile='b/RealisticVisionMod.as'))
(Path(__file__).parent/'production.patch').write_text(patch,'utf8')
print(target)
