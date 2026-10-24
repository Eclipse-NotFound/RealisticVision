"""Follow-up variant: share the bitmap fill, not only filtered sample work."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shared-mask-output'
source=OUT/'candidates/shared/src';target=OUT/'candidates/reference/src';assert not target.exists()
pins=json.loads((source.parent/'manifest.json').read_text());assert all(hashlib.sha256((source/p).read_bytes()).hexdigest()==h for p,h in pins.items())
shutil.copytree(source,target);path=target/'RealisticVisionMod.as';s=path.read_text(encoding='utf-8')
def patch(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
patch('''      private function refreshMask(rec:Object,bb:Array):void
      {
''','''      private function refreshMask(rec:Object,bb:Array):void
      {
         // A retained fill keeps this shared bitmap alive even if the complete
         // local input is unchanged and skips filtering for many generations.
         if(rec.sharedSource!=null)rec.sharedSource.used=this.worldPass;
''')
patch('''         if(rec.maskDrawBitmap !== bdb || rec.maskBounds != sig)
         {''','''         var fillData:BitmapData=shared!=null ? shared.soft as BitmapData : bdb;
         var fillX:int=shared!=null ? shared.x : x0,fillY:int=shared!=null ? shared.y : y0;
         rec.sharedSource=shared;
         if(rec.maskDrawBitmap !== fillData || rec.maskBounds != sig)
         {''')
patch('''         var m:Matrix = new Matrix(cs,0,0,cs,x0 * Tile.tileX,y0 * Tile.tileY);
         g.beginBitmapFill(bdb,m,false,true);''','''         var m:Matrix = new Matrix(cs,0,0,cs,fillX * Tile.tileX,fillY * Tile.tileY);
         g.beginBitmapFill(fillData,m,false,true);''')
patch('''            rec.maskDrawBitmap=bdb;''','''            rec.maskDrawBitmap=fillData;''')
path.write_text(s,encoding='utf-8',newline='\n')
(target.parent/'manifest.json').write_text(json.dumps({p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*.as')},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Reference-fill variant prepared; not validated or installed')
