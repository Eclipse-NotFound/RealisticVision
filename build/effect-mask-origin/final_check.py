"""Post-archive index integrity, preserving external WIP and exact binary bytes."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/effect-mask-origin-output';DEST=MOD/'knowledge/experiments/effect-mask-origin-d56-20261029'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
attrs=DEST/'.gitattributes';attrs.write_text(attrs.read_text(),encoding='utf-8',newline='\n')
pins=json.loads((DEST/'archive.json').read_text());pins['.gitattributes']=sha(attrs)
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
git('add','--','build/effect-mask-origin','knowledge/experiments/2026-10-29-effect-mask-origin.md');git('add','-f','--',str(DEST))
prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in pins)+'\n').encode());offset=0
for rel,h in pins.items():
 assert sha(DEST/rel)==h,rel
 end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[1]==b'blob';size=int(header[2]);body=raw[end+1:end+size+1];offset=end+size+2;assert hashlib.sha256(body).hexdigest()==h,rel
assert offset==len(raw)
mapping=json.loads((DEST/'object-map.json').read_text())
for rel,value in mapping.items():assert sha(DEST/value['stored'])==value['sha256'],rel
git('diff','--cached','--check')
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()};assert actual==expected,actual
receipt=json.loads((OUT/'deployment/receipt.json').read_text());assert sha(MOD/'release/RealisticVisionMod.swf')==receipt['new']
assert sha(MOD/'src/RealisticVisionMod.as')==json.loads((OUT/'integration-final.json').read_text())['mainSource']
print(json.dumps({'deployed':receipt['version'],'sha256':receipt['new'],'files':len(pins),'bytes':sum((DEST/p).stat().st_size for p in pins),'aliases':len(mapping),'externalWipPreserved':True,'reportSha256':sha(MOD/'knowledge/experiments/2026-10-29-effect-mask-origin.md')}))
