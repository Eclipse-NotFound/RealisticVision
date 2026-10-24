"""Final byte-preserving archive check and isolated D45 commit."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];DEST=MOD/'knowledge/experiments/mask-area-d45-20261025'
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
pins=json.loads((DEST/'archive.json').read_text())
for path,digest in pins.items():
 if path!='.gitattributes':assert hashlib.sha256((DEST/path).read_bytes()).hexdigest()==digest,path
pins['.gitattributes']=hashlib.sha256((DEST/'.gitattributes').read_bytes()).hexdigest()
(DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
git('add','--','build/mask-area/commit.py','knowledge/experiments/mask-area-d45-20261025/.gitattributes','knowledge/experiments/mask-area-d45-20261025/archive.json')
p=subprocess.run(['git','diff','--cached','--check'],cwd=MOD,capture_output=True)
assert p.returncode==0,p.stdout.decode()[:1500]
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()}
assert actual==expected,actual
git('-c','user.name=eclipse','-c','user.email=helloimyyt@163.com','commit','-m','D45: 排除遮罩面积与隐藏缓存候选并记录长帧线索')
print(git('log','-1','--oneline').decode().strip())
