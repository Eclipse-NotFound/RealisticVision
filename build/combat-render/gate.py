"""Bind D44 acceptance to actual bytes and the tested installed combination."""
import json,re,sys
from pathlib import Path
import package
r=package.run;OUT=package.OUT;GAME=package.GAME;MOD=package.MOD
names=['small-02','bindings-controlled-01','bindings-free-01','bindings-pixels-01','bindings-native-01']
def main():
 evidence={}
 for name in names:
  folder=OUT/name
  assert json.loads((folder/'last-run.json').read_text())['exit']==0,name
  build=json.loads((folder/'build.json').read_text())
  for rel,digest in build['files'].items():assert r.sha(folder/rel)==digest,(name,rel)
  if name in ['small-02','bindings-controlled-01','bindings-free-01']:
   log=(folder/'air-output.log').read_text(encoding='utf-8-sig')
   selected=set(json.loads((folder/'selection.json').read_text())['configuration']['selected'])
   assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==selected,(name,'runtime requests')
   assert set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==selected,(name,'runtime init')
   assert log.count('ModLoader[boot_start]')==1 and 'ModLoader[err_' not in log,name
   evidence[name+'/air-output.log']=r.sha(folder/'air-output.log')
   data=json.loads((folder/'evidence/result.json').read_text());assert len(data['cases'])==(42 if name=='small-02' else 12)
   for c in data['cases']:
    assert len(c['frames'])==c['sampleFrames']
    if c['crowd']:assert c['attacks']>0 and c['maxProjectiles']>0
   proof='evidence/result.json'
  else:
   data=json.loads((folder/'validation.json').read_text());assert data['pass']
   assert data['checks']>= (360 if name=='bindings-pixels-01' else 888);proof='validation.json'
  for rel in ['build.json','last-run.json',proof]:evidence[name+'/'+rel]=r.sha(folder/rel)
 settings=json.loads((package.PACKAGE/'settings.json').read_text());assert len(settings)==2 and all(x['exit']==0 and x['passed']==18 for x in settings)
 manifest=json.loads((package.PACKAGE/'manifest.json').read_text());assert manifest['version']==package.VERSION
 guard=OUT/'candidates/bindings/src'
 for p in (package.PACKAGE/'src').rglob('*.as'):
  original=(guard/p.relative_to(package.PACKAGE/'src')).read_text(encoding='utf-8')
  assert p.read_text(encoding='utf-8')==original.replace('v0.33.9-effect-load',package.VERSION)
 tested=OUT/'bindings-free-01';files=json.loads((tested/'build.json').read_text())['files']
 assert files['pfe.swf']==r.sha(GAME/'pfe.swf')
 combo={}
 for rel,digest in files.items():
  if rel.replace('\\','/').startswith('mods/') and '/release/' in rel.replace('\\','/') and Path(rel).suffix in ('.swf','.txt','.xml','.json') and 'CombatRenderProbe' not in rel:
   assert r.sha(GAME/rel)==digest,'Installed combination changed: '+rel
   combo[rel]=digest
 expected={entry+'.swf' for entry in json.loads((tested/'build.json').read_text())['selected'] if entry!='CombatRenderProbeMod'}
 assert expected <= {Path(rel).name for rel in combo},'Tested module fingerprints incomplete'
 perf=json.loads((OUT/'performance.json').read_text())
 for name in ['bindings-controlled-01','bindings-free-01']:
  groups=perf[name]['groups']
  for mode in ['current','classic']:
   before=groups['6/'+mode+'/normal']['frame'];after=groups['6/'+mode+'/candidate']['frame']
   assert after['mean']<before['mean'] and after['p95']<=before['p95'],(name,mode,before,after)
   assert after['>100']<=before['>100'],('long-frame count',name,mode,before,after)
 for rel in ['performance.json','production-final2/manifest.json','production-final2/settings.json']:evidence[rel]=r.sha(OUT/rel)
 proof={'status':'PASS','version':package.VERSION,'swf':r.sha(package.PACKAGE/'RealisticVisionMod.swf'),'host':r.sha(GAME/'pfe.swf'),'combination':combo,'evidence':evidence,'limitations':'Live native AI/fire is not deterministic replay. Does not establish all long frames eliminated.'}
 r.save(OUT/'verified.json',proof);print('GATE PASS',proof['swf'])
if __name__=='__main__':main()
