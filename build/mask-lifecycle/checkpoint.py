"""Stage D46 and verify raw evidence while preserving the authority WIP."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/mask-lifecycle-output'
def git(*args,input=None):
 p=subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True);return p.stdout
assert git('rev-parse','HEAD').decode().startswith('43e7121')
assert not git('diff','--cached','--name-only')
git('add','--','.gitignore','build/mask-lifecycle','build/mask-area/register_report.py','knowledge/experiments/2026-10-25-mask-lifecycle.md','knowledge/experiments/mask-lifecycle-d46-20261025')
for name in ['MEMORY.md','journal.md']:
 oid=git('hash-object','-w','--stdin',input=(OUT/'owned-state'/name).read_bytes()).decode().strip()
 git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
prefix='knowledge/experiments/mask-lifecycle-d46-20261025/'
pins=json.loads((MOD/prefix/'archive.json').read_text());paths=[prefix+p for p in pins]
git('add','-f','--pathspec-from-file=-','--pathspec-file-nul',input=('\0'.join(paths)+'\0').encode())
raw=git('cat-file','--batch',input=('\n'.join(':'+p for p in paths)+'\n').encode());offset=0
for path,digest in pins.items():
 end=raw.index(b'\n',offset);head=raw[offset:end].decode().split();assert head[1]=='blob'
 size=int(head[2]);data=raw[end+1:end+1+size];offset=end+size+2
 assert hashlib.sha256(data).hexdigest()==digest,path
assert offset==len(raw)
p=subprocess.run(['git','diff','--cached','--check'],cwd=MOD,capture_output=True)
assert p.returncode==0,p.stdout.decode()[:1500]
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()}
assert actual==expected,actual
git('-c','user.name=eclipse','-c','user.email=helloimyyt@163.com','commit','-m','D46: 排除集中释放主因并保留分类复用无收益证据')
print(git('log','-1','--oneline').decode().strip());print('Evidence byte hashes:',len(pins),'; external WIP unchanged 24/2/4/15')
