  private function checkPixels(w:*):Array {
   var h:*=rv.wallSurface;if(h.contourFog==null)return [];
   var expected:BitmapData=new BitmapData(h.floorField.width,h.floorField.height,true,0);
   expected.paletteMap(h.floorField,h.floorField.rect,new Point(),h.alphaMap,h.zeroMap,h.zeroMap,h.zeroMap);
   function same(a:BitmapData,b:BitmapData):Boolean {
    var value:Object=a.compare(b);if(value is Number)return value===0;
    if(value is BitmapData)BitmapData(value).dispose();return false;
   }
   var fieldEqual:Boolean=same(h.contourFog,expected);
   var original:BitmapData=new BitmapData(host.stage.stageWidth,host.stage.stageHeight,true,0),after:BitmapData=original.clone(),control:BitmapData=original.clone();
   original.draw(host.stage);
   h.contourFog.paletteMap(h.floorField,h.floorField.rect,new Point(),h.alphaMap,h.zeroMap,h.zeroMap,h.zeroMap);
   after.draw(host.stage);control.draw(host.stage);
   var answer:Array=[{difference:{equal:same(original,after)},repeatControl:{equal:same(after,control)},fieldEqual:fieldEqual,
       paletteUploads:h.d61PaletteUploads,paletteSkipped:h.d61PaletteSkipped,fieldUpdates:h.fieldUpdates}];
   original.dispose();after.dispose();control.dispose();expected.dispose();return answer;
  }
