from pathlib import Path
import importlib.util,json,re,shutil,subprocess,sys,os
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/sustained-fire-output'
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
SEED=OUT/'player-seed';assert (SEED/'manifest.json').exists()
for rel,h in json.loads((SEED/'manifest.json').read_text()).items():assert r.sha(SEED/rel)==h
assert not folder.exists(),'Use new evidence directory'
with r.Registration(owner='RealisticVision / D54 存档轻机枪',purpose=name,run_dir=folder,evidence=folder/'analysis.json',wait=900) as rec:
 r.runtime(folder)
 s=(HERE/'SavedProbe.as').read_text()
 if '--sweep' in sys.argv:s=s.replace('SWEEP=false','SWEEP=true')
 if '--solo' in sys.argv:s=s.replace('SOLO=false','SOLO=true')
 if '--private-visible' in sys.argv:s=s.replace('SHOW_WINDOW=false','SHOW_WINDOW=true')
 if '--visual' in sys.argv:
  s=s.replace('VISUAL=false','VISUAL=true').replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal']")
 if split:s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal','nomouse','nodraw','noeffects','noeffects','nodraw','nomouse','normal']")
 if candidate:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['off','normal','candidate','candidate','normal','off']")
  if '--reverse' in sys.argv:s=s.replace("['off','normal','candidate','candidate','normal','off']","['off','candidate','normal','normal','candidate','off']")
 if '--both' in sys.argv:s=s.replace("for each(var variant:String in", "for each(var mode:String in ['current','classic'])for each(var variant:String in").replace("mode:'current',variant:variant", "mode:mode,variant:variant")
 if bursts:
  assert not candidate and not split
  s=s.replace("['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']","['normal-burst','off-burst','off-burst','normal-burst']").replace('SAMPLE_COUNT=180','SAMPLE_COUNT=360').replace('WARMUP_COUNT=90','WARMUP_COUNT=0')
  if '--reverse' in sys.argv:s=s.replace("['normal-burst','off-burst','off-burst','normal-burst']","['off-burst','normal-burst','normal-burst','off-burst']")
 (folder/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8')
 r.runner.compile(folder/'CombatRenderProbeMod.as',folder/'mods/CombatRenderProbe/release/CombatRenderProbeMod.swf',[folder])
 sources=[('rv',BASE)]
 if candidate:sources.append(('candidate',OUT/('candidates/direct-cache/src' if '--direct-cache' in sys.argv else 'candidates/pixel-cache/src' if '--pixel-cache' in sys.argv else 'candidates/integer-v2/src' if '--integer-v2' in sys.argv else 'candidates/integer/src' if '--integer' in sys.argv else 'candidates/trailing-current/src' if '--current-only' in sys.argv else 'candidates/trailing-v2/src' if '--v2' in sys.argv else 'candidates/trailing/src')))
 for variant,source in sources:
  src=folder/(variant+'-src');r.public(source,src)
  p=src/'RealisticVisionMod.as';s=p.read_text();pos=s.index('{',s.index('public class'))+1
  s=s[:pos]+'\n public var d53SkipEffects:Boolean=false;public var trailingHits:int=0;\n'+s[pos:]
  s=s.replace('// D54_TRAILING','trailingHits++;')
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
 data=json.loads((folder/'evidence/result.json').read_text());assert data['weapon']=='lmg' and data['audioVolume']==0
 groups={}
 for c in data['cases']:
  if 'idle' not in c['variant']:assert c['attacks']>10 and c['maxProjectiles']>0, (c['variant'],c['attacks'],c['maxProjectiles'])
  fs=[f for f in c['frames'] if 'nextInterval' in f];groups.setdefault(c['mode']+'/'+c['variant'],[]).extend(fs)
  print(c['variant'],'shots',c['attacks'],'bullets',c['maxProjectiles'],'profile',c.get('profile'))
 def stats(v):
  v=sorted(v);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v)}
 result={'environment':eligibility,'groups':{k:{f:stats([x[f] for x in a]) for f in ['nextInterval','rv']} for k,a in groups.items()}}
 r.save(folder/'analysis.json',result);print(json.dumps(result));rec.outcome='passed';rec.note='LMG原生射击和计时完成；插桩归因不作最终发布收益'
