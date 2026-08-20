package
{
   import flash.display.Sprite;
   import flash.display.BitmapData;
   import flash.display.BlendMode;
   import flash.filesystem.File;
   import flash.filesystem.FileMode;
   import flash.filesystem.FileStream;

   public class BlendTest extends Sprite
   {
      private function w(s:String):void
      {
         try
         {
            var fl:File = new File("C:/Users/micha/AppData/Local/Temp/blendtest.log");
            var fs:FileStream = new FileStream();
            fs.open(fl,FileMode.APPEND);
            fs.writeUTFBytes(s + "\n");
            fs.close();
         }
         catch(err:Error)
         {
         }
      }

      public function BlendTest()
      {
         w("ctor start");
         try
         {
            var a:BitmapData = new BitmapData(2,2,true,0);
            a.setPixel32(0,0,166 << 24);
            a.setPixel32(1,0,255 << 24);
            a.setPixel32(0,1,0);
            a.setPixel32(1,1,50 << 24);
            var b:BitmapData = new BitmapData(2,2,true,0);
            b.setPixel32(0,0,50 << 24);
            b.setPixel32(1,0,0);
            b.setPixel32(0,1,255 << 24);
            b.setPixel32(1,1,166 << 24);
            b.draw(a, null, null, BlendMode.LIGHTEN);
            w("BT dst50+src166 -> " + (b.getPixel32(0,0) >>> 24) + " (max=166 / so=183)");
            w("BT dst0+src255 -> " + (b.getPixel32(1,0) >>> 24) + " (max=255)");
            w("BT dst255+src0 -> " + (b.getPixel32(0,1) >>> 24) + " (max=255)");
            w("BT dst166+src50 -> " + (b.getPixel32(1,1) >>> 24) + " (max=166 / so=181)");
            var c:BitmapData = new BitmapData(1,1,true,0xFF0000);
            var d:BitmapData = new BitmapData(1,1,true,0x00FF00);
            d.draw(c, null, null, BlendMode.LIGHTEN);
            w("BT RGB red|green -> " + (d.getPixel32(0,0) & 0xFFFFFF).toString(16) + " (expect ffff00)");
            var e2:BitmapData = new BitmapData(1,1,true,0);
            e2.setPixel32(0,0,100 << 24);
            var f:BitmapData = new BitmapData(1,1,true,0);
            f.setPixel32(0,0,200 << 24);
            f.draw(e2, null, null, BlendMode.LIGHTEN);
            f.draw(e2, null, null, BlendMode.LIGHTEN);
            w("BT double 200|100 -> " + (f.getPixel32(0,0) >>> 24) + " (expect 200)");
            w("BT done");
         }
         catch(err:Error)
         {
            w("BT EXC " + err);
         }
      }
   }
}
