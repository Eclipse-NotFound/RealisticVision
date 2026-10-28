from pathlib import Path
import importlib.util,json,re,shutil,subprocess,sys,os
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/effect-replay-output'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('solo_runtime',MOD/'build/motion-performance/run.py')
media=module('solo_media',MOD/'build/candidate-comparison/runtime.py');media.bind(r)
from test_resources import snapshot,comparison_environment
from air_test_process import HiddenProcess
class Recorded(HiddenProcess):
 def __init__(self,*a,**kw):
  run=Path(kw['cwd']);descriptor=(run/'test.xml').read_text();appid=re.search(r'<id>(.*?)</id>',descriptor)[1]
  if '--large-screen' in sys.argv:
   descriptor=descriptor.replace('<width>1280</width>','<width>1936</width>').replace('<height>720</height>','<height>1119</height>')
   (run/'test.xml').write_text(descriptor,encoding='utf-8')
  if '--native-screen' in sys.argv:
   descriptor=descriptor.replace('<width>1280</width>','<width>2576</width>').replace('<height>720</height>','<height>1560</height>')
   (run/'test.xml').write_text(descriptor,encoding='utf-8')
  if '--private-visible' in sys.argv:
   descriptor=descriptor.replace('<visible>false</visible>','<visible>true</visible>');(run/'test.xml').write_text(descriptor,encoding='utf-8')
  assert appid.startswith('pfe-modsettings-rv-motion-') and appid!='pfe'
  target=Path(os.environ['APPDATA'])/appid/'Local Store';assert not target.exists();target.mkdir(parents=True)
  for p in SEED.rglob('*'):
   if p.is_file() and p.name!='manifest.json':
    out=target/p.relative_to(SEED);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
  super().__init__(*a,**kw);r.save(Path(kw['cwd'])/'resource-policy.json',self.resource_policy)
