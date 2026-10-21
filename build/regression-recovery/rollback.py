"""D35: restore the exact pre-afternoon RV package, retaining the regressed one."""
from pathlib import Path
import ctypes, datetime, hashlib, json, os, re, shutil, sys, time, uuid, zlib

MOD=Path(__file__).resolve().parents[2]
GAME=MOD.parents[1]
OUT=MOD/'build/regression-recovery-output'
TARGET=MOD/'release/RealisticVisionMod.swf'
BASE=MOD/'build/stair-shadow-output/merged-v0323/candidate/RealisticVisionMod.swf'
OLD='f2b8a973d9d2a374c9bd8f5da9d29040266954c8f139b8c85bfa0aaaa749a561'
NEW='76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeB83d4caf5c46b7'.lower()
VERSION='v0.32.3-stair-performance'
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import Registration
from air_test_process import HiddenProcess

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def replace(source):
    temp=TARGET.with_name('RealisticVisionMod.recovery-'+uuid.uuid4().hex+'.tmp')
    shutil.copyfile(source,temp)
    fn=ctypes.WinDLL('kernel32',use_last_error=True).ReplaceFileW
    fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p]
    fn.restype=ctypes.c_int
    try:
        if not fn(str(TARGET),str(temp),None,0,None,None):raise ctypes.WinError(ctypes.get_last_error())
    finally:temp.unlink(missing_ok=True)

def main():
    assert sha(BASE)==NEW
    assert sha(MOD/'build/backups/before-vision-settings-20261021-151427-0f4bec/RealisticVisionMod.before.swf')==NEW
    folder=OUT/'rollback';folder.mkdir(parents=True,exist_ok=False)
    with Registration(owner='RealisticVision / D35 回退',purpose='恢复下午修改前v0.32.3；正式路径隔离启动',run_dir=folder,evidence=folder/'receipt.json',wait=300) as rec:
        assert sha(TARGET)==OLD,'Concurrent RV deployment; stop'
        manifest=(GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig')
        assert 'RealisticVision|RealisticVisionMod|1|0|0' in manifest
        xml=(GAME/'application.xml').read_text(encoding='utf-8-sig')
        assert '<content>pfe.swf</content>' in xml and '<id>pfe</id>' in xml
        raw=(GAME/'pfe.swf').read_bytes();body=zlib.decompress(raw[8:]) if raw[:3]==b'CWS' else raw[8:]
        assert b'mods/RealisticVision/release/RealisticVisionMod.swf' in body
        paths=[GAME/'pfe.swf',GAME/'application.xml',GAME/'mods/loader-manifest.txt',MOD/'release/config.txt']
        for line in manifest.splitlines():
            cols=line.strip().split('|')
            if line.startswith('#') or len(cols)<2:continue
            p=GAME/'mods'/cols[0]/'release'/(cols[1]+'.swf')
            if p.exists() and p.resolve()!=TARGET.resolve():paths.append(p)
        before={p.relative_to(GAME).as_posix():sha(p) for p in paths}
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
        backup=MOD/'build/backups'/('before-afternoon-rollback-'+stamp);backup.mkdir(parents=True,exist_ok=False)
        old=backup/'RealisticVisionMod.v0331.swf';shutil.copyfile(TARGET,old);assert sha(old)==OLD
        config=Path(os.environ['APPDATA'])/'pfe/Local Store/RealisticVision_config.txt'
        config_hash=sha(config) if config.exists() else None
        if config.exists():shutil.copyfile(config,backup/'RealisticVision_config.before.txt')
        appid='pfe-modsettings-rv-recovery-'+uuid.uuid4().hex
        desc=GAME/('app-rv-recovery-test-'+stamp+'.xml')
        desc.write_text(xml.replace('<id>pfe</id>','<id>'+appid+'</id>').replace('<visible>true</visible>','<visible>false</visible>'),encoding='utf-8')
        receipt={'time':stamp,'version':VERSION,'old':OLD,'new':NEW,'backup':str(old.relative_to(MOD)),'before':before,'user_config_sha256':config_hash,'appid':appid,'result':'PENDING','authorization':'User explicitly requested rollback before afternoon changes; GOVERNANCE 6'}
        proc=None;installed=False
        try:
            assert sha(TARGET)==OLD
            replace(BASE);installed=True;assert sha(TARGET)==NEW
            save(folder/'receipt.json',receipt)
            print('RESTORED '+VERSION+' '+NEW,flush=True)
            rec.before_launch(appid+' / '+str(desc))
            with (folder/'formal-output.txt').open('wb') as stream:
                proc=HiddenProcess([GAME/'adl64.exe','-runtime',GAME/'runtimes/air/win64',desc,'-nodebug'],cwd=GAME,stdout=stream,stderr=stream)
                rec.child(proc.pid);receipt['pid']=proc.pid
                logfile=Path(os.environ['APPDATA'])/appid/'Local Store/RVision.log'
                deadline=time.monotonic()+90
                while time.monotonic()<deadline:
                    assert proc.poll() is None,'Native host exited early'
                    log=logfile.read_text(encoding='utf-8-sig') if logfile.exists() else ''
                    if 'init ok '+VERSION in log and 'ModSettings settings registered' in log and all('tick '+str(t) in log for t in [1,181,361]):break
                    time.sleep(1)
                else:raise RuntimeError('Formal startup timed out')
                assert not re.search(r'ERROR|register failed|#1009|#1069',log),log
                (folder/'formal-runtime.txt').write_text(log,encoding='utf-8')
                proc.kill();proc.wait();proc.close();proc=None;rec.child_stopped()
            for rel,digest in before.items():assert sha(GAME/rel)==digest,'Concurrent protected-file change: '+rel
            assert sha(TARGET)==NEW
            assert (sha(config) if config.exists() else None)==config_hash,'User config changed concurrently'
            receipt['result']='PASS';rec.outcome='passed';rec.note='v0.32.3正式路径初始化/设置注册/tick1/181/361通过；真实配置未改'
        except BaseException as err:
            if proc:
                if proc.poll() is None:proc.kill();proc.wait()
                proc.close();proc=None;rec.child_stopped()
            if installed:
                assert sha(TARGET)==NEW,'Newer RV installed; do not overwrite'
                replace(old);assert sha(TARGET)==OLD
            receipt.update(result='SMOKE_FAILED_RESTORED_PRE_OPERATION' if installed else 'NOT_CHANGED',error=repr(err));raise
        finally:
            desc.unlink(missing_ok=True);receipt['descriptor_removed']=not desc.exists();receipt['own_process_closed']=proc is None
            save(folder/'receipt.json',receipt)
        print('ROLLBACK VERIFIED',flush=True)

if __name__=='__main__':main()
