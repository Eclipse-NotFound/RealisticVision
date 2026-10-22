      private function inspectWeapons(w:*):void {
         var uc:Class=host.loaderInfo.applicationDomain.getDefinition("fe.unit.UnitRaider") as Class;
         var u:*=new uc("1",10,null,{weap:"smg10"});
         u.putLoc(w.loc,600,640);w.loc.addObj(u);w.loc.units.push(u);u.step();u.setVisPos();
         var wp:*=u.currentWeapon;wp.step();
         var chain:Boolean=false,obj:*=w.loc.firstObj,n:int=0;
         while(obj&&n++<5000){if(obj===wp)chain=true;obj=obj.nobj;}
         result.weapon={id:wp.id,inChain:chain,bodyParent:String(u.vis.parent),weaponParent:String(wp.vis.parent)};
         result.rows=[];
         for each(var mode:String in ["current","classic"]) for each(var name:String in ["baseline","candidate"]){
            var cls:Class=classes[name],m:*=new cls();m.cfgMode=mode;m.cfgDim=mode=="classic"?0.35:0.6;m.cfgSoftCurrent=25;m.cfgWallBright=false;m.cfgEnabled=true;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,w.loc);
            w.gg.setPos(480,640);w.gg.setVisPos();m.frameCount++;m.onFrameInner();
            if(m.currentSight==null)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);
            // Native actors/visuals, controlled logical boundary isolates attachment ownership.
            for(var i:int=0;i<m.fov.length;i++)m.fov[i]=0;
            var bb:Array=m.unitBBox(w.loc,u);m.fov[bb[0]+bb[1]*m.spaceX]=1;
            m.currentSight.fillRect(m.currentSight.rect,0);
            m.currentSight.setPixel32(4+bb[0]*8,4+bb[1]*8,0xffffffff);
            m.currentSightData=null;m.classifiedSight=null;m.sightClasses=null;m.fovVersion++;
            m.fogCache.fillRect(m.fogCache.rect,0xff000000);
            for(var f:int=0;f<6;f++){
               m.frameCount=f;m.hideEnemies(w,w.loc,f==0);
               var pixels:int=actorPixels(w,wp.vis,name+"-"+mode+"-"+f);
               result.rows.push({variant:name,mode:mode,frame:f,pixels:pixels,state:m.enemyState(w.loc,u),bodyVisible:u.vis.visible,weaponVisible:wp.vis.visible,bodyMask:u.vis.mask!=null,weaponMask:wp.vis.mask!=null,sameMask:u.vis.mask===wp.vis.mask,bodyCache:u.vis.cacheAsBitmap,weaponCache:wp.vis.cacheAsBitmap});
               check(name+" "+mode+" pixel reproduction "+f,name=="baseline"?pixels>0:pixels==0);
               if(name=="candidate") check(mode+" independent mask "+f,u.vis.mask!=null&&wp.vis.mask!=null&&u.vis.mask!==wp.vis.mask);
            }
            if(name=="candidate") {
               // Every frame, even without field changes: full dark -> visible -> partial.
               for(i=0;i<m.fov.length;i++)m.fov[i]=0;
               m.frameCount=7;m.hideEnemies(w,w.loc,false);check(mode+" hidden native child",!wp.vis.visible);
               for(i=0;i<m.fov.length;i++)m.fov[i]=1;
               m.currentSight.fillRect(m.currentSight.rect,0xffffffff);m.currentSightData=m.currentSight.getVector(m.currentSight.rect);m.fovVersion++;
               m.frameCount=8;m.hideEnemies(w,w.loc,false);check(mode+" restored visible child",wp.vis.visible&&wp.vis.mask==null&&!wp.vis.cacheAsBitmap);
               for(i=0;i<m.fov.length;i++)m.fov[i]=0;m.fov[bb[0]+bb[1]*m.spaceX]=1;
               m.currentSight.fillRect(m.currentSight.rect,0);m.currentSightData=null;m.fovVersion++;
               m.hideEnemies(w,w.loc,true);
               check(mode+" attached again",wp.vis.mask!=null);
               var old:*=wp.vis,oldShape:*=old.mask;wp.remVisual();wp.addVisual();wp.step();m.hideEnemies(w,w.loc,false);
               check(mode+" rebuilt visual mask",wp.vis.mask!=null);
               if(wp.vis!==old)check(mode+" old visual released",old.mask==null&&oldShape.parent==null);
               m.restoreAll(w,w.loc);check(mode+" switch off restores",wp.vis.mask==null&&wp.vis.visible&&!wp.vis.cacheAsBitmap);
               wp.vis.visible=false;m.hideEnemies(w,w.loc,true);m.restoreAll(w,w.loc);check(mode+" native hidden preserved",!wp.vis.visible);wp.vis.visible=true;
               for(i=0;i<m.fov.length;i++)m.fov[i]=0;m.hideEnemies(w,w.loc,true);u.sost=3;wp.vis.visible=false;m.hideEnemies(w,w.loc,true);check(mode+" dead weapon stays hidden",!wp.vis.visible&&wp.vis.mask==null);u.sost=1;wp.vis.visible=true;
               m.hideEnemies(w,w.loc,true);m.resetRoom(w,w.loc);check(mode+" room reset restores weapon",wp.vis.visible&&wp.vis.mask==null);
            }
            m.restoreAll(w,w.loc);if(m.fogVis)m.fogVis.visible=false;
         }
         save();trace("D36 WEAPON "+JSON.stringify(result));timer.stop();trace("FRAME COMPLETE");NativeApplication.nativeApplication.exit(0);
      }
      private function check(label:String,ok:Boolean):void {result.checks.push({label:label,pass:ok});trace((ok?"PASS ":"FAIL ")+label);if(!ok)throw new Error(label);}
      private function actorPixels(w:*,visual:DisplayObject,label:String):int {
         var layer:DisplayObjectContainer=visual.parent,states:Array=[],i:int;
         for(i=0;i<layer.numChildren;i++){var child:DisplayObject=layer.getChildAt(i);states.push([child,child.visible]);if(child!==visual&&child!==visual.mask)child.visible=false;}
         var bitmap:BitmapData=new BitmapData(240,180,true,0);
         bitmap.draw(layer,new Matrix(1,0,0,1,-480,-520),null,null,null,true);
         for each(var pair:Array in states)pair[0].visible=pair[1];
         var values:Vector.<uint>=bitmap.getVector(bitmap.rect),count:int=0;for each(var pixel:uint in values)if(pixel>>>24)count++;
         if(label.charAt(label.length-1)=="0"){
            var fs:FileStream=new FileStream();fs.open(new File(File.applicationDirectory.nativePath+"/evidence/"+label+".png"),FileMode.WRITE);fs.writeBytes(bitmap.encode(bitmap.rect,new PNGEncoderOptions()));fs.close();
         }
         bitmap.dispose();return count;
      }
