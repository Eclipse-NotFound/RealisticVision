"""Append finished D44 evidence, preserving prior raw bytes and line endings."""
from pathlib import Path
import hashlib,json,shutil,sys
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/combat-render-output';DEST=MOD/'knowledge/experiments/combat-render-d44-20261025'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
pins=json.loads((DEST/'archive.json').read_text())
for rel,digest in pins.items():assert sha(DEST/rel)==digest,rel
for name in sys.argv[1:]:
 folder=OUT/name;assert (folder/'last-run.json').exists(),name
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  if rel.parts[0]=='storage':continue
  if p.suffix=='.as' or (len(rel.parts)==1 and p.suffix in ('.json','.txt','.log')) or (rel.parts[0]=='evidence' and p.suffix in ('.json','.png')):
   dest=DEST/name/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():assert sha(dest)==sha(p),str(dest)
   else:shutil.copyfile(p,dest)
   pins[dest.relative_to(DEST).as_posix()]=sha(dest)
for name in ['performance.json','outliers.json']:
 p=OUT/name
 if p.exists():shutil.copyfile(p,DEST/name);pins[name]=sha(DEST/name)
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('archived and verified',len(pins),'files')
