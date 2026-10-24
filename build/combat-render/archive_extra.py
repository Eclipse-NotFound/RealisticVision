"""Archive exact-package provenance and failed/queued work without inventing runs."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-render-output';DEST=MOD/'knowledge/experiments/combat-render-d44-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((DEST/'archive.json').read_text())
for rel,digest in pins.items():assert sha(DEST/rel)==digest,rel
files=[]
for folder in [OUT/'group-steps',OUT/'support-native-02',OUT/'production-final',OUT/'production-final2',OUT/'development-check']:
    if not folder.exists():continue
    for p in folder.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(folder)
        if 'storage' in rel.parts:continue
        if p.suffix=='.as' or (p.suffix in ('.json','.txt','.log') and (len(rel.parts)==1 or p.name=='last-run.json')):files.append(p)
for name in ['verified.json','source-merge.json','verified-source.patch','development-source.patch','candidate-review.patch','review.json','coordination.json','deployment/receipt.json','deployment/formal-output.txt','deployment/formal-runtime.txt']:
    p=OUT/name
    if p.exists():files.append(p)
for p in files:
    rel=p.relative_to(OUT);dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(dest)==sha(p),'Frozen evidence changed: '+str(rel)
    else:shutil.copyfile(p,dest)
    pins[rel.as_posix()]=sha(dest)
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('exact-package and failed-step archive verified:',len(pins))
