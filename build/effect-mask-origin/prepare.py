"""D56: normalize mask-local coordinates, retaining complete alpha and bounds."""
from pathlib import Path
import hashlib,shutil
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
BASE=MOD/'build/combat-render-output/production-final2/src';OUT=MOD/'build/effect-mask-origin-output'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
dest=OUT/'candidates/local/src';assert not dest.exists();shutil.copytree(BASE,dest)
p=dest/'RealisticVisionMod.as';s=p.read_text()
old='''            if(drawDark)shape.graphics.clear();
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);'''
new='''            if(drawDark)shape.graphics.clear();
            else {
               var originX:Number=Math.max(0,x0-MASK_PAD_X)*Tile.tileX;
               var originY:Number=Math.max(0,y0-MASK_PAD_TOP)*Tile.tileY;
               var source:BitmapData=raster.m2e as BitmapData;
               var scale:Number=Tile.tileX/MASK_SUB;
               shape.graphics.clear();
               shape.graphics.beginBitmapFill(source,new Matrix(scale,0,0,scale),false,true);
               shape.graphics.drawRect(0,0,source.width*scale,source.height*scale);
               shape.graphics.endFill();
               if(shape.x!=originX)shape.x=originX;if(shape.y!=originY)shape.y=originY;
               // D56_LOCAL
            }'''
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf-8',newline='\n')
assert not (HERE/'check.py').exists()
s=(MOD/'build/effect-replay/check.py').read_text().replace('D55','D56').replace('effect-replay-output','effect-mask-origin-output')
a=s.index(" src=folder/'src';");b=s.index("\n p=src/",a)
s=s[:a]+" src=folder/'src';r.public(OUT/'candidates/local/src',src)"+s[b:]
s=s.replace("s=s.replace('// D56_STABLE','trailingHits++;')","s=s.replace('// D56_LOCAL','trailingHits++;')")
(HERE/'check.py').write_text(s,encoding='utf-8',newline='\n')
for name in ['run.py','SavedReplayProbe.as','native_run.py','SavedFireProbe.as']:
 s=(MOD/'build/effect-replay'/name).read_text().replace('D55','D56').replace('effect-replay-output','effect-mask-origin-output')
 if name=='run.py':
  a=s.index(" source=MOD/'build/frame-attribution-output");b=s.index(" sources.append(('candidate',source))",a)
  s=s[:a]+" source=OUT/'candidates/local/src'\n"+s[b:]
  s=s.replace("s=s.replace('// D54_TRAILING','trailingHits++;')", "s=s.replace('// D56_LOCAL','trailingHits++;').replace('// D54_TRAILING','trailingHits++;')")
 if name=='native_run.py':
  a=s.index(" if candidate:sources.append");b=s.index('\n for variant,source in sources:',a)
  s=s[:a]+" if candidate:sources.append(('candidate',OUT/'candidates/local/src'))"+s[b:]
  s=s.replace("s=s.replace('// D56_STABLE','if(mx0!=x0 || my0!=y0 || mx1!=x1 || my1!=y1)trailingHits++;')", "s=s.replace('// D56_LOCAL','trailingHits++;')")
 (HERE/name).write_text(s,encoding='utf-8',newline='\n')
ignore=MOD/'.gitignore';s=ignore.read_text()
if 'build/effect-mask-origin-output/' not in s:ignore.write_text(s.rstrip()+'\nbuild/effect-mask-origin-output/\n',encoding='utf-8',newline='\n')
