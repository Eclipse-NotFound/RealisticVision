package {
 import flash.display.*;import flash.geom.*;import flash.filters.*;import flash.desktop.NativeApplication;import flash.events.Event;import flash.filesystem.*;
 import fe.World;import fe.loc.Tile;import fe.unit.Unit;import fe.unit.UnitPlayer;import fe.graph.Grafon;import fe.weapon.Weapon;
 public class MaskRenderChecks extends Sprite {
  private var a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod();
  private var w:World,loc:MotionLocation,u:Unit,v:Unit,ua:MovieClip,ub:MovieClip,wa:Weapon,wb:Weapon;
  private var frame:int=0,passed:int=0;
  private var roots:Array=[new Sprite(),new Sprite()],layers:Array=[];
  public function MaskRenderChecks(){try{init();addEventListener(Event.ENTER_FRAME,step);}catch(e:Error){fail(e);}}
  private function init():void {
   stage.scaleMode=StageScaleMode.NO_SCALE;stage.align=StageAlign.TOP_LEFT;
   Tile.tileX=Tile.tileY=40;World.fps=30;loc=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   w=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.grafon=new Grafon();w.grafon.visual=new Sprite();
   w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   addChild(w.grafon.visObjs[2]);addChild(w.grafon.visObjs[3]);
   u=unit(roots[0]);v=unit(roots[1]);ua=new MovieClip();ub=new MovieClip();
   for each(var gun:Sprite in [ua,ub])gun.addChild(new Bitmap(new BitmapData(95,17,true,0xff32da13),'auto',true));
   u.vis.parent.addChild(ua);v.vis.parent.addChild(ub);
   wa=new Weapon();wa.owner=u;wa.vis=ua;wb=new Weapon();wb.owner=v;wb.vis=ub;
   for each(var m:* in [a,b]){m.mswRegistered=true;m.resetRoom(w,loc);}
  }
  private function unit(root:Sprite):Unit {addChild(root);var body:Sprite=new Sprite(),bar:Sprite=new Sprite();root.addChild(body);root.addChild(bar);layers.push(body,bar);var n:Unit=new Unit();n.X=440;n.Y=440;n.scX=80;n.scY=80;n.vis=new MovieClip();n.vis.addChild(new Bitmap(new BitmapData(83,79,true,0xffdf4231),'auto',true));n.hpbar=new Sprite();body.addChild(n.vis);bar.addChild(n.hpbar);return n;}
  private function same(x:BitmapData,y:BitmapData):Boolean {var d:Object=x.compare(y);var ok:Boolean=d is uint && uint(d)==0;if(d is BitmapData){trace('DIFF '+BitmapData(d).getColorBoundsRect(0xffffffff,0,false));BitmapData(d).dispose();}return ok;}
  private function check(ok:Boolean,label:String):void {if(!ok)throw new Error(label+' frame='+frame);passed++;}
  private function capture(n:Unit,other:Unit,own:Sprite,away:Sprite):BitmapData {
   var result:BitmapData=new BitmapData(960,720,false,0x334455);result.draw(n.vis.parent.parent);return result;
  }
  private function step(e:Event):void {try{
   var mode:String=frame<360?'classic':'current',blur:Number=[0,1,2,4,6,9][int(frame/24)%6],k:int=frame%24;
   if(k==0)for each(var m:* in [a,b]){m.cfgMode=mode;m.resetRoom(w,loc);m.onFrameInner();}
   for each(m in [a,b]){
    if(m.currentSight==null)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);
    m.classicLogicTiles=null;m.currentSight.fillRect(m.currentSight.rect,0);m.fogCache.fillRect(m.fogCache.rect,0xff000000);
    var spacing:int=k<12?3:11,offset:int=k*3;
    for(var x:int=0;x<m.currentSight.width;x++)if(int((x+offset)/spacing)%2==0){m.currentSight.fillRect(new Rectangle(x,0,1,m.currentSight.height),0xffffffff);m.fogCache.fillRect(new Rectangle(x,0,1,m.fogCache.height),0);}
    m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.fovVersion++;
   }
   var zoom:Number=[1,1,.5,.75,1.25,1.5,2,1][int(frame/6)%8],shift:Number=frame%3==0?0:.35;
   for each(var layer:Sprite in layers){layer.transform.matrix=new Matrix(zoom,0,0,zoom,shift,shift);layer.alpha=frame%11==0?.5:1;}
   u.X=v.X=440+(k>=16?(k-16)*27.3:0);u.Y=v.Y=440;u.scX=v.scX=k>=20?120:80;
   for each(var n:Unit in [u,v]){
    n.vis.x=n.X;n.vis.y=n.Y;n.vis.alpha=[1,.75,.5,.25][frame%4];n.vis.scaleX=frame%9<4?-1:1;
    var child:Bitmap=n.vis.getChildAt(0) as Bitmap;child.x=-40;child.y=-80;child.bitmapData.setPixel32(3,7,frame%2?0x702080f0:0xff30f040);
    n.vis.filters=frame%13==0?[new GlowFilter(0x00ffff,.7,8,8)]:[];
    n.hpbar.visible=frame%5!=0;
    Sprite(n.hpbar).graphics.clear();Sprite(n.hpbar).graphics.beginFill(0xfae430);Sprite(n.hpbar).graphics.drawRect(n.X-40,frame%17==0?20:n.Y-95,20+(frame%9)*8,8);Sprite(n.hpbar).graphics.endFill();
   }
   for each(var gun:Sprite in [ua,ub]){gun.x=u.X+60;gun.y=u.Y-45;gun.rotation=frame%31;gun.alpha=[1,.75,.5,.25][frame%4];Bitmap(gun.getChildAt(0)).bitmapData.setPixel32(1,1,frame%2?0xff80f030:0x802080f0);gun.filters=frame%19==0?[new GlowFilter(0x11ff11,.7,9,9)]:[];}
   // FRESH_REFERENCE
   a.applyMask(w,u,a.unitBBox(loc,u));b.applyMask(w,v,b.unitBBox(loc,v));
   var ar:Object=a.unitVis[u],br:Object=b.unitVis[v];
   check(same(ar.m2d,br.m2d)&&same(ar.m2e,br.m2e),'exact source/soft pixels');
   a.applyWeaponVisual(wa,u,2);b.applyWeaponVisual(wb,v,2);
   var ca:BitmapData=capture(u,v,ua,ub),cb:BitmapData=capture(v,u,ub,ua);var equal:Boolean=same(ca,cb);
   if(!equal){
    trace('COUNTEREXAMPLE '+JSON.stringify({frame:frame,mode:mode,unit:[u.X,u.Y],body:String(v.vis.getBounds(v.vis.parent)),weapon:String(ub.getBounds(ub.parent)),clipBody:br.bodyDraw?String(br.bodyDraw.clip):null,clipWeapon:b.weaponVisuals[ub]?String(b.weaponVisuals[ub].clip):null}));
    var out:String=File.applicationDirectory.nativePath.replace(/\\/g,'/');if(out.indexOf('/RealisticVision/build/enemy-combat-output/')<0)throw new Error('wrong image root');
    for each(var item:Object in [{name:'baseline',pixels:ca},{name:'candidate',pixels:cb}]){var file:FileStream=new FileStream();file.open(new File(out+'/'+item.name+'.png'),FileMode.WRITE);file.writeBytes(BitmapData(item.pixels).encode(BitmapData(item.pixels).rect,new PNGEncoderOptions()));file.close();}
   }
   check(equal,'body/bar/extended weapon render');ca.dispose();cb.dispose();
   if(k==14){a.clearMask(u);b.clearMask(v);a.fovVersion++;b.fovVersion++;a.applyMask(w,u,a.unitBBox(loc,u));b.applyMask(w,v,b.unitBBox(loc,v));check(v.vis.mask!=null&&v.vis.mask.parent!=null,'reattach reused shape');}
   if(k==22){a.applyWeaponVisual(wa,u,0);b.applyWeaponVisual(wb,v,0);check(ua.visible==ub.visible,'hidden weapon');a.applyWeaponVisual(wa,u,1);b.applyWeaponVisual(wb,v,1);check(ua.mask==ub.mask&&ua.cacheAsBitmap==ub.cacheAsBitmap,'restore native weapon');}
   if(++frame>=720){check(b.clipHits>50,'clip path exercised');trace('RENDER COMPLETE passed='+passed+' clipHits='+b.clipHits);removeEventListener(Event.ENTER_FRAME,step);NativeApplication.nativeApplication.exit(0);}
  }catch(error:Error){fail(error);}}
  private function fail(e:Error):void {removeEventListener(Event.ENTER_FRAME,step);trace('FAIL '+e+' '+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
 }
}
