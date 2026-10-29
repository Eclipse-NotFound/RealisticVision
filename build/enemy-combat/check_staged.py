"""Check the exact archived/staged bytes without repeating tests or state edits."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];DEST=MOD/'knowledge/experiments/enemy-combat-d57-20261029'
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
pins=json.loads((DEST/'archive.json').read_text())
prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in pins)+'\n').encode());offset=0
for rel,h in pins.items():
 assert hashlib.sha256((DEST/rel).read_bytes()).hexdigest()==h,rel
 end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[1]==b'blob';size=int(header[2]);data=raw[end+1:end+size+1];offset=end+size+2
 assert hashlib.sha256(data).hexdigest()==h,rel
assert offset==len(raw)
git('diff','--cached','--check')
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()}
assert actual=={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)},actual
assert hashlib.sha256((MOD/'release/RealisticVisionMod.swf').read_bytes()).hexdigest()=='bd64b5bbfe5a07a0b5bff38e4c344652e1df526cfd5c308d63b607123ce4a9ad'
print(json.dumps({'archiveFiles':len(pins),'stagedBytesMatch':True,'externalWipUnchanged':True,'installedUnchanged':True}))
