  // Called only after every timed window. Synthetic geometry uses the actual
  // loaded production-derived implementation; no player files are touched.
  private function auditChecks(w:*):void {
   var a:*=new candidateClass();a.cfgMode='current';a.spaceX=16;a.spaceY=16;a.fovVersion=1;a.frameCount=1;
   a.currentSight=new BitmapData(136,136,true,0);
   a.currentSight.fillRect(new Rectangle(54,0,82,136),0xffffffff);
   var layer:Sprite=new Sprite(),v:Sprite=new Sprite(),child:Shape=new Shape();
   layer.addChild(v);v.addChild(child);v.x=240;v.y=240;
   var output:Object={geometry:[],fade:{},scope:'synthetic animation geometry and controlled native-enemy fade history, after timing'};
   for each(var kind:String in ['child-graphics','scaleY']) {
    v.scaleY=1;child.graphics.clear();child.graphics.beginFill(0xffffff);child.graphics.drawRect(0,0,40,30);child.graphics.endFill();
    a.frameCount++;a.applyWorldVisual(v);a.applyWorldVisual(v);
    var record:Object=a.worldVisuals[v];if(!record || !record.lastBounds)throw new Error('audit partial mask missing');
    if(kind=='child-graphics'){child.graphics.clear();child.graphics.beginFill(0xffffff);child.graphics.drawRect(0,0,160,30);child.graphics.endFill();}
    else v.scaleY=4;
    a.frameCount++;a.applyWorldVisual(v);
    var cached:Rectangle=record.lastBounds.clone(),actual:Rectangle=v.getBounds(layer);
    var stale:BitmapData=new BitmapData(640,640,true,0);stale.draw(layer);
    a.releaseWorldVisual(v,record);a.applyWorldVisual(v);
    var fresh:BitmapData=new BitmapData(640,640,true,0);fresh.draw(layer);
    var aa:Vector.<uint>=stale.getVector(stale.rect),bb:Vector.<uint>=fresh.getVector(fresh.rect),changed:int=0;
    for(var i:int=0;i<aa.length;i++)if(aa[i]!=bb[i])changed++;
    var baseline:*=new rvClass();baseline.cfgMode='current';baseline.spaceX=16;baseline.spaceY=16;baseline.fovVersion=1;baseline.frameCount=1;baseline.currentSight=a.currentSight.clone();
    var baselineLayer:Sprite=new Sprite(),baselineV:Sprite=new Sprite(),baselineChild:Shape=new Shape();baselineLayer.addChild(baselineV);baselineV.addChild(baselineChild);baselineV.x=240;baselineV.y=240;
    baselineChild.graphics.beginFill(0xffffff);baselineChild.graphics.drawRect(0,0,40,30);baselineChild.graphics.endFill();baseline.applyWorldVisual(baselineV);baseline.applyWorldVisual(baselineV);
    if(kind=='child-graphics'){baselineChild.graphics.clear();baselineChild.graphics.beginFill(0xffffff);baselineChild.graphics.drawRect(0,0,160,30);baselineChild.graphics.endFill();}else baselineV.scaleY=4;
    baseline.frameCount++;baseline.applyWorldVisual(baselineV);var baseImage:BitmapData=new BitmapData(640,640,true,0);baseImage.draw(baselineLayer);
    var basePixels:Vector.<uint>=baseImage.getVector(baseImage.rect),staleVsBaseline:int=0,freshVsBaseline:int=0;
    for(i=0;i<aa.length;i++){if(aa[i]!=basePixels[i])staleVsBaseline++;if(bb[i]!=basePixels[i])freshVsBaseline++;}
    output.geometry.push({kind:kind,cached:cached.toString(),actual:actual.toString(),stale:!cached.equals(actual),changedPixels:changed,staleVsLoadedBaseline:staleVsBaseline,freshVsLoadedBaseline:freshVsBaseline});
    baseline.restoreWorldVisuals();baseline.currentSight.dispose();baseImage.dispose();
    for each(var pair:Array in [['stale',stale],['fresh',fresh]]){
     var stream:FileStream=new FileStream();stream.open(new File(File.applicationDirectory.nativePath+'/evidence/audit-'+kind+'-'+pair[0]+'.png'),FileMode.WRITE);
     stream.writeBytes(BitmapData(pair[1]).encode(stale.rect,new PNGEncoderOptions()));stream.close();
    }
    stale.dispose();fresh.dispose();a.releaseWorldVisual(v,a.worldVisuals[v]);
   }
   a.restoreWorldVisuals();a.currentSight.dispose();
   var f:*=new candidateClass();f.cfgMode='current';f.cfgEnabled=true;f.cfgDim=.6;f.cfgSoftCurrent=25;f.cfgWallBright=false;f.mswRegistered=true;f.cfgBaseRooms={};f.resetRoom(w,w.loc);f.frameCount++;f.onFrameInner();
   if(crowd.length==0){var unitClass:Class=host.loaderInfo.applicationDomain.getDefinition('fe.unit.UnitMerc') as Class;var extra:*=new unitClass('1',10,null,{weap:'smg10'});extra.putLoc(w.loc,w.gg.X+30,w.gg.Y);w.loc.addObj(extra);w.loc.units.push(extra);extra.step();crowd.push(extra);}
   var u:*=crowd[0],oldX:Number=u.X,oldY:Number=u.Y,oldAlpha:Number=u.vis.alpha,found:Boolean=false;
   for each(var dx:int in [30,60,90,-30,-60]){u.setPos(w.gg.X+dx,w.gg.Y);u.setVisPos();if(f.enemyState(w.loc,u)>0){found=true;break;}}
   output.fade.visibleEnemyFound=found;
   if(found){
    f.hideEnemies(w,w.loc,true);var rec:Object=f.unitVis[u];
    rec.prevState=0;delete rec.fadeCount;u.vis.alpha=1;f.hideEnemies(w,w.loc,true);
    output.fade.firstAppearanceAlpha=u.vis.alpha;output.fade.firstFadeCount=String(rec.fadeCount);
    rec.prevState=0;rec.fadeCount=0;u.vis.alpha=1;f.hideEnemies(w,w.loc,true);
    output.fade.beforeRestore=u.vis.alpha;output.fade.countBeforeRestore=rec.fadeCount;
    f.restoreAll(w,w.loc);output.fade.afterRestore=u.vis.alpha;
   }else f.restoreAll(w,w.loc);
   u.vis.alpha=oldAlpha;u.setPos(oldX,oldY);u.setVisPos();
   if(f.fogVis&&f.fogVis.parent)f.fogVis.parent.removeChild(f.fogVis);
   result.audit=output;save();
  }
