from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/combat-visibility-output'
BASE=MOD/'build/regression-recovery-output/production-singlepass/src'

def transform(s):
    s=s.replace('v0.33.2-settings-performance','v0.33.3-combat-visibility')
    s=s.replace('      private var classifiedSight:', '      private var weaponVisuals:Dictionary = new Dictionary(true);\n      private var weaponPass:int = 0;\n      private var classifiedSight:')
    s=s.replace('         s3.graphics.copyFrom(g);','         s3.graphics.copyFrom(g);\n         rec.maskRevision = int(rec.maskRevision)+1;')
    s=s.replace('         var any:Boolean = false;','         this.restoreWeaponVisuals();\n         var any:Boolean = false;',1)
    s=s.replace('         this.releaseClassicLogic();','         this.restoreWeaponVisuals();\n         this.releaseClassicLogic();')
    # Native unit childObjs includes held weapons, which are absent from firstObj.
    s=s.replace('         var units:Array = loc.units;','         var units:Array = loc.units;\n         this.weaponPass++;')
    s=s.replace('                  visiblePos.push([u.X,u.Y]);\n                  continue;', '                  this.applyUnitWeapons(u,1,exempt);\n                  visiblePos.push([u.X,u.Y]);\n                  continue;')
    s=s.replace('                  this.applyMask(w,u,this.unitBBox(loc,u));\n                  visiblePos.push([u.X,u.Y]);\n               }', '                  this.applyMask(w,u,this.unitBBox(loc,u));\n                  visiblePos.push([u.X,u.Y]);\n               }\n               this.applyUnitWeapons(u,st,exempt);')
    start=s.index('                  var owner:Unit = wpn.owner;',s.index('private function hideEnemies'))
    end=s.index('\n               }\n               obj = obj.nobj;',start)
    s=s[:start]+'''                  var owner:Unit = wpn.owner;
                  var wr:Object = wpn.vis ? this.weaponVisuals[wpn.vis] : null;
                  if(wr == null || wr.pass != this.weaponPass)
                  {
                     var wst:int = owner != null && owner != gg && !owner.player && !owner.npc && owner.fraction != Unit.F_PLAYER && !owner.invis && owner.sost < 3
                        ? this.enemyState(loc,owner) : 1;
                     this.applyWeaponVisual(wpn,owner,wst);
                  }'''+s[end:]
    s=s.replace('         // 显示树扫描：隐藏未被识别的子对象', '''         // Rebuilt/removed native visuals must not retain a detached mask.
         for(var oldVisual:Object in this.weaponVisuals)
         {
            var oldRecord:Object=this.weaponVisuals[oldVisual];
            if(oldRecord.weapon.vis !== oldVisual || oldRecord.owner != oldRecord.weapon.owner || DisplayObject(oldVisual).parent == null)
               this.releaseWeaponVisual(oldVisual as DisplayObject,oldRecord);
         }
         // 显示树扫描：隐藏未被识别的子对象''')
    at=s.index('      private function setWeaponVis(')
    s=s[:at]+(HERE/'weapon-methods.as.inc').read_text(encoding='utf-8')+'\n'+s[at:]
    return s

if __name__=='__main__':
    dest=OUT/'candidate/src';assert not dest.exists();shutil.copytree(BASE,dest)
    p=dest/'RealisticVisionMod.as';p.write_text(transform(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
