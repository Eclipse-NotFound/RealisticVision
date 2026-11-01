  private function checkPixels(w:*):Array {
   if(!('syncContourClipping' in rv))return [];
   var answer:Array=[],ancestor:DisplayObject=w.grafon.visual;
   var saved:Matrix=ancestor.transform.matrix;
   var transforms:Array=[saved.clone(),new Matrix(saved.a,saved.b,saved.c,saved.d,saved.tx+.35,saved.ty-.05),new Matrix(.658333,0,0,.658333,saved.tx-.35,saved.ty+.05),new Matrix(1,0,0,1,0,0)];
   function arrange(original:Boolean):void {
    for each(var child:DisplayObject in [rv.fogBitmap,rv.wallLayer,rv.wallClip,rv.floorClip]){
     var parent:Sprite=!original&&!rv.cfgWallBright&&(child===rv.fogBitmap||child===rv.floorClip)?rv.fogShadow:rv.fogBase;
     if(child.parent!==parent){if(parent===rv.fogShadow)parent.addChildAt(child,0);else parent.addChild(child);}
    }
    rv.wallLayer.mask=rv.wallClip;rv.wallClip.visible=true;rv.contourWallClip.visible=false;
    rv.fogBase.mask=rv.cfgWallBright?rv.wallSurface.onClip:rv.wallSurface.baseClip;
    if(rv.fogBase.mask)rv.fogBase.mask.visible=true;
    if(!original)rv.syncContourClipping(w.loc);
   }
   function take():BitmapData {var b:BitmapData=new BitmapData(host.stage.stageWidth,host.stage.stageHeight,true,0);b.draw(host.stage);return b;}
   function compare(a:BitmapData,b:BitmapData):Object {
    var value:Object=a.compare(b);if(value is Number)return {equal:value===0,code:value};
    var d:BitmapData=value as BitmapData,r:Rectangle=d.getColorBoundsRect(0xFFFFFFFF,0,false);d.dispose();
    return {equal:false,bounds:[r.x,r.y,r.width,r.height]};
   }
   try {
    for(var i:int=0;i<transforms.length;i++){
     ancestor.transform.matrix=transforms[i];arrange(true);var original:BitmapData=take();
     arrange(false);var candidate:BitmapData=take();
     arrange(true);var control:BitmapData=take();
     var delta:Object=compare(original,candidate),repeat:Object=compare(original,control);
     answer.push({transform:i,bright:rv.cfgWallBright,difference:delta,repeatControl:repeat});
     if(!delta.equal||!repeat.equal){
      for each(var kind:String in ['original','candidate','control']){
       var f:FileStream=new FileStream();f.open(new File(File.applicationDirectory.nativePath+'/evidence/merged-'+index+'-'+i+'-'+kind+'.png'),FileMode.WRITE);
       var image:BitmapData=kind=='original'?original:kind=='candidate'?candidate:control;f.writeBytes(image.encode(image.rect,new PNGEncoderOptions()));f.close();
      }
     }
     original.dispose();candidate.dispose();control.dispose();
    }
   }finally{ancestor.transform.matrix=saved;arrange(false);}
   return answer;
  }
