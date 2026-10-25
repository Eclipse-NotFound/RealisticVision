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
  private var ready:int=0,passed:int=0,failed:int=0;
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
   var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   loc.lDist1=150;loc.lDist2=600;
   var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;
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
   for each(var dim:Number in [0,0.35,0.6,1])for each(var soft:Number in [0,20])for each(var bright:Boolean in [false,true]){
    var a:Object=fixture(BaselineVision,dim,soft,bright),b:Object=fixture(RealisticVisionMod,dim,soft,bright);
    for(var frame:int=0;frame<24;frame++){
     a.loc.gg.X=b.loc.gg.X=200+int(frame/3)*43;
     if(frame==5){a.loc.getTile(10,8).opac=b.loc.getTile(10,8).opac=0;}
     if(frame==7){a.loc.getTile(7,10).visi=b.loc.getTile(7,10).visi=.27;}
     if(frame==14){a.m.cfgDim=b.m.cfgDim=.35;}
     if(frame==17){a.m.cfgDim=b.m.cfgDim=.6;}
     if(frame==20){a.m.resetOff();b.m.resetOff();}
     step(a);step(b);
     var label:String=dim+"/"+soft+"/"+bright+"/"+frame;
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
     if(b.m.classicLogicInterpolated)ready++;
     check(same(a.m.fogBmp,b.m.fogBmp)&&same(a.m.classicWallShade,b.m.classicWallShade),"lazy leaves display "+label);
    }
    b.m.resetOff();a.m.resetOff();
   }
   check(ready>0,"private small-room interpolation actually used");trace("READY "+ready);
   trace("PASS "+passed+" exact display, canonical field, moving/new mask and terrain checks");
  }
 }
}
