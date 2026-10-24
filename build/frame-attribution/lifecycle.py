from pathlib import Path
import json,re,sys
import validate as v
def build(name):
 folder=v.OUT/name;assert not folder.exists();folder.mkdir(parents=True)
 with v.r.Registration(owner='RealisticVision / D47 状态恢复构建',purpose=name,run_dir=folder,evidence=folder/'build.json',resource='offline') as rec:
  v.r.public(v.OUT/'candidates/identity/src',folder/'src')
  (folder/'IdentityLifecycleChecks.as').write_bytes((v.HERE/'IdentityLifecycleChecks.as').read_bytes())
  v.r.runner.compile(folder/'IdentityLifecycleChecks.as',folder/'IdentityLifecycleChecks.swf',[folder,folder/'src',v.MOD/'build/motion-tests',v.MOD/'build/stubs'])
  v.r.save(folder/'build.json',{'files':{str(p.relative_to(folder)):v.r.sha(p) for p in folder.rglob('*') if p.is_file()}});rec.outcome='passed'
def run(name):
 folder=v.OUT/name;assert not (folder/'last-run.json').exists()
 assert all(v.r.sha(folder/k)==h for k,h in json.loads((folder/'build.json').read_text())['files'].items())
 with v.r.Registration(owner='RealisticVision / D47 状态恢复验证',purpose=name,run_dir=folder,evidence=folder/'validation.json',wait=900) as rec:
  code,log=v.r.air(folder,'IdentityLifecycleChecks.swf',rec,120)
  (folder/'result.txt').write_text(log,encoding='utf-8')
  match=re.search(r'LIFECYCLE COMPLETE passed=(\d+)',log)
  v.r.save(folder/'validation.json',{'pass':code==0 and match is not None,'checks':int(match[1]) if match else 0,'exit':code})
  print(log[-2500:]);assert code==0 and match and 'FAIL ' not in log;rec.outcome='passed'
if __name__=='__main__':{'build':build,'run':run}[sys.argv[1]](sys.argv[2])
