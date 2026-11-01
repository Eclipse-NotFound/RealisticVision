"""Candidate 3: only upload the contour fog when its input field changes."""
from pathlib import Path
import shutil,json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/maximized-flow-output'
assert not (OUT/'merged-candidate').exists()
shutil.copytree(OUT/'candidate',OUT/'merged-candidate')
for p in (OUT/'baseline/src').rglob('*.as'):
    target=OUT/'candidate/src'/p.relative_to(OUT/'baseline/src');shutil.copyfile(p,target)
p=OUT/'candidate/src/RVWallSurface.as';s=p.read_text(encoding='utf-8')
s=s.replace('private var contourFog:BitmapData;', 'private var contourFog:BitmapData;\n      private var contourFogVersion:int = -1;')
old='if(contourFog!=null)contourFog.dispose();contourFog=new BitmapData(field.width,field.height,true,0xff000000);'
assert s.count(old)==1;s=s.replace(old,old+'contourFogVersion=-1;')
old='contourFog.paletteMap(floorField,floorField.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);'
assert s.count(old)==1;s=s.replace(old,'''// floorField changes only in the field rebuild above. Avoid notifying
         // the display list when the same alpha texture would be uploaded again.
         if(contourFogVersion!=fieldUpdates){
            contourFog.paletteMap(floorField,floorField.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);
            contourFogVersion=fieldUpdates;
         }''')
p.write_text(s,encoding='utf-8',newline='\n')
(OUT/'candidate/change.json').write_text(json.dumps({'kind':'contour-palette-input-version','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'candidate/src').glob('*.as')}},indent=2)+'\n',encoding='utf-8')
