"""Test-only exact bitmap oracle for each early return; never a performance build."""
def instrument(s):
 marker='// REGION_HIT: preserve raster identity, sampling and attachment history.'
 assert marker in s
 s=s.replace(marker,'regionHits++;verifyRegionInput(rec,x0,y0,x1,y1);'+marker)
 at=s.index('{',s.index('public class'))+1
 s=s[:at]+'''
 public var regionHits:int=0,regionVerified:int=0;
 public function verifyRegionInput(rec:Object,x0:int,y0:int,x1:int,y1:int):void {
  var rect:Rectangle=new Rectangle(FOG_PAD+x0*MASK_SUB,FOG_PAD+y0*MASK_SUB,(x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB);
  var input:BitmapData=new BitmapData(rect.width,rect.height,true,0);
  if(cfgMode=="current")input.copyPixels(currentSight,rect,fogPoint);
  else input.threshold(fogCache,rect,fogPoint,"<",uint(MASK_LIT_A)<<24,0xFFFFFFFF,0xFF000000,false);
  var delta:Object=input.compare(rec.m2d);input.dispose();
  if(delta is BitmapData)BitmapData(delta).dispose();
  if(!(delta is uint && uint(delta)==0))throw new Error("REGION invalid reuse "+cfgMode+" "+rect+" f="+frameCount);
  regionVerified++;
 }
'''+s[at:]
 return s
