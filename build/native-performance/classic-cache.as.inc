      private function classicDifference(a:BitmapData,b:BitmapData):Rectangle
      {
         var difference:Object=a.compare(b);
         if(difference is uint && uint(difference)==0)return new Rectangle();
         if(!(difference is BitmapData))return a.rect;
         var bitmap:BitmapData=difference as BitmapData;
         var region:Rectangle=bitmap.getColorBoundsRect(0xFFFFFFFF,0,false);
         bitmap.dispose();return region;
      }

      /** Cache only after comparing actual raster inputs and complete geometry.
       * The two join passes own separate snapshots, including softened-floor blue.
       * No timer, camera guess or native-light revision stands in for pixel data. */
      private function prepareClassicJoin(slot:int,loc:Location):Object
      {
         var item:Object=this.classicJoins[slot];
         if(item==null || item.raw.width!=this.fogRaw.width || item.raw.height!=this.fogRaw.height)
         {
            if(item!=null)this.disposeClassicJoin(item);
            item={raw:this.fogRaw.clone(),visibility:this.classicVisibilityField.clone(),wall:this.wallRaw.clone(),
               output:this.fogBmp.clone(),shade:this.classicWallShade.clone(),walls:this.wallTiles.concat(),
               region:new Rectangle(0,0,this.spaceX,this.spaceY)};
            this.classicJoins[slot]=item;return item;
         }
         var dirty:Rectangle=this.classicDifference(this.fogRaw,item.raw);
         var change:Rectangle=this.classicDifference(this.classicVisibilityField,item.visibility);
         if(!change.isEmpty())dirty=dirty.isEmpty()?change:dirty.union(change);
         change=this.classicDifference(this.wallRaw,item.wall);
         if(!change.isEmpty())
         {
            change=new Rectangle(FOG_PAD+change.x*FOG_SUB,FOG_PAD+(change.y-1)*FOG_SUB,change.width*FOG_SUB,change.height*FOG_SUB);
            if(dirty.isEmpty())dirty=change;else dirty=dirty.union(change);
         }
         var geometryChanged:Boolean=item.walls.length!=this.wallTiles.length;
         if(!geometryChanged)for(var i:int=0;i<this.wallTiles.length;i++)if(item.walls[i]!=this.wallTiles[i]){geometryChanged=true;break;}
         if(geometryChanged){dirty=this.fogRect.clone();item.walls=this.wallTiles.concat();}
         item.raw.copyPixels(this.fogRaw,this.fogRect,this.fogPoint);
         item.visibility.copyPixels(this.classicVisibilityField,this.fogRect,this.fogPoint);
         item.wall.copyPixels(this.wallRaw,this.wallRaw.rect,this.fogPoint);
         if(dirty.isEmpty()){item.region=new Rectangle();return item;}
         // Joins use bilinear corner and edge samples from adjacent tiles.
         var x0:int=Math.max(0,Math.floor((dirty.left-FOG_PAD)/FOG_SUB)-2);
         var y0:int=Math.max(0,Math.floor((dirty.top-FOG_PAD)/FOG_SUB)-2);
         var x1:int=Math.min(this.spaceX,Math.ceil((dirty.right-FOG_PAD)/FOG_SUB)+2);
         var y1:int=Math.min(this.spaceY,Math.ceil((dirty.bottom-FOG_PAD)/FOG_SUB)+2);
         item.region=new Rectangle(x0,y0,x1-x0,y1-y0);
         // Preserve the new uncorrected input inside the dirty area. Reuse only
         // the already-corrected pixels whose complete dependencies are equal.
         var left:int=FOG_PAD+x0*FOG_SUB,top:int=FOG_PAD+y0*FOG_SUB;
         var right:int=FOG_PAD+x1*FOG_SUB,bottom:int=FOG_PAD+y1*FOG_SUB;
         var areas:Array=[new Rectangle(FOG_PAD,FOG_PAD,this.spaceX*FOG_SUB,top-FOG_PAD),
            new Rectangle(FOG_PAD,bottom,this.spaceX*FOG_SUB,FOG_PAD+this.spaceY*FOG_SUB-bottom),
            new Rectangle(FOG_PAD,top,left-FOG_PAD,bottom-top),
            new Rectangle(right,top,FOG_PAD+this.spaceX*FOG_SUB-right,bottom-top)];
         for each(var area:Rectangle in areas)if(!area.isEmpty())this.fogBmp.copyPixels(item.output,area,new Point(area.x,area.y));
         return item;
      }

      private function disposeClassicJoin(item:Object):void
      {
         item.raw.dispose();item.visibility.dispose();item.wall.dispose();item.output.dispose();item.shade.dispose();
      }

      private function releaseClassicJoins():void
      {
         for each(var item:Object in this.classicJoins)if(item!=null)this.disposeClassicJoin(item);
         this.classicJoins=[];
      }
