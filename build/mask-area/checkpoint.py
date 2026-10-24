"""Stage D45 evidence and owned state while leaving the four external WIP files."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-area-output'
def git(*args,input=None):
 p=subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True)
 return p.stdout
assert git('rev-parse','HEAD').decode().startswith('9f23c45'),'Review newer commits before staging'
assert not git('diff','--cached','--name-only'),'Another staged change exists'
paths=['.gitignore','build/mask-area','knowledge/experiments/2026-10-25-mask-area.md','knowledge/experiments/mask-area-d45-20261025']
git('add','--',*paths)
for name in ['MEMORY.md','journal.md']:
 data=(OUT/'owned-state'/name).read_bytes()
 oid=git('hash-object','-w','--stdin',input=data).decode().strip()
 git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
prefix='knowledge/experiments/mask-area-d45-20261025/'
pins=json.loads((MOD/prefix/'archive.json').read_text())
raw_paths=[prefix+p for p in pins]
git('add','-f','--pathspec-from-file=-','--pathspec-file-nul',input=('\0'.join(raw_paths)+'\0').encode())
raw=git('cat-file','--batch',input=('\n'.join(':'+p for p in raw_paths)+'\n').encode());offset=0
for path,digest in pins.items():
 end=raw.index(b'\n',offset);head=raw[offset:end].decode().split();assert head[1]=='blob'
 size=int(head[2]);data=raw[end+1:end+1+size];offset=end+size+2
 assert hashlib.sha256(data).hexdigest()==digest,path
assert offset==len(raw)
git('diff','--cached','--check')
remaining=git('diff','--numstat').decode().splitlines()
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in remaining}
assert actual==expected,actual
print('Owned changes staged,',len(pins),'raw evidence byte hashes match; outside WIP remains 24/2/4/15')
