"""Pin successful evidence and distinguish native timings from pixel checks."""
from pathlib import Path
import json,re,statistics
from PIL import Image
import package as p
OUT=p.OUT;r=p.run
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def stats(a):
 s=sorted(a);return {'n':len(a),'mean':round(statistics.mean(a),3),'p95':s[int(.95*(len(s)-1))],'max':max(a),'over100':sum(x>100 for x in a)}
def normal(s):return re.sub(r'\bprivate\b','public',s).replace(p.VERSION,'v0.33.7-boundary-performance').replace('\n public var profile:Object={},calls:Object={};\n','')
def main():
 manifest=read('production-final/manifest.json');assert manifest['version']==p.VERSION and manifest['swf']==r.sha(p.PACKAGE/'RealisticVisionMod.swf')
 for rel,digest in manifest['sources'].items():
  assert r.sha(p.PACKAGE/'src'/rel)==digest
  text=normal((p.PACKAGE/'src'/rel).read_text(encoding='utf-8-sig'))
  for name in ['functional-optimized','native-final-02','safe-final-parent']:
   assert text==normal((OUT/name/'candidate-src'/rel).read_text(encoding='utf-8-sig')),(name,rel)
  if rel!='RealisticVisionMod.as':assert text==normal((OUT/'baseline/src'/rel).read_text(encoding='utf-8-sig'))
 final=read('functional-optimized/evidence/result.json');assert len(final['checks'])==311 and all(x['pass'] for x in final['checks'])
 assert all(x['pixels']==0 for x in final['rows'] if x['variant']=='candidate')
 for mode in ['classic','current']:
  im=Image.open(OUT/'functional-optimized/evidence'/(mode+'-visbullaser.png')).convert('RGBA').getchannel('A')
  assert im.getbbox() is not None and im.crop((260,0,400,240)).getbbox() is None,'partial laser must keep its visible segment'
 # Only world-visual code changed after this raster/render check. Compare both
 # extracted functions exactly; do not infer equivalence from a version label.
 def mask_methods(s):return s.split('function applyMask(')[1].split('function finishCurrentMask(')[0]
 assert mask_methods((OUT/'unit-render-01/src/RealisticVisionMod.as').read_text())==mask_methods(normal((p.PACKAGE/'src/RealisticVisionMod.as').read_text()))
 assert read('unit-render-01/result.json')['exit']==0 and 'RENDER COMPLETE passed=589 reused=216' in (OUT/'unit-render-01/result.txt').read_text()
 checks=read('safe-final-parent/evidence/result.json')['checks'];assert len(checks)==64 and all(x['exact'] for x in checks)
 settings=read('production-final/settings.json');assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 trace=read('native-final-02/evidence/result.json');assert len(trace['cases'])==12
 for c in trace['cases']:
  assert len(c['frames'])==240 and c['grounded']>=200 and c['maxFloorDeviation']<=40 and c['walkDistance']>300 and c['reversals']>=1 and c['attackStarts']>0 and c['maxProjectiles']>0
  for a,b in zip(c['frames'],c['frames'][1:]):assert a['nextInterval']==b['liveStart']-a['liveStart'] and a['rvEnd']-a['rvStart']==a['rv']
 perf=[]
 for mode in ['current','classic']:
  for variant in ['off','baseline','candidate']:
   rows=[x for c in trace['cases'] if c['mode']==mode and c['variant']==variant for x in c['frames'] if 'nextInterval' in x]
   perf.append({'mode':mode,'variant':variant,'interval':stats([x['nextInterval'] for x in rows]),'update':stats([x['rv'] for x in rows])})
 r.save(OUT/'performance.json',perf)
 decision=read('performance-decision.json');assert decision['accepted'] is True
 assert decision['native_result']==r.sha(OUT/'native-final-02/evidence/result.json')
 assert decision['candidate_source']==r.sha(OUT/'candidate/src/RealisticVisionMod.as')
 loads={}
 for name in ['functional-optimized','native-final-02','safe-final-parent']:
  log=(OUT/name/'air-output.log').read_text(encoding='utf-8-sig');req=set(re.findall(r'ModLoader\[requested_(\w+)\]',log));ok=set(re.findall(r'ModLoader\[ok_(\w+)\]',log));assert req and req==ok and 'FAIL ' not in log;loads[name]=sorted(ok)
  assert r.sha(OUT/name/'pfe.swf')==r.sha(p.GAME/'pfe.swf')
 for rel,digest in read('native-final-02/build.json')['files'].items():
  if rel.startswith('mods/') and rel.endswith('.swf') and 'RecoveryFrameProbe' not in rel:assert r.sha(p.GAME/rel)==digest,('dependency drift',rel)
 evidence={}
 for name in ['functional-optimized','unit-render-01','safe-final-parent','native-final-02','production-final']:
  for f in (OUT/name).rglob('*'):
   if f.is_file() and 'storage' not in f.parts and f.suffix in ['.json','.log','.txt','.png','.as']:evidence[f.relative_to(OUT).as_posix()]=r.sha(f)
 for name in ['performance.json','performance-decision.json','inputs.json']:evidence[name]=r.sha(OUT/name)
 r.save(OUT/'verified.json',{'status':'PASS','version':p.VERSION,'swf':manifest['swf'],'host':r.sha(p.GAME/'pfe.swf'),'evidence':evidence,'checks':1000,'native_windows':12,'loading':loads})
 print(json.dumps(perf,ensure_ascii=False,indent=2));print('D42 REVIEW PASS')
if __name__=='__main__':main()
