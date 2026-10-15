"""Install the reviewed D27 bytes only, with isolated startup and automatic rollback."""
from pathlib import Path
import argparse, ctypes, datetime, hashlib, json, os, re, shutil, subprocess, time, uuid, zlib

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
GAME = MOD.parents[1]
OUT = MOD / 'build/wall-options-output/deployment'
OUT.mkdir(parents=True, exist_ok=True)
NEW = 'baa48289d9cf86f64cff53b4734032ad29c89c3ac1704db2d89038d4b8db4275'
OLD = 'e99608088a8b00b4442bc3aef52d8035336f0123ea5a96d55503c90b1f6e0808'
VERSION = 'v0.31.1-wall-options-candidate'
CANDIDATE = MOD / 'build/wall-options-output/candidate/RealisticVisionMod.swf'
TARGET = MOD / 'release/RealisticVisionMod.swf'
PROTECTED = {
    'pfe.swf': '9987c696bebbeb0626d8f73da775cf867b2ced4ff626137fd9f161264270f938',
    'application.xml': '70dd3b085e5f6c66c03693cf68ce5e93a4e4136dd745d40d1a5b2a49863ba236',
    'mods/RealisticVision/release/config.txt': '5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f',
}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
def runtime_log(appid):
    path = Path(os.environ['APPDATA']) / appid / 'Local Store/RVision.log'
    return path.read_text(encoding='utf-8-sig') if path.exists() else ''
def validate_inputs():
    assert sha(CANDIDATE) == NEW, 'Candidate changed'
    assert sha(TARGET) == OLD, 'Installed version changed; re-evaluate before deployment'
    for path, expected in PROTECTED.items(): assert sha(GAME/path) == expected, path
    proof = json.loads((MOD/'knowledge/experiments/wall-options-v0311-20261015/final-checks.json').read_text(encoding='utf-8'))
    assert proof['candidate_sha256'] == NEW and proof['checks_passed'] == 212 and proof['pixel_groups_passed'] == 8
    assert not proof['embedded_game_classes'] and proof['installed_keybinds_preserved_in_candidate']

def preflight():
    validate_inputs()
    assert not (OUT/'preflight.json').exists(), 'Do not overwrite a previous run'
    folder = OUT/'probe'; folder.mkdir(exist_ok=True)
    shutil.copyfile(CANDIDATE, folder/'candidate.swf')
    sdk = GAME/'mods/Sandevistan/build/tools/flexsdk'
    air = GAME/'mods/Sandevistan/build/tools/airsdk/frameworks/libs/air/airglobal.swc'
    java = Path('D:/Program Files/Adobe Animate 2024/jre/bin/java.exe')
    config = folder/'probe.compiler.xml'
    config.write_text('<flex-config><compiler><external-library-path><path-element>'+str(air)+
        '</path-element></external-library-path><include-libraries><library>'+str(MOD/'build/GameStubs.swc')+
        '</library></include-libraries><source-path><path-element>'+str(HERE)+
        '</path-element></source-path><debug>false</debug><optimize>true</optimize><omit-trace-statements>false</omit-trace-statements><theme/></compiler>'+
        '<target-player>32.0</target-player><swf-version>32</swf-version><use-network>false</use-network><static-link-runtime-shared-libraries>true</static-link-runtime-shared-libraries></flex-config>', encoding='utf-8')
    build = subprocess.run([str(java),'-Dfile.encoding=UTF-8','-jar',str(sdk/'lib/mxmlc.jar'),'+flexlib='+str(sdk/'frameworks'),
        '-load-config='+str(config),'-output='+str(folder/'InstalledOptionsProbe.swf'),str(HERE/'InstalledOptionsProbe.as')],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    (folder/'compile.txt').write_text(build.stdout+build.stderr, encoding='utf-8')
    assert build.returncode == 0, build.stdout+build.stderr
    appid = 'pfe-modsettings-rv-d27-probe-'+uuid.uuid4().hex
    desc = folder/'app-rv-options-test.xml'
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+appid+
        '</id><versionNumber>1.0</versionNumber><filename>RVOptionsProbe</filename><initialWindow><content>InstalledOptionsProbe.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>',encoding='utf-8')
    result = dict(candidate_sha256=NEW, appid=appid, runs=[], status='pending')
    try:
        for index in (1,2):
            with (OUT/('probe-'+str(index)+'.txt')).open('wb') as output:
                p = subprocess.Popen([str(GAME/'adl64.exe'),'-runtime',str(GAME/'runtimes/air/win64'),str(desc),'-nodebug'],
                    cwd=folder, stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW)
                try: code = p.wait(timeout=55)
                except subprocess.TimeoutExpired:
                    p.kill();p.wait(timeout=10);raise RuntimeError('Production-byte probe timed out')
            text = (OUT/('probe-'+str(index)+'.txt')).read_text(encoding='utf-8',errors='replace')
            result['runs'].append(dict(pid=p.pid,exit=code,checks=text.count('PASS ')))
            print(text,flush=True)
            assert code == 0 and 'INSTALLED OPTIONS COMPLETE passed=10' in text and 'FAIL ' not in text
        log = runtime_log(appid)
        (OUT/'probe-runtime.txt').write_text(log,encoding='utf-8')
        assert log.count('init ok '+VERSION) == 2 and log.count('tick 181') == 2
        assert 'ERROR' not in log and 'register failed' not in log
        result['status']='PASS'
    except BaseException as error:
        result.update(status='FAIL',error=repr(error));raise
    finally:
        desc.unlink(missing_ok=True)
        save(OUT/'preflight.json',result)