r.HiddenProcess=Recorded
name=sys.argv[1];full='--full' in sys.argv;split='--split' in sys.argv;candidate='--candidate' in sys.argv;plain='--plain' in sys.argv;folder=OUT/name
bursts='--bursts' in sys.argv
BASE=MOD/'build/combat-render-output/production-final2/src'
SEED=MOD/'build/sustained-fire-output/player-seed';assert (SEED/'manifest.json').exists()
for rel,h in json.loads((SEED/'manifest.json').read_text()).items():assert r.sha(SEED/rel)==h
assert not folder.exists(),'Use new evidence directory'
with r.Registration(owner='RealisticVision / D55 存档轻机枪',purpose=name,run_dir=folder,evidence=folder/'analysis.json',wait=900) as rec:
 r.runtime(folder)
 s=(HERE/'SavedReplayProbe.as').read_text()
 s=s.replace('SWEEP=false','SWEEP=true').replace('SOLO=false','SOLO=true').replace('SHOW_WINDOW=false','SHOW_WINDOW=true')
 s=s.replace('EXPERIMENT=false','EXPERIMENT=true')
 if '--validate' in sys.argv:
  assert s.count('REPLAY_VALIDATE:Boolean=false')==1
  s=s.replace('REPLAY_VALIDATE:Boolean=false','REPLAY_VALIDATE:Boolean=true')
 if '--diagnostic' in sys.argv:s=s.replace("['off','normal','candidate','candidate','normal','off']","['off','normal','fixed','fixed','normal','off']")
 (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8')
 r.runner.compile(folder/'CombatRenderProbeMod.as',folder/'mods/CombatRenderProbe/release/CombatRenderProbeMod.swf',[folder])
 sources=[('rv',BASE)]
 source=MOD/'build/frame-attribution-output/candidates/identity/src' if '--identity' in sys.argv else OUT/'candidates/stable-v4/src' if '--stable-v4' in sys.argv else OUT/'candidates/stable-v2/src' if '--stable-v2' in sys.argv else MOD/'build/sustained-fire-output/candidates'/('pixel-cache' if '--pixel-cache' in sys.argv else 'integer-v2')/'src'
 if '--identity-blit' in sys.argv:source=OUT/'candidates/identity-blit/src'
 if '--identity' in sys.argv:
  pins=json.loads((source.parent/'manifest.json').read_text());assert all(r.sha(source/p)==h for p,h in pins.items())
 sources.append(('candidate',source))
 for variant,source in sources:
  src=folder/(variant+'-src');r.public(source,src)
  p=src/'RealisticVisionMod.as';s=p.read_text();pos=s.index('{',s.index('public class'))+1
  s=s[:pos]+'\n public var d53SkipEffects:Boolean=false;public var trailingHits:int=0;public var stableSavings:int=0;public var drawCalls:int=0;\n'+s[pos:]
  s=s.replace('// D54_TRAILING','trailingHits++;').replace('// D55_TRAILING','trailingHits++;').replace('// D55_STABLE','trailingHits++;if(mx0!=x0 || my0!=y0 || mx1!=x1 || my1!=y1)stableSavings++;')
  s=s.replace('// D47_IDENTITY_HIT','trailingHits++;')
  s=s.replace('if(drawDark)shape.graphics.clear();','drawCalls++;if(drawDark)shape.graphics.clear();')
  s=s.replace('public function applyWorldVisuals(w:World,loc:Location):void\n      {','public function applyWorldVisuals(w:World,loc:Location):void\n      {\nif(d53SkipEffects)return;')
  if plain:
   pos=s.index('{',s.index('public class'))+1;s=s[:pos]+'\npublic var profile:Object={},calls:Object={};\n'+s[pos:]
  else:s=r.fp.instrument(s,['prepareOcclusion','computeFov','applyVision','updateWallSurface','hideEnemies','refreshMask','fillFogCache','refreshWallField','applyWorldVisuals','applyWorldVisual'])
  p.write_text(s,encoding='utf-8');r.runner.compile(p,folder/(variant+'.swf'),[src],stubs=True)
 selected=['CombatRenderProbeMod']
 if full:
  for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
   c=line.split('|')
   if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1]!='RealisticVisionMod':
    selected.append(c[1]);shutil.copytree(GAME/'mods'/c[0]/'release',folder/'mods'/c[0]/'release',dirs_exist_ok=True)
 catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
 (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nCombatRenderProbe|CombatRenderProbeMod|1|0|0\n',encoding='utf-8')
 a=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8');assert a.returncode==0,a.stdout+a.stderr
 r.save(folder/'build.json',{'full':full,'selected':selected,'installed':r.sha(MOD/'release/RealisticVisionMod.swf'),'profile':not plain,'candidate':candidate,'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.as','.swf','.xml','.txt')}})
 before=snapshot();r.save(folder/'before.json',before)
 code,log=r.air(folder,'pfe.swf',rec,timeout=650)
 after=snapshot();r.save(folder/'after.json',after)
 eligibility=comparison_environment('benchmark',before,after,json.loads((folder/'resource-policy.json').read_text()));r.save(folder/'environment.json',eligibility)
 print(log[-3000:]);assert code==0 and 'COMPLETE' in log and 'FAIL ' not in log
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==set(selected)

 data=json.loads((folder/'evidence/result.json').read_text())
 assert data['weapon']=='lmg' and data['audioVolume']==0 and data['windowVisible']
 assert data['replay']['count']>10 and data['capture']['attacks']>10
 if '--validate' in sys.argv:
  assert data['exactFrames']==60
  assert data['optimizedCalls']>0,'Candidate fast path was not exercised'
  result={'exactFrames':data['exactFrames'],'optimizedCalls':data['optimizedCalls'],'replay':data['replay'],'environment':eligibility}
 else:
  groups={}
  for c in data['replayCases']:
   if c['variant']!='fixed':assert c['fingerprint']==data['replayCases'][0]['fingerprint'],'Replay input differs'
   groups.setdefault(c['variant'],[]).extend(c['frames'])
  def stats(v):
   v=sorted(v);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
  result={'environment':eligibility,'replay':data['replay'],'groups':{k:{f:stats([x[f] for x in a if f in x]) for f in ['interval','rv','restore']} for k,a in groups.items()}}
 r.save(folder/'analysis.json',result);print(json.dumps(result));rec.outcome='passed';rec.note='固定真实特效受控回放；不是完整游戏性能验收'
