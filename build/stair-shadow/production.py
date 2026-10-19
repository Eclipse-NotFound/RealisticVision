"""Two-process settings validation of the exact candidate bytes; no deployment."""
from pathlib import Path
import importlib.util,sys,subprocess,uuid,os,json,hashlib,shutil
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/stair-shadow-output'
sys.path.append(str(HERE))
import run as verify

def run():
    folder=OUT/'production';folder.mkdir(exist_ok=True)
    candidate=OUT/'candidate/RealisticVisionMod.swf'
    shutil.copyfile(candidate,folder/'candidate.swf')
    verify.runner.compile(HERE/'CandidateOptionsProbe.as',folder/'CandidateOptionsProbe.swf',[HERE],definitions=['-include-libraries='+str(MOD/'build/GameStubs.swc')])
    appid='pfe-modsettings-rv-d30-'+uuid.uuid4().hex
    desc=folder/'test.xml'
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+appid+'</id><versionNumber>1.0</versionNumber><filename>RVRestoreProbe</filename><initialWindow><content>CandidateOptionsProbe.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>',encoding='utf-8')
    results={'appid':appid,'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'runs':[]}
    try:
        for i in (1,2):
            path=folder/('process-'+str(i)+'.txt')
            with path.open('wb') as log:
                proc=subprocess.Popen([str(verify.runner.GAME/'adl64.exe'),'-runtime',str(verify.runner.GAME/'runtimes/air/win64'),str(desc),'-nodebug'],cwd=folder,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                try:code=proc.wait(timeout=55)
                except subprocess.TimeoutExpired:proc.kill();proc.wait();raise RuntimeError('probe timeout')
            text=path.read_text(encoding='utf-8',errors='replace');print(text,flush=True)
            results['runs'].append({'exit':code,'pid':proc.pid,'checks':text.count('PASS ')})
            assert code==0 and 'INSTALLED OPTIONS COMPLETE passed=10' in text and 'FAIL ' not in text
        runtime=(Path(os.environ['APPDATA'])/appid/'Local Store/RVision.log').read_text(encoding='utf-8-sig')
        (folder/'runtime.txt').write_text(runtime,encoding='utf-8')
        assert runtime.count('init ok v0.32.2-stair-candidate')==2 and runtime.count('tick 181')==2
        results['status']='PASS'
    finally:
        desc.unlink(missing_ok=True)
        (folder/'result.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

if __name__=='__main__':run()
