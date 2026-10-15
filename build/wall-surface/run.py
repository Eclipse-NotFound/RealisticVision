"""Build and test a pinned production candidate; never writes release or user saves."""
from pathlib import Path
import argparse, json, os, re, shutil, subprocess, uuid
import prepare

HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
GAME=MOD.parents[1]
OUT=prepare.OUT
TOOLS=GAME/'mods/Sandevistan/build/tools'
JAVA=Path('D:/Program Files/Adobe Animate 2024/jre/bin/java.exe')
SDK=TOOLS/'flexsdk'
AIR=TOOLS/'airsdk/frameworks/libs/air/airglobal.swc'

def compile(entry,out,sources,stubs=False,definitions=()):
    out.parent.mkdir(parents=True,exist_ok=True)
    config=out.with_suffix('.compiler.xml')
    externs=[AIR]+([MOD/'build/GameStubs.swc'] if stubs else [])
    config.write_text('<flex-config><compiler><external-library-path>'+''.join('<path-element>'+str(p)+'</path-element>' for p in externs)+
        '</external-library-path><source-path>'+''.join('<path-element>'+str(p)+'</path-element>' for p in sources)+
        '</source-path><debug>false</debug><optimize>true</optimize><omit-trace-statements>false</omit-trace-statements><theme/></compiler>'+
        '<target-player>32.0</target-player><swf-version>32</swf-version><use-network>false</use-network><static-link-runtime-shared-libraries>true</static-link-runtime-shared-libraries></flex-config>',encoding='utf-8')
    result=subprocess.run([str(JAVA),'-Dfile.encoding=UTF-8','-jar',str(SDK/'lib/mxmlc.jar'),'+flexlib='+str(SDK/'frameworks'),
        '-load-config='+str(config),'-output='+str(out),*definitions,str(entry)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    out.with_suffix('.compile.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    print('Built',out.relative_to(MOD),out.stat().st_size,flush=True)

def run_air(folder,entry,timeout=55):
    desc=folder/'test.xml'
    app_id='pfe-modsettings-rv-surface-'+uuid.uuid4().hex
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+app_id+
        '</id><versionNumber>1.0</versionNumber><filename>RVWallSurface</filename><initialWindow><content>'+entry+
        '</content><visible>false</visible><width>1280</width><height>720</height><renderMode>'+('direct' if entry=='pfe.swf' else 'cpu')+'</renderMode></initialWindow></application>',encoding='utf-8')
    try:
        with (folder/'air-output.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([str(GAME/'adl64.exe'),'-runtime',str(GAME/'runtimes/air/win64'),str(desc),'-nodebug'],cwd=folder,
                stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            try:code=process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill();process.wait();code=124
        evidence=Path(os.environ['APPDATA'])/app_id/'Local Store/evidence'
        if evidence.exists():shutil.copytree(evidence,folder/'evidence',dirs_exist_ok=True)
        (folder/'last-run.json').write_text(json.dumps({'app_id':app_id,'pid':process.pid,'exit':code},indent=2),encoding='utf-8')
        return code,(folder/'air-output.log').read_text(encoding='utf-8',errors='replace')
    finally:desc.unlink(missing_ok=True)

def checks():
    folder=OUT/'checks';source=folder/'src';source.mkdir(parents=True,exist_ok=True)
    for f in (OUT/'candidate/src').rglob('*.as'):
        dest=source/f.relative_to(OUT/'candidate/src');dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(re.sub(r'\bprivate\b','public',f.read_text(encoding='utf-8-sig')),encoding='utf-8')
    results={}
    for harness in ['SurfaceChecks','SoftHarness','SharedExplorationHarness']:
        entry=HERE/(harness+'.as') if harness=='SurfaceChecks' else MOD/'build/motion-tests'/(harness+'.as')
        compile(entry,folder/(harness+'.swf'),[source,HERE,MOD/'build/motion-tests',MOD/'build/stubs'])
        code,log=run_air(folder,harness+'.swf')
        (folder/(harness+'.log')).write_text(log,encoding='utf-8')
        print(log,flush=True)
        results[harness]={'exit':code,'passed':len(re.findall(r'^PASS ',log,re.M)),'failed':len(re.findall(r'^FAIL ',log,re.M))}
        (folder/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        if code or 'COMPLETE' not in log or 'FAIL ' in log or 'MOTION RED' in log:raise RuntimeError(harness+' failed')

def game(rock=False,bench=False):
    folder=OUT/('bench' if bench else 'game-rock' if rock else 'game');folder.mkdir(exist_ok=True)
    (folder/'evidence').mkdir(exist_ok=True)
    for path in GAME.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',path.name):
            dest=folder/path.name
            if not dest.exists() or dest.stat().st_mtime_ns!=path.stat().st_mtime_ns:shutil.copy2(path,dest)
    shutil.copytree(GAME/'Rooms',folder/'Rooms',dirs_exist_ok=True)
    boot=folder/'mods/WallSurfaceProbe/release';boot.mkdir(parents=True,exist_ok=True)
    compile(HERE/'WallSurfaceProbe.as',boot/'WallSurfaceProbe.swf',[HERE],definitions=['-define=CONFIG::rockFixture,'+str(rock).lower(),'-define=CONFIG::wallBench,'+str(bench).lower()])
    (folder/'mods/loader-manifest.txt').write_text('WallSurfaceProbe|WallSurfaceProbe|1|0|0\n',encoding='utf-8')
    for variant in ('baseline','candidate'):
        source=folder/(variant+'-src');source.mkdir(exist_ok=True)
        for f in (OUT/variant/'src').rglob('*.as'):
            dest=source/f.relative_to(OUT/variant/'src');dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(re.sub(r'\bprivate\b','public',f.read_text(encoding='utf-8-sig')),encoding='utf-8')
        compile(source/'RealisticVisionMod.as',folder/(variant+'.swf'),[source],stubs=True)
    code,log=run_air(folder,'pfe.swf',150)
    brief=[]
    for line in log.splitlines():
        if line.startswith('PNG '):
            _,name,data=line.split(' ',2);(folder/'evidence'/name).write_bytes(bytes.fromhex(data))
        elif line.startswith('RESULT '):
            _,name,data=line.split(' ',2);(folder/'evidence'/name).write_text(data,encoding='utf-8')
        elif line.strip():brief.append(line)
    (folder/'game.log').write_text('\n'.join(brief),encoding='utf-8');print('\n'.join(brief[-65:]),flush=True)
    if code or 'SURFACE GAME COMPLETE' not in log or 'FAIL ' in log:raise RuntimeError('Full game capture failed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','checks','game','game-rock','bench']);args=p.parse_args()
    if args.action=='checks':checks()
    elif args.action=='game':game()
    elif args.action=='game-rock':game(True)
    elif args.action=='bench':game(bench=True)
    else:
        for variant in ('baseline','candidate'):
            folder=OUT/variant
            compile(folder/'src/RealisticVisionMod.as',folder/'RealisticVisionMod.swf',[folder/'src'],stubs=True)
