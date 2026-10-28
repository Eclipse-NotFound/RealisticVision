
  private static const REPLAY_VALIDATE:Boolean=false;
  private var replaying:Boolean=false,replayRoot:Sprite=new Sprite(),replayItems:Array=[],replayLayers:Array=[],replayPlan:Array=['off','normal','candidate','candidate','normal','off'];
  private var replayIndex:int=0,replayAge:int=0,replayLast:int=0,replayPrevious:Object,replayRow:Object,replayMod:*,compareMod:*,sightSeed:BitmapData;
  private var replayWidth:int=0,replayHeight:int=0,referenceFingerprint:String=null;
  private function stopTree(v:DisplayObject):void {
   if(v is MovieClip)MovieClip(v).stop();
   if(v is DisplayObjectContainer){var c:DisplayObjectContainer=v as DisplayObjectContainer;for(var i:int=0;i<c.numChildren;i++)stopTree(c.getChildAt(i));}
  }
  private function freezeReplay(w:*):void {
   if(!rv.currentSight)throw new Error('Native sight absent');
   sightSeed=rv.currentSight.clone();replayWidth=rv.spaceX;replayHeight=rv.spaceY;
   result.capture={attacks:row.attacks,maxParticles:row.maxParticles,maxProjectiles:row.maxProjectiles};
   rv.restoreWorldVisuals();w.ctr.clearAll();w.mm.active=true;
   var layerMap:Dictionary=new Dictionary(true),obj:*=w.loc.firstObj,guard:int=0;
   var kinds:Object={},blitCount:int=0,animated:int=0,area:Number=0;
   while(obj&&guard++<5000){
    var name:String=getQualifiedClassName(obj),v:DisplayObject=obj.vis;
    if((name=='fe.graph::Part'||name.indexOf('Bullet')>=0)&&v&&v.parent&&v.visible){
     var parent:DisplayObjectContainer=v.parent,layer:Sprite=layerMap[parent];
     if(!layer){layer=new Sprite();layer.transform.matrix=parent.transform.concatenatedMatrix;layer.transform.colorTransform=parent.transform.concatenatedColorTransform;layerMap[parent]=layer;replayLayers.push(layer);replayRoot.addChild(layer);}
     var record:Object={v:v,obj:obj,m:v.transform.matrix.clone(),ct:v.transform.colorTransform,visible:v.visible,alpha:v.alpha,frame:v is MovieClip?MovieClip(v).currentFrame:1,frames:v is MovieClip?MovieClip(v).totalFrames:1,blitFrames:0,layer:layer,order:parent.getChildIndex(v)};
     if(name=='fe.graph::Part' && obj.blitData && v is DisplayObjectContainer){
      var container:DisplayObjectContainer=v as DisplayObjectContainer;
      if(container.numChildren==1&&container.getChildAt(0) is Bitmap){
       var bmp:Bitmap=container.getChildAt(0) as Bitmap;
       if(bmp.bitmapData){record.blitFrames=int(obj.blitData.width/bmp.bitmapData.width);blitCount++;area+=bmp.bitmapData.width*bmp.bitmapData.height;}
      }
     }
     if(record.frames>1||record.blitFrames>1)animated++;
     stopTree(v);replayItems.push(record);kinds[getQualifiedClassName(v)]=int(kinds[getQualifiedClassName(v)])+1;
    }
    obj=obj.nobj;
   }
   replayItems.sortOn('order',Array.NUMERIC);
   for each(record in replayItems)record.layer.addChild(record.v);
   host.visible=false;host.stage.addChild(replayRoot);
   replayRoot.graphics.beginFill(0x263747);replayRoot.graphics.drawRect(0,0,host.stage.stageWidth,host.stage.stageHeight);replayRoot.graphics.endFill();
   host.stage.frameRate=120;
   result.replay={count:replayItems.length,blitCount:blitCount,animated:animated,sourceBitmapArea:area,kinds:kinds,stageFps:host.stage.frameRate,screen:[host.stage.stageWidth,host.stage.stageHeight],boundary:'Frozen native effect batch; controlled transforms and original sprite-strip/timeline frames; native world paused. Not full gameplay.'};
   result.replayCases=[];replaying=true;
   trace('D55 REPLAY '+JSON.stringify(result.replay));
   startReplay();
  }
  private function freshReplay(cls:Class):* {
   var m:*=new cls();m.cfgMode='current';m.spaceX=replayWidth;m.spaceY=replayHeight;m.currentSight=sightSeed.clone();m.fovVersion=1;m.mswRegistered=true;return m;
  }
  private function startReplay():void {
   if(replayMod){replayMod.restoreWorldVisuals();replayMod.currentSight.dispose();}
   var variant:String=replayPlan[replayIndex];
   replayMod=freshReplay(variant=='candidate'?candidateClass:rvClass);
   if(REPLAY_VALIDATE){replayMod=freshReplay(rvClass);compareMod=freshReplay(candidateClass);}
   replayAge=0;replayLast=0;replayPrevious=null;replayRow={variant:variant,frames:[],fingerprint:'',masked:[],cacheBytes:[]};
   trace('D55 REPLAY START '+replayIndex+' '+variant);
  }
  private function restoreFrame(frame:int):uint {
   var hash:uint=2166136261;
   for(var i:int=0;i<replayItems.length;i++){
    var r:Object=replayItems[i],v:DisplayObject=r.v;
    var a:int=(frame+i*7)%60;
    var m:Matrix=Matrix(r.m).clone();m.tx+=80*Math.sin(a*Math.PI/30);m.ty+=40*Math.cos(a*Math.PI/30);
    if(replayRow.variant=='fixed')m=Matrix(r.m).clone();
    v.transform.matrix=m;v.transform.colorTransform=r.ct;v.visible=r.visible;
    if(r.blitFrames>0)r.obj.blit((r.frame+frame)%r.blitFrames);
    else if(r.frames>1)MovieClip(v).gotoAndStop((r.frame+frame-1)%r.frames+1);
    hash=uint((hash^int(m.tx*1000))*16777619);hash=uint((hash^int(m.ty*1000))*16777619);hash=uint((hash^int((r.frame+frame)%Math.max(1,r.blitFrames)))*16777619);
   }
   return hash;
  }
  private function applyReplay(m:*):int {
   var start:int=getTimer();m.worldPass++;
   for each(var r:Object in replayItems)m.applyWorldVisual(r.v);
   return getTimer()-start;
  }
  private function captureReplay():BitmapData {
   var data:BitmapData=new BitmapData(host.stage.stageWidth,host.stage.stageHeight,true,0);data.draw(replayRoot);return data;
  }
  private function replayStep():void {
   var now:int=getTimer();if(replayPrevious)replayPrevious.interval=now-replayLast;replayLast=now;
   var frame:int=replayAge%60,t:int=getTimer();var inputHash:uint=restoreFrame(frame);var restoreMs:int=getTimer()-t,rvMs:int=0;
   if(REPLAY_VALIDATE){
    applyReplay(replayMod);var a:BitmapData=captureReplay();replayMod.restoreWorldVisuals();
    applyReplay(compareMod);var b:BitmapData=captureReplay();compareMod.restoreWorldVisuals();
    var diff:Object=a.compare(b);if(!(diff is uint)||uint(diff)!=0)throw new Error('Replay pixel difference frame '+frame);
    a.dispose();b.dispose();
    if(++replayAge<60)return;
    result.exactFrames=60;save();host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D55 COMPLETE');NativeApplication.nativeApplication.exit(0);return;
   }
   if(replayRow.variant!='off')rvMs=applyReplay(replayMod);
   if(replayAge>=60){
    replayPrevious={frame:frame,rv:rvMs,restore:restoreMs};replayRow.frames.push(replayPrevious);
    if(replayAge<120)replayRow.fingerprint+=inputHash.toString(16)+',';
   }
   if(++replayAge<180)return;
   if(replayRow.variant!='fixed'){
    if(referenceFingerprint==null)referenceFingerprint=replayRow.fingerprint;
    else if(replayRow.fingerprint!=referenceFingerprint)throw new Error('Input fingerprint mismatch');
   }
   var maskCount:int=0;for(var key:Object in replayMod.worldVisuals)maskCount++;
   replayRow.maskCount=maskCount;result.replayCases.push(replayRow);save();trace('D55 REPLAY END '+replayIndex+' masks='+maskCount);
   if(++replayIndex<replayPlan.length){startReplay();return;}
   replayMod.restoreWorldVisuals();host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D55 COMPLETE');NativeApplication.nativeApplication.exit(0);
  }