def replace_target(source):
    temp = TARGET.with_name('RealisticVisionMod.deploy-'+uuid.uuid4().hex+'.tmp')
    shutil.copyfile(source,temp)
    replace = ctypes.WinDLL('kernel32',use_last_error=True).ReplaceFileW
    replace.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p]
    replace.restype=ctypes.c_int
    try:
        if not replace(str(TARGET),str(temp),None,0,None,None): raise ctypes.WinError(ctypes.get_last_error())
    finally: temp.unlink(missing_ok=True)

def deploy():
    validate_inputs()
    assert not (OUT/'deployment-receipt.json').exists(), 'Do not overwrite deployment history'
    proof=json.loads((OUT/'preflight.json').read_text(encoding='utf-8'))
    assert proof['status']=='PASS' and proof['candidate_sha256']==NEW
    xml=(GAME/'application.xml').read_text(encoding='utf-8')
    assert '<content>pfe.swf</content>' in xml
    host=(GAME/'pfe.swf').read_bytes()
    decoded=zlib.decompress(host[8:]) if host[:3]==b'CWS' else host[8:]
    loaders=sorted(set(x.decode('ascii') for x in re.findall(rb'mods/[^\x00-\x20]+?/release/[^\x00-\x20]+?\.swf',decoded)))
    assert 'mods/RealisticVision/release/RealisticVisionMod.swf' in loaders
    manifest=GAME/'mods/loader-manifest.txt'
    assert 'RealisticVision|RealisticVisionMod|1|0|0' in manifest.read_text(encoding='utf-8-sig')
    protected=dict(PROTECTED);protected['mods/loader-manifest.txt']=sha(manifest)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    backup=MOD/'build/backups'/('before-wall-options-'+stamp)
    backup.mkdir(parents=True,exist_ok=False)
    oldfile=backup/'RealisticVisionMod.before.swf'
    with oldfile.open('xb') as stream:stream.write(TARGET.read_bytes())
    assert sha(oldfile)==OLD and sha(TARGET)==OLD
    appid='pfe-modsettings-rv-deploy-v0311-'+uuid.uuid4().hex
    desc=GAME/('app-rv-options-test-'+stamp+'.xml')
    assert not desc.exists()
    desc.write_text(xml.replace('<id>pfe</id>','<id>'+appid+'</id>').replace('<visible>true</visible>','<visible>false</visible>'),encoding='utf-8')
    record=dict(time=stamp,version=VERSION,source_commit='5222966',new_sha256=NEW,previous_sha256=OLD,
        backup=oldfile.relative_to(MOD).as_posix(),before=protected,static_host_paths=loaders,
        appid=appid,descriptor=str(desc),result='pending',authorization='User explicitly requested deployment in this thread')
    installed=False
    try:
        replace_target(CANDIDATE);installed=True
        assert sha(TARGET)==NEW
        print('DEPLOYED '+NEW+' backup='+str(oldfile),flush=True)
        with (OUT/'formal-output.txt').open('wb') as output:
            p=subprocess.Popen([str(GAME/'adl64.exe'),'-runtime',str(GAME/'runtimes/air/win64'),str(desc),'-nodebug'],
                cwd=GAME,stdout=output,stderr=output,creationflags=subprocess.CREATE_NO_WINDOW)
            record['pid']=p.pid
            try:
                deadline=time.monotonic()+55
                while time.monotonic()<deadline:
                    assert p.poll() is None,'Native game process exited early'
                    log=runtime_log(appid)
                    if ('init ok '+VERSION in log and 'ModSettings settings registered' in log
                        and all('tick '+str(n) in log for n in (1,181,361))):break
                    time.sleep(1)
                else:raise RuntimeError('Native startup checks timed out')
                assert not re.search(r'ERROR|register failed|#1009|#1069',log),log
            finally:
                if p.poll() is None:p.terminate()
                p.wait(timeout=10);record['test_process_closed']=True
                log=runtime_log(appid);(OUT/'formal-runtime.txt').write_text(log,encoding='utf-8')
                print(log,flush=True)
        record['heartbeat_count']=log.count('tick ')
        assert sha(TARGET)==NEW
        for path,expected in protected.items():assert sha(GAME/path)==expected,path
        record['result']='PASS'
    except BaseException as error:
        if installed:
            assert sha(TARGET)==NEW,'Unexpected concurrent target replacement; do not overwrite it'
            assert sha(oldfile)==OLD
            replace_target(oldfile);assert sha(TARGET)==OLD
        record.update(result='ROLLED BACK' if installed else 'NOT DEPLOYED',error=repr(error));raise
    finally:
        desc.unlink(missing_ok=True);record['test_descriptor_removed']=not desc.exists()
        save(OUT/'deployment-receipt.json',record)
    print('DEPLOYMENT PASS',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','deploy']);args=parser.parse_args()
    preflight() if args.action=='preflight' else deploy()
