  // Same frame, identical rasters and transforms; only the tested hierarchy
  // changes. Run after the last timing sample, then restore the running tree.
  private function checkPixels(w:*):Array {
   var answer:Array=[],ancestor:DisplayObject=w.grafon.visual;
   var saved:Matrix=ancestor.transform.matrix;
   var detached:Boolean=rv.fogBitmap.parent===rv.fogShadow;
   var transforms:Array=[saved.clone(),new Matrix(saved.a,saved.b,saved.c,saved.d,saved.tx+.35,saved.ty-.05),new Matrix(.658333,0,0,.658333,saved.tx-.35,saved.ty+.05)];
   function arrange(outside:Boolean):void {
    for each(var child:DisplayObject in [rv.fogBitmap,rv.wallLayer,rv.wallClip,rv.floorClip]){
     var parent:Sprite=outside&&(child===rv.fogBitmap||child===rv.floorClip)?rv.fogShadow:rv.fogBase;
     if(child.parent!==parent){if(parent===rv.fogShadow)parent.addChildAt(child,0);else parent.addChild(child);}
    }
   }
   function take():BitmapData {var b:BitmapData=new BitmapData(host.stage.stageWidth,host.stage.stageHeight,true,0);b.draw(host.stage);return b;}
   function compare(a:BitmapData,b:BitmapData):Object {
    var value:Object=a.compare(b);if(value is Number)return {equal:value===0,code:value};
    var d:BitmapData=value as BitmapData,r:Rectangle=d.getColorBoundsRect(0xFFFFFFFF,0,false);d.dispose();
    return {equal:false,bounds:[r.x,r.y,r.width,r.height]};
   }
   try {
    for(var i:int=0;i<transforms.length;i++){
     ancestor.transform.matrix=transforms[i];arrange(false);var original:BitmapData=take();
     arrange(!rv.cfgWallBright);var candidate:BitmapData=take();
     arrange(false);var control:BitmapData=take();
     var delta:Object=compare(original,candidate),repeat:Object=compare(original,control);
     answer.push({transform:i,bright:rv.cfgWallBright,difference:delta,repeatControl:repeat});
     if(!delta.equal||!repeat.equal){
      for each(var kind:String in ['original','candidate','control']){
       var f:FileStream=new FileStream();f.open(new File(File.applicationDirectory.nativePath+'/evidence/branch-'+index+'-'+i+'-'+kind+'.png'),FileMode.WRITE);
       var image:BitmapData=kind=='original'?original:kind=='candidate'?candidate:control;f.writeBytes(image.encode(image.rect,new PNGEncoderOptions()));f.close();
      }
     }
     original.dispose();candidate.dispose();control.dispose();
    }
   }finally{ancestor.transform.matrix=saved;arrange(detached);}
   return answer;
  }
