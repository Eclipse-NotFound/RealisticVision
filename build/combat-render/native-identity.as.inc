         // Same animation frame and visibility field, whole native effect parent.
         // Restoring each version prevents its mask from contaminating the next.
         var filtersIdentity:Array=[],supportHits:int=0;
         for each(var originalRow:Object in visuals)filtersIdentity.push(originalRow.vis.filters);
         for each(var identityMode:String in ["current","classic"]){
            var references:Array=[];
            for(var ageIdentity:int=0;ageIdentity<12;ageIdentity++){
               var filterIndex:int=0;
               for each(var visualRow:Object in visuals){
                  visualRow.vis.visible=true;
                  visualRow.vis.filters=(filtersIdentity[filterIndex++] as Array).concat(ageIdentity%3==0?[new GlowFilter(0xff44aa,1,20,20,2,1)]:[]);
                  if(visualRow.vis is MovieClip)MovieClip(visualRow.vis).nextFrame();
               }
               for each(var identityName:String in ["baseline","candidate"]){
                  var identityClass:Class=classes[identityName],identity:*=new identityClass();
                  identity.cfgMode=identityMode;identity.cfgEnabled=true;identity.cfgDim=.6;identity.mswRegistered=true;identity.cfgBaseRooms={};identity.resetRoom(w,w.loc);identity.onFrameInner();
                  if(identity.currentSight==null)identity.currentSight=new BitmapData(identity.fogCache.width,identity.fogCache.height,true,0);
                  identity.classicLogicCache=null;identity.currentSight.fillRect(identity.currentSight.rect,0xffffffff);identity.fogCache.fillRect(identity.fogCache.rect,0);
                  var cutoff:int=90+ageIdentity*5;
                  identity.currentSight.fillRect(new Rectangle(cutoff,0,identity.currentSight.width-cutoff,identity.currentSight.height),0);
                  identity.fogCache.fillRect(new Rectangle(cutoff,0,identity.fogCache.width-cutoff,identity.fogCache.height),0xff000000);
                  identity.currentSightData=null;identity.classifiedSight=null;identity.fovVersion++;
                  for(var repeatIdentity:int=0;repeatIdentity<3;repeatIdentity++){
                     identity.hideEnemies(w,w.loc,true);
                     if(identityName=="candidate" && ("worldVisualHasFilters" in identity))for each(var supportRecord:Object in identity.worldVisuals)
                        if(supportRecord.dark && !supportRecord.raster.fullyDark)supportHits++;
                     for(var visualIndex:int=0;visualIndex<visuals.length;visualIndex++){
                        var captured:BitmapData=effectImage(visuals[visualIndex].vis),referenceIndex:int=repeatIdentity*visuals.length+visualIndex;
                        if(identityName=="baseline")references[referenceIndex]=captured;
                        else {check("exact native repeated mask "+identityMode+" "+ageIdentity+" "+repeatIdentity+" "+visuals[visualIndex].kind,equal(captured,references[referenceIndex]));captured.dispose();BitmapData(references[referenceIndex]).dispose();}
                     }
                  }
                  identity.restoreAll(w,w.loc);if(identity.fogVis)identity.fogVis.visible=false;
               }
            }
         }
         for(var filterRestore:int=0;filterRestore<visuals.length;filterRestore++)visuals[filterRestore].vis.filters=filtersIdentity[filterRestore];
         if("worldVisualHasFilters" in identity)check("transparent-support shortcut actually exercised",supportHits>0);
