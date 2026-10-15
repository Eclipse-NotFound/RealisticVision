"""Build the wall option from our pinned installed-lineage snapshot, not live HEAD."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/wall-options-output'
BASE=MOD/'build/wall-surface-output/baseline/src'
PIN='6979263b178b4deedf563a88c560614bd867d4fad89d806484b5a5b851c0d446'
KEYS=OUT/'installed-keys/src'
KEY_PINS={
    'RealisticVisionMod.as':'83f274141e8a73347f18e61642e7fc5ac9a46606c71418eaf4cf6290bd3f58c8',
    'RVKeybinds.as':'50ba8a05b41c3b188f3e78b3deb060ecd152c5e8e940590a78c08ab9b65c334e',
    'modlocales/vision/RVLocaleMessages.as':'e215891fce8be4f7f42d166afe5b6c0460c6752c8e5360d42365ec209bb9fe16'}
LABEL='已探索墙边常亮'
HINT='关闭后墙面随视野变暗；两种模式始终修正墙边阴影'
MESSAGES={LABEL:{'en':'Keep explored wall edges bright','ru':'Яркие края изученных стен'},
          HINT:{'en':'When off, walls dim with visibility. Wall-edge shadow fixes remain active in both modes.',
                'ru':'Если выключено, стены темнеют вне видимости. Исправление границ теней действует в обоих режимах.'}}

def upgrade(source):
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1,old[:100]
        source=source.replace(old,new)
    replace('      private var cfgDim:Number = 0.35;', '      private var cfgDim:Number = 0.35;\n      private var cfgWallBright:Boolean = true;')
    replace('      private var fogShadow:Sprite = null;', '      private var fogShadow:Sprite = null;\n      private var fogBase:Sprite = null;')
    replace('                else if(key == "dim")', '''               else if(key == "wallbright")
               {
                  if(val == "1" || val == "0") this.cfgWallBright = val == "1";
               }
                else if(key == "dim")''')
    replace('               + "dim=" + this.cfgDim + "\\n"', '               + "wallbright=" + (this.cfgWallBright ? "1" : "0") + "\\n"\n               + "dim=" + this.cfgDim + "\\n"')
    replace('         for each(var fogChild:DisplayObject in [this.fogBitmap,this.wallLayer,this.wallClip,this.floorClip])\n            if(fogChild.parent != this.fogShadow) this.fogShadow.addChild(fogChild);', '''         if(this.fogBase == null)
         {
            this.fogBase = new Sprite();
            this.fogBase.mouseEnabled = this.fogBase.mouseChildren = false;
            this.fogShadow.addChild(this.fogBase);
         }
         for each(var fogChild:DisplayObject in [this.fogBitmap,this.wallLayer,this.wallClip,this.floorClip])
            if(fogChild.parent != this.fogBase) this.fogBase.addChild(fogChild);''')
    replace('''         this.wallSurface.update(this.fogVis,w.grafon,loc,this.scenePaintBounds(),
            function(tx:int,ty:int):Boolean { return self.memoryExplored(tx+ty*self.spaceX); });''', '''         this.wallSurface.update(this.fogShadow,this.fogBase,w.grafon,loc,this.scenePaintBounds(),
            function(tx:int,ty:int):Boolean { return self.memoryExplored(tx+ty*self.spaceX); },
            function(tx:int,ty:int,wx:Number,wy:Number,dir:int):Number { return self.wallEdgeLight(tx,ty,wx,wy,dir); },
            this.cfgWallBright);''')
    anchor='      private function wallCornerAlpha(tx:int, ty:int):Number'
    replace(anchor,'''      /** Read light from the open side, never from the wall-centre shadow.
       * This is display-only; no ray result is added to sight or exploration. */
      private function wallEdgeLight(tx:int, ty:int, wx:Number, wy:Number, dir:int):Number
      {
         var tile:Tile = this.curLoc.getTile(tx,ty);
         if(this.cfgMode == "current" && tile.opac < 1 && this.fogRaw != null)
         {
            if(dir == 0) wy -= 2.5;
            else if(dir == 1) wy += 2.5;
            else if(dir == 2) wx -= 2.5;
            else wx += 2.5;
            return 1 - (this.fogRaw.getPixel32(FOG_PAD+Math.floor(wx/5),FOG_PAD+Math.floor(wy/5)) >>> 24)/255;
         }
         var i:int = tx+ty*this.spaceX;
         var memory:Number = this.memCur[i];
         var nativeLight:Number = this.explorationLight(this.curLoc,tx,ty);
         if(tile.opac < 1 && this.fov[i] == FOV_DIM) nativeLight = Math.max(nativeLight,this.cfgDoorDim);
         return Math.max(0,Math.min(1,nativeLight*(1-memory)+this.cfgDim*memory));
      }

'''+anchor)
    anchor='         items[items.length] = {"key":"dim","label":"记忆区暗度","kind":"slider",'
    replace(anchor,f'''         items[items.length] = {{"key":"wallbright","label":"{LABEL}","kind":"check",
            "min":0,"max":1,"step":1,"hint":"{HINT}","def":true,
            "get":function():* {{ return self.cfgWallBright; }},
            "set":function(v:*):void {{ self.setWallBright(v == true); }}}};
'''+anchor)
    anchor='      /** 总开关（与 F11 同路径：落盘 + 重建视野状态）。 */'
    replace(anchor,'''      private function setWallBright(v:Boolean):void
      {
         if(this.cfgWallBright == v) return;
         this.cfgWallBright = v;
         this.saveConfig();
      }

'''+anchor)
    replace('v0.31.0-wall-surface-candidate','v0.31.1-wall-options-candidate')
    return source

def locales(folder,from_as=False):
    path=folder/'modlocales/vision/messages.json'
    body=path.read_text(encoding='utf-8-sig') if path.exists() and not from_as else (path.parent/'RVLocaleMessages.as').read_text(encoding='utf-8-sig').split('DATA:Object =',1)[1].rsplit(';',1)[0]
    catalog=json.loads(body);catalog.update(MESSAGES)
    body=json.dumps(catalog,ensure_ascii=False,indent=2)
    path.write_text(body+'\n',encoding='utf-8')
    (path.parent/'RVLocaleMessages.as').write_text('package modlocales.vision {\n   public class RVLocaleMessages {\n      public static const DATA:Object = '+body+';\n   }\n}\n',encoding='utf-8')

def prepare():
    assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()==PIN,'Frozen production snapshot changed'
    spec=importlib.util.spec_from_file_location('old_surface_prepare',MOD/'build/wall-surface/prepare.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    # The shortcut build was installed while this task was running. Freeze its
    # exact published source and keep that input behavior in both A/B variants.
    # Never follow a freshly regenerated candidate directory without checking it.
    for name,pin in KEY_PINS.items():
        owned=KEYS/name
        if not owned.exists():
            source=MOD/'build/keybind-output/src'/name
            assert hashlib.sha256(source.read_bytes()).hexdigest()==pin,'Published shortcut source changed'
            owned.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,owned)
        assert hashlib.sha256(owned.read_bytes()).hexdigest()==pin,'Frozen shortcut source changed'
    published=(KEYS/'RealisticVisionMod.as').read_text(encoding='utf-8-sig')
    for variant in ['baseline','candidate']:
        target=OUT/variant/'src';shutil.copytree(BASE,target,dirs_exist_ok=True)
        for name in KEY_PINS:
            (target/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(KEYS/name,target/name)
        if variant=='candidate':
            (target/'RealisticVisionMod.as').write_text(upgrade(old.integrate(published)),encoding='utf-8')
            shutil.copyfile(MOD/'src/RVWallSurface.as',target/'RVWallSurface.as');locales(target,from_as=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--integrate-main',action='store_true');args=parser.parse_args()
    if args.integrate_main:
        main=MOD/'src/RealisticVisionMod.as'
        main.write_text(upgrade(main.read_text(encoding='utf-8-sig')),encoding='utf-8');locales(MOD/'src')
    prepare();print('Prepared wall option candidate; installed files untouched')
