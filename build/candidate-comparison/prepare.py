"""D52: resume two frozen candidates in one complete combat comparison."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/candidate-comparison-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources={'classic':MOD/'build/classic-inputs-output/candidates/all/src','ray':MOD/'build/ray-clearance-output/candidate-v2/src'}
expected={'classic':json.loads((sources['classic'].parent/'inputs.json').read_text()),
          'ray':json.loads((MOD/'build/ray-clearance-output/inputs-v2.json').read_text())['candidate']}
assert not OUT.exists();OUT.mkdir()
for label,source in sources.items():
 assert all(sha(source/p)==h for p,h in expected[label].items())
 assert not any('d51Fast' in p.read_text(encoding='utf-8') or 'd51Steps' in p.read_text(encoding='utf-8') for p in source.rglob('*.as'))
 shutil.copytree(source,OUT/'candidates'/label/'src')
resume={'user_instruction':'可进行测试','date':'2026-10-25','candidates':expected,'prior_pauses':{}}
for previous in ['classic-inputs-output','ray-clearance-output']:
 p=MOD/'build'/previous/'PERFORMANCE-PAUSED.json';q=p.with_name('PERFORMANCE-PAUSED.resumed-d52.json')
 assert p.exists() and not q.exists();resume['prior_pauses'][str(p.relative_to(MOD))]=sha(p);p.rename(q)
(OUT/'resumed.json').write_text(json.dumps(resume,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['perf.py','IdentityCombatProbe.as','runtime.py','verify-results.py']:
 s=(MOD/'build/classic-inputs'/name).read_text(encoding='utf-8').replace('classic-inputs-output','candidate-comparison-output').replace('D50','D52').replace('d50','d52')
 if name=='IdentityCombatProbe.as':
  s=s.replace('candidateClass:Class,loader:', 'candidateClass:Class,rayClass:Class,rayLoader:Loader=new Loader(),loader:')
  needle="   for each(var n:int"
  pos=s.index(needle)
  s=s[:pos]+'''   rayLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {rayClass=rayLoader.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod') as Class;});
   var rayCtx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));rayCtx.allowCodeImport=true;rayLoader.load(new URLRequest('app:/ray.swf'),rayCtx);
'''+s[pos:]
  s=s.replace("['off','normal','candidate','candidate','normal','off']","['off','normal','candidate','ray','ray','candidate','normal','off']")
  s=s.replace('if(!rvClass||','if(!rayClass||!rvClass||')
  s=s.replace("p.variant=='candidate'?candidateClass:rvClass", "p.variant=='candidate'?candidateClass:(p.variant=='ray'?rayClass:rvClass)")
 if name=='perf.py':
  needle="        selected=['CombatRenderProbeMod']"
  assert s.count(needle)==1
  s=s.replace(needle,"""        r.public(OUT/'candidates/ray/src',folder/'ray-src')
        r.runner.compile(folder/'ray-src/RealisticVisionMod.as',folder/'ray.swf',[folder/'ray-src'],stubs=True)
"""+needle)
 if name=='verify-results.py':
  s=s.replace("build['candidate'] in ('raw','all')","build['candidate'] == 'classic'")
  s=s.replace("['off','normal','candidate','candidate','normal','off']","['off','normal','candidate','ray','ray','candidate','normal','off']")
  needle=" assert 'sharedHits' not in (folder/'candidate-src/RealisticVisionMod.as').read_text()"
  assert s.count(needle)==1
  s=s.replace(needle,needle+"\n assert all(x not in (folder/'ray-src/RealisticVisionMod.as').read_text() for x in ['d51Fast','d51Steps'])")
 (HERE/name).write_text(s,encoding='utf-8',newline='\n')
print('D52 freezes D50 all and D51 v2; performance pause explicitly resumed')
