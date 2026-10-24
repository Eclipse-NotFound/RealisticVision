"""Deduplicate identical read-only assets in completed owned D45/D46/D47/D48 trials."""
from pathlib import Path
import hashlib,json,os,uuid
MOD=Path(__file__).resolve().parents[2].resolve();OUT=MOD/'build/shared-mask-output'
names={'sound.swf','sound_unit.swf','sound_weapon.swf','sprite.swf','sprite1.swf','texture.swf','texture1.swf'}
known={};changed=[];freed=0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for root in [MOD/'build/mask-area-output',MOD/'build/mask-lifecycle-output',MOD/'build/frame-attribution-output',MOD/'build/shared-mask-output']:
 for run in sorted(root.iterdir()):
  if not run.is_dir() or not (run/'last-run.json').exists():continue
  for name in sorted(names):
   p=run/name
   if not p.is_file():continue
   p=p.resolve();assert p.is_relative_to(MOD) and p.parent==run.resolve()
   stat=p.stat();digest=sha(p);key=(name,stat.st_size,digest)
   if key not in known:known[key]=p;continue
   base=known[key]
   if os.path.samefile(base,p):continue
   # Only previously unlinked duplicates count as released disk blocks.
   if stat.st_nlink==1:freed+=stat.st_size
   temp=p.with_name(p.name+'.rv-hardlink-'+uuid.uuid4().hex)
   os.link(base,temp)
   try:
    assert sha(temp)==digest and sha(p)==digest
    os.replace(temp,p)
   finally:
    if temp.exists():temp.unlink()
   assert os.path.samefile(base,p) and sha(p)==digest
   changed.append({'path':str(p.relative_to(MOD)),'source':str(base.relative_to(MOD)),'sha256':digest,'bytes':stat.st_size})
receipt=OUT/'asset-deduplication-01.json';assert not receipt.exists()
receipt.write_text(json.dumps({'changed':changed,'uniqueBytesReleased':freed,'rule':'same module; completed trials only; exact hashes; immutable native media; no game host or mod binaries'},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Preserved bytes; linked',len(changed),'duplicate media files; released',round(freed/1024**3,2),'GiB')
