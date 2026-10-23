package {
 import flash.display.*;import flash.geom.*;import flash.desktop.NativeApplication;import flash.events.Event;
 import fe.World;import fe.loc.Tile;import fe.unit.Unit;import fe.unit.UnitPlayer;import fe.graph.Grafon;
 public class MaskRenderChecks extends Sprite {
  private var a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod();
  private var w:World,loc:MotionLocation,u:Unit,v:Unit,ua:Sprite,ub:Sprite;
  private var frame:int=0,passed:int=0,reuses:int=0,lastRevision:int=0,lastBitmap:BitmapData;
  public function MaskRenderChecks(){try{init();addEventListener(Event.ENTER_FRAME,step);}catch(e:Error){fail(e);}}
  private function init():void {
   Tile.tileX=Tile.tileY=40;World.fps=30;loc=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   w=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.grafon=new Grafon();w.grafon.visual=new Sprite();
   w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   addChild(w.grafon.visObjs[2]);addChild(w.grafon.visObjs[3]);
   u=unit();v=unit();ua=new Sprite();ub=new Sprite();ua.cacheAsBitmap=ub.cacheAsBitmap=true;
   ua.graphics.beginFill(0x32da13);ua.graphics.drawRect(80,0,40,20);ua.graphics.endFill();ub.graphics.copyFrom(ua.graphics);
   w.grafon.visObjs[2].addChild(ua);w.grafon.visObjs[2].addChild(ub);
   for each(var m:* in [a,b]){m.mswRegistered=true;m.resetRoom(w,loc);}
  }
  private function unit():Unit {var n:Unit=new Unit();n.X=440;n.Y=440;n.scX=80;n.scY=80;n.vis=new MovieClip();n.hpbar=new Sprite();w.grafon.visObjs[2].addChild(n.vis);w.grafon.visObjs[3].addChild(n.hpbar);return n;}
  private function same(x:BitmapData,y:BitmapData):Boolean {var d:Object=x.compare(y);var ok:Boolean=d is uint && uint(d)==0;if(d is BitmapData)BitmapData(d).dispose();return ok;}
  private function check(ok:Boolean,label:String):void {if(!ok)throw new Error(label+" frame="+frame);passed++;}
  private function capture(n:Unit,other:Unit,own:Sprite,away:Sprite):BitmapData {
   n.vis.visible=n.hpbar.visible=own.visible=true;other.vis.visible=other.hpbar.visible=away.visible=false;
   var result:BitmapData=new BitmapData(960,720,false,0x334455);result.draw(this);return result;
  }
  private function step(e:Event):void {try{
   var mode:String=frame<144?"classic":"current",blur:Number=[0,1,2,4,6,9][int(frame/24)%6],k:int=frame%24;
   if(k==0)for each(var m:* in [a,b]){m.cfgMode=mode;m.resetRoom(w,loc);m.onFrameInner();}
   for each(m in [a,b]){
    if(m.currentSight==null)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);
    m.classicLogicTiles=null;m.currentSight.fillRect(m.currentSight.rect,0);m.fogCache.fillRect(m.fogCache.rect,0xff000000);
    // Multiple edges move inside a stable region; later frames change bounds.
    var spacing:int=k<12?3:11,offset:int=k*3;
    for(var x:int=0;x<m.currentSight.width;x++)if(int((x+offset)/spacing)%2==0){m.currentSight.fillRect(new Rectangle(x,0,1,m.currentSight.height),0xffffffff);m.fogCache.fillRect(new Rectangle(x,0,1,m.fogCache.height),0);}
    m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.fovVersion++;
   }
   u.X=v.X=440+(k>=16?(k-16)*27.3:0);u.Y=v.Y=440;u.scX=v.scX=k>=20?120:80;
   for each(var n:Unit in [u,v]){
    n.vis.x=n.X;n.vis.y=n.Y;n.vis.graphics.clear();n.vis.graphics.beginFill(0xdf4231+k*7);n.vis.graphics.drawRect(-40,-80,80,80);n.vis.graphics.endFill();
    Sprite(n.hpbar).graphics.clear();Sprite(n.hpbar).graphics.beginFill(0xfae430);Sprite(n.hpbar).graphics.drawRect(n.X-40,n.Y-95,80,8);Sprite(n.hpbar).graphics.endFill();
   }
   a.applyMask(w,u,a.unitBBox(loc,u));b.applyMask(w,v,b.unitBBox(loc,v));
   var ar:Object=a.unitVis[u],br:Object=b.unitVis[v];
   check(same(ar.m2d,br.m2d)&&same(ar.m2e,br.m2e),"exact source/soft pixels");
   // Model a separate weapon mask copying fill references only on revision.
   var am:Shape=new Shape(),bm:Shape;
   if(ua.mask && ua.mask.parent)ua.mask.parent.removeChild(ua.mask);
   am.graphics.copyFrom(Shape(ar.m2).graphics);am.cacheAsBitmap=true;addChild(am);ua.mask=am;
   if(!ub.mask || br.maskRevision!=lastRevision || lastBitmap!==br.m2e){if(ub.mask && ub.mask.parent)ub.mask.parent.removeChild(ub.mask);bm=new Shape();bm.graphics.copyFrom(Shape(br.m2).graphics);bm.cacheAsBitmap=true;addChild(bm);ub.mask=bm;}else reuses++;
   lastRevision=br.maskRevision;lastBitmap=br.m2e;ua.x=ub.x=u.X;ua.y=ub.y=u.Y-45;
   var ca:BitmapData=capture(u,v,ua,ub),cb:BitmapData=capture(v,u,ub,ua);check(same(ca,cb),"body/bar/shared raster weapon render");ca.dispose();cb.dispose();
   if(k==14){a.clearMask(u);b.clearMask(v);a.fovVersion++;b.fovVersion++;a.applyMask(w,u,a.unitBBox(loc,u));b.applyMask(w,v,b.unitBBox(loc,v));check(v.vis.mask===br.m2&&br.m2.parent!=null,"reattach reused shape");}
   if(++frame>=288){check(reuses>150,"reuse path exercised");trace("RENDER COMPLETE passed="+passed+" reused="+reuses);NativeApplication.nativeApplication.exit(0);}
  }catch(error:Error){fail(error);}}
  private function fail(e:Error):void {removeEventListener(Event.ENTER_FRAME,step);trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
 }
}
