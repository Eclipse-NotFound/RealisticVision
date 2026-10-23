from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/boundary-load-output';GAME=MOD.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 assert sha(MOD/'release/RealisticVisionMod.swf')=='83d8e590c062e181b70bd5cabef2200084d5e81aaca081d1d1ebc347205c7e65'
 assert not OUT.exists();OUT.mkdir()
 src=MOD/'build/long-frame-output/production/src';shutil.copytree(src,OUT/'candidate-00/src');shutil.copytree(src,OUT/'candidate-01/src')
 p=OUT/'candidate-01/src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8-sig')
 start=s.index('         var g:flash.display.Graphics = s2.graphics;',s.index('private function applyMask'))
 end=s.index('         if(previousInput == null',start)
 block=s[start:end]
 s=s[:start]+'''         // Bitmap fill keeps the raster reference. Updating its pixels does not
         // change the fill geometry; retain body/bar/weapon shapes until the
         // world rectangle or raster allocation changes.
         if(rec.maskDrawBitmap !== bdb || rec.maskBounds != sig)
         {
'''+block+'''            rec.maskDrawBitmap=bdb;
         }
'''+s[end:]
 p.write_text(s,encoding='utf-8',newline='\n')
 (OUT/'inputs.json').write_text(json.dumps({'installed':sha(MOD/'release/RealisticVisionMod.swf'),'host':sha(GAME/'pfe.swf'),'sources':{p.relative_to(src).as_posix():sha(p) for p in src.rglob('*.as')}},indent=2)+'\n',encoding='utf-8')
