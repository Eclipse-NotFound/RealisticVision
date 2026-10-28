"""D55 exact rendered comparisons including proof that the new path executes."""
from pathlib import Path
import importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/effect-replay-output'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load('d53_check_runtime',MOD/'build/motion-performance/run.py')
name=sys.argv[1];folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
with r.Registration(owner='RealisticVision / D55 严格画面对照',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 src=folder/'src';r.public(OUT/'candidates'/('identity-blit' if '--identity-blit' in sys.argv else 'stable-v4' if '--stable-v4' in sys.argv else 'stable-v3' if '--stable-v3' in sys.argv else 'stable-v2' if '--stable-v2' in sys.argv else 'stable')/'src',src)
 p=src/'RealisticVisionMod.as';s=p.read_text();s=s.replace('public var worldPass:int = 0;','public var worldPass:int = 0;public var trailingHits:int=0;');s=s.replace('// D55_STABLE','trailingHits++;').replace('// D47_IDENTITY_HIT','trailingHits++;');p.write_text(s,encoding='utf-8')
 s=re.sub(r'\bprivate\b','public',(MOD/'build/combat-render-output/production-final2/src/RealisticVisionMod.as').read_text()).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
 t=(MOD/'build/effect-load-v3/EffectLoadChecks.as').read_text()
 if '--identity-blit' in sys.argv:
  t=t.replace('package {','package {\n import flash.filters.GlowFilter;')
  old='v.graphics.beginFill(0x12fd88+i);v.graphics.drawRect(-4,-2,8+(i%6)*7,4);v.graphics.endFill();'
  new='var data:BitmapData=new BitmapData([3,6,12][i%3],[3,6,12][i%3],true,0xff12fd88+i);data.setPixel32(0,0,0);v.addChild(new Bitmap(data,"auto",i%2==0));v.alpha=.25+(i%4)*.25;if(i%17==0)v.filters=[new GlowFilter(0x00ffff,.7,8,8)];'
  assert t.count(old)==1;t=t.replace(old,new)
  old='va.rotation=vb.rotation=(i+age)%19;'
  new=old+'Bitmap(va.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);Bitmap(vb.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);'
  assert t.count(old)==1;t=t.replace(old,new)
 t=t.replace('m.fovVersion++;m.worldPass++;','var blur:Number=[0,1,2,4,6,9][age%6];m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;m.fovVersion++;m.worldPass++;')
 t=t.replace('100+(i*61+age*17)%730+.3','(i*61+age*17)%920+.3').replace('140+(i*37)%500+.7','(i*37+age*5)%710+.7')
 t=t.replace('out.draw(layer);return out;','var zoom:Number=[.5,.75,1,1.5,2,1.25,4/3,2/3][f%8];out.draw(layer,new Matrix(zoom,0,0,zoom,.35,.65),null,null,null,true);return out;')
 if any(k in sys.argv for k in ['--stable','--integer','--integer-v2','--tight','--grid','--cell','--pixel-cache','--direct-cache','--direct-v2']):
  t=t.replace('Tile.tileX=Tile.tileY=40;', 'stage.scaleMode=StageScaleMode.NO_SCALE;stage.align=StageAlign.TOP_LEFT;Tile.tileX=Tile.tileY=40;')
  t=t.replace('addChild(la);addChild(lb);','var pa:Sprite=new Sprite(),pb:Sprite=new Sprite();addChild(pa);addChild(pb);pa.addChild(la);pb.addChild(lb);')
  t=t.replace('var start:int=getTimer();','var zoom:Number=[.5,.75,1,1.5,2,1.25,4/3,2/3][f%8],offset:Number=f%3==0?0:.35;la.transform.matrix=lb.transform.matrix=new Matrix(zoom,0,0,zoom,offset,offset);var start:int=getTimer();')
  t=t.replace('var zoom:Number=[.5,.75,1,1.5,2,1.25,4/3,2/3][f%8];out.draw(layer,new Matrix(zoom,0,0,zoom,.35,.65),null,null,null,true);return out;','out.draw(layer.parent);return out;')
 t=t.replace('if(++f>=360){','if(++f>=360){check(b.trailingHits>0,"early dark is exercised");trace("TRAILING hits="+b.trailingHits);removeEventListener(Event.ENTER_FRAME,step);')
 if '--explain' in sys.argv:
  marker='check(d is uint&&uint(d)==0,"exact dense moving visuals");'
  detail='''if(d is BitmapData){
   var hits:int=0,visList:Array=[];for(var j:int=0;j<500;j++){visList.push(aa[j].visible);aa[j].visible=bb[j].visible=false;}
   for(j=0;j<count;j++){aa[j].visible=bb[j].visible=true;var ia:BitmapData=imageOf(la),ib:BitmapData=imageOf(lb),idiff:Object=ia.compare(ib);
    if(idiff is BitmapData){
     var ar:Object=a.worldVisuals[aa[j]],br:Object=b.worldVisuals[bb[j]];
     if(ar && br && ar.raster && br.raster && ar.raster.m2e && br.raster.m2e){
      var ab:Array=ar.raster.lastBb.split(','),bbounds:Array=br.raster.lastBb.split(','),area:Rectangle=bb[j].getBounds(lb),changes:Array=[];
      for(var yy:int=Math.max(0,int(area.top/5)-1);yy<=int(area.bottom/5)+1;yy++)for(var xx:int=Math.max(0,int(area.left/5)-1);xx<=int(area.right/5)+1;xx++){
       var aval:uint=ar.raster.m2e.getPixel32(xx-int(ab[0])*8,yy-int(ab[1])*8),bval:uint=br.raster.m2e.getPixel32(xx-int(bbounds[0])*8,yy-int(bbounds[1])*8);
       if(aval!=bval && changes.length<12)changes.push([xx,yy,aval>>>24,bval>>>24]);
      }trace('MASK DATA '+JSON.stringify(changes));
     }
     trace('COUNTEREXAMPLE '+JSON.stringify({frame:f,index:j,bounds:String(bb[j].getBounds(lb)),position:[bb[j].x,bb[j].y],baseline:ar&&ar.raster?ar.raster.lastBb:null,candidate:br&&br.raster?br.raster.lastBb:null,stable:br?br.stableBb:null,baselineLit:ar&&ar.raster?ar.raster.fullyLit:null,candidateLit:br&&br.raster?br.raster.fullyLit:null,delta:String(BitmapData(idiff).getColorBoundsRect(0xffffffff,0,false))}));
     BitmapData(idiff).dispose();hits++;
    }ia.dispose();ib.dispose();aa[j].visible=bb[j].visible=false;if(hits>=8)break;
   }
   for(j=0;j<500;j++)aa[j].visible=bb[j].visible=visList[j];
  }'''+marker
  assert t.count(marker)==1;t=t.replace(marker,detail)
 if any(k in sys.argv for k in ['--stable','--integer','--integer-v2','--tight','--grid','--cell','--pixel-cache','--direct-cache','--direct-v2']):
  t=t.replace('group:int=int(f/30)','group:int=int(f/30)%12').replace('if(++f>=360){','if(++f>=720){')
  t=t.replace('offset:Number=f%3==0?0:.35;', 'offset:Number=f%3==0?0:.35;if(f<360){zoom=1;offset=0;}')
 if '--stable-v4' in sys.argv:
  t=t.replace('if(++f>=720){','if(++f>=1080){').replace('if(f<360){zoom=1;offset=0;}','if(f<360 || f>=720){zoom=1;offset=0;}')
  t=t.replace('var blur:Number=[0,1,2,4,6,9][age%6];','var blur:Number=f>=720?4:[0,1,2,4,6,9][age%6];')
  t=t.replace('20+age%10','20+(f>=720?0:age%10)').replace('m.fovVersion++;m.worldPass++;','if(f<720 || age==0)m.fovVersion++;m.worldPass++;')
 (folder/'EffectLoadChecks.as').write_text(t,encoding='utf-8')
 r.runner.compile(folder/'EffectLoadChecks.as',folder/'EffectLoadChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
 r.save(folder/'build.json',{'files':{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()}})
 code,log=r.air(folder,'EffectLoadChecks.swf',rec,300);(folder/'result.txt').write_text(log,encoding='utf-8')
 ok=code==0 and 'LOAD COMPLETE' in log and 'FAIL ' not in log
 r.save(folder/'validation.json',{'passed':ok,'exit':code,'checks':int(re.search(r'LOAD COMPLETE passed=(\d+)',log)[1]) if ok else 0})
 print(log[-1200:]);assert ok;rec.outcome='passed';rec.note='严格像素比较，仅功能证据'
