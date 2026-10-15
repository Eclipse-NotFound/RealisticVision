"""Apply the same display-only wall-face integration to the installed lineage and HEAD.

The CS-generated source is read-only and fingerprint-pinned: authority WIP is
never accidentally added to a candidate for the currently installed game.
"""
from pathlib import Path
import argparse, hashlib, re, shutil

MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/wall-surface-output'
FROZEN=MOD.parent/'ContinuousScene/build/generated/rv-production'
FROZEN_SHA='6979263b178b4deedf563a88c560614bd867d4fad89d806484b5a5b851c0d446'

def integrate(source):
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1,old[:100]
        source=source.replace(old,new)
    replace('      private var wallLayer:Sprite = null;',
            '      private var wallLayer:Sprite = null;\n      private var fogShadow:Sprite = null;\n      private var wallSurface:RVWallSurface = new RVWallSurface();')
    replace('         this.hideEnemies(w,loc,needFov);',
            '         this.updateWallSurface(w,loc);\n         this.hideEnemies(w,loc,needFov);')
    replace('      private function resetOff():void\n      {',
            '      private function resetOff():void\n      {\n         this.wallSurface.reset();')
    replace('         var visual:Sprite = w.grafon.visual;', '''         // Keep the native infrared fog transform separate from the bright surface.
         if(this.fogShadow == null)
         {
            this.fogShadow = new Sprite();
            this.fogShadow.mouseEnabled = this.fogShadow.mouseChildren = false;
            this.fogVis.addChild(this.fogShadow);
         }
         for each(var fogChild:DisplayObject in [this.fogBitmap,this.wallLayer,this.wallClip,this.floorClip])
            if(fogChild.parent != this.fogShadow) this.fogShadow.addChild(fogChild);
         var visual:Sprite = w.grafon.visual;''')
    replace('         this.fogVis.visible = true;', '''         this.fogShadow.scrollRect = this.fogVis.scrollRect;
         this.fogShadow.x = this.fogVis.x; this.fogShadow.y = this.fogVis.y;
         this.fogVis.visible = true;''')
    for prop in ('transform.colorTransform = this.infraCT','transform.colorTransform = this.defCT',
                 'blendMode = "multiply"','blendMode = "normal"'):
        replace('this.fogVis.'+prop,'this.fogShadow.'+prop)
    anchor='      private function wallCornerAlpha(tx:int, ty:int):Number'
    replace(anchor,'''      /** Surface protection changes only the displayed fog, never enemy sight. */
      private function updateWallSurface(w:World, loc:Location):void
      {
         if(this.fogShadow == null) return;
         var self:RealisticVisionMod = this;
         this.wallSurface.update(this.fogVis,w.grafon,loc,this.scenePaintBounds(),
            function(tx:int,ty:int):Boolean { return self.memoryExplored(tx+ty*self.spaceX); });
      }

'''+anchor)
    source=re.sub(r'private static const VERSION:String = "[^"]+";',
                  'private static const VERSION:String = "v0.31.0-wall-surface-candidate";',source,count=1)
    return source

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--integrate-main',action='store_true');args=parser.parse_args()
    # A concurrent ContinuousScene experiment may regenerate its working source.
    # Keep using our verified installed-lineage snapshot once one has been taken.
    owned=OUT/'baseline/src'
    base=owned if (owned/'RealisticVisionMod.as').exists() else FROZEN
    source=base/'RealisticVisionMod.as'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==FROZEN_SHA,'Installed lineage changed; inspect before preparing'
    for variant in ('baseline','candidate'):
        target=OUT/variant/'src';target.mkdir(parents=True,exist_ok=True)
        for f in base.rglob('*.as'):
            dest=target/f.relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.resolve()!=f.resolve():dest.write_bytes(f.read_bytes())
        if variant=='candidate':
            (target/'RealisticVisionMod.as').write_text(integrate(source.read_text(encoding='utf-8-sig')),encoding='utf-8')
            shutil.copyfile(MOD/'src/RVWallSurface.as',target/'RVWallSurface.as')
    if args.integrate_main:
        main=MOD/'src/RealisticVisionMod.as'
        main.write_text(integrate(main.read_text(encoding='utf-8-sig')),encoding='utf-8')
    print('Frozen baseline and wall-surface candidate prepared; release untouched')
