package {
 import flash.display.*;
 import flash.desktop.NativeApplication;
 import flash.geom.*;
 import fe.World;
 import fe.loc.Tile;
 import fe.unit.Unit;
 import fe.unit.UnitPlayer;
 import fe.graph.Grafon;
 public class LazyClassicChecks extends Sprite {
  private var roomW:int,roomH:int; private var ready:int=0,passed:int=0,failed:int=0;
  public function LazyClassicChecks(){try{run();}catch(e:Error){failed++;trace("FAIL "+e+" "+e.getStackTrace());}trace("LAZY COMPLETE passed="+passed+" failed="+failed);NativeApplication.nativeApplication.exit(failed?1:0);}
  private function check(ok:Boolean,label:String):void {if(!ok){failed++;trace("FAIL "+label);}else passed++;}
  private function same(a:BitmapData,b:BitmapData):Boolean {var d:Object=a.compare(b);if(d is BitmapData){d.dispose();return false;}return d===0;}
  private function sameCanonical(a:BitmapData,b:BitmapData,area:Rectangle,label:String):Boolean {
   var inside:int=0,outside:int=0;
   for(var y:int=0;y<a.height;y++)for(var x:int=0;x<a.width;x++)if(a.getPixel32(x,y)!=b.getPixel32(x,y)){
    if(area.contains(x,y)){if(inside==0)trace("CANONICAL FIRST INSIDE "+label+" @"+x+","+y+" "+a.getPixel32(x,y).toString(16)+"/"+b.getPixel32(x,y).toString(16));inside++;}else outside++;
   }
   if(inside||outside)trace("CANONICAL DELTA "+label+" queried="+inside+" unusedPadding="+outside);
   return inside==0;
  }
  private function fixture(cls:Class,dim:Number,soft:Number,bright:Boolean):Object {
   Tile.tileX=Tile.tileY=40;World.fps=30;
   var loc:MotionLocation=new MotionLocation(roomW,roomH);loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   loc.lDist1=150;loc.lDist2=600;
   var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;w.cam={vx:0,vy:0,scaleV:1,screenX:640,screenY:400};
   w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   var m:*=new cls();m.mswRegistered=true;m.cfgMode="classic";m.cfgDim=dim;m.cfgSoftClassic=soft;m.cfgWallBright=bright;
   return {m:m,w:w,loc:loc};
  }
  private function step(o:Object):void {World.w=o.w;o.m.frameCount++;o.m.onFrameInner();}
  private function makeMask(o:Object,x:int,y:int):Object {
   var u:Unit=new Unit();u.X=x;u.Y=y;u.scX=60;u.scY=70;u.fraction=2;u.sost=1;u.vis=new MovieClip();o.w.grafon.visObjs[2].addChild(u.vis);
   o.m.applyMask(o.w,u,o.m.unitBBox(o.loc,u));return {u:u,rec:o.m.unitVis[u]};
  }
  private function run():void {
   for each(var size:Array in [[24,18],[48,25],[49,25],[48,26]]){
   roomW=size[0];roomH=size[1];var readyBefore:int=ready;
   for each(var dim:Number in [0,0.35,0.6,1])for each(var soft:Number in [0,20])for each(var bright:Boolean in [false,true]){
    var a:Object=fixture(BaselineVision,dim,soft,bright),b:Object=fixture(RealisticVisionMod,dim,soft,bright);
    for(var frame:int=0;frame<32;frame++){
     a.loc.gg.X=b.loc.gg.X=200+int(frame/3)*43;
     if(frame==5){a.loc.getTile(10,8).opac=b.loc.getTile(10,8).opac=0;}
     if(frame==7){a.loc.getTile(7,10).visi=b.loc.getTile(7,10).visi=.27;}
     if(frame==14){a.m.setVisualSetting("dim",.35);b.m.setVisualSetting("dim",.35);}
     if(frame==17){
      for each(var change:Array in [["dim",.6],["soft_classic",20],["viewscale",1.5]]){
       a.m.setVisualSetting(change[0],change[1]);b.m.setVisualSetting(change[0],change[1]);
      }
     }
     if(frame==20){a.m.resetOff();b.m.resetOff();}
     if(frame==23 || frame==26){
      a.m.cfgMode=b.m.cfgMode=frame==23?"current":"classic";
      a.m.curLoc=b.m.curLoc=null; // Same invalidation as the mode menu.
     }
     if(frame==29){
      for each(var o:Object in [a,b]){
       o.loc=new MotionLocation(roomW,roomH);o.loc.gg=new UnitPlayer();
       o.loc.gg.X=200;o.loc.gg.Y=500;o.loc.gg.scY=40;o.loc.lDist1=150;o.loc.lDist2=600;
       o.w.loc=o.loc;o.w.gg=o.loc.gg;
      }
     }
     step(a);step(b);
     var label:String=roomW+"x"+roomH+"/"+dim+"/"+soft+"/"+bright+"/"+frame;
     check(same(a.m.fogBmp,b.m.fogBmp)&&same(a.m.classicWallShade,b.m.classicWallShade),"display "+label);
     check(JSON.stringify(a.m.memCur)==JSON.stringify(b.m.memCur)&&JSON.stringify(a.m.fov)==JSON.stringify(b.m.fov),"logic/fade "+label);
     // Masks request disjoint/overlapping areas, then a unit moves again with
     // no fog update: demand must extend the current generation immediately.
     for each(var pos:Array in [[180,420],[640,500],[800,600],[180,420]]){
      var ar:Object=makeMask(a,pos[0],pos[1]),br:Object=makeMask(b,pos[0],pos[1]);
      check(same(ar.rec.m2d,br.rec.m2d)&&same(ar.rec.m2e,br.rec.m2e),"mask "+label+" @"+pos);
      check(same(a.m.fogCache,b.m.fogCache),"exact published extent after each query "+label+" @"+pos);
      check(same(a.m.fogBmp,b.m.fogBmp),"query retains fog display "+label+" @"+pos);
      a.m.clearMask(ar.u);b.m.clearMask(br.u);
     }
     check(same(a.m.fogCache,b.m.fogCache),"entire published field identical "+label);
     check(String(a.m.classicLogicTiles)==String(b.m.classicLogicTiles),"same published tile flags "+label);
     for each(var request:Array in [[0,0,1,1],[roomW-1,roomH-1,1,1],[10,8,2,2],[roomW-2,0,2,2]]){
      a.m.classicLogicRegion(new Rectangle(request[0],request[1],request[2],request[3]));
      b.m.classicLogicRegion(new Rectangle(request[0],request[1],request[2],request[3]));
      check(same(a.m.fogCache,b.m.fogCache),"edge query entire published field "+label+" @"+request);
      check(same(a.m.fogBmp,b.m.fogBmp),"edge query retains display "+label+" @"+request);
      check(String(a.m.classicLogicTiles)==String(b.m.classicLogicTiles),"edge query flags "+label+" @"+request);
     }
     if(b.m.classicLogicInterpolated)ready++;
     check(same(a.m.fogBmp,b.m.fogBmp)&&same(a.m.classicWallShade,b.m.classicWallShade),"lazy leaves display "+label);
    }
    b.m.resetOff();a.m.resetOff();
   }
   check((roomW<=48 && roomH<=25)?ready>readyBefore:ready==readyBefore,"correct small/large route "+roomW+"x"+roomH);
   trace("SIZE "+roomW+"x"+roomH+" privateReady="+(ready-readyBefore));
   }
   check(ready>0,"private small-room interpolation actually used");trace("READY "+ready);
   trace("PASS "+passed+" exact display, canonical field, moving/new mask and terrain checks");
  }
 }
}
