from pathlib import Path
import importlib.util,re,sys,shutil
H=Path(__file__).resolve().parent;M=H.parents[1];O=M/'build/enemy-combat-output'
spec=importlib.util.spec_from_file_location('d57_check_runtime',M/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
name=sys.argv[1];chosen=sys.argv[2];folder=O/name;assert not folder.exists()
with r.Registration(owner='RealisticVision / D57 敌人遮罩像素',purpose=name,run_dir=folder,evidence=folder/'result.json',wait=900) as rec:
 src=folder/'src';r.public(O/'candidates'/chosen/'src',src)
 p=src/'RealisticVisionMod.as';s=p.read_text().replace('public var worldPass:int = 0;','public var worldPass:int = 0;public var clipHits:int=0;').replace('// D57_CLIP','clipHits++; // D57_CLIP');p.write_text(s,encoding='utf-8')
 s=re.sub(r'\bprivate\b','public',(O/'baseline/src/RealisticVisionMod.as').read_text()).replace('RealisticVisionMod','BaselineVision');(src/'BaselineVision.as').write_text(s,encoding='utf-8')
 t=(H/'MaskRenderChecks.as').read_text()
 if '--fresh' in sys.argv:t=t.replace('// FRESH_REFERENCE','if(mode=="current"){if(u.vis.mask)u.vis.mask=null;if(u.hpbar.mask)u.hpbar.mask=null;if(ua.mask)ua.mask=null;}')
 if '--recreate' in sys.argv:
  t=t.replace('   if(k==0)for each', '''   if(mode=="current"){
    a.restoreAll(w,loc);if(a.fogVis&&a.fogVis.parent)a.fogVis.parent.removeChild(a.fogVis);
    a=new BaselineVision();a.mswRegistered=true;a.cfgMode=mode;a.resetRoom(w,loc);a.onFrameInner();
   }
   if(k==0)for each''')
 if '--min-case' in sys.argv:t=t.replace('private var frame:int=0,','private var frame:int=432,').replace('++frame>=720','++frame>=433').replace('b.clipHits>50','b.clipHits>0')
 (folder/'MaskRenderChecks.as').write_text(t,encoding='utf-8')
 r.runner.compile(folder/'MaskRenderChecks.as',folder/'MaskRenderChecks.swf',[folder,src,M/'build/motion-tests',M/'build/stubs'])
 r.save(folder/'build.json',{'swf':r.sha(folder/'MaskRenderChecks.swf'),'sources':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*.as')}})
 code,log=r.air(folder,'MaskRenderChecks.swf',rec,130);(folder/'result.txt').write_text(log,encoding='utf-8');r.save(folder/'result.json',{'exit':code,'summary':log.splitlines()[-6:]});print(log[-2600:]);assert code==0 and 'RENDER COMPLETE' in log and 'FAIL ' not in log;rec.outcome='passed'
