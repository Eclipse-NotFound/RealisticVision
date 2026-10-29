"""Deploy the exact D56 package after focused evidence, with atomic rollback."""
from pathlib import Path
import ctypes,datetime,json,shutil,uuid,xml.etree.ElementTree as ET
import package
r=package.run;MOD=package.MOD;GAME=package.GAME;OUT=package.OUT;P=package.PACKAGE
OLD='638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710'
CONFIG='5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f'
TARGET=MOD/'release/RealisticVisionMod.swf'

def replace(source):
 temp=TARGET.with_name('RealisticVisionMod.deploy-'+uuid.uuid4().hex+'.tmp');shutil.copyfile(source,temp)
 fn=ctypes.WinDLL('kernel32',use_last_error=True).ReplaceFileW
 fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p];fn.restype=ctypes.c_int
 try:
  if not fn(str(TARGET),str(temp),None,0,None,None):raise ctypes.WinError(ctypes.get_last_error())
 finally:temp.unlink(missing_ok=True)

def main():
 manifest=json.loads((P/'manifest.json').read_text());new=manifest['swf'];assert new==r.sha(P/'RealisticVisionMod.swf')
 assert manifest['version']==package.VERSION and len(manifest['classes'])==6
 for rel,h in manifest['sources'].items():assert r.sha(P/'src'/rel)==h
 for path in (OUT/'candidates/grid_current/src').rglob('*.as'):
  src=path.read_text();final=(P/'src'/path.relative_to(OUT/'candidates/grid_current/src')).read_text()
  assert final==src.replace('v0.33.10-render-cache',package.VERSION)
 checks=json.loads((OUT/'current-final-pixels-26/validation.json').read_text());assert checks=={'passed':True,'exit':0,'checks':721}
 timing=json.loads((OUT/'current-final-native-27/analysis.json').read_text());assert timing['environment']['performanceEligible']
 groups=timing['groups'];a=groups['current/normal']['nextInterval'];b=groups['current/candidate']['nextInterval']
 assert a['n']==b['n']==358 and b['mean']<a['mean'] and b['p95']<a['p95']
 settings=json.loads((P/'settings.json').read_text());assert len(settings)==2 and all(v['passed']==18 and v['exit']==0 for v in settings)
 smoke=OUT/'production-smoke-29';validated=json.loads((smoke/'validation.json').read_text());assert validated['passed'] and validated['swf']==new
 assert validated['native']['shots']>20 and validated['native']['audioVolume']==0
 assert ET.parse(GAME/'application.xml').find('.//{*}content').text=='pfe.swf'
 installed=(GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig');assert 'RealisticVision|RealisticVisionMod|1|0|0' in installed
 pins=json.loads((smoke/'build.json').read_text())['files'];protected={}
 for rel,h in pins.items():
  if rel.startswith('mods/ProductionSmoke/') or rel=='mods/RealisticVision/release/RealisticVisionMod.swf':continue
  assert r.sha(GAME/rel)==h,'Runtime dependency drift: '+rel
  protected[rel]=h
 protected['application.xml']=r.sha(GAME/'application.xml');protected['mods/loader-manifest.txt']=r.sha(GAME/'mods/loader-manifest.txt')
 assert r.sha(TARGET)==OLD and r.sha(MOD/'release/config.txt')==CONFIG
 evidence={}
 for rel in ['current-final-pixels-26/validation.json','current-final-pixels-26/build.json','current-final-native-27/analysis.json','current-final-native-27/build.json','current-final-native-27/evidence/result.json','production/manifest.json','production/settings.json','production-smoke-29/validation.json','production-smoke-29/build.json']:
  evidence[rel]=r.sha(OUT/rel)
 r.save(OUT/'verified.json',{'status':'PASS','version':package.VERSION,'swf':new,'evidence':evidence,'dependencies':protected,'boundary':'Current optimized and invalidated; classic retains installed algorithm. Native exact-byte smoke and settings checks completed before same-path copy.'})
 folder=OUT/'deployment';folder.mkdir(exist_ok=False)
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
 backup=MOD/'build/backups'/('before-effect-clip-'+stamp);backup.mkdir(exist_ok=False)
 old=backup/'RealisticVisionMod.before.swf';shutil.copyfile(TARGET,old);assert r.sha(old)==OLD
 receipt={'version':package.VERSION,'old':OLD,'new':new,'backup':str(old.relative_to(MOD)),'time':stamp,'result':'PENDING','authorization':'GOVERNANCE 6 standing local deployment authorization','smoke':'production-smoke-29/validation.json','samePathAndDependencies':True,'configUnchanged':CONFIG,'protected':protected}
 changed=False
 try:
  assert r.sha(TARGET)==OLD
  replace(P/'RealisticVisionMod.swf');changed=True;assert r.sha(TARGET)==new
  assert r.sha(MOD/'release/config.txt')==CONFIG
  for rel,h in protected.items():assert r.sha(GAME/rel)==h,'Concurrent dependency change: '+rel
  receipt['result']='PASS'
 except BaseException as e:
  if changed:
   assert r.sha(TARGET)==new,'Newer RV found; do not overwrite'
   replace(old);assert r.sha(TARGET)==OLD
  receipt.update(result='ROLLED_BACK' if changed else 'NOT_DEPLOYED',error=repr(e));raise
 finally:r.save(folder/'receipt.json',receipt)
 print('DEPLOYED '+package.VERSION+' '+new)

if __name__=='__main__':main()
