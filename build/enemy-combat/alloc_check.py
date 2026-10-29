"""D56 exact rendered comparisons including proof that the new path executes."""
from pathlib import Path
import importlib.util,json,re,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/enemy-combat-output'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=load('d53_check_runtime',MOD/'build/motion-performance/run.py')
name=sys.argv[1];folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
chosen=next((x.split('=',1)[1] for x in sys.argv if x.startswith('--source=')),None)
assert chosen is None or (chosen.isidentifier() and (OUT/'candidates'/chosen/'src').is_dir())
with r.Registration(owner='RealisticVision / D57 严格画面对照',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 src=folder/'src';r.public(OUT/'candidates'/chosen/'src',src)
 p=src/'RealisticVisionMod.as';s=p.read_text();s=s.replace('public var worldPass:int = 0;','public var worldPass:int = 0;public var trailingHits:int=0;');s=s.replace('// D56_LOCAL','trailingHits++;').replace('// D56_SOLID','trailingHits++;').replace('// D56_DARK_CHILD','trailingHits++;').replace('// D54_TRAILING','trailingHits++;').replace('// D47_IDENTITY_HIT','trailingHits++;');p.write_text(s,encoding='utf-8')
 if chosen:
  import shutil
  for original in (OUT/'candidates'/chosen/'src').rglob('*.as'):
   target=src/original.relative_to(OUT/'candidates'/chosen/'src')
   target.write_text(re.sub(r'\bprivate\b','public',original.read_text()).replace('public var worldPass:int = 0;','public var worldPass:int = 0;public var trailingHits:int=0;').replace('// D56_REFRESH:','trailingHits++; // D56_REFRESH:'),encoding='utf-8')
 if '--offscreen' in sys.argv:
  s=p.read_text().replace('// D56_OFFSCREEN:','trailingHits++; // D56_OFFSCREEN:');p.write_text(s,encoding='utf-8')
 s=re.sub(r'\bprivate\b','public',(OUT/'baseline/src/RealisticVisionMod.as').read_text()).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
 t=(MOD/'build/effect-load-v3/EffectLoadChecks.as').read_text()
 if '--dark-native' in sys.argv:t=t.replace('b.applyWorldVisual(bb[i])','b.applyWorldVisual(bb[i],true)')
 if '--dark-native' in sys.argv:
  t=t.replace(' private function fail(', (HERE/'DarkChildChecks.inc.as').read_text()+'\n private function fail(')
  t=t.replace('trace("LOAD COMPLETE passed="+passed);','darkChildChecks();trace("LOAD COMPLETE passed="+passed);')
 if '--identity-blit' in sys.argv:
  t=t.replace('package {','package {\n import flash.filters.GlowFilter;')
  old='v.graphics.beginFill(0x12fd88+i);v.graphics.drawRect(-4,-2,8+(i%6)*7,4);v.graphics.endFill();'
  new='var data:BitmapData=new BitmapData([3,6,12][i%3],[3,6,12][i%3],true,0xff12fd88+i);data.setPixel32(0,0,0);v.addChild(new Bitmap(data,"auto",i%2==0));v.alpha=.25+(i%4)*.25;if(i%17==0)v.filters=[new GlowFilter(0x00ffff,.7,8,8)];'
  assert t.count(old)==1;t=t.replace(old,new)
  old='va.rotation=vb.rotation=(i+age)%19;'
  new=old+'Bitmap(va.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);Bitmap(vb.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);'
  assert t.count(old)==1;t=t.replace(old,new)
 if '--opaque' in sys.argv:
  t=t.replace('va.rotation=vb.rotation=(i+age)%19;', 'va.rotation=vb.rotation=(i+age)%19;va.alpha=vb.alpha=[1,.75,.5,.25][(i+age)%4];')
  t=t.replace('var start:int=getTimer();','la.alpha=lb.alpha=f%9==0?.5:1;var start:int=getTimer();')
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
 if '--min-case' in sys.argv:
  assert '--explain' in sys.argv
  t=t.replace('package {','package {\n import flash.filesystem.*;')
  t=t.replace('addEventListener(Event.ENTER_FRAME,step);','f=120;addEventListener(Event.ENTER_FRAME,step);')
  hook='BitmapData(idiff).dispose();hits++;'
  capture='''if(hits==0){
    var outRoot:String=File.applicationDirectory.nativePath.replace(/\\\\/g,'/');
    if(outRoot.indexOf('/RealisticVision/build/enemy-combat-output/')<0)throw new Error('wrong image directory');
    var outDir:File=new File(outRoot+'/evidence');outDir.createDirectory();
    var roi:Rectangle=bb[j].getBounds(lb);roi=new Rectangle(Math.floor(roi.x)-4,Math.floor(roi.y)-4,Math.ceil(roi.width)+9,Math.ceil(roi.height)+9);
    var maskA:BitmapData=new BitmapData(960,720,true,0),maskB:BitmapData=new BitmapData(960,720,true,0);
    var maskClone:Shape=new Shape();maskClone.graphics.copyFrom(Shape(ar.shape).graphics);maskClone.transform.matrix=ar.shape.transform.matrix;maskA.draw(maskClone);
    maskClone=new Shape();maskClone.graphics.copyFrom(Shape(br.shape).graphics);maskClone.transform.matrix=br.shape.transform.matrix;maskB.draw(maskClone);
    var details:Array=[],differing:int=0,maskDiff:int=0,maxChannel:int=0;
    for(var py:int=roi.y;py<roi.bottom;py++)for(var px:int=roi.x;px<roi.right;px++){
     var av:uint=ia.getPixel32(px,py),bv:uint=ib.getPixel32(px,py),am:uint=maskA.getPixel32(px,py)>>>24,bm:uint=maskB.getPixel32(px,py)>>>24;
     if(am!=bm)maskDiff++;
     if(av!=bv){differing++;for(var channel:int=0;channel<4;channel++)maxChannel=Math.max(maxChannel,Math.abs(int((av>>>(channel*8))&255)-int((bv>>>(channel*8))&255)));if(details.length<12)details.push({x:px,y:py,a:av.toString(16),b:bv.toString(16),mask:[am,bm]});}
    }
    trace('PIXEL DETAILS '+JSON.stringify({frame:f,index:j,alpha:bb[j].alpha,roi:String(roi),differing:differing,maxChannel:maxChannel,maskAlphaDifferences:maskDiff,pixels:details}));
    for each(var capture:Object in [{name:'baseline',data:ia},{name:'candidate',data:ib},{name:'mask-baseline',data:maskA},{name:'mask-candidate',data:maskB}]){
     var small:BitmapData=new BitmapData(roi.width,roi.height,true,0);small.copyPixels(capture.data,roi,new Point());
     var file:FileStream=new FileStream();file.open(outDir.resolvePath(capture.name+'.png'),FileMode.WRITE);file.writeBytes(small.encode(small.rect,new PNGEncoderOptions()));file.close();small.dispose();
    }maskA.dispose();maskB.dispose();
   }
   '''+hook
  if '--fresh' in sys.argv:
   point="trace('PIXEL DETAILS '+JSON.stringify({frame:f,index:j,alpha:bb[j].alpha,roi:String(roi),differing:differing,maxChannel:maxChannel,maskAlphaDifferences:maskDiff,pixels:details}));"
   fresh='''
    a.restoreWorldVisuals();a.applyWorldVisual(aa[j]);var fresh:BitmapData=imageOf(la);
    var freshOld:Object=fresh.compare(ia),freshCandidate:Object=fresh.compare(ib);
    trace('FRESH BASELINE '+JSON.stringify({frame:f,index:j,oldEqual:freshOld is uint && uint(freshOld)==0,candidateEqual:freshCandidate is uint && uint(freshCandidate)==0,oldDelta:freshOld is BitmapData?String(BitmapData(freshOld).getColorBoundsRect(0xffffffff,0,false)):null,candidateDelta:freshCandidate is BitmapData?String(BitmapData(freshCandidate).getColorBoundsRect(0xffffffff,0,false)):null}));
    if(freshOld is BitmapData)BitmapData(freshOld).dispose();if(freshCandidate is BitmapData)BitmapData(freshCandidate).dispose();
   '''
   assert capture.count(point)==1;capture=capture.replace(point,point+fresh)
   capture=capture.replace("[{name:'baseline',data:ia}","[{name:'fresh-baseline',data:fresh},{name:'baseline',data:ia}")
   capture=capture.replace('}maskA.dispose();maskB.dispose();','}maskA.dispose();maskB.dispose();fresh.dispose();')
   t=t.replace('if(hits>=8)break;','if(hits>=1)break;')
  if '--invalidate-steps' in sys.argv:
   assert '--fresh' in sys.argv
   point='a.restoreWorldVisuals();a.applyWorldVisual(aa[j]);var fresh:BitmapData=imageOf(la);'
   steps='''
    var oldMask:Shape=ar.shape as Shape,oldCache:Boolean=aa[j].cacheAsBitmap;
    for(var action:int=0;action<4;action++){
     if(action==0){aa[j].mask=null;aa[j].mask=oldMask;}
     if(action==1){aa[j].cacheAsBitmap=false;oldMask.cacheAsBitmap=false;oldMask.cacheAsBitmap=true;aa[j].cacheAsBitmap=oldCache;}
     if(action==2){oldMask.graphics.clear();oldMask.graphics.copyFrom(Shape(ar.raster.m2).graphics);}
     if(action==3){var directSource:BitmapData=ar.raster.m2e as BitmapData,origin:Array=ar.raster.lastBb.split(',');oldMask.graphics.clear();oldMask.graphics.beginBitmapFill(directSource,new Matrix(5,0,0,5,int(origin[0])*40,int(origin[1])*40),false,true);oldMask.graphics.drawRect(int(origin[0])*40,int(origin[1])*40,directSource.width*5,directSource.height*5);oldMask.graphics.endFill();}
     var shot:BitmapData=imageOf(la),deltaOld:Object=shot.compare(ia),deltaNew:Object=shot.compare(ib);
     trace('INVALIDATE STEP '+JSON.stringify({action:action,oldEqual:deltaOld is uint && uint(deltaOld)==0,candidateEqual:deltaNew is uint && uint(deltaNew)==0}));
     if(deltaOld is BitmapData)BitmapData(deltaOld).dispose();if(deltaNew is BitmapData)BitmapData(deltaNew).dispose();shot.dispose();
    }
    '''+point
   assert capture.count(point)==1;capture=capture.replace(point,steps)
  assert t.count(hook)==1;t=t.replace(hook,capture)
 if '--fresh-reference' in sys.argv:
  t=t.replace('var start:int=getTimer();','a.restoreWorldVisuals();var start:int=getTimer();')
 if '--fresh-current-reference' in sys.argv:
  assert '--fresh-reference' not in sys.argv
  t=t.replace('var start:int=getTimer();','if(a.cfgMode=="current")a.restoreWorldVisuals();var start:int=getTimer();')
 if '--offscreen' in sys.argv:
  t=t.replace('(i*61+age*17)%920+.3','(i*61+age*57)%1900+.3').replace('(i*37+age*5)%710+.7','(i*37+age*31)%1500+.7')
  t=t.replace('new BitmapData(960,720,true,0);out.draw', 'new BitmapData(Math.min(960,stage.stageWidth),Math.min(720,stage.stageHeight),true,0);out.draw')
  t=t.replace('f=120;addEventListener', "trace('ACTUAL VIEWPORT '+stage.stageWidth+','+stage.stageHeight);f=120;addEventListener")
  t=t.replace('addEventListener(Event.ENTER_FRAME,step);', "trace('ACTUAL VIEWPORT '+stage.stageWidth+','+stage.stageHeight);addEventListener(Event.ENTER_FRAME,step);")
 if any(k in sys.argv for k in ['--stable','--integer','--integer-v2','--tight','--grid','--cell','--pixel-cache','--direct-cache','--direct-v2']):
  t=t.replace('group:int=int(f/30)','group:int=int(f/30)%12').replace('if(++f>=360){','if(++f>=720){')
  t=t.replace('offset:Number=f%3==0?0:.35;', 'offset:Number=f%3==0?0:.35;if(f<360){zoom=1;offset=0;}')
 if '--stable-v4' in sys.argv:
  t=t.replace('if(++f>=720){','if(++f>=1080){').replace('if(f<360){zoom=1;offset=0;}','if(f<360 || f>=720){zoom=1;offset=0;}')
  t=t.replace('var blur:Number=[0,1,2,4,6,9][age%6];','var blur:Number=f>=720?4:[0,1,2,4,6,9][age%6];')
  t=t.replace('20+age%10','20+(f>=720?0:age%10)').replace('m.fovVersion++;m.worldPass++;','if(f<720 || age==0)m.fovVersion++;m.worldPass++;')

 p=src/'RealisticVisionMod.as';code=p.read_text();code=code.replace('public var trailingHits:int=0;','public var trailingHits:int=0;public var auxHits:int=0;public var vectorHits:int=0;').replace('/* D57_AUX_OMITTED */','auxHits++;').replace('/* D57_VECTOR_SKIPPED */','vectorHits++;');p.write_text(code,encoding='utf-8')
 t=t.replace('trace("LOAD COMPLETE passed="+passed);','check(b.auxHits>100,"unused effect shape omitted");for each(var raster:Object in b.worldMasks)check(raster.m3==null,"effect raster has no unused HP shape");check(b.vectorHits>100,"early alpha rejection exercised");trace("VECTOR HITS "+b.vectorHits);trace("AUX HITS "+b.auxHits);trace("LOAD COMPLETE passed="+passed);')
 (folder/'EffectLoadChecks.as').write_text(t,encoding='utf-8')
 r.runner.compile(folder/'EffectLoadChecks.as',folder/'EffectLoadChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
 r.save(folder/'build.json',{'files':{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()}})
 code,log=r.air(folder,'EffectLoadChecks.swf',rec,300);(folder/'result.txt').write_text(log,encoding='utf-8')
 ok=code==0 and 'LOAD COMPLETE' in log and 'FAIL ' not in log
 if '--min-case' in sys.argv:
  expected=code==1 and 'f=121' in log and 'PIXEL DETAILS ' in log and (folder/'evidence/baseline.png').exists()
  r.save(folder/'validation.json',{'passed':False,'exit':code,'expectedCounterexample':expected,'checks':0})
  print(log[-2200:]);assert expected;rec.outcome='passed';rec.note='两帧反例复现并保存原图；候选未通过';sys.exit(0)
 r.save(folder/'validation.json',{'passed':ok,'exit':code,'checks':int(re.search(r'LOAD COMPLETE passed=(\d+)',log)[1]) if ok else 0})
 print(log[-1200:]);assert ok;rec.outcome='passed';rec.note='严格像素比较，仅功能证据'
