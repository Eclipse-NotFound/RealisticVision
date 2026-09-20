package {
  import flash.display.*;
  import flash.desktop.NativeApplication;
  import flash.geom.*;
  import fe.World;
  import fe.loc.Tile;
  import fe.unit.Unit;
  import fe.unit.UnitPlayer;
  import fe.graph.Grafon;
  public class SoftHarness extends Sprite {
    private var failures:int=0;
    public function SoftHarness(){
      try{run();}catch(e:Error){failures++;trace(e.getStackTrace());}
      trace("MOTION "+(failures?"RED":"GREEN")+" soft assertions failures="+failures);
      trace("MOTION COMPLETE");NativeApplication.nativeApplication.exit(failures?1:0);
    }
    private function check(v:Boolean,msg:String):void{if(!v)failures++;trace((v?"PASS ":"FAIL ")+msg);}
    private function fixture():Object {
      Tile.tileX=Tile.tileY=40;World.fps=30;
      var loc:MotionLocation=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
      var w:World=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;
      w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();
      w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
      var m:RealisticVisionMod=new RealisticVisionMod();m.mswRegistered=true;
      return {m:m,w:w,loc:loc};
    }
    private function step(o:Object):void{World.w=o.w;o.m.frameCount++;o.m.onFrameInner();}
    private function warm(o:Object):void{for(var i:int=0;i<40;i++)step(o);}
    private function same(a:BitmapData,b:BitmapData):Boolean{
      var d:Object=a.compare(b),ok:Boolean=d is uint && uint(d)==0;if(d is BitmapData)BitmapData(d).dispose();return ok;
    }
    private function run():void {
      var o:Object=fixture(),m:RealisticVisionMod=o.m;
      step(o);var last:BitmapData=m.fogBmp.clone(),fadeChanges:int=0;
      for(var k:int=0;k<12;k++){step(o);if(!same(last,m.fogBmp))fadeChanges++;last.dispose();last=m.fogBmp.clone();}
      check(fadeChanges>=8,"stationary startup fade reaches display: "+fadeChanges);
      warm(o);
      var p:Object=fixture();p.m.curBlur.blurX=p.m.curBlur.blurY=6;warm(p);
      check(same(m.fogCache,p.m.fogCache)&&same(m.currentSight,p.m.currentSight),"blur width leaves raw field and enemy eligibility identical");
      check(JSON.stringify(m.seenSub)==JSON.stringify(p.m.seenSub)&&JSON.stringify(m.explored)==JSON.stringify(p.m.explored),"blur width leaves exploration identical");
      // Independent line/rectangle intersection for the single vertical wall.
      var badSeen:int=0,softOutside:int=0,farGlow:int=0;
      for(var y:int=0;y<18*8;y++)for(var x:int=0;x<24*8;x++){
        var wx:Number=(x+0.5)*5,wy:Number=(y+0.5)*5;
        var enters:Boolean=wx>400 && (470+(wy-470)*200/(wx-200)>=240) && (470+(wy-470)*240/(wx-200)<=440);
        if(wx>=440 && enters && m.seenSub[x+y*m.subW]==1)badSeen++;
        var a:int=m.fogCache.getPixel32(4+x,4+y)>>>24,b:int=m.fogBmp.getPixel32(4+x,4+y)>>>24;
        if(a==255 && b<255){
          softOutside++;
          var near:Boolean=false;
          for(var dy:int=-8;dy<=8&&!near;dy++)for(var dx:int=-8;dx<=8;dx++)
            if((m.fogCache.getPixel32(4+x+dx,4+y+dy)>>>24)<255){near=true;break;}
          if(!near)farGlow++;
        }
      }
      check(badSeen==0,"no false seen subcells behind wall: "+badSeen);
      check(softOutside>0 && farGlow==0,"intentional soft band has bounded support: pixels="+softOutside+" distant="+farGlow);
      // Cache equals uncached DDA for partial opacity/water, diagonals and out-of-room rays.
      o.loc.getTile(6,8).opac=0.3;o.loc.getTile(7,9).water=1;o.loc.opacWater=0.45;
      m.prepareOcclusion(o.loc);var diffs:int=0;
      for(k=0;k<1000;k++){
        var tx:int=(k*17%28)-2,ty:int=(k*11%22)-2;
        wx=(tx+0.15+(k%7)*0.1)*40;wy=(ty+0.25)*40;
        m.rayBatch=false;var live:Number=m.castRay(o.loc,200,470,wx,wy,tx,ty);
        m.rayBatch=true;var cached:Number=m.castRay(o.loc,200,470,wx,wy,tx,ty);
        if(live!==cached)diffs++;
      }
      m.rayBatch=false;check(diffs==0,"cached/live rays match in 1000 door/water/out-of-bounds cases");
      var radius:Object=fixture();radius.loc.lDist1=220;radius.loc.lDist2=700;warm(radius);
      var distanceErrors:int=0;
      for(y=8;y<112;y++)for(x=8;x<64;x++){
        var dist:Number=Math.sqrt(Math.pow((x+0.5)*5-200,2)+Math.pow((y+0.5)*5-470,2));
        var expected:int=Math.round((1-Math.max(0.35,dist<=220?1:(700-dist)/480))*255);
        if(Math.abs((radius.m.fogCache.getPixel32(4+x,4+y)>>>24)-expected)>1)distanceErrors++;
      }
      check(distanceErrors==0,"short view-distance falloff matches independent formula: "+distanceErrors);
      step(o);var old:int=m.fovVersion;o.loc.getTile(6,8).opac=0.6;step(o);
      check(m.fovVersion>old,"stationary partial-door change refreshes immediately");
      old=m.fovVersion;o.loc.opacWater=0.7;step(o);check(m.fovVersion>old,"stationary water opacity refreshes immediately");
      old=m.fovVersion;o.loc.getTile(10,7).opac=0;step(o);check(m.fovVersion>old&&!m.wallTopology[10+7*24],"broken wall updates geometry immediately");
      // Mask draws no eligible alpha into hidden samples, including a bright memory setting.
      o=fixture();m=o.m;m.cfgDim=0.9;warm(o);
      var u:Unit=new Unit();u.X=650;u.Y=440;u.scX=80;u.scY=80;u.vis=new MovieClip();u.hpbar=new Sprite();
      var bb:Array=m.unitBBox(o.loc,u);m.applyMask(o.w,u,bb);
      var rec:Object=m.unitVis[u],leaks:int=0,fades:int=0;
      for(y=0;y<rec.m2e.height;y++)for(x=0;x<rec.m2e.width;x++){
        a=rec.m2d.getPixel32(x,y)>>>24;b=rec.m2e.getPixel32(x,y)>>>24;
        if(a==0&&b>0)leaks++;if(b>0&&b<255)fades++;
      }
      check(leaks==0&&fades>0,"enemy mask fades inward without hidden-sample leakage: "+leaks+" fades="+fades);
      // All coarse centers lit is insufficient to bypass the subcell mask.
      for(k=0;k<m.fov.length;k++)m.fov[k]=2;
      check(m.enemyState(o.loc,u)==2,"all-lit tile centers still respect partial subcell occlusion");
      m.clearMask(u);check(u.vis.mask==null&&rec.m2.parent==null,"mask cleanup leaves no white shape");
      // Same dimensions, different room and mode: no stale opacity or sight.
      var next:MotionLocation=new MotionLocation();next.id="other";next.gg=o.loc.gg;next.getTile(10,7).opac=0;
      o.loc=next;o.w.loc=next;step(o);check(m.rayLoc===next&&!m.wallTopology[10+7*24],"same-size room replaces occlusion snapshot");
      m.cfgMode="classic";m.resetRoom(o.w,next);step(o);
      m.cfgMode="current";m.resetRoom(o.w,next);step(o);
      check(m.rayLoc===next&&!m.fogBlurPending,"classic/current switch rebuilds and displays same frame");
      next.spaceX=18;next.spaceY=24;m.resetRoom(o.w,next);step(o);
      check(m.rayWidth==18&&m.rayHeight==24&&m.currentSight.width==152,"equal-area different dimensions rebuild all buffers");
    }
  }
}
