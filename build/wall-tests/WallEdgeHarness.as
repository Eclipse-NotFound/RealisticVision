package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import flash.geom.*;
  import flash.utils.ByteArray;
  import fe.World;
  import fe.loc.Tile;
  import fe.graph.Grafon;
  import fe.unit.UnitPlayer;
  import fe.unit.Unit;
  // Smallest training-room pattern: one 40x80 block and an eye below/right.
  // The measured contour is outside the wall, where the old wall tests skipped it.
  public class WallEdgeHarness extends Sprite {
    public function WallEdgeHarness() {
      try { run(); } catch(e:Error) { trace("WALL_EDGE_TESTS FAIL "+e.getStackTrace());NativeApplication.nativeApplication.exit(1); }
    }
    private function run():void {
      Tile.tileX=Tile.tileY=40;World.fps=30;
      var loc:FixtureLocation=new FixtureLocation();
      for(var y:int=0;y<10;y++)for(var x:int=0;x<12;x++) {
        var t:Tile=loc.getTile(x,y);t.opac=(x==6 && y>=4 && y<=5)?1:0;t.phis=t.opac?1:0;
        t.visi=t.t_visi=t.opac?0:1;
      }
      loc.gg=new UnitPlayer();loc.gg.X=400;loc.gg.Y=350;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();
      w.grafon.visual.addChild(w.grafon.visLight);World.w=w;
      var m:RealisticVisionMod=new RealisticVisionMod();m.cfgMode="classic";
      m.resetRoom(w,loc);m.computeFov(loc);
      for(var f:int=0;f<24;f++){m.frameCount=f;m.applyVisionClassic(w,loc,f==0);}
      var b:BitmapData=new BitmapData(480,400,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);
      var sampleY:int=159;
      var expected:Number=280+(sampleY-160)*(280-m.eyeX)/(160-m.eyeY);
      var edge:int=-1;
      for(x=200;x<340;x++)if(255-(b.getPixel(x,sampleY)&255)>=128)edge=x;
      var delta:Number=Math.abs(edge-expected);
      trace("EDGE top-right expected="+expected.toFixed(2)+" actual="+edge+" offset="+delta.toFixed(2)+" pixels");
      var hidden:int=b.getPixel(150,60)&255;
      var visible:int=b.getPixel(420,320)&255;
      trace("EDGE interior unexplored="+hidden+" visible="+visible);
      var unit:Unit=new Unit();m.applyMask(w,unit,[0,0,11,9]);
      var unitMask:BitmapData=m.unitVis[unit].m2d;
      var maskErrors:int=0;
      for(y=0;y<80;y++)for(x=0;x<96;x++) {
        var fogAlpha:int=255-(b.getPixel(x*5+2,y*5+2)&255);
        if(Math.abs(fogAlpha-140)>1 && ((unitMask.getPixel32(x,y)>>>24)>0)!=(fogAlpha<140))maskErrors++;
      }
      trace("EDGE partial-enemy mask classification mismatches="+maskErrors);
      var settledVersion:int=m.fovVersion;m.frameCount=100;m.applyVisionClassic(w,loc,false);
      var cacheStable:Boolean=m.fovVersion==settledVersion;
      trace("EDGE stationary settled cache stable="+cacheStable);
      CONFIG::edgeProbes {
        var mismatches:int=0;
        for(y=1;y<9;y++)for(x=1;x<11;x++) {
          if(loc.getTile(x,y).opac>=1)continue;
          var cx:Number=(x+0.5)*40,cy:Number=(y+0.5)*40;
          var dx:Number=cx-m.eyeX,dy:Number=cy-m.eyeY;
          var xt0:Number=(240-m.eyeX)/dx,xt1:Number=(280-m.eyeX)/dx;
          var yt0:Number=(160-m.eyeY)/dy,yt1:Number=(240-m.eyeY)/dy;
          var enters:Number=Math.max(0,Math.min(xt0,xt1),Math.min(yt0,yt1));
          var exits:Number=Math.min(1,Math.max(xt0,xt1),Math.max(yt0,yt1));
          var blocked:Boolean=enters<exits;
          if((m.fov[x+y*12]==0)!=blocked)mismatches++;
        }
        trace("PROBE ray vs geometric rectangle wrong floor centers="+mismatches);
        var legacy:Bitmap=m["classicBmp"] as Bitmap;
        if(!legacy)throw new Error("--probes requires a pre-fix revision");
        legacy.x+=20;legacy.y+=20;
        trace("PROBE floor bitmap +20,+20 contact="+contact(m,sampleY));
        legacy.x-=20;legacy.y-=20;
        legacy.mask=null;m.wallBmp.visible=false;m.floorClip.visible=false;m.wallClip.visible=false;
        trace("PROBE without wall/floor clips contact="+contact(m,sampleY));
      }
      var bytes:ByteArray=b.encode(b.rect,new PNGEncoderOptions());var hex:String="";
      for(var i:int=0;i<bytes.length;i++){var h:String=bytes[i].toString(16);hex+=(h.length==1?"0":"")+h;}
      trace("PNG edge-contact "+hex);
      var ok:Boolean=delta<=4 && hidden<=2 && visible>=253 && maskErrors==0 && cacheStable;
      if(!currentAfterClassic(w,loc,m))ok=false;
      if(!unshadowedWall(w,loc))ok=false;
      if(!rememberedShadowFade(w,loc))ok=false;
      for each(var horizontal:Boolean in [false,true])
        for each(var rightSide:Boolean in [false,true])
          for each(var below:Boolean in [false,true])
            if(!directional(horizontal,rightSide,below,1,0,0))ok=false;
      if(!directional(false,true,true,0.8,13.25,8.5))ok=false;
      if(!directional(false,true,true,1.25,13.25,8.5))ok=false;
      trace("WALL_EDGE_TESTS "+(ok?"PASS":"FAIL")+" block=(240,160)-(280,240), eye=(400,320)");
      NativeApplication.nativeApplication.exit(ok?0:1);
    }
    private function directional(horizontal:Boolean,rightSide:Boolean,below:Boolean,scale:Number,ox:Number,oy:Number):Boolean {
      var xmin:int=240,xmax:int=horizontal?320:280,ymin:int=160,ymax:int=horizontal?200:240;
      var ex:Number=rightSide?420:120,ey:Number=below?320:80;
      var loc:FixtureLocation=new FixtureLocation();
      for(var y:int=0;y<10;y++)for(var x:int=0;x<12;x++) {
        var t:Tile=loc.getTile(x,y);t.opac=(x*40>=xmin && x*40<xmax && y*40>=ymin && y*40<ymax)?1:0;
        t.phis=t.opac?1:0;t.visi=t.t_visi=1;
      }
      loc.gg=new UnitPlayer();loc.gg.X=ex;loc.gg.Y=ey+30;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);World.w=w;
      var m:RealisticVisionMod=new RealisticVisionMod();m.cfgMode="classic";m.resetRoom(w,loc);m.computeFov(loc);
      for(var f:int=0;f<24;f++){m.frameCount=f;m.applyVisionClassic(w,loc,f==0);}
      var b:BitmapData=new BitmapData(int(480*scale+40),int(400*scale+40),false,0xffffff);
      b.draw(m.fogVis,new Matrix(scale,0,0,scale,ox,oy),null,null,null,true);
      var cornerX:Number=rightSide?xmax:xmin,cornerY:Number=below?ymin:ymax;
      var row:int=below?int(Math.floor(cornerY*scale+oy))-1:int(Math.ceil(cornerY*scale+oy));
      var sampleY:Number=(row+0.5-oy)/scale;
      var expected:Number=(cornerX+(sampleY-cornerY)*(cornerX-ex)/(cornerY-ey))*scale+ox;
      // Classic deliberately interpolates one sample per tile. At a grazing corner,
      // that coarse contour can differ from the continuous tangent. Independently
      // intersect the rectangle at grid centers to check phase without pretending
      // the 40px interpolation is an exact polygon shadow.
      var raw:BitmapData=new BitmapData(13,12,true,0xff000000);
      for(y=1;y<10;y++)for(x=1;x<12;x++) {
        var dx:Number=(x+0.5)*40-ex,dy:Number=(y+0.5)*40-ey;
        var x0:Number=(xmin-ex)/dx,x1:Number=(xmax-ex)/dx;
        var y0:Number=(ymin-ey)/dy,y1:Number=(ymax-ey)/dy;
        var enter:Number=Math.max(0,Math.min(x0,x1),Math.min(y0,y1));
        var leave:Number=Math.min(1,Math.max(x0,x1),Math.max(y0,y1));
        raw.setPixel32(x,y+1,enter<leave?0xff000000:0);
      }
      var reference:Sprite=new Sprite();var rb:Bitmap=new Bitmap(raw,"auto",true);
      rb.scaleX=rb.scaleY=40;rb.y=-40;reference.addChild(rb);
      var ref:BitmapData=new BitmapData(b.width,b.height,false,0xffffff);
      ref.draw(reference,new Matrix(scale,0,0,scale,ox,oy),null,null,null,true);
      var found:int=-1,referenceEdge:int=-1;
      for(x=int((xmin-60)*scale+ox);x<int((xmax+60)*scale+ox);x++) {
        if(255-(b.getPixel(x,row)&255)>=128) {
          if(rightSide || found<0)found=x;
        }
        if(255-(ref.getPixel(x,row)&255)>=128 && (rightSide || referenceEdge<0))referenceEdge=x;
      }
      var error:Number=Math.abs(found-referenceEdge);
      var good:Boolean=found>=0 && referenceEdge>=0 && error<=2;
      trace((good?"PASS":"FAIL")+" EDGE "+(horizontal?"horizontal":"vertical")+" eye="+ex+","+ey+" scale="+scale+" centeredFieldDelta="+error.toFixed(2)+" coarseVsTangent="+Math.abs(referenceEdge+0.5-expected).toFixed(2));
      b.dispose();ref.dispose();raw.dispose();return good;
    }
    private function contact(m:RealisticVisionMod,y:int):int {
      var b:BitmapData=new BitmapData(480,400,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);
      var edge:int=-1;
      for(var x:int=200;x<340;x++)if(255-(b.getPixel(x,y)&255)>=128)edge=x;
      b.dispose();return edge;
    }
    private function currentAfterClassic(w:World,loc:FixtureLocation,m:RealisticVisionMod):Boolean {
      // Exercise the real same-size reset and initial fade, not a forced settled frame.
      m.cfgMode="current";m.resetRoom(w,loc);m.computeFov(loc);
      var clean:RealisticVisionMod=new RealisticVisionMod();clean.cfgMode="current";
      clean.roomMem[loc.id]=m.roomMem[loc.id];
      clean.resetRoom(w,loc);clean.computeFov(loc);
      var errors:int=0,padding:int=0;
      for(var f:int=0;f<14;f++) {
        m.frameCount=clean.frameCount=f;
        m.applyVision(w,loc,f==0);clean.applyVision(w,loc,f==0);
        var a:Vector.<uint>=m.fogBmp.getVector(m.fogBmp.rect);
        var b:Vector.<uint>=clean.fogBmp.getVector(clean.fogBmp.rect);
        for(var i:int=0;i<a.length;i++)if(a[i]!=b[i])errors++;
        for(var y:int=0;y<m.fogRaw.height;y++)for(var x:int=0;x<m.fogRaw.width;x++) {
          if(x>=4 && x<100 && y>=4 && y<84)continue;
          if(m.fogRaw.getPixel32(x,y)!=clean.fogRaw.getPixel32(x,y))padding++;
        }
      }
      trace("EDGE classic-to-current initial fade differences="+errors+" padding differences="+padding);
      return errors==0 && padding==0;
    }
    private function unshadowedWall(w:World,loc:FixtureLocation):Boolean {
      var delta:int=0;
      for each(var light:Number in [0.2,0.5,1]) {
        for(var y:int=0;y<10;y++)for(var x:int=0;x<12;x++)loc.getTile(x,y).visi=loc.getTile(x,y).t_visi=light;
        var m:RealisticVisionMod=new RealisticVisionMod();m.cfgMode="classic";m.resetRoom(w,loc);
        for(var i:int=0;i<120;i++){m.fov[i]=2;m.explored[i]=1;}
        for(var f:int=0;f<24;f++){m.frameCount=f;m.applyVisionClassic(w,loc,f==0);}
        var b:BitmapData=new BitmapData(480,400,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);
        for(y=140;y<260;y++)for(x=220;x<300;x++) {
          if(loc.getTile(int(x/40),int(y/40)).opac>=1)continue;
          delta=Math.max(delta,Math.abs((b.getPixel(x,y)&255)-Math.ceil(light*255)));
        }
        b.dispose();
      }
      trace("EDGE wall without adjacent shadow preserves native floor light delta="+delta);
      return delta<=1;
    }
    private function rememberedShadowFade(w:World,loc:FixtureLocation):Boolean {
      var m:RealisticVisionMod=new RealisticVisionMod();m.cfgMode="classic";m.resetRoom(w,loc);
      for(var i:int=0;i<120;i++){m.fov[i]=2;m.explored[i]=1;}
      m.fov[6+3*12]=0;
      for(var f:int=0;f<24;f++){m.frameCount=f;m.applyVisionClassic(w,loc,f==0);}
      var b:BitmapData=new BitmapData(480,400,false,0xffffff);b.draw(m.fogVis,null,null,null,null,true);
      var first:int=b.getPixel(260,159)&255,prev:int=first,step:int=0,backwards:Boolean=false;
      m.fov[6+3*12]=2;
      for(f=0;f<12;f++) {
        m.frameCount=100+f*2;m.applyVisionClassic(w,loc,f==0);
        b.fillRect(b.rect,0xffffff);b.draw(m.fogVis,null,null,null,null,true);
        var now:int=b.getPixel(260,159)&255;
        step=Math.max(step,now-prev);if(now<prev)backwards=true;prev=now;
      }
      b.dispose();
      trace("EDGE remembered shadow fades from="+first+" to="+prev+" maxStep="+step+" monotonic="+!backwards);
      return first<230 && prev>=253 && step<=40 && !backwards;
    }
  }
}
