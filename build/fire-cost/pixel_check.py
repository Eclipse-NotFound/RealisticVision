from pathlib import Path
import importlib.util,re,sys,shutil
from instrument import once
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/fire-cost-output'
spec=importlib.util.spec_from_file_location('fire_pixels',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
folder=OUT/sys.argv[1];assert not folder.exists();folder.mkdir()
chosen=next((x.split('=',1)[1] for x in sys.argv if x.startswith('--source=')),'phase')
assert chosen.isidentifier() and (OUT/'candidates'/chosen/'src').is_dir()
with r.Registration(owner='RealisticVision / 缩放遮罩像素对照',purpose=sys.argv[1],run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 src=folder/'src';r.public(OUT/'candidates'/chosen/'src',src)
 p=src/'RealisticVisionMod.as';s=p.read_text('utf8')
 s=once(s,'public var worldPass:int = 0;','public var worldPass:int = 0;public var phaseHits:int=0;').replace('// FIRE_PHASE_HIT','phaseHits++;').replace('// FIRE_PROVEN_CHANGE','phaseHits++;')
 if chosen=='witness':
  s=once(s,'phaseHits++;','''phaseHits++;var witnessOracle:Object=bd.compare(previousInput);
  if(witnessOracle is uint && uint(witnessOracle)==0)throw new Error("inequality shortcut on equal input");
  if(witnessOracle is BitmapData)BitmapData(witnessOracle).dispose();''')
 p.write_text(s,'utf8',newline='\n')
 baseline=re.sub(r'\bprivate\b','public',(OUT/'baseline/src/RealisticVisionMod.as').read_text('utf8')).replace('RealisticVisionMod','BaselineVision')
 (src/'BaselineVision.as').write_text(baseline,'utf8',newline='\n')
 for name in ['RegionGrafon.as','RegionWorld.as']:shutil.copyfile(MOD/'build/local-mask-regions'/name,folder/name)
 t=(MOD/'build/effect-load-v3/EffectLoadChecks.as').read_text('utf8')
 t=t.replace('import flash.display.*;','import flash.display.*;import flash.filters.GlowFilter;import flash.filesystem.*;')
 t=t.replace('Tile.tileX=Tile.tileY=40;','stage.scaleMode=StageScaleMode.NO_SCALE;stage.align=StageAlign.TOP_LEFT;Tile.tileX=Tile.tileY=40;')
 t=t.replace('w=new World();','w=new RegionWorld();').replace('w.grafon=new Grafon();','w.grafon=new RegionGrafon();')
 t=once(t,'addChild(la);addChild(lb);','var pa:Sprite=new Sprite(),pb:Sprite=new Sprite();addChild(pa);addChild(pb);pa.addChild(la);pb.addChild(lb);')
 t=t.replace('i<500','i<160').replace('count:int=group%2?500:100','count:int=group%2?128:32').replace('group:int=int(f/30)','group:int=int(f/30)%12')
 old='v.graphics.beginFill(0x12fd88+i);v.graphics.drawRect(-4,-2,8+(i%6)*7,4);v.graphics.endFill();'
 new='var data:BitmapData=new BitmapData([3,6,12][i%3],[3,6,12][i%3],true,0xff12fd88+i);data.setPixel32(0,0,0);v.addChild(new Bitmap(data,"auto",i%2==0));v.alpha=.25+(i%4)*.25;if(i%17==0)v.filters=[new GlowFilter(0x00ffff,.7,8,8)];'
 t=once(t,old,new)
 t=once(t,'va.rotation=vb.rotation=(i+age)%19;','va.rotation=vb.rotation=(i+age)%19;Bitmap(va.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);Bitmap(vb.getChildAt(0)).bitmapData.setPixel32(1,1,age%2?0xff80f030:0x802080f0);')
 t=t.replace('20+age%10','20+(f<360?age%10:0)')
 t=once(t,'m.fovVersion++;m.worldPass++;','var blur:Number=f<360?[0,1,2,4,6,9][age%6]:4;m.maskBlurCurrent.blurX=m.maskBlurCurrent.blurY=blur;m.maskBlurClassic.blurX=m.maskBlurClassic.blurY=blur;if(f<360||age==0)m.fovVersion++;m.worldPass++;m.frameCount++;')
 t=once(t,'var start:int=getTimer();','var zoom:Number=[2/3,4/3,.75,1.5,1,1.25,.5,2][f%8],offset:Number=[0,.05,.35,.65,1,.95,-.35,-1.05][f%8];la.transform.matrix=lb.transform.matrix=new Matrix(zoom,0,0,zoom,offset,-offset*.7);la.alpha=lb.alpha=f%9==0?.5:1;var start:int=getTimer();')
 t=t.replace('100+(i*61+age*17)%730+.3','(i*61+(f<360?age*17:0))%920+.3').replace('140+(i*37)%500+.7','(i*37+(f<360?age*5:0))%710+.7')
 t=once(t,'out.draw(layer);return out;','out.draw(layer.parent);return out;')
 t=once(t,'check(d is uint&&uint(d)==0,"exact dense moving visuals");','''if(d is BitmapData){
   trace("PHASE DIFFERENCE "+JSON.stringify({frame:f,mode:mode,zoom:zoom,offset:offset,hits:b.phaseHits,region:String(BitmapData(d).getColorBoundsRect(0xffffffff,0,false))}));
   var root:String=File.applicationDirectory.nativePath.replace(/\\\\/g,'/');if(root.indexOf('/RealisticVision/build/fire-cost-output/')<0)throw new Error('wrong evidence root');
   for each(var shot:Object in [{name:'baseline',data:ca},{name:'candidate',data:cb}]){var fs:FileStream=new FileStream();try{fs.open(new File(root+'/evidence/'+shot.name+'.png'),FileMode.WRITE);fs.writeBytes(BitmapData(shot.data).encode(BitmapData(shot.data).rect,new PNGEncoderOptions()));}finally{fs.close();}}
  }check(d is uint&&uint(d)==0,"exact dense moving visuals");''')
 t=t.replace('if(++f>=360){','if(++f>=720){check(b.phaseHits>100,"scaled crop exercised");trace("PHASE HITS "+b.phaseHits);removeEventListener(Event.ENTER_FRAME,step);')
 if chosen=='witness':
  t=t.replace('scaled crop exercised','proven inequality exercised').replace('PHASE HITS','PROVEN INEQUALITY HITS')
  # Stable filter parameters are required to exercise the original compare guard.
  # The earlier fixture changed blur every frame, so it compared pixels but never
  # reached the candidate shortcut. Keep that failed coverage run as evidence.
  t=once(t,'var blur:Number=f<360?[0,1,2,4,6,9][age%6]:4;','var blur:Number=4;')
 if '--offset-grid' in sys.argv:
  t=t.replace('offset:Number=[0,.05,.35,.65,1,.95,-.35,-1.05][f%8]','offset:Number=[0,.05,.35,.65,1,.95,-.35,-1.05][int(f/8)%8]').replace('if(++f>=720){','if(++f>=1440){')
 (folder/'EffectLoadChecks.as').write_text(t,'utf8',newline='\n')
 r.runner.compile(folder/'EffectLoadChecks.as',folder/'EffectLoadChecks.swf',[folder,src,MOD/'build/motion-tests',MOD/'build/stubs'])
 r.save(folder/'build.json',{'files':{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()}})
 code,log=r.air(folder,'EffectLoadChecks.swf',rec,240)
 ok=code==0 and 'LOAD COMPLETE' in log and 'FAIL ' not in log
 r.save(folder/'validation.json',{'passed':ok,'exit':code});print(log[-2000:]);assert ok
 rec.outcome='passed';rec.note='独立连续显示树严格ARGB对照；包含缩放、小数位移、滤镜和固定视野多帧'
