"""Read the installed native entry point into this test's reference folder."""
from pathlib import Path
import hashlib,json,re,subprocess
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/frame-attribution-output'
dest=OUT/'native-source';assert not dest.exists();dest.mkdir()
java=Path('D:/Program Files/Adobe Animate 2024/jre/bin/java.exe');jar=GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'
host=GAME/'pfe.swf';digest=hashlib.sha256(host.read_bytes()).hexdigest()
cmd=[str(java),'-jar',str(jar),'-selectclass','fe.MainMenu','-export','script',str(dest),str(host)]
p=subprocess.run(cmd,capture_output=True,timeout=180)
(dest/'export.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-1800:]
source=dest/'scripts/fe/MainMenu.as';text=source.read_text(encoding='utf-8-sig');compact=re.sub(r'\s+','',text)
assert 'this.main.stage.addEventListener(Event.ENTER_FRAME,this.mainStep);' in compact
assert 'publicfunctionmainStep(param1:Event):void' in compact
assert compact.count('this.world.step();')==1
assert digest==hashlib.sha256(host.read_bytes()).hexdigest()
(dest/'checked.json').write_text(json.dumps({'host':digest,'mainMenuSource':hashlib.sha256(source.read_bytes()).hexdigest(),'checks':['native listener priority 0','public mainStep(Event):void','single World.step call']},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Installed native entry verified; no host changes')
