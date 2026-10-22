"""D37: exact-input dirty regions for classic wall joins (candidate only)."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/native-performance-output'
BASE=MOD/'build/combat-visibility-output/production/src'

def transform(s):
    s=s.replace('private var classicCornerDeltas:Array = [];','private var classicCornerDeltas:Array = [];\n      private var classicJoins:Array = [];')
    s=s.replace('this.restoreWeaponVisuals();','this.releaseClassicJoins();\n         this.restoreWeaponVisuals();')
    start=s.index('      private function applyVisionClassic(')
    end=s.index('      private function joinClassicWalls(',start)
    part=s[start:end]
    assert part.count('this.joinClassicWalls(loc);')==2
    part=part.replace('this.joinClassicWalls(loc);','this.joinClassicWalls(loc,null,false,null,0);',1)
    part=part.replace('this.joinClassicWalls(loc);','this.joinClassicWalls(loc,null,false,null,1);',1)
    s=s[:start]+part+s[end:]
    s=s.replace('visited:Vector.<int> = null):void','visited:Vector.<int> = null, cacheSlot:int = -1):void')
    start=s.index('      private function joinClassicWalls(')
    end=s.index('      /** Materialize each requested',start)
    part=s[start:end]
    marker='         if(!prepared)\n'
    assert part.count(marker)==1
    part=part.replace(marker,'''         var cached:Object=null;
         if(cacheSlot>=0 && !prepared && bounds==null)
         {
            cached=this.prepareClassicJoin(cacheSlot,loc);
            if(cached.region.isEmpty())
            {
               this.fogBmp.copyPixels(cached.output,this.fogRect,this.fogPoint);
               this.classicWallShade.copyPixels(cached.shade,this.fogRect,this.fogPoint);
               return;
            }
            bounds=cached.region;
         }
'''+marker,1)
    # The existing full prepass continues to update wallShade and corner values.
    # Only the expensive per-tile correction is restricted to changed support.
    at=part.rfind('      }')
    part=part[:at]+'''         if(cached!=null)
         {
            cached.output.copyPixels(this.fogBmp,this.fogRect,this.fogPoint);
            cached.shade.copyPixels(this.classicWallShade,this.fogRect,this.fogPoint);
         }
'''+part[at:]
    s=s[:start]+part+s[end:]
    methods=(Path(__file__).parent/'classic-cache.as.inc').read_text(encoding='utf-8')
    return s.replace('      /** Materialize each requested',methods+'\n      /** Materialize each requested',1)

def main():
    dest=OUT/'candidate-01/src';assert not dest.exists()
    shutil.copytree(BASE,dest)
    src=dest/'RealisticVisionMod.as';src.write_text(transform(src.read_text(encoding='utf-8-sig')),encoding='utf-8')
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    (OUT/'inputs.json').write_text(json.dumps({'installed':sha(MOD/'release/RealisticVisionMod.swf'),'baseline':{f.relative_to(BASE).as_posix():sha(f) for f in BASE.rglob('*.as')}},indent=2),encoding='utf-8')
if __name__=='__main__':main()
