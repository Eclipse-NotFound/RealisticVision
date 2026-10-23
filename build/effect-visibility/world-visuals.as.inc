      /** Native transient visuals are independent of their shooter. Never change
       * visible/alpha or reparent content: native animation and lifetime own them. */
      private function applyWorldVisuals(w:World,loc:Location):void
      {
         this.worldPass++;
         var obj:Pt=loc.firstObj,guard:int=0;
         while(obj != null && guard++<5000)
         {
            var cls:Object=Object(obj).constructor;
            var kind:*=this.worldTypes[cls];
            if(kind === undefined)
            {
               var name:String=getQualifiedClassName(obj);
               kind=name=="fe.graph::Part" || name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet";
               this.worldTypes[cls]=kind;
            }
            if(kind && obj.vis != null)this.applyWorldVisual(obj.vis);
            obj=obj.nobj;
         }
         // UnitMerc.arm is package-internal, but its native display class is
         // unambiguous. Spatial clipping also works with overlapping mercenaries.
         if(w.grafon != null) for(var layerIndex:int=0;layerIndex<w.grafon.visObjs.length;layerIndex++)
         {
            var layer:DisplayObjectContainer=w.grafon.visObjs[layerIndex];
            // Releasing a now-fully-lit mask removes a sibling. Walk backwards
            // so that native reattachment and mask removal cannot stale length.
            for(var i:int=layer.numChildren-1;i>=0;i--)
            {
               var child:DisplayObject=layer.getChildAt(i);
               if(child is Shape)continue;
               cls=Object(child).constructor;kind=this.worldTypes[cls];
               if(kind === undefined){kind=getQualifiedClassName(child).indexOf("visualGrifArm")==0;this.worldTypes[cls]=kind;}
               if(kind)this.applyWorldVisual(child);
            }
         }
         // A fully visible body can carry a long gun beyond its own bounds.
         for each(var unit:Unit in loc.units)
         {
            if(unit == null || unit.player || unit.npc || unit.invis || unit.fraction==Unit.F_PLAYER || unit.sost>=3)continue;
            var ur:Object=this.unitVis[unit];
            if(ur == null || ur.state!=1)continue;
            var children:Array=Object(unit)["childObjs"] as Array;
            if(children == null)continue;
            for each(var entry:Object in children)
            {
               var weapon:Weapon=entry as Weapon;
               if(weapon != null && weapon.owner===unit && weapon.vis != null)this.applyWorldVisual(weapon.vis);
            }
         }
         for(var visual:Object in this.worldVisuals)
         {
            var record:Object=this.worldVisuals[visual];
            if(record.pass!=this.worldPass || DisplayObject(visual).parent==null)this.releaseWorldVisual(visual as DisplayObject,record);
         }
         if(this.worldPass%60==0)for(var key:String in this.worldMasks)
         {
            var raster:Object=this.worldMasks[key];
            if(this.worldPass-int(raster.used)>120)
            {
               this.disposeWorldMask(raster);delete this.worldMasks[key];
            }
         }
      }

      private function applyWorldVisual(visual:DisplayObject):void
      {
         if(visual.parent==null)return;
         var record:Object=this.worldVisuals[visual];
         if(record != null && visual.mask !== record.shape && visual.mask !== record.baseMask)
         {
            this.releaseWorldVisual(visual,record);record=null;
         }
         // Respect masks owned by the game or another mod. Existing native
         // projectile/particle/griffon visuals have none; unit masks stay separate.
         if(record==null && visual.mask!=null)return;
         if(!visual.visible && record==null)return;
         var bounds:Rectangle=visual.getBounds(visual.parent);
         var x0:int=Math.max(0,Math.floor(bounds.left/Tile.tileX));
         var y0:int=Math.max(0,Math.floor(bounds.top/Tile.tileY));
         var x1:int=Math.min(this.spaceX-1,Math.floor(bounds.right/Tile.tileX));
         var y1:int=Math.min(this.spaceY-1,Math.floor(bounds.bottom/Tile.tileY));
         if(x0>x1 || y0>y1)return;
         var key:String=x0+","+y0+","+x1+","+y1;
         var raster:Object=this.worldMasks[key];
         if(raster==null){raster={lastFov:-1,lastBb:"",m2:null,m3:null,m2d:null,m2e:null};this.worldMasks[key]=raster;}
         raster.used=this.worldPass;
         this.refreshMask(raster,[x0,y0,x1,y1]);
         // Leave fully lit native visuals untouched. Besides avoiding needless
         // caches, this preserves subpixel animation rendering exactly.
         if(raster.coverageFov!==this.fovVersion)
         {
            var rx:int=(x0-Math.max(0,x0-MASK_PAD_X))*MASK_SUB;
            var ry:int=(y0-Math.max(0,y0-MASK_PAD_TOP))*MASK_SUB;
            var pixels:Vector.<uint>=BitmapData(raster.m2e).getVector(new Rectangle(rx,ry,(x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB));
            var lit:Boolean=true;
            for each(var pixel:uint in pixels)if((pixel>>>24)!=255){lit=false;break;}
            // Include the full support region, including any native glow, in
            // the empty-mask fast path; it is exactly zero everywhere.
            var dark:Boolean=BitmapData(raster.m2e).getColorBoundsRect(0xff000000,0,false).isEmpty();
            raster.fullyLit=lit;raster.fullyDark=dark;raster.coverageFov=this.fovVersion;
         }
         if(raster.fullyLit)
         {
            if(record!=null)this.releaseWorldVisual(visual,record);
            return;
         }
         if(record==null)
         {
            record={shape:new Shape(),baseMask:visual.mask,cache:visual.cacheAsBitmap,raster:null,revision:-1};
            this.worldVisuals[visual]=record;
         }
         record.pass=this.worldPass;
         var shape:Shape=record.shape as Shape;
         if(record.raster!==raster || record.revision!=raster.maskRevision || record.dark!==raster.fullyDark)
         {
            if(raster.fullyDark)shape.graphics.clear();
            else shape.graphics.copyFrom(Shape(raster.m2).graphics);
            record.raster=raster;record.revision=raster.maskRevision;record.dark=raster.fullyDark;
         }
         if(shape.parent!==visual.parent)visual.parent.addChild(shape);
         shape.cacheAsBitmap=!raster.fullyDark;visual.cacheAsBitmap=raster.fullyDark?record.cache:true;visual.mask=shape;
      }

      private function releaseWorldVisual(visual:DisplayObject,record:Object):void
      {
         if(visual.mask===record.shape){visual.mask=record.baseMask;visual.cacheAsBitmap=record.cache;}
         var shape:Shape=record.shape as Shape;
         if(shape.parent!=null)shape.parent.removeChild(shape);
         delete this.worldVisuals[visual];
      }
      private function disposeWorldMask(record:Object):void
      {
         for each(var key:String in ["m2d","m2e","maskInput"])
            if(record[key] != null)BitmapData(record[key]).dispose();
      }
      private function restoreWorldVisuals():void
      {
         for(var visual:Object in this.worldVisuals)this.releaseWorldVisual(visual as DisplayObject,this.worldVisuals[visual]);
         for each(var raster:Object in this.worldMasks)this.disposeWorldMask(raster);
         this.worldMasks={};this.worldPass=0;
      }
