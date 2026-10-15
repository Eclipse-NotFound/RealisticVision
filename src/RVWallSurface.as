package {
   import flash.display.Bitmap;
   import flash.display.BitmapData;
   import flash.display.BitmapDataChannel;
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Sprite;
   import flash.display.Shape;
   import flash.geom.ColorTransform;
   import flash.geom.Matrix;
   import flash.geom.Point;
   import flash.geom.Rectangle;

   /** Display-only fog replacement at explored wall boundaries. Native alpha
    * separates rock from air. Constant wall brightness is optional; contour
    * correction is always active. Logic light and unit masks remain untouched. */
   public class RVWallSurface {
      private static const CELL:int = 40;
      private static const STEP:int = 5;
      private static const BRIGHT:Number = 12;
      private static const DEPTH:Number = 32;
      private static const FRINGE:Number = 10;
      private var owner:*;
      private var bounds:Rectangle;
      private var shapeKey:String = "";
      private var seenKey:String = "";
      private var lightKey:String = "";
      private var faces:Array = [];
      private var heights:Vector.<int>;
      private var cols:int;
      private var rows:int;
      private var left:int;
      private var top:int;
      private var field:BitmapData;
      private var floorField:BitmapData;
      private var wallField:BitmapData;
      private var fieldStamp:BitmapData;
      private var baseLight:BitmapData;
      private var wallPixels:Sprite = new Sprite();
      private var baseOwner:Sprite;
      private var baseClip:Shape = new Shape();
      private var alphaMap:Array=[];
      private var zeroMap:Array=[];
      private var origin:Point = new Point();
      private var support:Array=[];
      private var pieces:Array=[];
      private var terrainUpdates:int = 0;
      private var fieldUpdates:int = 0;

      public function RVWallSurface() {
         wallPixels.mouseEnabled=wallPixels.mouseChildren=false;
         for(var i:int=0;i<256;i++){alphaMap[i]=uint(255-i)<<24;zeroMap[i]=0;}
      }

      public function update(parent:Sprite, base:Sprite, grafon:*, loc:*, view:Rectangle,
                             known:Function, light:Function, alwaysBright:Boolean):void {
         if(baseOwner!==base) {
            if(baseOwner!=null && baseOwner.mask===baseClip)baseOwner.mask=null;
            baseOwner=base;
         }
         var front:DisplayObjectContainer = null;
         try { front = grafon.visFront as DisplayObjectContainer; } catch(e:Error) {}
         if(front == null || !front.visible || view.width <= 0 || view.height <= 0) {
            wallPixels.visible=false;base.mask=null;
            if(baseClip.parent)baseClip.parent.removeChild(baseClip);
            return;
         }
         if(wallPixels.parent != parent) parent.addChild(wallPixels);
         if(baseClip.parent != parent)parent.addChild(baseClip);
         parent.setChildIndex(wallPixels,parent.numChildren-1);
         wallPixels.visible = true;
         var reset:Boolean = owner !== loc || bounds == null || !bounds.equals(view);
         if(reset) {
            owner=loc; bounds=view.clone(); shapeKey=seenKey=lightKey="";
            left=int(view.x); top=int(view.y); cols=int(view.width); rows=int(view.height);
            if(field == null || field.width!=cols*CELL/STEP || field.height!=rows*CELL/STEP) {
               if(field != null) field.dispose();
               field=new BitmapData(cols*CELL/STEP,rows*CELL/STEP,true,0);
               if(floorField!=null){floorField.dispose();wallField.dispose();fieldStamp.dispose();}
               floorField=new BitmapData(field.width,field.height,false,0);
               wallField=new BitmapData(field.width,field.height,false,0);
               fieldStamp=new BitmapData(field.width,field.height,false,0);
            }
            if(baseLight==null || baseLight.width!=cols*CELL || baseLight.height!=rows*CELL){
               if(baseLight!=null)baseLight.dispose();
               baseLight=new BitmapData(cols*CELL,rows*CELL,false,0xffffff);
            }
            wallPixels.x=left*CELL; wallPixels.y=top*CELL;
            heights=new Vector.<int>((cols+2)*(rows+2),true);
         }
         // One-cell halo distinguishes exterior faces from joins, including two
         // touching half-height tiles. Geometry is checked even when FOV is static.
         var key:Array=[];
         for(var y:int=top-1;y<=top+rows;y++) for(var x:int=left-1;x<=left+cols;x++) {
            var h:int=heightAt(loc,x,y);
            heights[x-left+1+(y-top+1)*(cols+2)]=h;
            key.push(h);
         }
         var nextShape:String=key.join(",");
         var changed:Boolean=nextShape!=shapeKey;
         if(changed) { shapeKey=nextShape; rebuildFaces(loc); seenKey=""; }
         var seen:Array=[],lights:Array=[];
         var count:int=0;
         for(var i:int=0;i<faces.length;i+=5) {
            var isKnown:int=known(faces[i+3],faces[i+4])?1:0;
            seen.push(isKnown);count+=isKnown;
            lights.push(isKnown?Math.round(255*Math.max(0,Math.min(1,
               light(faces[i+3],faces[i+4],faces[i],faces[i+1],faces[i+2])))):0);
         }
         var nextSeen:String=seen.join("");
         var fieldChanged:Boolean=reset || changed || nextSeen!=seenKey;
         var nextLight:String=String(alwaysBright)+":"+lights.join(",");
         if(fieldChanged || lightKey!=nextLight){
            lightKey=nextLight;
            seenKey=nextSeen;field.lock();field.fillRect(field.rect,0);
            floorField.lock();wallField.lock();floorField.fillRect(floorField.rect,0);wallField.fillRect(wallField.rect,0);
            for(i=0;i<faces.length;i+=5) if(seen[i/5]) paintFace(faces[i],faces[i+1],faces[i+2],lights[i/5],alwaysBright);
            floorField.unlock();wallField.unlock();
            field.unlock();fieldUpdates++;
            fieldStamp.copyChannel(floorField,floorField.rect,origin,BitmapDataChannel.RED,BitmapDataChannel.RED);
            fieldStamp.copyChannel(wallField,wallField.rect,origin,BitmapDataChannel.GREEN,BitmapDataChannel.GREEN);
            if(fieldChanged){rebuildSupport();rebuildPieces();rebuildClip(loc);}
         }
         wallPixels.visible=count>0;
         if(!wallPixels.visible){base.mask=null;if(baseClip.parent)baseClip.parent.removeChild(baseClip);return;}
         var sources:Array=alwaysBright?foregroundSources(front):null,updated:Boolean=false;
         // Rasterize the unmodified fog once per update. Drawing it separately
         // for each small rectangle repeats the nested masks and blur work.
         base.mask=null;
         try {
         baseLight.fillRect(baseLight.rect,0xffffff);
         baseLight.draw(base,new Matrix(1,0,0,1,-left*CELL,-top*CELL),null,null,null,true);
         for each(var piece:Object in pieces){
            var scratch:BitmapData=piece.next,terrain:BitmapData=piece.previous;
            var pixelsChanged:Boolean=false;
            if(alwaysBright){
            scratch.fillRect(scratch.rect,0);
            if(sources!=null)copyForeground(sources,piece.rect,scratch);
            else {
               var matrix:Matrix=front.transform.matrix;
               matrix.tx-=left*CELL+piece.rect.x;matrix.ty-=top*CELL+piece.rect.y;
               scratch.draw(front,matrix,front.transform.colorTransform,null,scratch.rect,true);
            }
            var delta:Object=scratch.compare(terrain);
            pixelsChanged=!(delta is uint && uint(delta)==0);
            if(delta is BitmapData)BitmapData(delta).dispose();
            if(pixelsChanged){piece.previous=scratch;piece.next=terrain;updated=true;}
            }
            var shadeChanged:Boolean=false;
            if(piece.version!=fieldUpdates){
               piece.nextStamp.copyPixels(fieldStamp,piece.stampRect,origin);
               delta=piece.nextStamp.compare(piece.stamp);
               shadeChanged=!(delta is uint && uint(delta)==0);
               if(delta is BitmapData)BitmapData(delta).dispose();
               if(shadeChanged){var swap:BitmapData=piece.stamp;piece.stamp=piece.nextStamp;piece.nextStamp=swap;}
               piece.version=fieldUpdates;
            }
            // Local fields include a one-sample halo for bilinear filtering.
            // Unchanged wall patches reuse their target shading while the
            // original moving fog is still sampled every frame below.
            if(shadeChanged || pixelsChanged){
            var scale:Matrix=new Matrix(STEP,0,0,STEP,-piece.rect.x,-piece.rect.y);
            piece.floor.fillRect(piece.floor.rect,0);
            piece.floor.draw(floorField,scale,null,null,null,true);
            if(alwaysBright){
            piece.wall.fillRect(piece.wall.rect,0);
            piece.wall.draw(wallField,scale,null,null,null,true);
            piece.wall.copyChannel(piece.previous,piece.previous.rect,origin,BitmapDataChannel.ALPHA,BitmapDataChannel.ALPHA);
            // Grayscale stores brightness: native alpha linearly selects rock
            // or air, including semitransparent and overlapping foregrounds.
            piece.floor.draw(piece.wall);
            }
            }
            piece.nextBase.copyPixels(baseLight,piece.rect,origin);
            delta=piece.nextBase.compare(piece.base);
            var baseChanged:Boolean=!(delta is uint && uint(delta)==0);
            if(delta is BitmapData)BitmapData(delta).dispose();
            if(baseChanged){swap=piece.base;piece.base=piece.nextBase;piece.nextBase=swap;}
            if(!piece.outputValid || baseChanged || shadeChanged || pixelsChanged){
               piece.light.copyPixels(piece.base,piece.base.rect,origin);
               piece.light.draw(piece.floor,null,null,"lighten");
               piece.output.paletteMap(piece.light,piece.light.rect,origin,alphaMap,zeroMap,zeroMap,zeroMap);
               piece.outputValid=true;
            }
         }} finally {base.mask=baseClip;}
         if(updated)terrainUpdates++;
      }

      private function heightAt(loc:*,x:int,y:int):int {
         if(x<0 || y<0 || x>=loc.spaceX || y>=loc.spaceY)return CELL;
         var t:*=loc.getTile(x,y);
         if(t.opac<1)return 0;
         var cut:int=0;
         if("zForm" in t)cut=int(t.zForm)*10;
         return Math.max(0,CELL-cut);
      }

      public function reset():void {
         if(baseOwner!=null && baseOwner.mask===baseClip)baseOwner.mask=null;baseOwner=null;
         if(baseClip.parent)baseClip.parent.removeChild(baseClip);baseClip.graphics.clear();
         if(wallPixels.parent)wallPixels.parent.removeChild(wallPixels);
         if(field!=null)field.dispose();field=null;
         if(baseLight!=null)baseLight.dispose();baseLight=null;
         if(floorField!=null){floorField.dispose();wallField.dispose();fieldStamp.dispose();}floorField=wallField=fieldStamp=null;
         for each(var piece:Object in pieces)disposePiece(piece);pieces=[];
         owner=null;bounds=null;shapeKey=seenKey=lightKey="";faces=[];support=[];heights=null;
      }

      private function rebuildClip(loc:*):void {
         baseClip.graphics.clear();baseClip.graphics.beginFill(0xffffff);
         // Flash's vector mask stencil can fill even-odd holes. Emit only the
         // positive complement rectangles, so drawing and masking agree.
         var ox:int=left*CELL,oy:int=top*CELL,w:int=cols*CELL,h:int=rows*CELL;
         baseClip.graphics.drawRect(-80,-80,loc.spaceX*CELL+160,oy+80);
         baseClip.graphics.drawRect(-80,oy+h,loc.spaceX*CELL+160,loc.spaceY*CELL+80-oy-h);
         baseClip.graphics.drawRect(-80,oy,ox+80,h);
         baseClip.graphics.drawRect(ox+w,oy,loc.spaceX*CELL+80-ox-w,h);
         var rectangles:Array=[],previous:Object={};
         for(var y:int=0;y<h;y+=STEP){
            var intervals:Array=[],current:Object={};
            for each(var area:Rectangle in support)if(y>=area.top&&y<area.bottom)intervals.push(area);
            intervals.sortOn("x",Array.NUMERIC);
            var x:int=0;
            for(var i:int=0;i<=intervals.length;i++){
               var end:int=i<intervals.length?intervals[i].left:w;
               if(end>x){
                  var key:String=x+":"+end,rect:Rectangle=previous[key] as Rectangle;
                  if(rect!=null)rect.height+=STEP;
                  else{rect=new Rectangle(ox+x,oy+y,end-x,STEP);rectangles.push(rect);}
                  current[key]=rect;
               }
               if(i<intervals.length)x=Math.max(x,intervals[i].right);
            }
            previous=current;
         }
         for each(rect in rectangles)baseClip.graphics.drawRect(rect.x,rect.y,rect.width,rect.height);
         baseClip.graphics.endFill();
      }

      private function rebuildPieces():void {
         var old:Object={};
         for each(var piece:Object in pieces)old[piece.rect.toString()]=piece;
         pieces=[];
         for each(var rect:Rectangle in support){
            var key:String=rect.toString();piece=old[key];
            if(piece!=null)delete old[key];
            else {
               var stampRect:Rectangle=new Rectangle(rect.x/STEP-1,rect.y/STEP-1,rect.width/STEP+2,rect.height/STEP+2).intersection(field.rect);
               piece={rect:rect,previous:new BitmapData(rect.width,rect.height,true,0),
                  next:new BitmapData(rect.width,rect.height,true,0),output:new BitmapData(rect.width,rect.height,true,0),
                  floor:new BitmapData(rect.width,rect.height,false,0),wall:new BitmapData(rect.width,rect.height,true,0),
                  light:new BitmapData(rect.width,rect.height,false,0xffffff),version:-1,stampRect:stampRect,
                  base:new BitmapData(rect.width,rect.height,false,0),nextBase:new BitmapData(rect.width,rect.height,false,0),outputValid:false,
                  stamp:new BitmapData(stampRect.width,stampRect.height,false,0),nextStamp:new BitmapData(stampRect.width,stampRect.height,false,0)};
               piece.display=new Bitmap(piece.output);piece.display.x=rect.x;piece.display.y=rect.y;
               wallPixels.addChild(piece.display);
            }pieces.push(piece);
         }
         for each(piece in old)disposePiece(piece);
      }

      private function disposePiece(piece:Object):void {
         if(piece.display.parent)piece.display.parent.removeChild(piece.display);
         piece.display.bitmapData=null;piece.previous.dispose();piece.next.dispose();piece.output.dispose();
         piece.floor.dispose();piece.wall.dispose();piece.light.dispose();
         piece.base.dispose();piece.nextBase.dispose();
         piece.stamp.dispose();piece.nextStamp.dispose();
      }

      /** Disjoint pixel rectangles around the nonzero field, with a 5px halo
       * for bilinear filtering. Avoid copying all the empty space between walls. */
      private function rebuildSupport():void {
         support=[];
         var width:int=field.width,height:int=field.height;
         var pixels:Vector.<uint>=field.getVector(field.rect);
         var active:Vector.<int>=new Vector.<int>(width*height,true);
         for(var y:int=0;y<height;y++)for(var x:int=0;x<width;x++)if(pixels[x+y*width]>>>24)
            for(var yy:int=Math.max(0,y-1);yy<=Math.min(height-1,y+1);yy++)
               for(var xx:int=Math.max(0,x-1);xx<=Math.min(width-1,x+1);xx++)active[xx+yy*width]=1;
         var previous:Object={};
         for(y=0;y<height;y++){
            var current:Object={};x=0;
            while(x<width){
               if(!active[x+y*width]){x++;continue;}
               var begin:int=x;while(x<width&&active[x+y*width])x++;
               var key:String=begin+":"+x;
               var rect:Rectangle=previous[key] as Rectangle;
               if(rect!=null)rect.height+=STEP;
               else {rect=new Rectangle(begin*STEP,y*STEP,(x-begin)*STEP,STEP);support.push(rect);}
               current[key]=rect;
            }previous=current;
         }
      }

      private function plain(node:DisplayObject):Boolean {
         var matrix:Matrix=node.transform.matrix;
         var color:*=node.transform.colorTransform;
         return matrix.a==1&&matrix.b==0&&matrix.c==0&&matrix.d==1&&matrix.tx==int(matrix.tx)&&matrix.ty==int(matrix.ty)
            &&node.alpha==1&&node.blendMode=="normal"&&node.mask==null&&node.filters.length==0
            &&color.redMultiplier==1&&color.greenMultiplier==1&&color.blueMultiplier==1&&color.alphaMultiplier==1
            &&color.redOffset==0&&color.greenOffset==0&&color.blueOffset==0&&color.alphaOffset==0;
      }

      /** Native and chunked foregrounds are untranslated pixels inside translated
       * Bitmap children. copyPixels keeps alpha exact and is much cheaper than
       * rerendering a masked display tree. Unusual transforms use the safe draw path. */
      private function foregroundSources(front:DisplayObjectContainer):Array {
         if(!plain(front)||front.scrollRect!=null)return null;
         var node:DisplayObject,bmp:Bitmap,i:int;
         for(i=0;i<front.numChildren;i++){
            node=front.getChildAt(i);
            if(node.visible&&(!(node is Bitmap)||!plain(node)))return null;
         }
         var sources:Array=[];
         for(i=0;i<front.numChildren;i++){
            bmp=front.getChildAt(i) as Bitmap;
            if(bmp==null||!bmp.visible||bmp.bitmapData==null)continue;
            var scroll:Rectangle=bmp.scrollRect;
            var clip:Rectangle=scroll==null?bmp.bitmapData.rect:scroll.intersection(bmp.bitmapData.rect);
            var ox:int=front.x+bmp.x-left*CELL-(scroll==null?0:scroll.x);
            var oy:int=front.y+bmp.y-top*CELL-(scroll==null?0:scroll.y);
            var local:Rectangle=new Rectangle(clip.x+ox,clip.y+oy,clip.width,clip.height);
            sources.push({data:bmp.bitmapData,rect:local,x:ox,y:oy});
         }return sources;
      }

      private function copyForeground(sources:Array,area:Rectangle,target:BitmapData):void {
         for each(var source:Object in sources){
            var region:Rectangle=area.intersection(source.rect);if(region.isEmpty())continue;
            var dest:Point=new Point(region.x-area.x,region.y-area.y);region.offset(-source.x,-source.y);
            target.copyPixels(source.data,region,dest,null,null,true);
         }
      }

      private function occupied(wx:Number,wy:Number):Boolean {
         var x:int=Math.floor(wx/CELL),y:int=Math.floor(wy/CELL);
         var h:int=heights[x-left+1+(y-top+1)*(cols+2)];
         return h>0 && wy-y*CELL>=CELL-h;
      }

      private function rebuildFaces(loc:*):void {
         faces=[];
         for(var y:int=top;y<top+rows;y++) for(var x:int=left;x<left+cols;x++) {
            var h:int=heights[x-left+1+(y-top+1)*(cols+2)];
            if(h==0)continue;
            var x0:int=x*CELL,y0:int=(y+1)*CELL-h;
            for(var q:int=0;q<CELL;q+=STEP) {
               edge(x0+q+STEP/2,y0,0,x0+q+STEP/2,y0-0.5,loc);
               edge(x0+q+STEP/2,(y+1)*CELL,1,x0+q+STEP/2,(y+1)*CELL+0.5,loc);
            }
            for(q=0;q<h;q+=STEP) {
               edge(x0,y0+q+STEP/2,2,x0-0.5,y0+q+STEP/2,loc);
               edge(x0+CELL,y0+q+STEP/2,3,x0+CELL+0.5,y0+q+STEP/2,loc);
            }
         }
      }

      private function edge(x:Number,y:Number,dir:int,outX:Number,outY:Number,loc:*):void {
         if(outX<0 || outY<0 || outX>=loc.spaceX*CELL || outY>=loc.spaceY*CELL || occupied(outX,outY))return;
         faces.push(x,y,dir,int(outX/CELL),int(outY/CELL));
      }

      private function paintFace(wx:Number,wy:Number,dir:int,light:int,alwaysBright:Boolean):void {
         var vertical:Boolean=dir>=2;
         var sign:int=(dir==0 || dir==2)?1:-1;
         var along:int=Math.floor(((vertical?wy:wx)-(vertical?top:left)*CELL)/STEP);
         var edge:Number=((vertical?wx:wy)-(vertical?left:top)*CELL)/STEP;
         var low:int=Math.floor(edge-(sign>0?FRINGE:DEPTH)/STEP);
         var high:int=Math.ceil(edge+(sign>0?DEPTH:FRINGE)/STEP);
         for(var q:int=low;q<high;q++) {
            var distance:Number=(q+0.5-edge)*STEP*sign;
            if(distance < -FRINGE || distance>=DEPTH)continue;
            var a:int=distance<=BRIGHT?255:Math.round(255*(DEPTH-distance)/(DEPTH-BRIGHT));
            if(distance<0)a=Math.round(a*Math.min(1,(distance+FRINGE)/STEP));
            var px:int=vertical?q:along,py:int=vertical?along:q;
            if(px<0 || py<0 || px>=field.width || py>=field.height)continue;
            if(a>(field.getPixel32(px,py)>>>24))field.setPixel32(px,py,uint(a)<<24);
            var floorValue:int=Math.round(a*light/255),wallValue:int=alwaysBright?a:floorValue;
            if(floorValue>(floorField.getPixel(px,py)&255))floorField.setPixel(px,py,floorValue*0x010101);
            if(wallValue>(wallField.getPixel(px,py)&255))wallField.setPixel(px,py,wallValue*0x010101);
         }
      }

   }
}
