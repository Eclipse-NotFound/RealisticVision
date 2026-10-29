 private function darkChildChecks():void {
  b.restoreWorldVisuals();b.cfgMode='current';b.classicLogicCache=null;
  var v:Sprite=new Sprite(),data:BitmapData=new BitmapData(3,3,true,0xffffffff),child:Bitmap=new Bitmap(data);
  v.addChild(child);la.addChild(v);v.x=300;v.y=300;v.alpha=.6;v.rotation=17;
  var rootAlpha:Number=v.alpha,rootRotation:Number=v.rotation,nativeBounds:Rectangle=v.getBounds(la);
  b.currentSight.fillRect(b.currentSight.rect,0);b.fovVersion++;b.worldPass++;
  b.applyWorldVisual(v);check(child.visible,'unclassified display keeps child visible');
  b.applyWorldVisual(v,true);check(!child.visible,'native zero-output child suppressed');
  check(v.visible && v.alpha==rootAlpha && v.rotation==rootRotation,'native root display state unchanged');
  check(v.getBounds(la).equals(nativeBounds),'hidden child preserves native bounds');
  check(b.worldVisuals[v].dark===true,'only zero-output mask is suppressed');
  data.setPixel32(1,1,0xffaabbcc);check(data.getPixel32(1,1)==0xffaabbcc,'hidden bitmap remains writable');
  b.applyWorldVisual(v,false);check(child.visible,'classification removal restores child');
  b.applyWorldVisual(v,true);b.currentSight.fillRect(b.currentSight.rect,0xffffffff);b.fovVersion++;b.worldPass++;
  b.applyWorldVisual(v,true);check(child.visible,'same-frame reentry restores child');check(v.mask==null,'lit native mask released');
  b.currentSight.fillRect(b.currentSight.rect,0);b.fovVersion++;b.worldPass++;b.applyWorldVisual(v,true);
  v.filters=[new GlowFilter(0xffffff,1,4,4)];b.applyWorldVisual(v,true);check(child.visible,'filter addition restores child');
  v.filters=[];b.applyWorldVisual(v,true);check(!child.visible,'removed filter permits zero-output path');
  var second:Bitmap=new Bitmap(new BitmapData(4,4,true,0xffffffff));v.removeChild(child);v.addChild(second);b.applyWorldVisual(v,true);
  check(child.visible,'replaced bitmap restored');check(!second.visible,'new native bitmap independently tracked');
  var thirdParty:Shape=new Shape();thirdParty.graphics.beginFill(0);thirdParty.graphics.drawRect(0,0,900,900);la.addChild(thirdParty);v.mask=thirdParty;
  b.applyWorldVisual(v,true);check(second.visible && v.mask===thirdParty,'foreign mask restored child and retained ownership');
  v.mask=null;la.removeChild(thirdParty);b.applyWorldVisual(v,true);b.restoreWorldVisuals();check(second.visible,'reset restores child');
  second.visible=false;b.applyWorldVisual(v,true);b.restoreWorldVisuals();check(!second.visible,'originally hidden child stays hidden');
  second.visible=true;b.applyWorldVisual(v,true);var extra:Shape=new Shape();v.addChild(extra);b.applyWorldVisual(v,true);
  check(second.visible,'additional child cancels special path');b.restoreWorldVisuals();
  la.removeChild(v);data.dispose();second.bitmapData.dispose();
 }
