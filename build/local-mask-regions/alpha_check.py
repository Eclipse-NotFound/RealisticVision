from pathlib import Path
import importlib.util,re,sys
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/local-mask-regions-output'
spec=importlib.util.spec_from_file_location('alpha_runtime',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
folder=OUT/sys.argv[1];assert not folder.exists();folder.mkdir()
with r.Registration(owner='RealisticVision / 墙面alpha输入',purpose=sys.argv[1],run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 src=folder/'src';src.mkdir()
 old=(OUT/'baseline/src/RVWallSurface.as').read_text('utf8').replace('RVWallSurface','FullScanWallSurface')
 (src/'FullScanWallSurface.as').write_text(old,'utf8',newline='\n')
 new=(OUT/'alpha-candidate/src/RVWallSurface.as').read_text('utf8')
 new=new.replace('public class RVWallSurface {','public class RVWallSurface {\n public var alphaOnlyHits:int=0;').replace('// ALPHA_ONLY_HIT','alphaOnlyHits++;')
 assert 'public var alphaOnlyHits' in new
 (src/'RVWallSurface.as').write_text(new,'utf8',newline='\n')
 t=(MOD/'build/wall-restore/ContourCacheChecks.as').read_text('utf8')
 start=t.index('         if(bright){');end=t.index('         if(ok)passed++',start);t=t[:start]+t[end:]
 t=t.replace('(bright?" material retained, air independent":" exact pixels")','" exact pixels"')
 marker='         surface.reset();oldSurface.reset();compare("room reset");'
 assert t.count(marker)==1
 t=t.replace(marker,'''
         for(var phase:int=0;phase<36;phase++){
            bright=phase%2==0;intensity=(phase%5)/4;
            pixels.fillRect(new Rectangle(90,120,35,25),phase%3==0?0:phase%3==1?0x80ff1122:0xff1144cc);
            front.x=phase%6==1?.35:0;
            var bitmap:Bitmap=front.getChildAt(0) as Bitmap;
            bitmap.scrollRect=phase%6==2?new Rectangle(10,10,380,300):null;
            var overlay:Bitmap=null;
            if(phase%6==3){overlay=new Bitmap(new BitmapData(150,100,true,0x608855ff));overlay.x=70;overlay.y=80;front.addChild(overlay);}
            compare("alpha/RGB edits and direct-to-composed transitions "+phase);
            if(overlay){front.removeChild(overlay);overlay.bitmapData.dispose();}
         }
         front.x=0;Bitmap(front.getChildAt(0)).scrollRect=null;
         surface.reset();oldSurface.reset();compare("room reset");
         if(surface.alphaOnlyHits<20)throw new Error("alpha fast path not exercised");
         trace("ALPHA HITS "+surface.alphaOnlyHits);
''')
 (folder/'ContourCacheChecks.as').write_text(t,'utf8',newline='\n')
 r.runner.compile(folder/'ContourCacheChecks.as',folder/'ContourCacheChecks.swf',[folder,src])
 r.save(folder/'build.json',{'files':{p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*') if p.is_file()}})
 code,log=r.air(folder,'ContourCacheChecks.swf',rec,120)
 ok=code==0 and 'failed=0' in log and 'ALPHA HITS ' in log
 r.save(folder/'validation.json',{'passed':ok,'exit':code});print(log[-1900:]);assert ok
 rec.outcome='passed';rec.note='原图逐像素对照，包含alpha/RGB改写、复合/变换/scrollRect回退和常亮开关'
