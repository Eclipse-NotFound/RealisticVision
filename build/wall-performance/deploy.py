"""Install exactly the verified D29 bytes; restore this mod alone on failure."""
from pathlib import Path
import argparse,ctypes,datetime,hashlib,json,os,re,shutil,subprocess,time,uuid,zlib
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1]
OUT=MOD/'build/wall-performance-output/deployment'
CANDIDATE=MOD/'build/wall-performance-output/candidate/RealisticVisionMod.swf'
TARGET=MOD/'release/RealisticVisionMod.swf'
OLD='baa48289d9cf86f64cff53b4734032ad29c89c3ac1704db2d89038d4b8db4275'
VERSION='v0.32.1-wall-performance'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def runtime(appid):
    p=Path(os.environ['APPDATA'])/appid/'Local Store/RVision.log'
    return p.read_text(encoding='utf-8-sig') if p.exists() else ''
def prepare():
    proof=json.loads((MOD/'build/wall-performance-output/final-checks.json').read_text(encoding='utf-8'))
    assert proof['status']=='PASS' and proof['candidate_sha256']==sha(CANDIDATE)
    assert sha(TARGET)==OLD,'Installed RV drifted'
    OUT.mkdir(exist_ok=True);assert not (OUT/'preflight.json').exists()
    paths=[GAME/'pfe.swf',GAME/'application.xml',GAME/'mods/loader-manifest.txt',MOD/'release/config.txt']
    # Read only the manifest's runtime artifacts to detect concurrent installs.
    for line in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig').splitlines():
        cols=line.strip().split('|')
        if len(cols)<2 or line.startswith('#'):continue
        folder=GAME/'mods'/cols[0]/'release'
        p=folder/(cols[1]+'.swf')
        if p.exists() and p.resolve()!=TARGET.resolve():paths.append(p)
    before={p.relative_to(GAME).as_posix():sha(p) for p in paths}
    assert '<content>pfe.swf</content>' in (GAME/'application.xml').read_text(encoding='utf-8')
    raw=(GAME/'pfe.swf').read_bytes();decoded=zlib.decompress(raw[8:]) if raw[:3]==b'CWS' else raw[8:]
    loaders=sorted(set(p.decode('ascii') for p in re.findall(rb'mods/[^\x00-\x20]+?/release/[^\x00-\x20]+?\.swf',decoded)))
    assert 'mods/RealisticVision/release/RealisticVisionMod.swf' in loaders
    assert 'RealisticVision|RealisticVisionMod|1|0|0' in (GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig')
    save(OUT/'preflight.json',dict(status='PASS',new_sha256=sha(CANDIDATE),old_sha256=OLD,before=before,loaders=loaders,version=VERSION,script_sha256=sha(Path(__file__))))
    print('PREDEPLOY PASS',flush=True)
def replace(source):
    temp=TARGET.with_name('RealisticVisionMod.deploy-'+uuid.uuid4().hex+'.tmp');shutil.copyfile(source,temp)
    fn=ctypes.WinDLL('kernel32',use_last_error=True).ReplaceFileW
    fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p];fn.restype=ctypes.c_int
    try:
        if not fn(str(TARGET),str(temp),None,0,None,None):raise ctypes.WinError(ctypes.get_last_error())
    finally:temp.unlink(missing_ok=True)
def deploy():
    proof=json.loads((OUT/'preflight.json').read_text(encoding='utf-8'));new=proof['new_sha256']
    assert proof['status']=='PASS' and sha(CANDIDATE)==new and sha(TARGET)==OLD
    assert proof['script_sha256']==sha(Path(__file__)),'Reviewed deployment script changed'
    assert not (OUT/'receipt.json').exists()
    for p,h in proof['before'].items():assert sha(GAME/p)==h,'Installation drift: '+p
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
    backup=MOD/'build/backups'/('before-wall-performance-'+stamp);backup.mkdir(parents=True,exist_ok=False)
    oldfile=backup/'RealisticVisionMod.before.swf'
    with oldfile.open('xb') as f:f.write(TARGET.read_bytes())
    assert sha(oldfile)==OLD
    appid='pfe-modsettings-rv-deploy-v0321-'+uuid.uuid4().hex
    desc=GAME/('app-rv-performance-test-'+stamp+'.xml')
    xml=(GAME/'application.xml').read_text(encoding='utf-8')
    assert xml.count('<id>pfe</id>')==1
    xml=xml.replace('<id>pfe</id>','<id>'+appid+'</id>').replace('<visible>true</visible>','<visible>false</visible>')
    with desc.open('x',encoding='utf-8') as f:f.write(xml)
    record=dict(proof,time=stamp,appid=appid,backup=oldfile.relative_to(MOD).as_posix(),result='pending',authorization='User explicitly requested performance optimization and deployment in this thread')
    installed=False
    try:
        replace(CANDIDATE);installed=True;assert sha(TARGET)==new
        print('DEPLOYED '+new+' backup='+str(oldfile),flush=True)
        with (OUT/'formal-output.txt').open('wb') as output:
            proc=subprocess.Popen([str(GAME/'adl64.exe'),'-runtime',str(GAME/'runtimes/air/win64'),str(desc),'-nodebug'],cwd=GAME,stdout=output,stderr=output,creationflags=subprocess.CREATE_NO_WINDOW)
            record['pid']=proc.pid
            try:
                deadline=time.monotonic()+60
                while time.monotonic()<deadline:
                    assert proc.poll() is None,'Native game exited early'
                    log=runtime(appid)
                    if 'init ok '+VERSION in log and 'ModSettings settings registered' in log and all('tick '+str(n) in log for n in (1,181,361)):break
                    time.sleep(1)
                else:raise RuntimeError('Native startup timed out')
                assert not re.search(r'ERROR|register failed|#1009|#1069',log),log
            finally:
                if proc.poll() is None:proc.terminate()
                proc.wait(timeout=10);record['test_process_closed']=True
                log=runtime(appid);(OUT/'formal-runtime.txt').write_text(log,encoding='utf-8')
        assert sha(TARGET)==new
        for p,h in proof['before'].items():assert sha(GAME/p)==h,'Postinstall drift: '+p
        record['result']='PASS';record['heartbeat_count']=log.count('tick ')
    except BaseException as error:
        if installed:
            assert sha(TARGET)==new,'Concurrent RV replacement; cannot overwrite'
            assert sha(oldfile)==OLD;replace(oldfile);assert sha(TARGET)==OLD
        record.update(result='ROLLED BACK' if installed else 'NOT DEPLOYED',error=repr(error));raise
    finally:
        desc.unlink(missing_ok=True);record['test_descriptor_removed']=not desc.exists();save(OUT/'receipt.json',record)
    print('DEPLOYMENT PASS',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','deploy']);a=p.parse_args()
    prepare() if a.action=='prepare' else deploy()
