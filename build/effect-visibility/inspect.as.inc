      private function inspectEffects(w:*):void {
         var domain:ApplicationDomain=host.loaderInfo.applicationDomain;
         var uc:Class=domain.getDefinition("fe.unit.UnitMerc") as Class;
         var u:*=new uc("1",10,null,{weap:"smg10"});
         u.putLoc(w.loc,600,640);w.loc.addObj(u);w.loc.units.push(u);u.step();u.setVisPos();u.currentWeapon.step();
         // An exempt neighbour defeats the legacy proximity guess without changing the mercenary.
         var friendClass:Class=domain.getDefinition("fe.unit.Unit") as Class,friend:*=new friendClass();
         friend.X=600;friend.Y=610;friend.npc=true;w.loc.units.push(friend);
         var arm:DisplayObject;
         for(var i:int=0;i<w.grafon.visObjs[2].numChildren;i++){
            var c:DisplayObject=w.grafon.visObjs[2].getChildAt(i);
            if(getQualifiedClassName(c).indexOf("visualGrifArm")==0)arm=c;
         }
         check("native mercenary arm found",arm!=null);
         var visuals:Array=[{kind:"merc-arm",vis:arm},{kind:"merc-weapon",vis:u.currentWeapon.vis}];
         var bulletClass:Class=domain.getDefinition("fe.weapon.Bullet") as Class;
         for each(var type:String in ["visualBullet","visbullaser"]){
            var vc:Class=domain.getDefinition(type) as Class,b:*=new bulletClass(w.gg,600,600,vc);
            b.vis.visible=true;b.vis.scaleX=2;visuals.push({kind:type,vis:b.vis,obj:b});
         }
         var ec:Class=domain.getDefinition("fe.graph.Emitter") as Class;
         for each(var effect:String in ["iskr_bul","iskr","expl","gilza"]){
            var p:*=ec.arr[effect].cast(w.loc,600,600,{kol:1});
            check("native emitter "+effect,p&&p.vis);p.step();visuals.push({kind:effect,vis:p.vis,obj:p});
         }
         result.rows=[];
         for each(var mode:String in ["current","classic"])for each(var name:String in ["baseline","candidate"]){
            var cls:Class=classes[name],m:*=new cls();m.cfgMode=mode;m.cfgDim=.6;m.cfgEnabled=true;m.mswRegistered=true;m.cfgBaseRooms={};m.resetRoom(w,w.loc);
            w.gg.setPos(480,640);w.gg.setVisPos();m.frameCount++;m.onFrameInner();
            if(m.currentSight==null)m.currentSight=new BitmapData(m.fogCache.width,m.fogCache.height,true,0);
            for(i=0;i<m.fov.length;i++)m.fov[i]=0;
            m.currentSight.fillRect(m.currentSight.rect,0);m.currentSightData=null;m.classifiedSight=null;m.sightClasses=null;m.fovVersion++;
            m.fogCache.fillRect(m.fogCache.rect,0xff000000);
            // Freeze the canonical classic logical raster for an exact visibility fixture.
            m.classicLogicCache=null;
            for(var f:int=0;f<4;f++){
               m.frameCount=f;m.hideEnemies(w,w.loc,f==0);
               for each(var row:Object in visuals){
                  var n:int=effectPixels(row.vis);
                  result.rows.push({mode:mode,variant:name,frame:f,kind:row.kind,pixels:n,mask:row.vis.mask!=null,visible:row.vis.visible});
                  if(name=="baseline"&&row.kind!="merc-weapon")check("reproduced "+mode+" "+row.kind+" "+f,n>0);
                  if(name=="candidate"&&("worldVisuals" in m))check("fixed dark "+mode+" "+row.kind+" "+f,n==0);
               }
            }
            m.restoreAll(w,w.loc);if(m.fogVis)m.fogVis.visible=false;
            if(name=="candidate"&&("worldVisuals" in m)){
               for each(var state:String in ["light","partial","light","dark","light"]){
                  for(i=0;i<m.fov.length;i++)m.fov[i]=state=="dark"?0:1;
                  m.classicLogicCache=null;m.currentSight.fillRect(m.currentSight.rect,state=="dark"?0:0xffffffff);m.fogCache.fillRect(m.fogCache.rect,state=="dark"?0xff000000:0);
                  if(state=="partial"){
                     m.currentSight.fillRect(new Rectangle(4+120,0,m.currentSight.width-124,m.currentSight.height),0);
                     m.fogCache.fillRect(new Rectangle(4+120,0,m.fogCache.width-124,m.fogCache.height),0xff000000);
                  }
                  m.currentSightData=null;m.classifiedSight=null;m.fovVersion++;
                  // Capture original visible material before applying the new world masks.
                  var originals:Array=[];
                  for each(row in visuals){row.vis.visible=true;originals.push(effectImage(row.vis));}
                  m.hideEnemies(w,w.loc,true);
                  for(i=0;i<visuals.length;i++){
                     row=visuals[i];var out:BitmapData=effectImage(row.vis),ref:BitmapData=originals[i];
                     if(state=="light")check("visible pixel identity "+mode+" "+row.kind,equal(out,ref));
                     if(state=="dark")check("reentry dark "+mode+" "+row.kind,out.getColorBoundsRect(0xff000000,0,false).isEmpty());
                     if(state=="partial"&&row.kind!="merc-weapon"){
                        var right:BitmapData=new BitmapData(140,240,true,0);right.copyPixels(out,new Rectangle(260,0,140,240),new Point());
                        check("partial hidden side "+mode+" "+row.kind,right.getColorBoundsRect(0xff000000,0,false).isEmpty());right.dispose();
                     }
                     if(state=="partial"){var fs:FileStream=new FileStream();fs.open(new File(File.applicationDirectory.nativePath+"/evidence/"+mode+"-"+row.kind+".png"),FileMode.WRITE);fs.writeBytes(out.encode(out.rect,new PNGEncoderOptions()));fs.close();}
                     ref.dispose();out.dispose();
                  }
                  m.restoreAll(w,w.loc);
                  for each(row in visuals)check("restored native mask "+mode+" "+row.kind,row.vis.mask==null);
               }
               arm.visible=false;m.hideEnemies(w,w.loc,true);m.restoreAll(w,w.loc);check("native dead arm preserved "+mode,!arm.visible);arm.visible=true;
               m.hideEnemies(w,w.loc,true);var prior:*=visuals[2].vis,priorMask:*=prior.mask;
               prior.parent.removeChild(prior);m.hideEnemies(w,w.loc,false);check("removed effect released "+mode,prior.mask==null&&(priorMask==null||priorMask.parent==null));w.grafon.visObjs[2].addChild(prior);
               m.hideEnemies(w,w.loc,false);m.resetRoom(w,w.loc);check("room reset releases effects "+mode,prior.mask==null&&arm.mask==null);
            }
         }
         save();trace("D42 EFFECT "+JSON.stringify(result));timer.stop();trace("FRAME COMPLETE");NativeApplication.nativeApplication.exit(0);
      }
      private function check(label:String,ok:Boolean):void {result.checks.push({label:label,pass:ok});trace((ok?"PASS ":"FAIL ")+label);if(!ok)throw new Error(label);}
      private function effectPixels(visual:DisplayObject):int {
         var bitmap:BitmapData=effectImage(visual);
         var values:Vector.<uint>=bitmap.getVector(bitmap.rect),count:int=0;for each(var pixel:uint in values)if(pixel>>>24)count++;
         bitmap.dispose();return count;
      }
      private function effectImage(visual:DisplayObject):BitmapData {
         var layer:DisplayObjectContainer=visual.parent,states:Array=[],i:int;
         for(i=0;i<layer.numChildren;i++){var c:DisplayObject=layer.getChildAt(i);states.push([c,c.visible]);if(c!==visual&&c!==visual.mask)c.visible=false;}
         var bitmap:BitmapData=new BitmapData(400,240,true,0);bitmap.draw(layer,new Matrix(1,0,0,1,-400,-480),null,null,null,true);
         for each(var pair:Array in states)pair[0].visible=pair[1];
         return bitmap;
      }
