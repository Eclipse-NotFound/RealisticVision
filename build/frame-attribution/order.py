"""Export the current loader constructor order for human source review."""
from pathlib import Path
import hashlib,json,subprocess
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/frame-attribution-output'
dest=OUT/'loader-order';assert not dest.exists();dest.mkdir()
host=GAME/'pfe.swf';digest=hashlib.sha256(host.read_bytes()).hexdigest()
assert digest==json.loads((OUT/'native-source/checked.json').read_text())['host']
p=subprocess.run(['D:/Program Files/Adobe Animate 2024/jre/bin/java.exe','-jar',str(GAME/'mods/Sandevistan/build/tools/ffdec/ffdec-cli.jar'),'-selectclass','MainFE','-export','script',str(dest),str(host)],capture_output=True,timeout=120)
(dest/'export.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
source=dest/'scripts/MainFE.as';assert source.exists()
(dest/'fingerprints.json').write_text(json.dumps({'host':digest,'source':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'exported; ordering needs review'},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Current MainFE exported; review constructor/loader order before interpreting instrumentation')
