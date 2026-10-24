"""Verify inputs and real loading before summarizing D49 comparisons."""
from pathlib import Path
import hashlib,json,re,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/fog-setters-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):
 v=sorted(values);return {'n':len(v),'mean':sum(v)/len(v),'p95':v[int(.95*(len(v)-1))],'max':v[-1],'>100':sum(x>100 for x in v),'>200':sum(x>200 for x in v)}
def verified(name,marker):
 folder=OUT/name;build=json.loads((folder/'build.json').read_text());data=json.loads((folder/'evidence/result.json').read_text())
 for rel,digest in build['files'].items():assert sha(folder/rel)==digest,rel
 assert json.loads((folder/'last-run.json').read_text())['exit']==0
 assert not (folder/'test.xml').exists()
 log=(folder/'air-output.log').read_text(encoding='utf-8-sig');selected=set(json.loads((folder/'selection.json').read_text())['configuration']['selected'])
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==selected
 assert 'ModLoader[err_' not in log and marker in log and 'FAIL ' not in log
 return folder,build,data
def combat(name):
 folder,build,data=verified(name,'D49P COMPLETE')
 assert build['candidate'] in ('guard',) and build['full'] and build['controlled']
 source=(folder/'CombatRenderProbeMod.as').read_text()
 assert 'nativeFrame' not in source and 'NativeTimingAccess' not in source and 'mainStep' not in source
 assert 'sharedHits' not in (folder/'candidate-src/RealisticVisionMod.as').read_text()
 expected=[(mode,variant) for mode in ['current','classic'] for variant in ['off','normal','candidate','candidate','normal','off']]
 assert [(c['mode'],c['variant']) for c in data['cases']]==expected
 groups={};windows=[]
 for index,c in enumerate(data['cases']):
  assert c['crowd']==6 and c['attacks']>0 and c['maxProjectiles']>0 and len(c['frames'])==build['samples']
  frames=[f for f in c['frames'] if 'nextInterval' in f];assert len(frames)==build['samples']-1
  key=c['mode']+'/'+c['variant'];groups.setdefault(key,[]).extend(frames)
  windows.append({'index':index,'group':key,'interval':stats([f['nextInterval'] for f in frames]),'rv':stats([f['rv'] for f in frames]),'attacks':c['attacks'],'particles':c['maxParticles'],'projectiles':c['maxProjectiles'],'maskInventory':c['maskInventory']})
 result={'verified':True,'measurementNote':json.loads((folder/'measurement-note.json').read_text()) if (folder/'measurement-note.json').exists() else None,'selected':sorted(build['selected']),'groups':{key:{field:stats([f[field] for f in frames]) for field in ['nextInterval','rv','diagnosticMs']} for key,frames in groups.items()},'windows':windows,'limitations':'Complete same-process controlled combat; native random animation/AI still advances. Endpoint mask counts are not same-input branch-hit measurements.'}
 (folder/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 for key,values in result['groups'].items():print(key,json.dumps(values['nextInterval']), 'rv',round(values['rv']['mean'],2))
def inventory(name):
 folder,build,data=verified(name,'D49 COMPLETE');assert build['inventory'] and len(data['cases'])==2
 result={'verified':True,'windows':[],'limitations':'Counts only originally cached (record.cache===true) hidden world visuals; not every filtered object. Inventory overhead means this is not a performance comparison.'}
 for c in data['cases']:
  assert c['crowd']==6 and c['attacks']>0 and c['maxProjectiles']>0 and len(c['frames'])==build['samples']
  frames=[f for f in c['frames'] if 'nextInterval' in f]
  for f in frames:
   assert f['worldStepsNext']==1 and f['probeMs']+f['nativeNext']+f['otherHandlersNext']+f['afterProbe']==f['nextInterval']
  result['windows'].append({'mode':c['mode'],'stats':{key:stats([f[key] for f in c['frames']]) for key in ['hiddenVisuals','hiddenForcedCache','hiddenPlainCache']}})
 (folder/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':{'combat':combat,'inventory':inventory}[sys.argv[1]](sys.argv[2])
