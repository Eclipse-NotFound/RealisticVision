"""Freeze the enabled lighting package for a private combination diagnostic."""
from pathlib import Path
import hashlib,json,shutil
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/fire-cost-output'
target=OUT/'frozen/mods/LightAndDarkness';assert not target.exists()
shutil.copytree(GAME/'mods/LightAndDarkness/release',target/'release')
config=GAME/'mods/LightAndDarkness/atmosphere.json'
if config.is_file():shutil.copyfile(config,target/'atmosphere.json')
(OUT/'optional-lad.json').write_text(json.dumps({p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()},indent=2)+'\n','utf8',newline='\n')
print('Frozen optional lighting input; installation unchanged')
