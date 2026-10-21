"""Keep small, checkable evidence in Git; leave runtime copies in ignored build/."""
import json,shutil
import investigate as inv
def main():
 out=inv.OUT
 dest=inv.MOD/'knowledge/experiments/settings-recovery-v0332-20261021'
 assert not dest.exists();dest.mkdir(parents=True)
 (dest/'.gitattributes').write_bytes(b"# Raw evidence must retain its bytes, including AIR's CR/CRLF output.\n* -text -diff\n")
 groups=['rollback','diagnose-01','fixed-profile-02','padding-audit-01','padding-audit-02','checks-05','checks-06','checks-07','checks-08','checks-09','baseline-trial-03','baseline-trial-04','baseline-trial-05','native-verify-02','combat-02','final-native-01','final-combat-01','production-singlepass','deployment']
 names={'receipt.json','build.json','inputs.json','result.json','analysis.json','environment.json','launch-state.json','last-run.json','running.json','selection.json','manifest.json','settings.json','classes.txt','formal-runtime.txt','formal-output.txt','air-output.log'}
 files=[]
 for group in groups:
  for f in (out/group).rglob('*'):
   rel=f.relative_to(out)
   if not f.is_file() or 'storage' in rel.parts or any(part.endswith('-src') for part in rel.parts):continue
   if f.name not in names and not f.name.endswith(('Checks.txt','Harness.txt')):continue
   target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
   files.append({'path':rel.as_posix(),'sha256':inv.r.sha(f),'bytes':f.stat().st_size})
 for name in ['verified.json','runtime-summary.json','cleanup.json']:
  f=out/name
  if f.exists():shutil.copyfile(f,dest/name);files.append({'path':name,'sha256':inv.r.sha(f),'bytes':f.stat().st_size})
 inv.r.save(dest/'archive.json',{'files':files,'note':'Exact input fingerprints and raw results retained; unique source/binary/rollback packages stay at their recorded build paths.'})
 print('Archived',len(files),'files,',sum(f['bytes'] for f in files),'bytes')

if __name__=='__main__':main()
