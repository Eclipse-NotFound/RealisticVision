"""Load the exact private production SWF through the native loader, in isolation."""
from pathlib import Path
import importlib.util,json,os,re,shutil,subprocess
import package
r=package.run;MOD=package.MOD;GAME=package.GAME;OUT=package.OUT
spec=importlib.util.spec_from_file_location('d56_smoke_media',MOD/'build/candidate-comparison/runtime.py');media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media);media.bind(r)
from air_test_process import HiddenProcess
SEED=MOD/'build/sustained-fire-output/player-seed'
for rel,h in json.loads((SEED/'manifest.json').read_text()).items():assert r.sha(SEED/rel)==h
class Recorded(HiddenProcess):
 def __init__(self,*args,**kw):
  folder=Path(kw['cwd']);desc=(folder/'test.xml').read_text();appid=re.search(r'<id>(.*?)</id>',desc)[1]
  assert appid.startswith('pfe-modsettings-rv-motion-')
  target=Path(os.environ['APPDATA'])/appid/'Local Store';target.mkdir(parents=True,exist_ok=False)
  for p in SEED.rglob('*'):
   if p.is_file() and p.name!='manifest.json':
    q=target/p.relative_to(SEED);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  # Only the unique test app's settings. Native entry/default keys are retained.
  (target/'RealisticVision_config.txt').write_text('enabled=1\nmode=current\ndim=0.35\nsoft_current=20\nsoft_classic=0\nviewscale=1\nwallbright=0\n',encoding='utf-8')
  (folder/'test.xml').write_text(desc.replace('<width>1280</width>','<width>2576</width>').replace('<height>720</height>','<height>1560</height>'),encoding='utf-8')
  super().__init__(*args,**kw)
r.HiddenProcess=Recorded
folder=OUT/'production-smoke-29';assert not folder.exists()
with r.Registration(owner='RealisticVision / D56 准确包原生加载',purpose=package.VERSION+' 原生轻机枪与遮罩',run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
 r.runtime(folder);selected=[]
 for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
  parts=line.split('|')
  if line.startswith('#') or len(parts)<3 or parts[2]!='1':continue
  selected.append(parts[1]);shutil.copytree(GAME/'mods'/parts[0]/'release',folder/'mods'/parts[0]/'release')
 assert 'RealisticVisionMod' in selected
 shutil.copyfile(package.PACKAGE/'RealisticVisionMod.swf',folder/'mods/RealisticVision/release/RealisticVisionMod.swf')
 shutil.copyfile(package.HERE/'ProductionSmokeMod.as',folder/'ProductionSmokeMod.as')
 r.runner.compile(folder/'ProductionSmokeMod.as',folder/'mods/ProductionSmoke/release/ProductionSmokeMod.swf',[folder])
 selected.append('ProductionSmokeMod');catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
 (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nProductionSmoke|ProductionSmokeMod|1|0|0\n',encoding='utf-8')
 proc=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True);assert proc.returncode==0
 pins={p.relative_to(folder).as_posix():r.sha(p) for p in folder.rglob('*.swf')};r.save(folder/'build.json',{'files':pins,'selected':selected,'probeSource':r.sha(folder/'ProductionSmokeMod.as')})
 code,log=r.air(folder,'pfe.swf',rec,150)
 assert code==0 and 'D56 PRODUCTION COMPLETE' in log and 'FAIL' not in log,log[-2200:]
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==set(selected)
 data=json.loads((folder/'evidence/production.json').read_text());assert data['shots']>20 and data['maskedParticleSamples']>0 and data['audioVolume']==0 and data['windowVisible']
 r.save(folder/'validation.json',{'passed':True,'swf':r.sha(package.PACKAGE/'RealisticVisionMod.swf'),'native':data});rec.outcome='passed';rec.note='原生loader加载准确私有SWF，持续射击/粒子遮罩/设置注册/心跳通过'
 print(json.dumps(data))
