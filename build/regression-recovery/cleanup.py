"""Remove only this task's duplicated runtime assets after all AIR has stopped."""
from pathlib import Path
import json, re
import investigate as inv

def main():
 out=inv.OUT.resolve();assert not inv.r.environment()['processes'],'AIR/Java active; cleanup deferred'
 receipt=out/'cleanup.json';assert not receipt.exists()
 removed=[]
 for marker in out.glob('*/selection.json'):
  folder=marker.parent.resolve();assert folder.is_relative_to(out)
  for p in list(folder.iterdir())+list((folder/'Rooms').rglob('*')):
   if not p.is_file() or p.is_symlink():continue
   rel=p.relative_to(folder)
   if rel.parts[0]!='Rooms' and not re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):continue
   original=inv.GAME/rel
   if not original.is_file():continue
   digest=inv.r.sha(p)
   if digest!=inv.r.sha(original):continue
   actual=p.resolve();assert actual.is_relative_to(out) and actual!=original.resolve()
   removed.append({'path':p.relative_to(out).as_posix(),'source':rel.as_posix(),'sha256':digest,'bytes':p.stat().st_size})
   p.unlink()
 inv.r.save(receipt,{'files':removed,'count':len(removed),'bytes':sum(p['bytes'] for p in removed),'note':'Only byte-identical runtime copies; unique hosts, sources, packages, results, logs and rollback copies retained.'})
 print('Removed identical runtime copies:',len(removed),'bytes:',sum(p['bytes'] for p in removed))

if __name__=='__main__':
 with inv.r.Registration(owner='RealisticVision / D35 重复素材清理',purpose='核对后移除同哈希测试素材，保留唯一证据',run_dir=inv.OUT,evidence=inv.OUT/'cleanup.json') as rec:
  main();rec.outcome='passed'
