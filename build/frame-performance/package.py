"""Freeze and test exact D31 production bytes. Never writes the installed release."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, uuid
import run

OUT=run.OUT;MOD=run.MOD;HERE=run.HERE
VERSION='v0.32.2-frame-performance'

def package():
    folder=OUT/'production';folder.mkdir(exist_ok=True)
    src=folder/'src';src.mkdir(exist_ok=True)
    for p in (OUT/'candidate/src').rglob('*.as'):
        dest=src/p.relative_to(OUT/'candidate/src');dest.parent.mkdir(parents=True,exist_ok=True)
        data=p.read_text(encoding='utf-8-sig')
        if p.name=='RealisticVisionMod.as':
            assert data.count('v0.32.1-wall-performance')==1
            data=data.replace('v0.32.1-wall-performance',VERSION)
        dest.write_text(data,encoding='utf-8')
    target=folder/'RealisticVisionMod.swf'
    run.runner.compile(src/'RealisticVisionMod.as',target,[src],stubs=True)
    (folder/'source-manifest.json').write_text(json.dumps({'version':VERSION,'swf':run.sha(target),'sources':{str(p.relative_to(src)):run.sha(p) for p in sorted(src.rglob('*.as'))}},indent=2),encoding='utf-8')
    probe=folder/'options';probe.mkdir(exist_ok=True);shutil.copyfile(target,probe/'candidate.swf')
    run.runner.compile(MOD/'build/wall-performance/CandidateOptionsProbe.as',probe/'CandidateOptionsProbe.swf',[MOD/'build/wall-performance'],definitions=['-include-libraries='+str(MOD/'build/GameStubs.swc')])
    appid='pfe-modsettings-rv-d30-'+uuid.uuid4().hex;desc=probe/'test.xml'
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+appid+'</id><versionNumber>1.0</versionNumber><filename>RVFrameProbe</filename><initialWindow><content>CandidateOptionsProbe.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>',encoding='utf-8')
    result={'app_id':appid,'sha256':run.sha(target),'runs':[]}
    try:
        for i in [1,2]:
            path=probe/('process-'+str(i)+'.txt')
            with path.open('wb') as log:
                proc=subprocess.Popen([str(run.runner.GAME/'adl64.exe'),'-runtime',str(run.runner.GAME/'runtimes/air/win64'),str(desc),'-nodebug'],cwd=probe,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                try:code=proc.wait(timeout=60)
                except subprocess.TimeoutExpired:proc.kill();proc.wait();raise RuntimeError('settings timeout')
            text=path.read_text(encoding='utf-8',errors='replace');print(text,flush=True)
            result['runs'].append({'exit':code,'pid':proc.pid,'checks':text.count('PASS ')})
            assert code==0 and 'INSTALLED OPTIONS COMPLETE passed=10' in text and 'FAIL ' not in text
        log=(Path(os.environ['APPDATA'])/appid/'Local Store/RVision.log').read_text(encoding='utf-8-sig')
        (probe/'runtime.txt').write_text(log,encoding='utf-8')
        assert log.count('init ok '+VERSION)==2 and log.count('tick 181')==2
        result['status']='PASS'
    finally:
        desc.unlink(missing_ok=True);(probe/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__':package()
