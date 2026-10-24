"""Validate identities and actual loader sessions before interpreting D46 timing."""
from pathlib import Path
import hashlib,json,re,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-lifecycle-output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in sys.argv[1:]:
 folder=OUT/name;build=json.loads((folder/'build.json').read_text())
 for rel,digest in build['files'].items():assert sha(folder/rel)==digest,(name,rel)
 assert json.loads((folder/'last-run.json').read_text())['exit']==0,name
 log=(folder/'air-output.log').read_text(encoding='utf-8-sig')
 selected=set(json.loads((folder/'selection.json').read_text())['configuration']['selected'])
 assert set(re.findall(r'ModLoader\[requested_(\w+)\]',log))==selected
 assert set(re.findall(r'ModLoader\[ok_(\w+)\]',log))==selected
 assert log.count('ModLoader[boot_start]')==1 and 'ModLoader[err_' not in log
 data=json.loads((folder/'evidence/result.json').read_text())
 assert len(data['cases'])==(20 if build['split'] else 12)
 for c in data['cases']:
  assert len(c['frames'])==c['sampleFrames'] and c['attacks']>0 and c['maxProjectiles']>0
 print(name,'source/runtime/shot checks PASS;',len(selected),'selected modules;',len(data['cases']),'windows')
