      private function applyUnitWeapons(u:Unit, state:int, exempt:Dictionary):void
      {
         var children:Array=Object(u)["childObjs"] as Array;
         if(children == null) return;
         for each(var child:Object in children)
         {
            var weapon:Weapon=child as Weapon;
            if(weapon == null || weapon.owner !== u) continue;
            if(weapon.vis) exempt[weapon.vis]=true;
            this.applyWeaponVisual(weapon,u,u.sost >= 3 ? 1 : state);
         }
      }

      private function applyWeaponVisual(weapon:Weapon, owner:Unit, state:int):void
      {
         var visual:DisplayObject=weapon.vis;
         if(visual == null) return;
         var record:Object=this.weaponVisuals[visual];
         if(state == 1)
         {
            if(record != null) this.releaseWeaponVisual(visual,record);
            return;
         }
         if(record == null)
         {
            record={weapon:weapon,owner:owner,visible:visual.visible,cache:visual.cacheAsBitmap,mask:visual.mask,shape:null,revision:-1,hidden:false};
            this.weaponVisuals[visual]=record;
         }
         record.pass=this.weaponPass;
         var shape:Shape=record.shape as Shape;
         if(state == 0)
         {
            visual.visible=false;record.hidden=true;
            visual.mask=record.mask;visual.cacheAsBitmap=record.cache;
            if(shape != null && shape.parent != null) shape.parent.removeChild(shape);
            return;
         }
         var unitRecord:Object=this.unitVis[owner];
         if(unitRecord == null || unitRecord.m2 == null || visual.parent == null) return;
         if(record.hidden) {visual.visible=record.visible;record.hidden=false;}
         if(shape == null) {shape=new Shape();shape.cacheAsBitmap=true;record.shape=shape;}
         if(record.revision != unitRecord.maskRevision)
         {
            shape.graphics.copyFrom(Shape(unitRecord.m2).graphics);
            record.revision=unitRecord.maskRevision;
         }
         if(shape.parent !== visual.parent) visual.parent.addChild(shape);
         // Each display object owns a mask. Only the immutable raster is shared.
         visual.cacheAsBitmap=true;visual.mask=shape;
      }

      private function releaseWeaponVisual(visual:DisplayObject, record:Object):void
      {
         if(record.hidden && (record.owner == null || record.owner.sost < 3)) visual.visible=record.visible;
         if(visual.mask === record.shape || record.hidden) visual.mask=record.mask;
         visual.cacheAsBitmap=record.cache;
         var shape:Shape=record.shape as Shape;
         if(shape != null && shape.parent != null) shape.parent.removeChild(shape);
         delete this.weaponVisuals[visual];
      }

      private function restoreWeaponVisuals():void
      {
         for(var visual:Object in this.weaponVisuals)
            this.releaseWeaponVisual(visual as DisplayObject,this.weaponVisuals[visual]);
      }
