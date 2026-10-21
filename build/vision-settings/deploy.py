"""D34: exact verified RV-only replacement, private-desktop smoke and rollback."""
from pathlib import Path
import ctypes, datetime, json, os, re, shutil, time, uuid, zlib
import run
p=run.p
MOD,GAME,OUT=run.MOD,run.GAME,run.OUT
TARGET=MOD/'release/RealisticVisionMod.swf'
CANDIDATE=OUT/'candidate/RealisticVisionMod.swf'
def replace(source):
    temp=TARGET.with_name('RealisticVisionMod.deploy-'+uuid.uuid4().hex+'.tmp');shutil.copyfile(source,temp)
    fn=ctypes.WinDLL('kernel32',use_last_error=True).ReplaceFileW
    fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p];fn.restype=ctypes.c_int
    try:
        if not fn(str(TARGET),str(temp),None,0,None,None):raise ctypes.WinError(ctypes.get_last_error())
    finally:temp.unlink(missing_ok=True)
def main():
    proof=json.loads((OUT/'verified.json').read_text(encoding='utf-8'))
    assert proof['status']=='PASS' and proof['swf']==p.sha(CANDIDATE) and proof['count']==251
    folder=OUT/'deployment';folder.mkdir(exist_ok=False)
    with run.Registration(owner='RealisticVision / D34 部署',purpose='准确设置包正式路径启动与失败回滚',run_dir=folder,evidence=folder/'receipt.json',wait=300) as registration:
        assert p.sha(TARGET)==p.OLD,'Installed RV changed; rebase and revalidate first'
        assert p.sha(GAME/'pfe.swf')==json.loads((OUT/'native-final/inputs.json').read_text())['host'],'Native host changed after validation'
        assert p.sha(CANDIDATE)==proof['swf']
        manifest=(GAME/'mods/loader-manifest.txt').read_text(encoding='utf-8-sig')
        assert 'RealisticVision|RealisticVisionMod|1|0|0' in manifest
        paths=[GAME/'pfe.swf',GAME/'application.xml',GAME/'mods/loader-manifest.txt',MOD/'release/config.txt']
        for line in manifest.splitlines():
            cols=line.strip().split('|')
            if line.startswith('#') or len(cols)<2:continue
            f=GAME/'mods'/cols[0]/'release'/(cols[1]+'.swf')
            if f.exists() and f.resolve()!=TARGET.resolve():paths.append(f)
        before={f.relative_to(GAME).as_posix():p.sha(f) for f in paths}
        xml=(GAME/'application.xml').read_text(encoding='utf-8')
        assert '<content>pfe.swf</content>' in xml
        raw=(GAME/'pfe.swf').read_bytes();body=zlib.decompress(raw[8:]) if raw[:3]==b'CWS' else raw[8:]
        assert b'mods/RealisticVision/release/RealisticVisionMod.swf' in body
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
        backup=MOD/'build/backups'/('before-vision-settings-'+stamp);backup.mkdir(parents=True,exist_ok=False)
        old=backup/'RealisticVisionMod.before.swf';old.write_bytes(TARGET.read_bytes());assert p.sha(old)==p.OLD
        appid='pfe-modsettings-rv-vision-settings-'+uuid.uuid4().hex
        desc=GAME/('app-rv-settings-test-'+stamp+'.xml')
        desc.write_text(xml.replace('<id>pfe</id>','<id>'+appid+'</id>').replace('<visible>true</visible>','<visible>false</visible>'),encoding='utf-8')
        receipt={'version':p.VERSION,'old':p.OLD,'new':proof['swf'],'backup':str(old.relative_to(MOD)),'before':before,'appid':appid,'result':'PENDING','authorization':'GOVERNANCE 6 continuous local deployment; user confirmed settings semantics'}
        installed=False;proc=None
        try:
            assert p.sha(TARGET)==p.OLD
            replace(CANDIDATE);installed=True;assert p.sha(TARGET)==proof['swf']
            registration.before_launch(appid+' / '+str(desc))
            with (folder/'formal-output.txt').open('wb') as stream:
                proc=run.HiddenProcess([GAME/'adl64.exe','-runtime',GAME/'runtimes/air/win64',desc,'-nodebug'],cwd=GAME,stdout=stream,stderr=stream)
                registration.child(proc.pid);receipt['pid']=proc.pid
                logfile=Path(os.environ['APPDATA'])/appid/'Local Store/RVision.log'
                deadline=time.monotonic()+90
                while time.monotonic()<deadline:
                    assert proc.poll() is None,'Native host exited early'
                    log=logfile.read_text(encoding='utf-8-sig') if logfile.exists() else ''
                    if 'init ok '+p.VERSION in log and 'ModSettings settings registered' in log and all('tick '+str(t) in log for t in [1,181,361]):break
                    time.sleep(1)
                else:raise RuntimeError('Formal startup timed out')
                assert not re.search(r'ERROR|register failed|#1009|#1069',log),log
                (folder/'formal-runtime.txt').write_text(log,encoding='utf-8')
                proc.kill();proc.wait();proc.close();proc=None;registration.child_stopped()
            for rel,digest in before.items():assert p.sha(GAME/rel)==digest,'Concurrent protected-file change: '+rel
            assert p.sha(TARGET)==proof['swf'];receipt['result']='PASS'
            registration.outcome='passed';registration.note='准确包正式路径init/设置注册/tick1/181/361通过'
        except BaseException as err:
            if proc:
                if proc.poll() is None:proc.kill();proc.wait()
                proc.close();proc=None;registration.child_stopped()
            if installed:
                assert p.sha(TARGET)==proof['swf'],'Newer RV installation exists; do not overwrite'
                replace(old);assert p.sha(TARGET)==p.OLD
            receipt.update(result='ROLLED_BACK' if installed else 'NOT_DEPLOYED',error=repr(err));raise
        finally:
            desc.unlink(missing_ok=True);receipt['descriptor_removed']=not desc.exists();receipt['own_process_closed']=proc is None
            run.save(folder/'receipt.json',receipt)
        print('DEPLOYMENT PASS '+proof['swf'],flush=True)
if __name__=='__main__':main()
