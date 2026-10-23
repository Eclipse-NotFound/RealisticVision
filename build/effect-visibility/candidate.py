"""Extract the unchanged unit raster builder, reuse it for spatial effect masks."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/effect-visibility-output'
if __name__=='__main__':
 p=OUT/'candidate/src/RealisticVisionMod.as';s=(OUT/'baseline/src/RealisticVisionMod.as').read_text(encoding='utf-8-sig')
 s=s.replace('      private var weaponPass:int = 0;','''      private var weaponPass:int = 0;
      private var worldVisuals:Dictionary = new Dictionary(true);
      private var worldMasks:Object = {};
      private var worldTypes:Dictionary = new Dictionary(true);
      private var worldPass:int = 0;
''')
 s=s.replace('         this.restoreWeaponVisuals();','         this.restoreWorldVisuals();\n         this.restoreWeaponVisuals();')
 a=s.index('         var x0:int = bb[0] - MASK_PAD_X;',s.index('private function applyMask('))
 s=s[:a]+'''         this.refreshMask(rec,bb);
         var s2:Shape=rec.m2 as Shape,s3:Shape=rec.m3 as Shape;
         s2.cacheAsBitmap=true;s3.cacheAsBitmap=true;
         if(u.vis != null && u.vis.parent != null) {
            if(s2.parent !== u.vis.parent)u.vis.parent.addChild(s2);
            u.vis.cacheAsBitmap=true;u.vis.mask=s2;
         } else if(s2.parent != null)s2.parent.removeChild(s2);
         if(u.hpbar != null && u.hpbar.parent != null) {
            if(s3.parent !== u.hpbar.parent)u.hpbar.parent.addChild(s3);
            u.hpbar.cacheAsBitmap=true;u.hpbar.mask=s3;
         } else if(s3.parent != null)s3.parent.removeChild(s3);
      }

      private function refreshMask(rec:Object,bb:Array):void
      {
'''+s[a:]
 a=s.index('         if(w.grafon != null)',s.index('private function refreshMask('));b=s.index('         // 子格级判定',a)
 s=s[:a]+s[b:]
 a=s.index('         // 显示树扫描：隐藏未被识别');b=s.index('\n      }',a)
 s=s[:a]+'         this.applyWorldVisuals(w,loc);'+s[b:]
 a=s.index('      private function scanArms(');b=s.index('      // ==================== 念力规则',a)
 s=s[:a]+(HERE/'world-visuals.as.inc').read_text(encoding='utf-8')+'\n'+s[b:]
 p.write_text(s,encoding='utf-8',newline='\n')
