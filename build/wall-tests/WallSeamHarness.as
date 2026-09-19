package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import flash.geom.*;
  import fe.World;
  import fe.loc.Tile;
  import fe.graph.Grafon;
  import fe.unit.UnitPlayer;
  // A fully remembered room with a three-tile-thick wall and one exposed corner.
  // Measures the adjacent pixels crossing the wall/floor boundary, not wall interiors.
  public class WallSeamHarness extends Sprite {
    public function WallSeamHarness() {
      try {run();} catch(e:Error) {trace("WALL_SEAM_TESTS FAIL "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
    }
    private function run():void {
      Tile.tileX=Tile.tileY=40;World.fps=30;
      var loc:FixtureLocation=new FixtureLocation();
      for(var y:int=0;y<10;y++)for(var x:int=0;x<12;x++) {
        var t:Tile=loc.getTile(x,y);
        t.opac=(x>=6 && x<=8 && y>=3 && y<=6)?1:0;t.phis=t.opac?1:0;
        t.visi=t.t_visi=t.opac>=1 && y>=4?0:1;
      }
      loc.gg=new UnitPlayer();loc.gg.X=100;loc.gg.Y=100;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();
      w.grafon.visual.addChild(w.grafon.visLight);World.w=w;
      var m:RealisticVisionMod=new RealisticVisionMod();m.cfgMode="classic";m.resetRoom(w,loc);
      var failed:Boolean=false;
      for each(var remembered:Boolean in [false,true]) {
        for(var i:int=0;i<120;i++){m.fov[i]=remembered?0:2;m.explored[i]=1;m.memCur[i]=remembered?1:0;}
        for(var f:int=0;f<24;f++){m.frameCount=f;m.applyVisionClassic(w,loc,f==0);}
        for each(var scale:Number in [1,1.3])for each(var offset:Number in [0,0.4]) {
          var b:BitmapData=new BitmapData(700,600,false,0xffffff);
          b.draw(m.fogVis,new Matrix(scale,0,0,scale,offset,offset),null,null,null,true);
          var boundary:int=Math.round(240*scale+offset),row:int=Math.round(200*scale+offset);
          var jump:int=Math.abs((b.getPixel(boundary-1,row)&255)-(b.getPixel(boundary,row)&255));
          var ok:Boolean=jump<=8;
          trace((ok?"PASS":"FAIL")+" SEAM remembered="+remembered+" scale="+scale+" offset="+offset+" adjacent="+(b.getPixel(boundary-1,row)&255)+","+(b.getPixel(boundary,row)&255)+" jump="+jump);
          if(!ok)failed=true;b.dispose();
        }
      }
      CONFIG::seamProbes {probe(m,w,loc);}
      trace("WALL_SEAM_TESTS "+(failed?"FAIL":"PASS"));
      NativeApplication.nativeApplication.exit(failed?1:0);
    }
    private function jump(m:RealisticVisionMod):int {
      var b:BitmapData=new BitmapData(480,400,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);
      var value:int=Math.abs((b.getPixel(239,200)&255)-(b.getPixel(240,200)&255));b.dispose();return value;
    }
    private function probe(m:RealisticVisionMod,w:World,loc:FixtureLocation):void {
      var floor:Bitmap=("classicBmp" in m)?m["classicBmp"]:m.fogBitmap;
      var mask:DisplayObject=floor.mask;
      floor.mask=null;m.wallBmp.visible=false;m.wallClip.visible=false;m.floorClip.visible=false;
      trace("SEAM_PROBE floor field alone jump="+jump(m));
      floor.mask=mask;m.wallBmp.visible=true;m.wallClip.visible=true;m.floorClip.visible=true;
      if("classicMemoryMatrix" in m) {
        var old:Matrix=m["classicMemoryMatrix"];
        m["classicMemoryMatrix"]=m["classicLightMatrix"].clone();
        m.frameCount=100;m.applyVisionClassic(w,loc,true);
        trace("SEAM_PROBE memory on light coordinates jump="+jump(m));
        m["classicMemoryMatrix"]=old;m.applyVisionClassic(w,loc,true);
      }
      m.cfgDim=0;m.frameCount=100;m.applyVisionClassic(w,loc,true);
      trace("SEAM_PROBE remembered brightness zero jump="+jump(m));
      // Identical half-transparent fields make any clip gap measurable on their own.
      for(var y:int=0;y<10;y++)for(var x:int=0;x<12;x++) {
        loc.getTile(x,y).visi=loc.getTile(x,y).t_visi=0.5;
        m.fov[x+y*12]=2;m.memCur[x+y*12]=0;
      }
      m.applyVisionClassic(w,loc,true);
      for each(var offset:Number in [0,0.4]) {
        var b:BitmapData=new BitmapData(700,600,false,0xffffff);
        b.draw(m.fogVis,new Matrix(1.3,0,0,1.3,offset,offset),null,null,null,true);
        var worst:int=0;
        for(y=220;y<260;y++)for(x=309;x<=315;x++)worst=Math.max(worst,Math.abs((b.getPixel(x,y)&255)-128));
        trace("SEAM_PROBE uniform field clip error offset="+offset+" max="+worst);b.dispose();
      }
    }
  }
}
