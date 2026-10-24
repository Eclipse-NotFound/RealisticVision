"""D48 candidate: reuse filtered samples in adjacent filterless world visuals."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=MOD/'build/shared-mask-output';BASE=MOD/'build/combat-render-output/production-final2/src'
assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()=='cb729dea25c7e2e2418212553e1f30f0153f34b3582a4a62b7825376762ba41d'
target=OUT/'candidates/shared/src';assert not target.exists();shutil.copytree(BASE,target)
path=target/'RealisticVisionMod.as';s=path.read_text(encoding='utf-8')
def patch(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
patch('      private var worldMasks:Object = {};','      private var worldMasks:Object = {};\n      private var sharedWorldMasks:Object = {};')
patch('''         raster.used=this.worldPass;
         this.refreshMask(raster,[x0,y0,x1,y1]);''','''         raster.used=this.worldPass;
         // Filter support can extend outside getBounds: preserve local masks.
         var shareAllowed:Boolean=!this.worldVisualHasFilters(visual);
         if(raster.shareAllowed!==shareAllowed){raster.shareAllowed=shareAllowed;raster.lastFov=-1;}
         this.refreshMask(raster,[x0,y0,x1,y1]);''')
patch('''            && rec.maskBounds == sig && rec.maskMode == this.cfgMode
            && rec.maskBlurX''','''            && rec.maskBounds == sig && rec.maskMode == this.cfgMode
            && rec.maskSharedAllowed === rec.shareAllowed
            && rec.maskBlurX''')
patch('''         rec.maskValid = false;
         if(blur.blurX > 0)''','''         rec.maskValid = false;
         var shared:Object=rec.worldRaster===true && rec.shareAllowed===true ? this.sharedWorldMask(bb,blur) : null;
         if(shared!=null)
         {
            // Only the invisible support gutter differs from a local blur.
            // Central samples and the bilinear neighbourhood are identical.
            bdb.copyPixels(shared.soft,new Rectangle((x0-shared.x)*MASK_SUB,(y0-shared.y)*MASK_SUB,totx,toty),this.fogPoint);
            // D48_SHARED_MASK_HIT
         }
         else if(blur.blurX > 0)''')
patch('''         if(this.cfgMode == "current")
         {
            // 只在可见侧淡出''','''         if(shared==null && this.cfgMode == "current")
         {
            // 只在可见侧淡出''')
patch('''         rec.maskBounds = sig; rec.maskMode = this.cfgMode;
         rec.maskBlurX''','''         rec.maskBounds = sig; rec.maskMode = this.cfgMode;rec.maskSharedAllowed=rec.shareAllowed;
         rec.maskBlurX''')
needle='      private function worldVisualHasFilters(visual:DisplayObject):Boolean'
patch(needle,'''      private function sharedWorldMask(bb:Array,blur:BlurFilter):Object
      {
         // Preserve local blur for wide kernels, cross-block objects, and
         // fields which have not yet been materialized by the original queries.
         if(blur.blurX<=0 || blur.blurY<=0
            || blur.blurX*blur.quality/2+2>MASK_PAD_X*MASK_SUB
            || blur.blurY*blur.quality/2+2>MASK_PAD_BOTTOM*MASK_SUB)return null;
         if(this.cfgMode!="current" && this.cfgMode!="classic")return null;
         if(this.cfgMode=="current" && this.currentSight==null)return null;
         if(this.cfgMode=="classic" && this.fogCache==null)return null;
         var bx:int=int(bb[0]/4)*4,by:int=int(bb[1]/4)*4;
         if(bb[2]>=bx+4 || bb[3]>=by+4)return null;
         var x0:int=Math.max(0,bx-MASK_PAD_X),y0:int=Math.max(0,by-MASK_PAD_TOP);
         var x1:int=Math.min(this.spaceX-1,bx+3+MASK_PAD_X),y1:int=Math.min(this.spaceY-1,by+3+MASK_PAD_BOTTOM);
         if(this.cfgMode=="classic" && this.classicLogicTiles!=null)
            for(var ty:int=y0;ty<=y1;ty++)for(var tx:int=x0;tx<=x1;tx++)
               if(!this.classicLogicTiles[tx+ty*this.spaceX])return null;
         var key:String=bx+","+by,rec:Object=this.sharedWorldMasks[key];
         if(rec==null){
            rec={x:x0,y:y0,lastFov:-1,raw:new BitmapData((x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB,true,0),soft:new BitmapData((x1-x0+1)*MASK_SUB,(y1-y0+1)*MASK_SUB,true,0)};
            this.sharedWorldMasks[key]=rec;
         }
         rec.used=this.worldPass;
         if(rec.lastFov==this.fovVersion && rec.mode==this.cfgMode && rec.bx==blur.blurX && rec.by==blur.blurY && rec.q==blur.quality)return rec;
         var raw:BitmapData=rec.raw as BitmapData,soft:BitmapData=rec.soft as BitmapData;
         var region:Rectangle=new Rectangle(FOG_PAD+x0*MASK_SUB,FOG_PAD+y0*MASK_SUB,raw.width,raw.height);
         if(this.cfgMode=="current")raw.copyPixels(this.currentSight,region,this.fogPoint);
         else {raw.fillRect(raw.rect,0);raw.threshold(this.fogCache,region,this.fogPoint,"<",uint(MASK_LIT_A)<<24,0xFFFFFFFF,0xFF000000,false);}
         soft.applyFilter(raw,raw.rect,this.fogPoint,blur);
         if(this.cfgMode=="current")this.finishCurrentMask(raw,soft);
         rec.lastFov=this.fovVersion;rec.mode=this.cfgMode;rec.bx=blur.blurX;rec.by=blur.blurY;rec.q=blur.quality;
         return rec;
      }

'''+needle)
patch('''         this.worldMasks={};this.worldPass=0;''','''         this.worldMasks={};this.worldPass=0;
         for each(var shared:Object in this.sharedWorldMasks){BitmapData(shared.raw).dispose();BitmapData(shared.soft).dispose();}
         this.sharedWorldMasks={};''')
patch('''               this.disposeWorldMask(raster);delete this.worldMasks[key];
            }
         }
      }

      private function applyWorldVisual''','''               this.disposeWorldMask(raster);delete this.worldMasks[key];
            }
         }
         if(this.worldPass%60==0)for(key in this.sharedWorldMasks){
            var shared:Object=this.sharedWorldMasks[key];
            if(this.worldPass-int(shared.used)>120){BitmapData(shared.raw).dispose();BitmapData(shared.soft).dispose();delete this.sharedWorldMasks[key];}
         }
      }

      private function applyWorldVisual''')
path.write_text(s,encoding='utf-8',newline='\n')
(target.parent/'manifest.json').write_text(json.dumps({p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*.as')},indent=2)+'\n',encoding='utf-8',newline='\n')
# Reuse known fixtures, with new paths and a new positive counter. Frozen D47
# sources are inputs only; no existing experiment is overwritten or rebuilt.
for name in ['group.py','validate.py','native-identity.as.inc','perf.py','IdentityCombatProbe.as']:
 text=(MOD/'build/frame-attribution'/name).read_text(encoding='utf-8').replace('frame-attribution','shared-mask').replace('D47','D48').replace('d47','d48')
 if name=='validate.py':
  text=text.replace("HERE/'run.py'","HERE/'perf.py'").replace('candidates/identity','candidates/shared').replace("candidate='identity'","candidate='shared'").replace("default='identity'","default='shared'")
  text=text.replace('identityHits','sharedHits').replace('// D48_IDENTITY_HIT','// D48_SHARED_MASK_HIT').replace("('identity','precise','cacheoff')","('shared','precise','cacheoff')").replace('IDENTITY hits=','SHARED hits=').replace('identity mask removal exercised','shared filtered field exercised')
 dest=HERE/name;assert not dest.exists();dest.write_text(text,encoding='utf-8',newline='\n')
steps=[['validate.py','dense-build','shared-pixels-01','--candidate','shared'],['validate.py','dense-run','shared-pixels-01'],['validate.py','native-build','shared-native-01','--candidate','shared'],['validate.py','native-run','shared-native-01']]
(HERE/'checks-steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8',newline='\n')
print('D48 shared-field candidate prepared; not installed')
