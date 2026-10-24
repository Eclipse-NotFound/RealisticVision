"""Preserve D45 completed evidence bytes, never freeze a still-running trial."""
from pathlib import Path
import hashlib,json,shutil,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output'
DEST=MOD/'knowledge/experiments/mask-area-d45-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
DEST.mkdir(exist_ok=True)
pins=json.loads((DEST/'archive.json').read_text()) if (DEST/'archive.json').exists() else {}
for rel,digest in pins.items():assert sha(DEST/rel)==digest,rel
paths=[OUT/'inputs.json']
for name in sys.argv[1:]:
 folder=OUT/name
 assert (folder/'last-run.json').exists(),name
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  if p.suffix=='.as' or (len(rel.parts)==1 and p.suffix in ('.json','.txt','.log')) or ('evidence' in rel.parts and p.suffix in ('.json','.png')):paths.append(p)
for p in paths:
 rel=p.relative_to(OUT);dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert sha(dest)==sha(p),'Frozen evidence changed '+str(rel)
 else:shutil.copyfile(p,dest)
 pins[rel.as_posix()]=sha(dest)
for name in ['performance.json','diagnostic-notes.json','precise-long-frames.json']:
 p=OUT/name
 if p.exists():shutil.copyfile(p,DEST/name);pins[name]=sha(DEST/name)
attributes=DEST/'.gitattributes'
if not attributes.exists():attributes.write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n',encoding='utf-8',newline='\n')
pins['.gitattributes']=sha(attributes)
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Verified archive files:',len(pins))
