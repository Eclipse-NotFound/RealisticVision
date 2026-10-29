"""D58: split the two D57 allocation changes, preserving frozen evidence."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OLD=MOD/'build/enemy-combat';PRIOR=MOD/'build/enemy-combat-output';OUT=MOD/'build/combat-split-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists();OUT.mkdir()
assert sha(MOD/'release/RealisticVisionMod.swf')=='bd64b5bbfe5a07a0b5bff38e4c344652e1df526cfd5c308d63b607123ce4a9ad'
shutil.copytree(PRIOR/'baseline',OUT/'baseline')
shutil.copytree(PRIOR/'native-source',OUT/'native-source')
for label in ['aux','vector']:
 shutil.copytree(PRIOR/'baseline/src',OUT/'candidates'/label/'src')
baseline=(PRIOR/'baseline/src/RealisticVisionMod.as').read_text()
aux=(PRIOR/'candidates/world_aux/src/RealisticVisionMod.as').read_text()
both=(PRIOR/'candidates/effect_alloc/src/RealisticVisionMod.as').read_text()
(OUT/'candidates/aux/src/RealisticVisionMod.as').write_text(aux,encoding='utf-8',newline='\n')
start=baseline.index('            var pixels:Vector.<uint>=BitmapData(raster.m2e).getVector(')
end=baseline.index('            // Include the full support',start)
ns=both.index('            // A non-opaque first sample');ne=both.index('            // Include the full support',ns)
vector=baseline[:start]+both[ns:ne]+baseline[end:]
assert 'D57_AUX_OMITTED' not in vector and 'D57_VECTOR_SKIPPED' in vector
(OUT/'candidates/vector/src/RealisticVisionMod.as').write_text(vector,encoding='utf-8',newline='\n')
pins={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*.as')}
(OUT/'frozen.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
probe=(OLD/'SavedFireProbe.as').read_text().replace('D57','D58').replace('enemy-combat-output','combat-split-output')
probe=probe.replace('candidateClass:Class,loader:', 'candidateClass:Class,vectorClass:Class,vectorLoader:Loader=new Loader(),loader:')
marker="candidateLoader.load(new URLRequest('app:/candidate.swf'),candidateCtx);"
assert probe.count(marker)==1
probe=probe.replace(marker,marker+'''
    vectorLoader.contentLoaderInfo.addEventListener(Event.COMPLETE,function(e:Event):void {vectorClass=vectorLoader.contentLoaderInfo.applicationDomain.getDefinition('RealisticVisionMod') as Class;});
    var vectorCtx:LoaderContext=new LoaderContext(false,new ApplicationDomain(host.loaderInfo.applicationDomain));vectorCtx.allowCodeImport=true;vectorLoader.load(new URLRequest('app:/vector.swf'),vectorCtx);''')
probe=probe.replace('(EXPERIMENT&&!candidateClass)', '(EXPERIMENT&&(!candidateClass||!vectorClass))')
probe=probe.replace("p.variant=='candidate'?candidateClass:rvClass", "p.variant=='candidate'?candidateClass:p.variant=='vector'?vectorClass:rvClass")
(HERE/'SavedFireProbe.as').write_text(probe,encoding='utf-8')
driver=(OLD/'run.py').read_text().replace('enemy-combat-output','combat-split-output').replace('D57','D58')
driver=driver.replace("['off','normal','candidate','candidate','normal','off']", "['off','normal','candidate','vector','vector','candidate','normal','off']")
driver=driver.replace("['off','candidate','normal','normal','candidate','off']", "['off','vector','candidate','normal','normal','candidate','vector','off']")
marker=' for variant,source in sources:'
assert driver.count(marker)==1
driver=driver.replace(marker," assert candidate and chosen=='aux'\n sources.append(('vector',OUT/'candidates/vector/src'))\n"+marker)
# Earlier marker rewriting refers to candidates from other experiments; their
# branches are unused here. Split the two counters to prove each path executes.
driver=driver.replace("public var alphaHits:int=0;", "public var alphaHits:int=0;public var auxHits:int=0;public var vectorHits:int=0;")
driver=driver.replace("  s=s.replace('// D58_ALPHA_CLIP'", "  s=s.replace('/* D57_AUX_OMITTED */','auxHits++;').replace('/* D57_VECTOR_SKIPPED */','vectorHits++;')\n  s=s.replace('// D58_ALPHA_CLIP'")
# Avoid large output; evidence files retain complete logs and metrics.
driver=driver.replace('print(log[-3000:]);','print(log[-500:]);')
driver=driver.replace("print(c['variant'],'enemyShots',c['enemyShots'],'shots',c['attacks'],'bullets',c['maxProjectiles'],'profile',c.get('profile'))", "print(c['mode'],c['variant'],'sampleShots',c['samplePlayerShotsLowerBound'],'enemies',c['sampleNativeEnemyShotsLowerBound'])")
(HERE/'run.py').write_text(driver,encoding='utf-8')
print('D58 two independent candidates and three-way controlled test prepared')
