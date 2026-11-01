  // Snapshot diagnostics occur after timing. They never advance the world.
  private function cachePixels(w:*):Array {
   var answer:Array=[],node:Sprite=rv.fogShadow,ancestor:DisplayObject=w.grafon.visual;
   var cached:Boolean=node.cacheAsBitmap,saved:Matrix=ancestor.transform.matrix;
   var transforms:Array=[saved.clone(),new Matrix(saved.a,saved.b,saved.c,saved.d,saved.tx+.35,saved.ty-.05),new Matrix(.658333,0,0,.658333,saved.tx-.35,saved.ty+.05)];
   function take():BitmapData {var b:BitmapData=new BitmapData(host.stage.stageWidth,host.stage.stageHeight,true,0);b.draw(host.stage);return b;}
   function compare(a:BitmapData,b:BitmapData):Object {
    var value:Object=a.compare(b);if(value is Number)return {equal:value===0,code:value};
    var d:BitmapData=value as BitmapData,r:Rectangle=d.getColorBoundsRect(0xFFFFFFFF,0,false);
    d.dispose();return {equal:false,bounds:[r.x,r.y,r.width,r.height]};
   }
   try {
    for(var i:int=0;i<transforms.length;i++){
     ancestor.transform.matrix=transforms[i];node.cacheAsBitmap=true;var on:BitmapData=take();
     node.cacheAsBitmap=false;var off:BitmapData=take(),repeat:BitmapData=take();
     var changed:Object=compare(on,off),control:Object=compare(off,repeat);
     answer.push({transform:i,cacheDifference:changed,repeatControl:control});
     if(i==0&&!changed.equal){
      for each(var kind:String in ['cached','normal']){
       var f:FileStream=new FileStream();f.open(new File(File.applicationDirectory.nativePath+'/evidence/cache-'+index+'-'+kind+'.png'),FileMode.WRITE);
       var image:BitmapData=kind=='cached'?on:off;f.writeBytes(image.encode(image.rect,new PNGEncoderOptions()));f.close();
      }
     }
     on.dispose();off.dispose();repeat.dispose();
    }
   }finally{ancestor.transform.matrix=saved;node.cacheAsBitmap=cached;}
   return answer;
  }
