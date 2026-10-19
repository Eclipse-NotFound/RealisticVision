"""Install the exact combined D31 + stair fix; retain a single-mod rollback."""
from pathlib import Path
import argparse, datetime, importlib.util, json, re, subprocess, time, uuid, zlib
import merge

MOD, GAME = merge.MOD, merge.GAME
OUT = merge.OUT / 'deployment'
CANDIDATE = merge.OUT / 'candidate/RealisticVisionMod.swf'
TARGET = MOD / 'release/RealisticVisionMod.swf'
COMMON = MOD / 'build/wall-performance/deploy.py'
helper = merge.load('reviewed_rv_deploy_helpers', COMMON)
sha, save, read = merge.sha, merge.save, merge.read
VERSION, OLD = merge.VERSION, merge.OLD


def prepare():
    build = merge.validate_build()
    assert sha(GAME / 'pfe.swf') == build['runtime']['pfe.swf'], 'Host changed after native validation build'
    verified = read(merge.OUT / 'verified.json')
    assert verified['status'] == 'PASS_WITH_RETAINED_REFERENCE_DIAGNOSTICS'
    assert verified['functional_checks'] == 299 and verified['sha256'] == sha(CANDIDATE)
    for rel, digest in verified['evidence'].items():
        assert sha(merge.OUT / rel) == digest, rel
    classes = read(merge.OUT / 'classes.json')
    assert classes['status'] == 'PASS' and classes['sha256'] == sha(CANDIDATE)
    assert sha(TARGET) == OLD, 'Current installation drifted'
    OUT.mkdir(exist_ok=True)
    assert not (OUT / 'preflight.json').exists(), 'Do not overwrite preflight'
    manifest = GAME / 'mods/loader-manifest.txt'
    paths = [GAME / 'pfe.swf', GAME / 'application.xml', manifest, MOD / 'release/config.txt']
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        fields = line.strip().split('|')
        if line.startswith('#') or len(fields) < 2:
            continue
        path = GAME / 'mods' / fields[0] / 'release' / (fields[1] + '.swf')
        if path.exists() and path.resolve() != TARGET.resolve():
            paths.append(path)
    assert '<content>pfe.swf</content>' in (GAME / 'application.xml').read_text(encoding='utf-8')
    raw = (GAME / 'pfe.swf').read_bytes()
    decoded = zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:]
    assert b'mods/RealisticVision/release/RealisticVisionMod.swf' in decoded
    assert 'RealisticVision|RealisticVisionMod|1|0|0' in manifest.read_text(encoding='utf-8-sig')
    save(OUT / 'preflight.json', {'status': 'PASS', 'version': VERSION,
         'old_sha256': OLD, 'new_sha256': sha(CANDIDATE),
         'before': {p.relative_to(GAME).as_posix(): sha(p) for p in paths},
         'script_sha256': sha(Path(__file__)), 'common_sha256': sha(COMMON),
         'merge_script_sha256': sha(Path(merge.__file__)),
         'verified_sha256': sha(merge.OUT / 'verified.json'), 'classes': classes})
    print('MERGE PREDEPLOY PASS', flush=True)


def deploy():
    proof = read(OUT / 'preflight.json')
    new = proof['new_sha256']
    assert proof['status'] == 'PASS' and sha(TARGET) == OLD and sha(CANDIDATE) == new
    assert proof['script_sha256'] == sha(Path(__file__)) and proof['common_sha256'] == sha(COMMON)
    assert proof['merge_script_sha256'] == sha(Path(merge.__file__))
    assert proof['verified_sha256'] == sha(merge.OUT / 'verified.json')
    assert not (OUT / 'receipt.json').exists(), 'Do not overwrite deployment history'
    for rel, digest in proof['before'].items():
        assert sha(GAME / rel) == digest, 'Installation drift: ' + rel
    merge.environment('deployment')
    stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    backup = MOD / 'build/backups' / ('before-stair-merge-' + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    oldfile = backup / 'RealisticVisionMod.before.swf'
    with oldfile.open('xb') as stream:
        stream.write(TARGET.read_bytes())
    assert sha(oldfile) == OLD and sha(TARGET) == OLD
    appid = 'pfe-modsettings-rv-deploy-v0323-' + uuid.uuid4().hex
    descriptor = GAME / ('app-rv-stair-merge-test-' + stamp + '.xml')
    xml = (GAME / 'application.xml').read_text(encoding='utf-8')
    assert xml.count('<id>pfe</id>') == 1 and xml.count('<visible>true</visible>') == 1
    xml = xml.replace('<id>pfe</id>', '<id>' + appid + '</id>').replace('<visible>true</visible>', '<visible>false</visible>')
    with descriptor.open('x', encoding='utf-8') as stream:
        stream.write(xml)
    record = dict(proof, time=stamp, timezone='Asia/Shanghai', appid=appid,
                  backup=oldfile.relative_to(MOD).as_posix(), result='pending',
                  authorization='User explicitly requested merging and deploying the other conversation stair fix')
    installed = False
    try:
        helper.replace(CANDIDATE)
        installed = True
        assert sha(TARGET) == new
        print('MERGE DEPLOYED ' + new, flush=True)
        with (OUT / 'formal-output.txt').open('wb') as output:
            proc = subprocess.Popen([str(GAME / 'adl64.exe'), '-runtime', str(GAME / 'runtimes/air/win64'), str(descriptor), '-nodebug'], cwd=GAME, stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW)
            record['pid'] = proc.pid
            try:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    assert proc.poll() is None, 'Native game exited early'
                    log = helper.runtime(appid)
                    if 'init ok ' + VERSION in log and 'ModSettings settings registered' in log and all('tick ' + str(n) in log for n in [1, 181, 361]):
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError('Native startup timed out')
                assert not re.search(r'ERROR|register failed|#1009|#1069', log), log
            finally:
                if proc.poll() is None:
                    proc.terminate()
                proc.wait(timeout=10)
                record['test_process_closed'] = True
                (OUT / 'formal-runtime.txt').write_text(helper.runtime(appid), encoding='utf-8')
        assert sha(TARGET) == new
        for rel, digest in proof['before'].items():
            assert sha(GAME / rel) == digest, 'Postinstall drift: ' + rel
        record['result'] = 'PASS'
    except BaseException as error:
        if installed:
            assert sha(TARGET) == new, 'Concurrent RV replacement; cannot overwrite'
            assert sha(oldfile) == OLD
            helper.replace(oldfile)
            assert sha(TARGET) == OLD
        record.update(result='ROLLED BACK' if installed else 'NOT DEPLOYED', error=repr(error))
        raise
    finally:
        descriptor.unlink(missing_ok=True)
        record['test_descriptor_removed'] = not descriptor.exists()
        save(OUT / 'receipt.json', record)
    print('MERGE DEPLOYMENT PASS; own process and descriptor closed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'deploy'])
    prepare() if parser.parse_args().action == 'prepare' else deploy()
