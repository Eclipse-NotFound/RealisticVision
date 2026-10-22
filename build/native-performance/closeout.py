"""Stage only D37 work, and verify archived bytes survive Git storage."""
import hashlib,json,subprocess
import package as p
MOD,OUT=p.MOD,p.OUT
ARCHIVE='knowledge/experiments/native-performance-v0334-20261022'
def git(*args,**kwargs):return subprocess.check_output(['git',*args],cwd=MOD,**kwargs)
def main():
 paths=['.gitignore','src/RealisticVisionMod.as','src/RVWallSurface.as','decisions/decisions.md','build/native-performance','knowledge/experiments/2026-10-22-native-performance.md',ARCHIVE]
 subprocess.run(['git','add','--',*paths],cwd=MOD,check=True)
 subprocess.run(['git','add','-f','--',ARCHIVE],cwd=MOD,check=True)
 for name in ['MEMORY.md','journal.md']:
  data=(OUT/'owned-state'/name).read_bytes();assert b'\r' not in data
  oid=git('hash-object','-w','--stdin',input=data).decode().strip()
  subprocess.run(['git','update-index','--cacheinfo','100644',oid,'state/'+name],cwd=MOD,check=True)
 pins=json.loads((MOD/ARCHIVE/'archive.json').read_text())
 for rel,digest in pins.items():
  file=MOD/ARCHIVE/rel;assert hashlib.sha256(file.read_bytes()).hexdigest()==digest
  assert hashlib.sha256(git('show',':'+ARCHIVE+'/'+rel)).hexdigest()==digest,rel
 assert not git('diff','--cached','--name-only','--','src/RVAuthorityView.as','tests/authority/AuthorityViewChecks.as').strip()
 remaining=git('diff','--numstat').decode().splitlines()
 assert set(remaining)=={'24\t0\tsrc/RVAuthorityView.as','2\t0\tstate/MEMORY.md','4\t0\tstate/journal.md','15\t0\ttests/authority/AuthorityViewChecks.as'},remaining
 subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
 print('D37 staged; archive byte checks:',len(pins),'; four unrelated changes preserved')
if __name__=='__main__':main()
