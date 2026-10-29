package {
 import flash.filters.GlowFilter;
 import flash.display.*;import flash.geom.*;import flash.events.Event;import flash.utils.getTimer;import flash.system.System;import flash.desktop.NativeApplication;
 import fe.World;import fe.loc.Tile;import fe.unit.UnitPlayer;import fe.graph.Grafon;
 public class EffectLoadChecks extends Sprite {
 private var a:BaselineVision=new BaselineVision(),b:RealisticVisionMod=new RealisticVisionMod(),w:World,loc:MotionLocation;
 private var la:Sprite=new Sprite(),lb:Sprite=new Sprite(),aa:Array=[],bb:Array=[],f:int=0,passed:int=0,ta:Array=[],tb:Array=[];
 public function EffectLoadChecks(){try{
  stage.scaleMode=StageScaleMode.NO_SCALE;stage.align=StageAlign.TOP_LEFT;Tile.tileX=Tile.tileY=40;World.fps=30;loc=new MotionLocation();loc.gg=new UnitPlayer();loc.gg.X=200;loc.gg.Y=500;loc.gg.scY=40;
  w=new World();w.loc=loc;w.gg=loc.gg;w.black=true;w.allStat=1;World.w=w;w.grafon=new Grafon();w.grafon.visual=new Sprite();w.grafon.visLight=new Sprite();w.grafon.visual.addChild(w.grafon.visLight);w.grafon.visObjs=[new Sprite(),new Sprite(),new Sprite(),new Sprite()];
  var pa:Sprite=new Sprite(),pb:Sprite=new Sprite();addChild(pa);addChild(pb);pa.addChild(la);pb.addChild(lb);
  for(var i:int=0;i<500;i++){aa.push(make(la,i));bb.push(make(lb,i));}
  for each(var m:* in [a,b]){m.mswRegistered=true;m.resetRoom(w,loc);m.onFrameInner();if(!m.currentSight)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);m.classicLogicCache=null;}
  addEventListener(Event.ENTER_FRAME,step);
 }catch(e:Error){fail(e);}}
 private function make(parent:Sprite,i:int):Sprite {var v:Sprite=new Sprite();var data:BitmapData=new BitmapData([3,6,12][i%3],[3,6,12][i%3],true,0xff12fd88+i);data.setPixel32(0,0,0);v.addChild(new Bitmap(data,"auto",i%2==0));v.alpha=.25+(i%4)*.25;if(i%17==0)v.filters=[new GlowFilter(0x00ffff,.7,8,8)];parent.addChild(v);return v;}
 private function imageOf(layer:Sprite):BitmapData {var out:BitmapData=new BitmapData(960,720,true,0);out.draw(layer.parent);return out;}
 private function check(ok:Boolean,label:String):void{if(!ok)throw new Error(label+" f="+f);passed++;}
 private function step(e:Event):void{try{
  var group:int=int(f/30)%12,age:int=f%30,mode:String=group<6?"current":"classic",state:int=int(group/2)%3,count:int=group%2?500:100;
  for each(var m:* in [a,b]){
   m.cfgMode=mode;m.classicLogicCache=null;m.currentSight.fillRect(m.currentSight.rect,state==1?0:0xffffffff);m.fogCache.fillRect(m.fogCache.rect,state==1?0xff000000:0);
   if(state==2)for(var x:int=20+age%10;x<m.currentSight.width;x+=35){m.currentSight.fillRect(new Rectangle(x,0,17,m.currentSight.height),0);m.fogCache.fillRect(new Rectangle(x,0,17,m.fogCache.height),0xff000000);}
   var blur:Number=[0,1,2,4,6,9][age%6];m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.fovVersion++;m.worldPass++;
  }
  for(var i:int=0;i<500;i++){var va:Sprite=aa[i],vb:Sprite=bb[i];va.visible=vb.visible=i<count;va.x=vb.x=(i*61+age*17)%920+.3;va.y=vb.y=(i*37+age*5)%710+.7;va.rotation=vb.rotation=(i+age)%19;Bitmap(va.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);Bitmap(vb.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);}
  var zoom:Number=[.5,.75,1,1.5,2,1.25,4/3,2/3][f%8],offset:Number=f%3==0?0:.35;if(f<360){zoom=1;offset=0;}la.transform.matrix=lb.transform.matrix=new Matrix(zoom,0,0,zoom,offset,offset);var start:int=getTimer();if(f%2){for(i=0;i<count;i++)b.applyWorldVisual(bb[i]);tb.push(getTimer()-start);start=getTimer();for(i=0;i<count;i++)a.applyWorldVisual(aa[i]);ta.push(getTimer()-start);}
  else {for(i=0;i<count;i++)a.applyWorldVisual(aa[i]);ta.push(getTimer()-start);start=getTimer();for(i=0;i<count;i++)b.applyWorldVisual(bb[i]);tb.push(getTimer()-start);}
  var ca:BitmapData=imageOf(la),cb:BitmapData=imageOf(lb),d:Object=ca.compare(cb);if(d is BitmapData){
   var hits:int=0,visList:Array=[];for(var j:int=0;j<500;j++){visList.push(aa[j].visible);aa[j].visible=bb[j].visible=false;}
   for(j=0;j<count;j++){aa[j].visible=bb[j].visible=true;var ia:BitmapData=imageOf(la),ib:BitmapData=imageOf(lb),idiff:Object=ia.compare(ib);
    if(idiff is BitmapData){
     var ar:Object=a.worldVisuals[aa[j]],br:Object=b.worldVisuals[bb[j]];
     if(ar && br && ar.raster && br.raster && ar.raster.m2e && br.raster.m2e){
      var ab:Array=ar.raster.lastBb.split(','),bbounds:Array=br.raster.lastBb.split(','),area:Rectangle=bb[j].getBounds(lb),changes:Array=[];
      for(var yy:int=Math.max(0,int(area.top/5)-1);yy<=int(area.bottom/5)+1;yy++)for(var xx:int=Math.max(0,int(area.left/5)-1);xx<=int(area.right/5)+1;xx++){
       var aval:uint=ar.raster.m2e.getPixel32(xx-int(ab[0])*8,yy-int(ab[1])*8),bval:uint=br.raster.m2e.getPixel32(xx-int(bbounds[0])*8,yy-int(bbounds[1])*8);
       if(aval!=bval && changes.length<12)changes.push([xx,yy,aval>>>24,bval>>>24]);
      }trace('MASK DATA '+JSON.stringify(changes));
     }
     trace('COUNTEREXAMPLE '+JSON.stringify({frame:f,index:j,bounds:String(bb[j].getBounds(lb)),position:[bb[j].x,bb[j].y],baseline:ar&&ar.raster?ar.raster.lastBb:null,candidate:br&&br.raster?br.raster.lastBb:null,stable:br?br.stableBb:null,baselineLit:ar&&ar.raster?ar.raster.fullyLit:null,candidateLit:br&&br.raster?br.raster.fullyLit:null,delta:String(BitmapData(idiff).getColorBoundsRect(0xffffffff,0,false))}));
     BitmapData(idiff).dispose();hits++;
    }ia.dispose();ib.dispose();aa[j].visible=bb[j].visible=false;if(hits>=8)break;
   }
   for(j=0;j<500;j++)aa[j].visible=bb[j].visible=visList[j];
  }check(d is uint&&uint(d)==0,"exact dense moving visuals");if(d is BitmapData)BitmapData(d).dispose();ca.dispose();cb.dispose();
  if(age==29){var na:int=0,nb:int=0;for(var key:String in a.worldMasks)na++;for(key in b.worldMasks)nb++;trace("LOAD ROW "+JSON.stringify({mode:mode,state:state,count:count,baseline:ta,candidate:tb,rasters:[na,nb],memory:System.totalMemory}));ta=[];tb=[];a.restoreWorldVisuals();b.restoreWorldVisuals();}
  if(++f>=720){check(b.trailingHits>0,"early dark is exercised");trace("TRAILING hits="+b.trailingHits);removeEventListener(Event.ENTER_FRAME,step);trace("LOAD COMPLETE passed="+passed);NativeApplication.nativeApplication.exit(0);}
 }catch(error:Error){fail(error);}}
 private function fail(e:Error):void{removeEventListener(Event.ENTER_FRAME,step);trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}
 }
}
