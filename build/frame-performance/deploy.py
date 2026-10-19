"""Install the exact validated D31 bytes; roll back RV alone if startup fails."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, os, re, subprocess, time, uuid, zlib
import psutil

HERE = Path(__file__).resolve().parent
MOD, GAME = HERE.parents[1], HERE.parents[3]
OUT = MOD / 'build/frame-performance-output/deployment'
PRODUCTION = MOD / 'build/frame-performance-output/production'
CANDIDATE = PRODUCTION / 'RealisticVisionMod.swf'
TARGET = MOD / 'release/RealisticVisionMod.swf'
OLD = '2e7150cf415355c2d7b809689aac3c4ca0bacbb5f6d8770066a6e887d8907a10'
NEW = 'decca3e0e1142eb8faf7e0e776f2b94fc67dce1c5503de7fba7b810c4a0b10ca'
VERSION = 'v0.32.2-frame-performance'
COMMON = MOD / 'build/wall-performance/deploy.py'
spec = importlib.util.spec_from_file_location('previous_rv_deployment', COMMON)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
assert common.TARGET == TARGET
sha, save, runtime, replace = common.sha, common.save, common.runtime, common.replace


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def validate_evidence():
    assert sha(CANDIDATE) == NEW and sha(TARGET) == OLD, 'Candidate or installed RV changed'
    manifest = read(PRODUCTION / 'source-manifest.json')
    assert manifest['swf'] == NEW and manifest['version'] == VERSION
    assert len(manifest['sources']) == 6
    for rel, digest in manifest['sources'].items():
        p = PRODUCTION / 'src' / rel
        assert sha(p) == digest, rel
        expected = (OUT.parent / 'candidate/src' / rel).read_text(encoding='utf-8-sig')
        if p.name == 'RealisticVisionMod.as':
            expected = expected.replace('v0.32.1-wall-performance', VERSION)
        assert p.read_text(encoding='utf-8-sig') == expected, 'Production differs from tested source: ' + rel
    options = read(PRODUCTION / 'options/result.json')
    assert options['status'] == 'PASS' and options['sha256'] == NEW
    assert len(options['runs']) == 2 and all(x['exit'] == 0 and x['checks'] == 10 for x in options['runs'])
    exact = read(OUT.parent / 'final-large-verify/evidence/result.json')
    assert len(exact['checks']) == 32 and all(x['exact'] for x in exact['checks']) and not exact.get('error')
    timing = read(OUT.parent / 'analysis-final.json')
    assert timing['last_run']['exit'] == 0 and len(timing['rows']) == 4
    for row in timing['rows']:
        assert all(s['n'] == 120 for s in row['total'])
    for name in ['final-large-trial', 'final-large-verify']:
        inputs = read(OUT.parent / name / 'build-inputs.json')
        for rel, digest in inputs['sources'].items():
            assert sha(OUT.parent / rel) == digest, rel
    for name in ['MaskChecks', 'SightChecks', 'SoftHarness', 'SharedExplorationHarness']:
        log = (OUT.parent / 'checks-final' / (name + '.txt')).read_text(encoding='utf-8-sig')
        assert 'COMPLETE' in log and 'FAIL ' not in log and 'MOTION RED' not in log
    viewport = (OUT.parent / 'viewport-checks-03/ViewportChecks.txt').read_text(encoding='utf-8-sig')
    assert 'COMPLETE' in viewport and 'FAIL ' not in viewport


def prepare():
    validate_evidence()
    OUT.mkdir(exist_ok=True)
    assert not (OUT / 'preflight.json').exists(), 'Do not overwrite a preflight record'
    manifest = GAME / 'mods/loader-manifest.txt'
    paths = [GAME / 'pfe.swf', GAME / 'application.xml', manifest, MOD / 'release/config.txt']
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        cols = line.strip().split('|')
        if len(cols) < 2 or line.startswith('#'):
            continue
        p = GAME / 'mods' / cols[0] / 'release' / (cols[1] + '.swf')
        if p.exists() and p.resolve() != TARGET.resolve():
            paths.append(p)
    assert '<content>pfe.swf</content>' in (GAME / 'application.xml').read_text(encoding='utf-8')
    raw = (GAME / 'pfe.swf').read_bytes()
    decoded = zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:]
    loaders = sorted(set(p.decode('ascii') for p in re.findall(rb'mods/[^\x00-\x20]+?/release/[^\x00-\x20]+?\.swf', decoded)))
    assert 'mods/RealisticVision/release/RealisticVisionMod.swf' in loaders
    assert 'RealisticVision|RealisticVisionMod|1|0|0' in manifest.read_text(encoding='utf-8-sig')
    save(OUT / 'preflight.json', {
        'status': 'PASS', 'version': VERSION, 'new_sha256': NEW, 'old_sha256': OLD,
        'before': {p.relative_to(GAME).as_posix(): sha(p) for p in paths}, 'loaders': loaders,
        'script_sha256': sha(Path(__file__)), 'common_script_sha256': sha(COMMON),
        'source_manifest_sha256': sha(PRODUCTION / 'source-manifest.json'),
        'evidence': {'production_options': '20 passed', 'logic_checks': '55 aggregate passed',
                     'viewport_images': 192, 'native_exact_groups': 32, 'paired_timing_cases': 4,
                     'limitation': 'Not total game FPS; classic peak rose from 243 to 266 ms'},
    })
    print('PREDEPLOY PASS; exact validated bytes; installed files unchanged', flush=True)


def deploy():
    proof = read(OUT / 'preflight.json')
    assert proof['status'] == 'PASS' and sha(CANDIDATE) == NEW and sha(TARGET) == OLD
    assert proof['script_sha256'] == sha(Path(__file__)) and proof['common_script_sha256'] == sha(COMMON)
    assert not (OUT / 'receipt.json').exists(), 'Do not overwrite deployment history'
    for rel, digest in proof['before'].items():
        assert sha(GAME / rel) == digest, 'Installation drift: ' + rel
    stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]
    available = psutil.virtual_memory().available
    environment = {'available_bytes': available, 'minimum_available_bytes': 6 * 1024**3,
                   'processes': [p.info for p in psutil.process_iter(['pid', 'name'])
                                 if (p.info['name'] or '').lower() in ['adl.exe', 'adl64.exe', 'java.exe', 'javaw.exe']]}
    save(OUT / ('launch-' + stamp + '.json'), environment)
    assert available >= 6 * 1024**3, 'Less than 6 GiB available; no installation or AIR start'
    backup = MOD / 'build/backups' / ('before-frame-performance-' + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    oldfile = backup / 'RealisticVisionMod.before.swf'
    with oldfile.open('xb') as stream:
        stream.write(TARGET.read_bytes())
    assert sha(oldfile) == OLD and sha(TARGET) == OLD
    appid = 'pfe-modsettings-rv-deploy-v0322-' + uuid.uuid4().hex
    desc = GAME / ('app-rv-performance-test-' + stamp + '.xml')
    xml = (GAME / 'application.xml').read_text(encoding='utf-8')
    assert xml.count('<id>pfe</id>') == 1 and xml.count('<visible>true</visible>') == 1
    xml = xml.replace('<id>pfe</id>', '<id>' + appid + '</id>').replace('<visible>true</visible>', '<visible>false</visible>')
    with desc.open('x', encoding='utf-8') as stream:
        stream.write(xml)
    record = dict(proof, time=stamp, timezone='Asia/Shanghai', appid=appid, environment=environment,
                  backup=oldfile.relative_to(MOD).as_posix(), result='pending',
                  authorization='User explicitly requested deployment of the final improved version in this thread')
    installed = False
    try:
        replace(CANDIDATE)
        installed = True
        assert sha(TARGET) == NEW
        print('DEPLOYED ' + NEW + ' backup=' + str(oldfile), flush=True)
        with (OUT / 'formal-output.txt').open('wb') as output:
            proc = subprocess.Popen([str(GAME / 'adl64.exe'), '-runtime', str(GAME / 'runtimes/air/win64'), str(desc), '-nodebug'],
                                    cwd=GAME, stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW)
            record['pid'] = proc.pid
            try:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    assert proc.poll() is None, 'Native game exited early'
                    log = runtime(appid)
                    if 'init ok ' + VERSION in log and 'ModSettings settings registered' in log and all('tick ' + str(n) in log for n in (1, 181, 361)):
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
                log = runtime(appid)
                (OUT / 'formal-runtime.txt').write_text(log, encoding='utf-8')
        assert sha(TARGET) == NEW
        for rel, digest in proof['before'].items():
            assert sha(GAME / rel) == digest, 'Postinstall drift: ' + rel
        record.update(result='PASS', heartbeat_count=log.count('tick '))
    except BaseException as error:
        if installed:
            assert sha(TARGET) == NEW, 'Concurrent RV replacement; cannot overwrite'
            assert sha(oldfile) == OLD
            replace(oldfile)
            assert sha(TARGET) == OLD
        record.update(result='ROLLED BACK' if installed else 'NOT DEPLOYED', error=repr(error))
        raise
    finally:
        desc.unlink(missing_ok=True)
        record['test_descriptor_removed'] = not desc.exists()
        save(OUT / 'receipt.json', record)
    print('DEPLOYMENT PASS; own process and descriptor closed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'deploy'])
    prepare() if parser.parse_args().action == 'prepare' else deploy()
