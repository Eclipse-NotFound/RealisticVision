               // A native long gun can extend beyond the body classification.
               // Keep the body fully lit while its actual muzzle points into dark space.
               var wp:*=u.currentWeapon,oldWX:Number=wp.X,oldWY:Number=wp.Y;
               var bb:Array=m.unitBBox(w.loc,u),edge:Number=(bb[2]+1)*40;
               for(i=0;i<m.fov.length;i++)m.fov[i]=1;
               m.classicLogicCache=null;m.currentSight.fillRect(m.currentSight.rect,0xffffffff);m.fogCache.fillRect(m.fogCache.rect,0);
               m.currentSight.fillRect(new Rectangle(4+edge/5,0,m.currentSight.width-4-edge/5,m.currentSight.height),0);
               m.fogCache.fillRect(new Rectangle(4+edge/5,0,m.fogCache.width-4-edge/5,m.fogCache.height),0xff000000);
               m.currentSightData=m.currentSight.getVector(m.currentSight.rect);m.classifiedSight=null;m.fovVersion++;
               wp.X=edge+80;wp.Y=600;wp.animate();wp.vis.visible=true;
               check("long weapon native positive "+mode,effectPixels(wp.vis)>0);
               m.hideEnemies(w,w.loc,true);
               check("body classification unchanged "+mode,m.enemyState(w.loc,u)==1);
               check("long weapon outside body hidden "+mode,effectPixels(wp.vis)==0);
               m.restoreAll(w,w.loc);wp.X=oldWX;wp.Y=oldWY;wp.animate();
               // New particle animation steps may set visible=true again. The
               // spatial mask must remain effective without suppressing step().
               for(i=0;i<m.fov.length;i++)m.fov[i]=0;
               m.currentSight.fillRect(m.currentSight.rect,0);m.currentSightData=null;m.fogCache.fillRect(m.fogCache.rect,0xff000000);m.fovVersion++;
               for(var age:int=0;age<8;age++){
                  var particle:*=ec.arr["iskr_bul"].cast(w.loc,600,600,{kol:1});particle.vis.visible=false;particle.step();
                  m.hideEnemies(w,w.loc,false);check("native particle animation cannot reveal "+mode+" "+age,effectPixels(particle.vis)==0);
               }
               m.restoreAll(w,w.loc);
