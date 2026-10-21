package {
 import flash.display.*;
 import flash.desktop.NativeApplication;
 import flash.filesystem.*;
 import fe.World;
 import fe.loc.Tile;
 import fe.unit.UnitPlayer;
 import fe.graph.Grafon;
 import modlocales.vision.RVLocale;
 public class SettingsChecks extends Sprite {
  private var passed:int=0,failed:int=0;
  public function SettingsChecks(){try{run();}catch(e:Error){failed++;trace("FAIL "+e+" "+e.getStackTrace());}trace("SETTINGS COMPLETE passed="+passed+" failed="+failed);NativeApplication.nativeApplication.exit(failed?1:0);}
  private function check(ok:Boolean,s:String):void {if(ok)passed++;else failed++;trace((ok?"PASS ":"FAIL ")+s);}
  private function same(a:BitmapData,b:BitmapData):Boolean {var d:Object=a.compare(b);if(d is BitmapData){d.dispose();return false;}return d===0;}
  private function fixture(cls:Class,mode:String="current",bright:Boolean=false):Object {
   Tile.tileX=Tile.tileY=40;World.fps=30;
   var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;
   w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);
   w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   var m:*=new cls();m.mswRegistered=true;m.cfgMode=mode;m.cfgWallBright=bright;return {m:m,w:w,loc:loc};
  }
  private function step(o:Object,count:int=30):void {World.w=o.w;for(var i:int=0;i<count;i++){o.m.frameCount++;o.m.onFrameInner();}}
  private function native(o:Object):String {var a:Array=[];for each(var t:Tile in o.loc.tiles)a.push(t.visi,t.t_visi,t.opac);return JSON.stringify(a)+o.loc.lDist1+"/"+o.loc.lDist2;}
  private function row(m:*,key:String):Object {for each(var r:Object in m.buildMswItems())if(r.key==key)return r;return null;}
  private function run():void {
   var o:Object,b:Object,m:*,snap:String,seen:String;
   for each(var mode:String in ["classic","current"])for each(var bright:Boolean in [false,true]){
    o=fixture(RealisticVisionMod,mode,bright);b=fixture(BaselineVision,mode,bright);
    for each(var x:int in [200,280,640,200]){
     o.loc.gg.X=b.loc.gg.X=x;step(o);step(b);
     check(same(o.m.fogBmp,b.m.fogBmp),mode+" default fog identical bright="+bright+" x="+x);
     check(same(o.m.fogCache,b.m.fogCache)&&JSON.stringify(o.m.fov)==JSON.stringify(b.m.fov),mode+" default eligibility identical "+bright+" "+x);
    }
   }
   for each(mode in ["classic","current"]){
    o=fixture(RealisticVisionMod,mode);o.loc.lDist1=150;o.loc.lDist2=600;step(o);m=o.m;snap=native(o);
    var logic:BitmapData=(mode=="current"?m.currentSight:m.fogCache).clone();seen=JSON.stringify(m.seenSub)+JSON.stringify(m.explored);
    for each(var dim:Number in [0,1,0.35]){
     m.setVisualSetting("dim",dim);step(o);
     check(same(logic,mode=="current"?m.currentSight:m.fogCache),mode+" brightness independent of enemy mask "+dim);
     check(seen==JSON.stringify(m.seenSub)+JSON.stringify(m.explored),mode+" brightness preserves exploration "+dim);
    }
    for each(var blur:Number in [0,40,20]){
     m.setVisualSetting(mode=="current"?"soft_current":"soft_classic",blur);step(o);
     check(same(logic,mode=="current"?m.currentSight:m.fogCache),mode+" softening independent of enemy mask "+blur);
     check(seen==JSON.stringify(m.seenSub)+JSON.stringify(m.explored),mode+" softening preserves exploration "+blur);
    }
    check(native(o)==snap,mode+" visual settings never write native state");logic.dispose();
    o=fixture(RealisticVisionMod,mode);for each(var clearTile:Tile in o.loc.tiles){clearTile.opac=clearTile.phis=0;}
    step(o);m=o.m;var remembered:int=16+11*24;
    check(m.explored[remembered]==1,mode+" brightness fixture starts genuinely explored");
    for(var barrier:int=0;barrier<o.loc.spaceY;barrier++){o.loc.getTile(10,barrier).opac=1;o.loc.getTile(10,barrier).phis=1;}
    m.setVisualSetting("dim",0);step(o);var dark:int=m.fogBmp.getPixel32(4+16*8+4,4+11*8+4)>>>24;
    m.setVisualSetting("dim",1);step(o);var light:int=m.fogBmp.getPixel32(4+16*8+4,4+11*8+4)>>>24;
    check(dark==255&&light==0&&m.fov[remembered]==0,mode+" slider visibly spans black to bright while region remains out of sight");
    // Empty room: an independently placed target outside 1x but inside 2x.
    o=fixture(RealisticVisionMod,mode);for each(var tile:Tile in o.loc.tiles){tile.opac=tile.phis=0;tile.visi=tile.t_visi=0;}
    o.loc.lDist1=120;o.loc.lDist2=300;step(o);m=o.m;snap=native(o);var index:int=16+11*24;
    check(m.fov[index]==0,mode+" distant target initially excluded");
    m.setVisualSetting("viewscale",2);step(o);
    check(m.fov[index]>0 && m.explored[index]==1,mode+" 2x admits unobstructed distant target");
    check(m.locDist1==240 && m.locDist2==600,mode+" both falloff radii scale");
    check(m.explorationLight(o.loc,16,11)>0,mode+" extended light stays in mod-owned field");
    m.setVisualSetting("viewscale",0.5);step(o);
    check(m.fov[index]==0&&m.explored[index]==1,mode+" shrink removes current sight but keeps memory");
    check(native(o)==snap,mode+" range never writes native light or distances");
    var rememberedLight:Array=m.rangeLight;
    var visited:MotionLocation=new MotionLocation();visited.id="visited-range-room";visited.gg=o.loc.gg;
    var originalRoom:MotionLocation=o.loc;o.loc=visited;o.w.loc=visited;step(o);
    o.loc=originalRoom;o.w.loc=originalRoom;step(o);
    check(m.rangeLight===rememberedLight,mode+" mod corner-light memory survives a room round trip");
    for(var y:int=0;y<o.loc.spaceY;y++){o.loc.getTile(10,y).opac=1;o.loc.getTile(10,y).phis=1;}
    m.setVisualSetting("viewscale",3);step(o);
    check(m.fov[index]==0,mode+" 3x still cannot see through a solid wall");
    o.loc.lDist1=100;o.loc.lDist2=200;step(o,1);check(m.locDist1==300&&m.locDist2==600,mode+" room distance updates while stationary");
   }
   m=new RealisticVisionMod();
   check(m.buildMswItems().length==11,"eleven controls retain the original eight keys");
   for each(var key:String in ["dim","viewscale","soft_current","soft_classic"]){
    var r:Object=row(m,key);check(r&&RVLocale.translate(r.label,"en")!=r.label&&RVLocale.translate(r.hint,"ru")!=r.hint,"localized control "+key);
   }
   row(m,"dim").set(.75);row(m,"viewscale").set(2.5);row(m,"soft_current").set(35);row(m,"soft_classic").set(15);
   var loaded:RealisticVisionMod=new RealisticVisionMod();loaded.loadConfig();
   check(loaded.cfgDim==.75&&loaded.cfgViewScale==2.5&&loaded.cfgSoftCurrent==35&&loaded.cfgSoftClassic==15,"all preferences save and reload");
   var f:File=File.applicationStorageDirectory.resolvePath("RealisticVision_config.txt"),fs:FileStream=new FileStream();
   fs.open(f,FileMode.WRITE);fs.writeUTFBytes("dim=0.45\nmode=classic\nwallbright=1\n");fs.close();loaded=new RealisticVisionMod();loaded.loadConfig();
   check(loaded.cfgDim==.45&&loaded.cfgMode=="classic"&&loaded.cfgWallBright&&loaded.cfgViewScale==1&&loaded.cfgSoftCurrent==20&&loaded.cfgSoftClassic==0,"old preferences migrate without loss");
   fs.open(f,FileMode.WRITE);fs.writeUTFBytes("dim=NaN\nviewscale=Infinity\nsoft_current=-5\nsoft_classic=9999\n");fs.close();loaded=new RealisticVisionMod();loaded.loadConfig();
   check(loaded.cfgDim==.35&&loaded.cfgViewScale==1&&loaded.cfgSoftCurrent==0&&loaded.cfgSoftClassic==40,"invalid and out-of-range preferences stay bounded");
   o=fixture(RealisticVisionMod);step(o);snap=native(o);o.m.setVisualSetting("viewscale",3);o.m.setModeIndex(0);step(o);
   check(o.m.fogVis.visible==false&&native(o)==snap,"vanilla bypass unaffected by custom settings");
   o.m.resetOff();check(o.m.rangeLight==null&&o.m.rangeRoom==null,"world reset releases custom range light memory");
  }
 }
}
