"""New isolated runtimes use immutable media from our finished D48 test."""
from pathlib import Path
import os,re,shutil,uuid
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1]
MEDIA=MOD/'build/shared-mask-output/shared-v2-combat-01'
NAMES={'sound.swf','sound_unit.swf','sound_weapon.swf','sprite.swf','sprite1.swf','texture.swf','texture1.swf'}
def bind(r):
 def runtime(folder):
  assert not list(folder.glob('*.swf')),'Do not overwrite any existing runtime'
  folder.mkdir(parents=True,exist_ok=True);(folder/'evidence').mkdir(exist_ok=True)
  for p in GAME.iterdir():
   if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):
    if p.name in NAMES:
     base=MEDIA/p.name;assert r.sha(base)==r.sha(p),p.name
     os.link(base,folder/p.name)
    else:shutil.copy2(p,folder/p.name)
  shutil.copytree(GAME/'Rooms',folder/'Rooms',dirs_exist_ok=True)
  desc=(GAME/'application.xml').read_text(encoding='utf-8-sig')
  desc=re.sub(r'<id>.*?</id>','<id>pfe-rv-fog-template-'+uuid.uuid4().hex+'</id>',desc)
  (folder/'application.xml').write_text(desc,encoding='utf-8')
 r.runtime=runtime
