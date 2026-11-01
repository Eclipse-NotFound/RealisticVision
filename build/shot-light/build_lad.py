"""Use the documented compiler CLI, with RV-owned output and frozen signatures.

The existing PowerShell helper was rejected by AuthorizationManager. No execution
policy or trust flag is changed; this invokes only the existing Java compiler.
"""
from pathlib import Path
import subprocess,hashlib,json,shutil
from xml.sax.saxutils import escape
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/shot-light-output'
def build_lighting(source,output):
 assert Path(output).resolve().is_relative_to(OUT.resolve())
 output.mkdir(parents=True,exist_ok=True)
 stubs=OUT/'lighting-stubs'
 if not stubs.exists():
  shutil.copytree(GAME/'mods/LightAndDarkness/build/stubs',stubs)
  (OUT/'stub-inputs.json').write_text(json.dumps({p.relative_to(stubs).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in stubs.rglob('*.as')},indent=2)+'\n','utf8',newline='\n')
 for name,h in json.loads((OUT/'stub-inputs.json').read_text()).items():assert hashlib.sha256((stubs/name).read_bytes()).hexdigest()==h
 sdk=GAME/'mods/Sandevistan/build/tools';flex=sdk/'flexsdk'
 air=sdk/'airsdk/frameworks/libs/air/airglobal.swc'
 java='D:/Program Files/Adobe Animate 2024/jre/bin/java.exe'
 def config(name,src,libs):
  p=output/(name+'.compiler.xml')
  paths=''.join('<path-element>'+escape(str(v))+'</path-element>' for v in libs)
  p.write_text('<flex-config xmlns="http://www.adobe.com/2006/flex-config"><target-player>32.0</target-player><compiler><source-path><path-element>'+escape(str(src))+'</path-element></source-path><external-library-path>'+paths+'</external-library-path><debug>false</debug><optimize>true</optimize></compiler></flex-config>','utf8')
  return p
 stub=output/'host-signatures.swc'
 commands=[['compc','-load-config='+str(config('signatures',stubs,[air])),'-include-classes=fe.unit.Unit,fe.weapon.Bullet,fe.loc.Box,fe.loc.Tile','-output='+str(stub)],
 ['mxmlc','-load-config='+str(config('lighting',source,[air,stub])),'-swf-version=32','-use-network=false','-static-link-runtime-shared-libraries=true','-includes=lad.native.LadLampTarget','-output='+str(output/'LightAndDarknessMod.swf'),str(source/'LightAndDarknessDoc.as')]]
 with (output/'compile.log').open('w',encoding='utf8') as log:
  for command in commands:
   result=subprocess.run([java,'-Xmx768m','-Dsun.io.useCanonCaches=false','-Djava.util.Arrays.useLegacyMergeSort=true','-jar',str(flex/'lib'/(command[0]+'.jar')),'+flexlib='+str(flex/'frameworks'),*command[1:]],stdout=log,stderr=subprocess.STDOUT)
   if result.returncode:break
 if result.returncode:raise RuntimeError((output/'compile.log').read_text('utf8')[-5000:])
 print('Lighting built',output.relative_to(MOD),flush=True)
 return output/'LightAndDarknessMod.swf'
