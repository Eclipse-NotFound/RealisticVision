from pathlib import Path
import shutil,json
MOD=Path(__file__).resolve().parents[2];OLD=MOD/'build/effect-load-v2-output';OUT=MOD/'build/effect-load-v3-output';HERE=MOD/'build/effect-load-v3'
assert not OUT.exists() and not HERE.exists();OUT.mkdir();HERE.mkdir()
for name in ['baseline','candidate']:shutil.copytree(OLD/'baseline',OUT/name)
shutil.copyfile(OLD/'inputs.json',OUT/'inputs.json')
for f in (MOD/'build/effect-load-v2').iterdir():
 if f.is_file() and f.name not in ['refine.py','prepare_singlepass.py']:
  (HERE/f.name).write_text(f.read_text(encoding='utf-8').replace('effect-load-v2-output','effect-load-v3-output'),encoding='utf-8',newline='\n')
p=OUT/'candidate/src/RealisticVisionMod.as';s=p.read_text(encoding='utf-8')
start=s.index('      private function refreshMask');end=s.index('      /** Same alpha arithmetic',start);part=s[start:end]
part=part.replace('            bdb = new BitmapData(totx,toty,true,0);','            bdb = null;')
a=part.index('         var s2:Shape');b=part.index('         // 子格级判定',a);shapes=part[a:b];part=part[:a]+part[b:]
part=part.replace('         bd.lock();','         var matches:int=-1;\n         bd.lock();',1)
part=part.replace('            bd.threshold(this.fogCache,','            matches=bd.threshold(this.fogCache,',1)
needle='         // Every eligible sample is still refreshed above.'
assert needle in part
part=part.replace(needle,'''         // Independent visuals can use native drawing / an empty shape when
         // the complete support field is uniform. Classify the samples already
         // written above; mixed fields never repeat classicLogicRegion/threshold.
         if(rec.worldRaster === true)
         {
            var dark:Boolean,lit:Boolean;
            if(matches>=0){dark=matches==0;lit=matches==totx*toty;}
            else {
               var first:uint=bd.getPixel32(0,0)>>>24;
               dark=first==0 && !bd.hitTest(this.fogPoint,1,bd.rect);
               lit=first==255 && bd.getColorBoundsRect(0xff000000,0xff000000,false).isEmpty();
            }
            if(lit && (bb[0]-x0<MASK_PAD_X || bb[1]-y0<MASK_PAD_TOP || x1-bb[2]<MASK_PAD_X || y1-bb[3]<MASK_PAD_BOTTOM
               || blur.blurX*blur.quality/2+2>MASK_PAD_X*MASK_SUB
               || blur.blurY*blur.quality/2+2>MASK_PAD_BOTTOM*MASK_SUB))lit=false;
            if(dark || lit){
               rec.fullyDark=dark;rec.fullyLit=lit;rec.coverageFov=this.fovVersion;
               rec.maskValid=false;
               return;
            }
         }
         if(bdb==null){bdb=new BitmapData(totx,toty,true,0);rec.m2e=bdb;}
'''+shapes+needle,1)
s=s[:start]+part+s[end:]
old='raster={lastFov:-1,lastBb:"",m2:null,m3:null,m2d:null,m2e:null}'
assert s.count(old)==1;s=s.replace(old,'raster={worldRaster:true,lastFov:-1,lastBb:"",m2:null,m3:null,m2d:null,m2e:null}')
p.write_text(s,encoding='utf-8',newline='\n')
(OLD/'performance-decision.json').write_text(json.dumps({'accepted':False,'reason':'360帧像素一致；密集交界仍需重复采样和分类，转为单次采样候选，不运行原生完整性能轮或部署。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('single-pass candidate prepared')
