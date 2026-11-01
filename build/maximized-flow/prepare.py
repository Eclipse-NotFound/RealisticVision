"""New frozen experiment; never rewrite previous investigation outputs."""
from pathlib import Path
import shutil,json,hashlib
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1]
OUT=MOD/'build/maximized-flow-output';OLD=MOD/'build/composite-followup'
assert not OUT.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(MOD/'release/RealisticVisionMod.swf')=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
assert sha(GAME/'pfe.swf')=='ca94af17ed56b273138789661bf725538e5cb7c161cf282ab8c4aa582f88b9b0'
OUT.mkdir()
for v in ('baseline','candidate'):
 shutil.copytree(MOD/'build/composite-followup-output/baseline/src',OUT/v/'src')
frozen=OUT/'frozen';frozen.mkdir();shutil.copyfile(GAME/'pfe.swf',frozen/'pfe.swf')
for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
 c=line.split('|')
 if len(c)>=3 and not line.startswith('#') and c[2]=='1' and c[1] not in ('RealisticVisionMod','LightAndDarknessMod'):
  shutil.copytree(GAME/'mods'/c[0]/'release',frozen/'mods'/c[0]/'release')
shutil.copytree(MOD/'build/composite-followup-output/native-source',OUT/'native-source')
(OUT/'inputs.json').write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()},indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ('cpu_sampler.py','CachePixels.as','DisplaySnapshot.as'):
 shutil.copyfile(OLD/name,HERE/name)
s=(OLD/'SavedFireProbe.as').read_text().replace('build/composite-followup-output','build/maximized-flow-output')
s=s.replace("['off','normal','skip-hide','hide-fog','both','both','hide-fog','skip-hide','normal','off']", "['off','normal','normal','off']")
s=s.replace('SAMPLE_COUNT=180','SAMPLE_COUNT=360')
s=s.replace('private static const SHOW_WINDOW=false;', 'private static const SHOW_WINDOW=false;\n  private static const MAXIMIZE=false;')
s=s.replace("wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;", "wc=host.loaderInfo.applicationDomain.getDefinition('fe.World') as Class;if(MAXIMIZE){host.stage.nativeWindow.visible=true;host.stage.nativeWindow.maximize();}")
s=s.replace('if(++settle<15)return;', "if(MAXIMIZE&&host.stage.nativeWindow.displayState!='maximized')return;if(++settle<15)return;")
s=s.replace('var p:Object=plan[index];', "var p:Object=plan[index];if(MAXIMIZE&&host.stage.nativeWindow.displayState!='maximized')throw new Error('window not maximized');")
s=s.replace('row={crowd:p.n,', 'row={windowDisplayState:host.stage.nativeWindow.displayState,windowBounds:String(host.stage.nativeWindow.bounds),stageScreen:[host.stage.stageWidth,host.stage.stageHeight],crowd:p.n,')
(HERE/'SavedFireProbe.as').write_text(s,encoding='utf-8',newline='\n')
s=(OLD/'run.py').read_text().replace('build/composite-followup-output','build/maximized-flow-output').replace('RealisticVision / 阴影交叉归因','RealisticVision / 最大化与重画复用')
s=s.replace('from cpu_sampler import OwnedCpuSampler', "from cpu_sampler import OwnedCpuSampler\nOwnedCpuSampler.INTERVAL_SECONDS=0.1")
s=s.replace(" s=(HERE/'SavedFireProbe.as').read_text()", """ s=(HERE/'SavedFireProbe.as').read_text()
 if '--maximize' in sys.argv:s=s.replace('MAXIMIZE=false','MAXIMIZE=true')
 if '--try-candidate' in sys.argv:
  s=s.replace('EXPERIMENT=false','EXPERIMENT=true').replace("['off','normal','normal','off']", "['off','normal','candidate','candidate','normal','off']")
 if '--pixel-checks' in sys.argv:
  s=s.replace('  private function undo():void {',(HERE/'PixelChecks.as').read_text(encoding='utf-8')+'\\n  private function undo():void {')
  s=s.replace('row.treeEnd=displaySnapshot(w);', 'row.treeEnd=displaySnapshot(w);if(rv.fogVis)row.pixelChecks=checkPixels(w);')
""")
# Count and log actual dirty work without modifying the results or refreshing it.
s=s.replace("p.write_text(s,encoding='utf-8')", "p.write_text(s,encoding='utf-8')")
(HERE/'run.py').write_text(s,encoding='utf-8',newline='\n')
s=(OLD/'analyze.py').read_text().replace('build/composite-followup-output','build/maximized-flow-output')
s=s.replace('delayed=wall>1500', "delayed=wall>cpu['metadata']['interval_seconds']*1500")
s=s.replace("summary.update(index=i,", "summary.update(windowDisplayState=c.get('windowDisplayState'),stageScreen=c.get('stageScreen'),index=i,")
s=s.replace("if 'cachePixels' in c:", "if 'pixelChecks' in c:summary['pixelChecks']=c['pixelChecks']\n        if 'cachePixels' in c:")
(HERE/'analyze.py').write_text(s,encoding='utf-8',newline='\n')
print('Frozen current package set; maximization and 100ms owned sampling prepared')
