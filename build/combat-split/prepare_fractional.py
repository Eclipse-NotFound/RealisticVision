"""D58 isolated hypothesis: keep scale=1 crop during fractional translation."""
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combat-split-output'
target=OUT/'candidates/fractional/src';assert not target.exists()
shutil.copytree(OUT/'baseline/src',target)
p=target/'RealisticVisionMod.as';s=p.read_text()
guard=' && screenMatrix.tx==Math.floor(screenMatrix.tx) && screenMatrix.ty==Math.floor(screenMatrix.ty)'
assert s.count(guard)==1;s=s.replace(guard,'')
marker='// D56_REFRESH: crop uses the original sample lattice'
assert s.count(marker)==1;s=s.replace(marker,marker+'\n            /* D58_FRACTIONAL_CROP */')
p.write_text(s,encoding='utf-8',newline='\n')
# Existing continuous independent-tree check, now exercising more fractional
# parent positions. No same-frame reference reattachment or pixel tolerances.
t=(MOD/'build/enemy-combat/alloc_check.py').read_text().replace('enemy-combat-output','combat-split-output').replace('D57','D58')
start=t.index(" p=src/'RealisticVisionMod.as';code=p.read_text();code=code.replace('public var trailingHits:int=0;'",t.index(" if '--stable-v4'"))
end=t.index(" (folder/'EffectLoadChecks.as').write_text",start)
t=t[:start]+''' p=src/'RealisticVisionMod.as';code=p.read_text();code=code.replace('public var trailingHits:int=0;','public var trailingHits:int=0;public var fractionHits:int=0;').replace('/* D58_FRACTIONAL_CROP */','if(screenMatrix.tx!=Math.floor(screenMatrix.tx)||screenMatrix.ty!=Math.floor(screenMatrix.ty))fractionHits++;');p.write_text(code,encoding='utf-8')
 t=t.replace('offset:Number=f%3==0?0:.35;', 'offset:Number=[0,.01,.25,.49,.5,.9,-.1,-.5][f%8];')
 t=t.replace('trace("LOAD COMPLETE passed="+passed);','check(b.fractionHits>100,"fractional translation crop exercised");trace("FRACTION HITS "+b.fractionHits);trace("LOAD COMPLETE passed="+passed);')
''' +t[end:]
(HERE/'fractional_check.py').write_text(t,encoding='utf-8')
print('Prepared fractional-only candidate and exact continuous comparison')
