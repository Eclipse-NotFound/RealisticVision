package {
 import flash.display.*;import flash.geom.*;import flash.filters.*;import flash.events.Event;import flash.desktop.NativeApplication;
 import fe.World;import fe.loc.Tile;import fe.unit.Unit;import fe.unit.UnitPlayer;import fe.graph.Grafon;
 public class RegionChecks extends Sprite {
  private var a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod();
  private var w:World,loc:MotionLocation,roots:Array=[new Sprite(),new Sprite()],units:Array=[],effects:Array=[[],[]];
  private var frame:int=0,passed:int=0;
  public function RegionChecks(){try{
   stage.scaleMode=StageScaleMode.NO_SCALE;stage.align=StageAlign.TOP_LEFT;
   Tile.tileX=Tile.tileY=40;World.fps=30;loc=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
   w=new RegionWorld();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.grafon=new RegionGrafon();w.grafon.visual=new Sprite();
   w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
   for(var side:int=0;side<2;side++){
    addChild(roots[side]);var u:Unit=new Unit();u.X=440;u.Y=440;u.scX=u.scY=80;u.vis=new MovieClip();u.hpbar=new Sprite();
    u.vis.addChild(new Bitmap(new BitmapData(83,79,true,0xffda3521),'auto',true));Bitmap(u.vis.getChildAt(0)).x=-40;Bitmap(u.vis.getChildAt(0)).y=-80;
    roots[side].addChild(u.vis);roots[side].addChild(u.hpbar);units.push(u);
    for(var i:int=0;i<48;i++){var v:Sprite=new Sprite();v.addChild(new Bitmap(new BitmapData(17+i%9,5+i%6,true,0xff32cc41),'auto',true));roots[side].addChild(v);effects[side].push(v);}
   }
   for each(var m:* in [a,b])m.mswRegistered=true;
   addEventListener(Event.ENTER_FRAME,step);
  }catch(e:Error){fail(e);}}
  private function check(ok:Boolean,label:String):void{if(!ok)throw new Error(label+' frame='+frame);passed++;}
  private function same(x:BitmapData,y:BitmapData):Boolean{if(x==null||y==null)return x==null&&y==null;var d:Object=x.compare(y),ok:Boolean=d is uint&&uint(d)==0;if(d is BitmapData)BitmapData(d).dispose();return ok;}
  private function image(root:Sprite):BitmapData{var out:BitmapData=new BitmapData(960,720,false,0x334455);out.draw(root);return out;}
  private function step(e:Event):void{try{
   var age:int=frame%120,mode:String=frame<120?'current':'classic';
   if(age==0)for each(var m:* in [a,b]){m.restoreWorldVisuals();m.cfgMode=mode;m.resetRoom(w,loc);}
   // Move, stand, change native wall light, break a wall and change transparent
   // collision/door and water inputs. Both versions read the same native state.
   w.gg.X=age<50?200+Math.floor(age/2)*3:age<75?275:200+(age-75)*2;w.gg.Y=500;
   Object(w).cam.vx=age<50?-Math.floor(age/5)*80:age<75?-800:-(119-age)*20;
   loc.getTile(10,8).opac=age>=65&&age<90?0:1;
   loc.getTile(6,8).opac=age>=35&&age<55?.3:0;
   loc.getTile(7,9).water=age>=40&&age<60?1:0;loc.opacWater=.45;
   for(var y:int=6;y<=10;y++){loc.getTile(10,y).visi=loc.getTile(10,y).t_visi=age>=50&&age<75?.3:0;}
   for each(m in [a,b]){
    m.cfgDim=[.35,.6,0,1][int(age/30)];m.cfgViewScale=[1,2,.5][int(age/40)];
    var blur:Number=[0,1,4,6][int(age/30)];m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;
    if(age%30==0){m.lastFovFrame=-100;m.fogDirty=true;}
    m.frameCount++;m.onFrameInner();
   }
   check(same(a.fogCache,b.fogCache)&&same(a.fogBmp,b.fogBmp),'fog inputs and display');
   if(mode=='current'){
    check(same(a.currentSight,b.currentSight),'current logical pixels');
    var bits:Vector.<uint>=b.currentSight.getVector(b.currentSight.rect),stride:int=b.currentSight.width;
    var wrong:int=0;
    for(y=0;y<b.spaceY;y++)for(var x:int=0;x<b.spaceX;x++){
     var lo:uint=0,hi:uint=0;
     for(var sy:int=0;sy<8;sy++)for(var sx:int=0;sx<8;sx++)if(bits[(RealisticVisionMod.FOG_PAD+y*8+sy)*stride+RealisticVisionMod.FOG_PAD+x*8+sx]){
      if(sy<4)lo|=uint(1)<<(sy*8+sx);else hi|=uint(1)<<((sy-4)*8+sx);
     }
     var ti:int=x+y*b.spaceX;if(b.regionLo[ti]!=lo||b.regionHi[ti]!=hi)wrong++;
    }
    check(wrong==0,'all current writer summaries exact '+wrong);
   }
   check(JSON.stringify(a.seenSub)==JSON.stringify(b.seenSub)&&JSON.stringify(a.explored)==JSON.stringify(b.explored),'exploration');
   for(var side:int=0;side<2;side++){
    m=side?b:a;var u:Unit=units[side];u.X=440+(age%13)*.35;u.Y=440;u.vis.x=u.X;u.vis.y=u.Y;
    var zoom:Number=[1,2/3,4/3,.75][int(age/30)];roots[side].transform.matrix=new Matrix(zoom,0,0,zoom,.35,.65);
    m.applyMask(w,u,m.unitBBox(loc,u));m.worldPass++;
    for(var i:int=0;i<48;i++){
     var v:Sprite=effects[side][i];v.x=40+(i*61+(age>80?age*3:0))%850;v.y=100+(i*37)%540;
     v.rotation=(i+age)%19;v.alpha=[1,.75,.5][age%3];
     Bitmap(v.getChildAt(0)).bitmapData.setPixel32(2,2,age%2?0xffdd88ff:0x8066ff22);
     v.filters=i%17==0?[new GlowFilter(0x00ffff,.5,8,8)]:[];m.applyWorldVisual(v);
    }
   }
   var ar:Object=a.unitVis[units[0]],br:Object=b.unitVis[units[1]];
   check(same(ar.m2d,br.m2d)&&same(ar.m2e,br.m2e),'body raw and soft mask');
   var ca:BitmapData=image(roots[0]),cb:BitmapData=image(roots[1]);check(same(ca,cb),'body and continuous independent visual rendering');ca.dispose();cb.dispose();
   if(age==80){a.clearMask(units[0]);b.clearMask(units[1]);}
   if(++frame>=240){check(b.regionHits>100,'exact early hits exercised');check(b.regionVerified==b.regionHits,'every early hit checked against native bitmap input');trace('REGION COMPLETE '+JSON.stringify({passed:passed,hits:b.regionHits}));removeEventListener(Event.ENTER_FRAME,step);NativeApplication.nativeApplication.exit(0);}
  }catch(error:Error){fail(error);}}
  private function fail(e:Error):void{removeEventListener(Event.ENTER_FRAME,step);trace('FAIL '+e+' '+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
 }
}
