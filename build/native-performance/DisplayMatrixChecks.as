package {
 import flash.display.*;import flash.geom.*;import flash.desktop.NativeApplication;
 public class DisplayMatrixChecks extends Sprite {
  public function DisplayMatrixChecks(){var count:int=0;try{
   for each(var scale:Number in [.5,.6583333333333333,1,1.25])for each(var offset:int in [0,120,240]){
    var parent:Sprite=new Sprite(),root:Sprite=new Sprite();parent.addChild(root);
    root.x=offset;root.y=80;root.scrollRect=new Rectangle(offset,80,150,100);
    root.graphics.beginFill(0x37ab92);root.graphics.drawRect(offset+25,100,70,60);root.graphics.endFill();
    var camera:Matrix=new Matrix(scale,0,0,scale,10,15),full:Matrix=root.transform.matrix;full.concat(camera);
    var a:BitmapData=new BitmapData(800,600,true,0),b:BitmapData=a.clone(),wrong:BitmapData=a.clone(),wrapped:BitmapData=a.clone();
    a.draw(parent,camera,null,null,null,true);b.draw(root,full,null,null,null,true);wrong.draw(root,camera,null,null,null,true);
    var d:Object=a.compare(b);if(d is BitmapData){trace("COMPOSED RASTER DIFFERENCE scale="+scale+" offset="+offset+" bounds="+d.getColorBoundsRect(0xFFFFFFFF,0,false));d.dispose();}else if(d!==0)throw new Error("compare failed");
    if(!a.getColorBoundsRect(0xFF000000,0,false).equals(b.getColorBoundsRect(0xFF000000,0,false)))throw new Error("composed geometry mismatch");count++;
    var wrapper:Sprite=new Sprite();wrapper.addChild(root);try{wrapped.draw(wrapper,camera,null,null,null,true);}finally{parent.addChild(root);}
    d=a.compare(wrapped);if(d is BitmapData){d.dispose();throw new Error("parent-preserving capture mismatch "+scale+"/"+offset);}if(d!==0)throw new Error("parent capture failed");count++;
    d=a.compare(wrong);if(!(d is BitmapData))throw new Error("old matrix failed to detect missing translation");d.dispose();count++;
    a.dispose();b.dispose();wrong.dispose();wrapped.dispose();
   }
   trace("DISPLAY MATRIX COMPLETE passed="+count);NativeApplication.nativeApplication.exit(0);
  }catch(e:Error){trace("FAIL "+e+" "+e.getStackTrace());NativeApplication.nativeApplication.exit(1);}}
 }
}
