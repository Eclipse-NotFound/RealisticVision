package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import flash.geom.*;
  import flash.utils.ByteArray;
  import flash.utils.getTimer;
  import fe.World;
  import fe.loc.Tile;
  import fe.graph.Grafon;
  import fe.unit.UnitPlayer;
  public class WallHarness extends Sprite {
    private var failures:int=0;
    public function WallHarness() {
      try {run();} catch(e:Error) {failures++;trace(e.getStackTrace());}
      trace("WALL_TESTS "+(failures?"FAIL":"PASS")+" failures="+failures);
      NativeApplication.nativeApplication.exit(failures?1:0);
    }
    private function check(ok:Boolean,msg:String):void {if(!ok) failures++;trace((ok?"PASS ":"FAIL ")+msg);}
    private function fixture(mode:String):Object {
      Tile.tileX=Tile.tileY=40; World.fps=30;
      var loc:FixtureLocation=new FixtureLocation();
      loc.gg=new UnitPlayer();loc.gg.X=100;loc.gg.Y=100;loc.gg.scY=40;
      var w:World=new World(); w.loc=loc;w.gg=loc.gg;w.black=true;
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();
      w.grafon.visual.addChild(w.grafon.visLight);World.w=w;
      var m:RealisticVisionMod=new RealisticVisionMod();m.cfgMode=mode;
      m.resetRoom(w,loc);
      for(var i:int=0;i<120;i++) {
        m.fov[i]=2; m.explored[i]=1; m.br[i]=1; m.litArr[i]=1;m.visCur[i]=1;
      }
      m.eyeX=100;m.eyeY=80;
      return {m:m,w:w,loc:loc};
    }
    private function restoreNative(o:Object):void {
      for(var y:int=0;y<10;y++) for(var x:int=0;x<12;x++)
        o.loc.getTile(x,y).visi=o.loc.getTile(x,y).t_visi=(y>=4 && y<=6)?0:1;
    }
    private function render(o:Object):BitmapData {
      var m:RealisticVisionMod=o.m;
      // onFrameInner marks the field dirty whenever it requests a new FOV.
      m.fogDirty=true;m.fovVersion++;
      for(var i:int=0;i<24;i++) {
        m.frameCount++;
        if(m.cfgMode=="classic") m.applyVisionClassic(o.w,o.loc,i==0);
        else m.applyVision(o.w,o.loc,i==0);
      }
      var b:BitmapData=new BitmapData(480,400,false,0xffffff);
      b.draw(m.fogVis,null,null,null,null,true);return b;
    }
    private function nativeImage(o:Object):BitmapData {
      var raw:BitmapData=new BitmapData(13,12,true,0xff000000);
      for(var y:int=1;y<10;y++) for(var x:int=1;x<12;x++)
        raw.setPixel32(x,y+1,uint(Math.floor((1-o.loc.getTile(x,y).visi)*255))<<24);
      var bmp:Bitmap=new Bitmap(raw,"auto",true);bmp.scaleX=bmp.scaleY=40;bmp.x=-20;bmp.y=-60;
      var s:Sprite=new Sprite();s.addChild(bmp);
      var b:BitmapData=new BitmapData(480,400,false,0xffffff);b.draw(s,null,null,null,null,true);return b;
    }
    private function emit(name:String,b:BitmapData):void {
      var bytes:ByteArray=b.encode(b.rect,new PNGEncoderOptions());var hex:String="";
      for(var i:int=0;i<bytes.length;i++){var h:String=bytes[i].toString(16);hex+=(h.length==1?"0":"")+h;}
      trace("PNG "+name+" "+hex);
    }
    private function run():void {
      var o:Object=fixture("current");
      check(o.loc.getTile(6,2).visi==1,"current room entry preserves native brightness");
      restoreNative(o);
      var ref:BitmapData=nativeImage(o);emit("reference",ref);
      var cur:BitmapData=render(o);emit("current",cur);
      check(o.loc.getTile(6,4).visi==0,"current render preserves black wall corner in game state");
      var maxDiff:int=0;
      for(var y:int=123;y<277;y++) maxDiff=Math.max(maxDiff,Math.abs((cur.getPixel(220,y)&255)-(ref.getPixel(220,y)&255)));
      check(maxDiff<=7,"current wall profile matches native: max brightness delta="+maxDiff);
      o.m.cfgMode="classic";o.m.lastA=null;
      var switched:BitmapData=render(o);emit("switched",switched);
      check((switched.getPixel(220,200)&255)<=2,"current to classic keeps wall black core");
      o=fixture("classic");restoreNative(o);
      var classic:BitmapData=render(o);emit("classic",classic);
      maxDiff=0;
      for(y=120;y<280;y++) maxDiff=Math.max(maxDiff,Math.abs((classic.getPixel(220,y)&255)-(ref.getPixel(220,y)&255)));
      check(maxDiff<=2,"classic visible wall profile matches native: delta="+maxDiff);
      o.loc.getTile(6,3).visi=0.1;o.loc.getTile(6,3).t_visi=0.1;
      o.m.fov[6+3*12]=0;
      render(o);
      var a:int=o.m.classicRaw.getPixel32(6,4)>>>24;
      check(a>=245,"classic remembered weak light only darkens: alpha="+a+" expected about 246");
      for each(var mode:String in ["current","classic"]) {
        for each(var layout:String in ["horizontal","vertical","corner"]) {
          o=fixture(mode);
          for(var yy:int=0;yy<10;yy++) for(var xx:int=0;xx<12;xx++) {
            var t:Tile=o.loc.getTile(xx,yy);
            t.opac=layout=="horizontal"?(yy>=3 && yy<=6?1:0):
              layout=="vertical"?(xx>=3 && xx<=6?1:0):(xx>=3 && xx<=6 && yy>=3 && yy<=6?1:0);
            t.phis=t.opac?1:0;
            // Includes black, weak light and gradients sourced by adjacent FLOOR corners.
            t.visi=t.t_visi=((xx*23+yy*37)%11)/10;
          }
          ref=nativeImage(o);
          var lit:BitmapData=render(o);
          maxDiff=wallDifference(o,lit,ref,1);
          check(maxDiff<=1,mode+" "+layout+" full wall pixels match native: delta="+maxDiff);
          for(var k:int=0;k<120;k++) o.m.fov[k]=0;
          var mem:BitmapData=render(o);
          maxDiff=wallDifference(o,mem,ref,0.35);
          check(maxDiff<=2,mode+" "+layout+" memory preserves weak floor-corner light: delta="+maxDiff);
          if(layout=="horizontal") emit(mode+"-memory",mem);
          o.loc.retDark=true;
          var darkRoom:BitmapData=render(o);
          check(wallDifference(o,darkRoom,ref,1)<=1,mode+" "+layout+" retDark follows native light");
        }
        // Native lighting changes while player/FOV stay fixed; wall layer must keep up.
        o=fixture(mode);restoreNative(o);render(o);
        for(xx=0;xx<12;xx++) o.loc.getTile(xx,3).visi=0.25;
        ref=nativeImage(o);
        o.m.frameCount+=2;
        if(mode=="current") o.m.applyVision(o.w,o.loc,false);
        else {o.m.frameCount=100;o.m.applyVisionClassic(o.w,o.loc,false);}
        var stationary:BitmapData=new BitmapData(480,400,false,0xffffff);
        stationary.draw(o.m.fogVis,null,null,null,null,true);
        check(wallDifference(o,stationary,ref,1)<=1,mode+" stationary native lighting refresh");
        check(o.loc.getTile(6,3).visi==0.25,mode+" leaves native light untouched after refresh");
        // Destruction must remove the old wall clip and leave native state untouched.
        for(xx=0;xx<12;xx++) for(yy=0;yy<10;yy++) {
          o.loc.getTile(xx,yy).opac=0;o.loc.getTile(xx,yy).phis=0;
          o.loc.getTile(xx,yy).visi=o.loc.getTile(xx,yy).t_visi=1;
        }
        var destroyed:BitmapData=render(o);
        check((destroyed.getPixel(220,200)&255)>=250,mode+" removed wall has no stale black mask");
        // A transmitting door may boost DISPLAY but must never write the two native fields.
        o=fixture(mode);restoreNative(o);o.loc.getTile(5,2).visi=o.loc.getTile(5,2).t_visi=0.12;
        o.m.fov[5+2*12]=1;render(o);
        // Older implementation invokes doorBoost after classic drawing in onFrameInner.
        if(mode=="classic" && "doorBoost" in o.m) o.m["doorBoost"](o.w,o.loc);
        check(o.loc.getTile(5,2).visi==0.12 && o.loc.getTile(5,2).t_visi==0.12,mode+" door leaves native fields untouched");
        // Same-size room replacement, then non-integer camera scale: complementary clips
        // must still select exactly one layer and leave no stale horizontal wall.
        o=fixture(mode);restoreNative(o);render(o);
        var next:FixtureLocation=new FixtureLocation();next.id="second-room";next.gg=o.loc.gg;
        for(yy=0;yy<10;yy++)for(xx=0;xx<12;xx++) {
          t=next.getTile(xx,yy);t.opac=(xx>=3 && xx<=6)?1:0;t.phis=t.opac?1:0;
          t.visi=t.t_visi=(xx>=4 && xx<=6)?0:1;
        }
        o.loc=next;o.w.loc=next;o.m.resetRoom(o.w,next);
        for(k=0;k<120;k++){o.m.fov[k]=2;o.m.explored[k]=1;o.m.br[k]=1;o.m.visCur[k]=1;}
        ref=nativeImage(o);var swapped:BitmapData=render(o);
        check(wallDifference(o,swapped,ref,1)<=1,mode+" same-size room replacement");
        // Uniform 50% light on every tile: any bright seam or doubled mask is measurable.
        for(yy=0;yy<10;yy++)for(xx=0;xx<12;xx++) {
          t=next.getTile(xx,yy);t.visi=t.t_visi=0.5;
          o.m.fov[xx+yy*12]=0;o.m.explored[xx+yy*12]=1;o.m.memCur[xx+yy*12]=1;
        }
        o.m.cfgDim=0.5;
        // For visible-wall profile scaling, use a native comparison with memory disabled.
        for(k=0;k<120;k++){o.m.fov[k]=2;o.m.memCur[k]=0;}
        render(o);ref=nativeImage(o);
        for each(var scale:Number in [0.8,1.25]) {
          var sm:Matrix=new Matrix(scale,0,0,scale,0,0);
          var scaled:BitmapData=new BitmapData(int(480*scale),int(400*scale),false,0xffffff);
          scaled.draw(o.m.fogVis,sm,null,null,null,true);
          // Mid-wall, away from floor boundary, matches the native bitmap at this scale.
          var expected:int=128;
          check(Math.abs((scaled.getPixel(int(200*scale),int(200*scale))&255)-expected)<=2,mode+" camera scale "+scale+" wall brightness");
        }
      }
      o=fixture("current");restoreNative(o);
      for(xx=0;xx<12;xx++)o.loc.getTile(xx,3).visi=0.1;
      render(o);var oldVersion:int=o.m.fovVersion;
      for(xx=0;xx<12;xx++)o.loc.getTile(xx,3).visi=1;
      o.m.applyVision(o.w,o.loc,false);
      check((o.m.fogCache.getPixel32(4+5*8,4+3*8)>>>24)<140 && o.m.fovVersion>oldVersion,
        "current stationary wall light refreshes partial-enemy mask cache");
      for each(mode in ["current","classic"]) {
        o=fixture(mode);restoreNative(o);render(o);
        var started:int=getTimer();
        for(var frame:int=0;frame<120;frame++) {
          o.m.frameCount=frame;o.m.fogDirty=(frame%3==0);
          if(mode=="current")o.m.applyVision(o.w,o.loc,frame%3==0);
          else o.m.applyVisionClassic(o.w,o.loc,frame%3==0);
        }
        trace("PERF "+mode+" 120 render updates ms="+(getTimer()-started)+" fixture=12x10");
      }
    }
    private function wallDifference(o:Object,actual:BitmapData,reference:BitmapData,scale:Number):int {
      var delta:int=0;
      for(var y:int=0;y<400;y++) for(var x:int=0;x<480;x++) {
        if(o.loc.getTile(int(x/40),int(y/40)).opac<1) continue;
        delta=Math.max(delta,Math.abs((actual.getPixel(x,y)&255)-Math.round((reference.getPixel(x,y)&255)*scale)));
      }
      return delta;
    }
  }
}
