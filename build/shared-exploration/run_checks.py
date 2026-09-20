"""Isolated RV assertions; only copied test source exposes private members."""
from pathlib import Path
import os, re, subprocess, uuid
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
GAME=MOD.parents[1]
SDK=Path(r'D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk')
JAVA=Path(r'C:\Users\hello\Documents\_sandevistan_dev\jdk-11.0.32.1+1-jre\bin\java.exe')
out=HERE/'checks';out.mkdir(exist_ok=True)
source=(MOD/'src/RealisticVisionMod.as').read_text(encoding='utf-8')
(out/'RealisticVisionMod.as').write_text(re.sub(r'\bprivate\b','public',source),encoding='utf-8')
env=dict(os.environ,AIR_HOME=str(SDK))
for harness in ('SoftHarness','SharedExplorationHarness'):
    cmd=[str(JAVA),'-Xmx384m','-jar',str(SDK/'lib/mxmlc.jar'),'+configname=air','+flexlib='+str(SDK/'frameworks'),
         '-swf-version=32','-debug=true','-optimize=false','-omit-trace-statements=false','-static-link-runtime-shared-libraries=true',
         '-source-path='+','.join(map(str,[out,MOD/'build/motion-tests',MOD/'build/stubs',MOD/'src'])),
         '-output='+str(out/(harness+'.swf')),str(MOD/'build/motion-tests'/(harness+'.as'))]
    subprocess.run(cmd,env=env,check=True)
    desc=out/(harness+'.xml')
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>rv-shared-check-'+uuid.uuid4().hex+
      '</id><versionNumber>1.0</versionNumber><filename>RVTest</filename><initialWindow><content>'+harness+
      '.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>',encoding='utf-8')
    try:
        run=subprocess.run([str(GAME/'adl64.exe'),'-runtime',str(GAME/'runtimes/air/win64'),str(desc)],
            cwd=out,capture_output=True,text=True,timeout=55,creationflags=subprocess.CREATE_NO_WINDOW)
        log=run.stdout+run.stderr
        (out/(harness+'.log')).write_text(log,encoding='utf-8')
        print(log,flush=True)
        assert run.returncode==0 and 'COMPLETE' in log and 'FAIL ' not in log and 'MOTION RED' not in log, harness+' failed'
    finally: desc.unlink(missing_ok=True)
