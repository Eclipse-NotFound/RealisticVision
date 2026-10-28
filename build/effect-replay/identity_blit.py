"""Limit the older identity-mask experiment to native bitmap-backed effects."""
from pathlib import Path
import json,hashlib,shutil
MOD=Path(__file__).resolve().parents[2]
src=MOD/'build/frame-attribution-output/candidates/identity/src'
dst=MOD/'build/effect-replay-output/candidates/identity-blit/src';assert not dst.exists()
pins=json.loads((src.parent/'manifest.json').read_text())
assert all(hashlib.sha256((src/p).read_bytes()).hexdigest()==h for p,h in pins.items())
shutil.copytree(src,dst)
p=dst/'RealisticVisionMod.as';s=p.read_text()
old='''      private function worldVisualFullyLit(visual:DisplayObject,bounds:Rectangle,x0:int,y0:int,raster:Object):Boolean
      {
'''
new=old+'''         // Vector/timeline effects retain the exact native mask pipeline.
         // Only a single bitmap-backed animation is eligible for this probe.
         var container:DisplayObjectContainer=visual as DisplayObjectContainer;
         if(container==null || container.numChildren!=1 || !(container.getChildAt(0) is Bitmap))return false;
'''
assert s.count(old)==1;s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
