"""Merge the reviewed stair condition into exact D31 sources; isolated checks only."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, uuid
import psutil

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
GAME = MOD.parents[1]
OUT = MOD / 'build/stair-shadow-output/merged-v0323'
BASE = MOD / 'build/frame-performance-output/production'
STAIR = MOD / 'build/stair-shadow-output/candidate'
VERSION = 'v0.32.3-stair-performance'
OLD = 'decca3e0e1142eb8faf7e0e776f2b94fc67dce1c5503de7fba7b810c4a0b10ca'
STAIR_SHA = '325a0ddc09adc286d442f02f81fe09cb9a4bafbbd7207e6c3d244fa7f6770a92'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stair = load('reviewed_stair_runner', MOD / 'build/stair-shadow/run.py')
stair.OUT = OUT
runner = stair.runner


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify_source():
    proof = read(OUT / 'merge-inputs.json')
    assert sha(BASE / 'RealisticVisionMod.swf') == OLD
    assert sha(STAIR / 'RealisticVisionMod.swf') == STAIR_SHA
    for variant in ['baseline', 'candidate']:
        for rel, digest in proof[variant].items():
            assert sha(OUT / variant / 'src' / rel) == digest, variant + '/' + rel
    return proof


def prepare():
    assert not OUT.exists(), 'Frozen merge output already exists'
    assert sha(BASE / 'RealisticVisionMod.swf') == OLD
    assert sha(STAIR / 'RealisticVisionMod.swf') == STAIR_SHA
    pins = read(BASE / 'source-manifest.json')
    assert pins['swf'] == OLD and len(pins['sources']) == 6
    for rel, digest in pins['sources'].items():
        assert sha(BASE / 'src' / rel) == digest
    old_helper = MOD / 'build/stair-shadow-output/baseline/src/RVWallSurface.as'
    assert sha(BASE / 'src/RVWallSurface.as') == sha(old_helper)
    expected_helper = stair.candidate_text(old_helper)
    assert expected_helper == (STAIR / 'src/RVWallSurface.as').read_text(encoding='utf-8-sig')
    OUT.mkdir(parents=True)
    for variant in ['baseline', 'candidate']:
        shutil.copytree(BASE / 'src', OUT / variant / 'src')
    source = OUT / 'candidate/src'
    (source / 'RVWallSurface.as').write_text(expected_helper, encoding='utf-8')
    main = source / 'RealisticVisionMod.as'
    text = main.read_text(encoding='utf-8-sig')
    assert text.count('v0.32.2-frame-performance') == 1
    main.write_text(text.replace('v0.32.2-frame-performance', VERSION), encoding='utf-8')
    proof = {'version': VERSION, 'base_swf': OLD, 'stair_swf': STAIR_SHA,
             'scope': 'Only contourRole physical-height condition plus version marker'}
    for variant in ['baseline', 'candidate']:
        root = OUT / variant / 'src'
        proof[variant] = {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*.as'))}
    assert {k for k in proof['baseline'] if proof['baseline'][k] != proof['candidate'][k]} == {'RealisticVisionMod.as', 'RVWallSurface.as'}
    save(OUT / 'merge-inputs.json', proof)
    print('MERGE PREPARED: D31 performance retained; reviewed D30 height condition only', flush=True)


def build():
    proof = verify_source()
    assert not (OUT / 'build-complete.json').exists(), 'Build already frozen'
    source = OUT / 'candidate/src'
    runner.compile(source / 'RealisticVisionMod.as', OUT / 'candidate/RealisticVisionMod.swf', [source], stubs=True)
    stair.checks('checks', False)
    stair.regression(False)
    capture = OUT / 'capture'
    capture.mkdir()
    (capture / 'evidence').mkdir()
    runtime_files = []
    for path in GAME.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml', path.name):
            shutil.copyfile(path, capture / path.name)
            runtime_files.append(path.name)
    shutil.copytree(GAME / 'Rooms', capture / 'Rooms')
    boot = capture / 'mods/WallSurfaceProbe/release'
    boot.mkdir(parents=True)
    probe = MOD / 'build/stair-shadow/WallSurfaceProbe.as'
    runner.compile(probe, boot / 'WallSurfaceProbe.swf', [probe.parent], definitions=['-define=CONFIG::rockFixture,false', '-define=CONFIG::wallBench,false'])
    (capture / 'mods/loader-manifest.txt').write_text('WallSurfaceProbe|WallSurfaceProbe|1|0|0\n', encoding='utf-8')
    for variant in ['baseline', 'candidate']:
        public = capture / (variant + '-src')
        stair.public_source(variant, public)
        runner.compile(public / 'RealisticVisionMod.as', capture / (variant + '.swf'), [public], stubs=True)
    options = OUT / 'options'
    options.mkdir()
    shutil.copyfile(OUT / 'candidate/RealisticVisionMod.swf', options / 'candidate.swf')
    option_probe = MOD / 'build/stair-shadow/CandidateOptionsProbe.as'
    runner.compile(option_probe, options / 'CandidateOptionsProbe.swf', [option_probe.parent], definitions=['-include-libraries=' + str(MOD / 'build/GameStubs.swc')])
    proof['candidate_swf'] = sha(OUT / 'candidate/RealisticVisionMod.swf')
    proof['bytes'] = (OUT / 'candidate/RealisticVisionMod.swf').stat().st_size
    proof['runtime'] = {name: sha(capture / name) for name in runtime_files}
    proof['harness_sources'] = {str(p.relative_to(MOD)): sha(p) for p in [probe, option_probe, MOD / 'build/stair-shadow/StairChecks.as']}
    proof['compiled'] = {p.relative_to(OUT).as_posix(): sha(p) for p in OUT.rglob('*.swf')}
    save(OUT / 'build-complete.json', proof)
    print('MERGE BUILD COMPLETE ' + proof['candidate_swf'], flush=True)


def environment(name):
    data = {'available_bytes': psutil.virtual_memory().available,
            'processes': [p.info for p in psutil.process_iter(['pid', 'name'])
                          if (p.info['name'] or '').lower() in ['adl.exe', 'adl64.exe', 'java.exe', 'javaw.exe']]}
    save(OUT / (name + '-environment-' + uuid.uuid4().hex[:12] + '.json'), data)
    assert data['available_bytes'] >= 6 * 1024**3, 'Below 6 GiB; do not start AIR'


def validate_build():
    verify_source()
    proof = read(OUT / 'build-complete.json')
    for rel, digest in proof['compiled'].items():
        assert sha(OUT / rel) == digest, rel
    return proof


def run_checks():
    validate_build()
    assert not (OUT / 'checks-result.json').exists()
    environment('checks')
    results = []
    for folder, entry, count in [('checks', 'StairChecks', 44), ('regression', 'EquivalenceChecks', 68),
                                  ('regression', 'RestoreChecks', 26), ('regression', 'SettingsChecks', 8),
                                  ('regression', 'SoftHarness', 16), ('regression', 'SharedExplorationHarness', 21)]:
        code, log = runner.run_air(OUT / folder, entry + '.swf')
        (OUT / folder / (entry + '.txt')).write_text(log, encoding='utf-8')
        record = read(OUT / folder / 'last-run.json')
        record.update(name=entry, passed=len(re.findall(r'^PASS ', log, re.M)))
        results.append(record)
        save(OUT / 'checks-result.json', results)
        print(entry, 'exit=' + str(code), 'passed=' + str(record['passed']), flush=True)
        assert code == 0 and 'COMPLETE' in log and 'FAIL ' not in log and 'MOTION RED' not in log
        assert record['passed'] == count


def run_capture():
    validate_build()
    capture = OUT / 'capture'
    assert not (capture / 'last-run.json').exists()
    environment('capture')
    code, log = runner.run_air(capture, 'pfe.swf', 200)
    (capture / 'game.log').write_text(log, encoding='utf-8')
    print('\n'.join(log.splitlines()[-8:]), flush=True)
    assert code == 0 and 'SURFACE GAME COMPLETE checks=96' in log and 'FAIL ' not in log


def run_options():
    proof = validate_build()
    folder = OUT / 'options'
    assert not (folder / 'result.json').exists()
    environment('options')
    appid = 'pfe-modsettings-rv-stair-merge-' + uuid.uuid4().hex
    desc = folder / 'test.xml'
    desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>' + appid + '</id><versionNumber>1.0</versionNumber><filename>RVMergeOptions</filename><initialWindow><content>CandidateOptionsProbe.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>', encoding='utf-8')
    result = {'appid': appid, 'sha256': proof['candidate_swf'], 'runs': [], 'status': 'INCOMPLETE'}
    try:
        for i in [1, 2]:
            path = folder / ('process-' + str(i) + '.txt')
            with path.open('wb') as output:
                proc = subprocess.Popen([str(GAME / 'adl64.exe'), '-runtime', str(GAME / 'runtimes/air/win64'), str(desc), '-nodebug'], cwd=folder, stdout=output, stderr=output, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    code = proc.wait(timeout=60)
                finally:
                    if proc.poll() is None:
                        proc.kill()
                        proc.wait(timeout=10)
            log = path.read_text(encoding='utf-8', errors='replace')
            result['runs'].append({'pid': proc.pid, 'exit': code, 'checks': log.count('PASS ')})
            assert code == 0 and 'INSTALLED OPTIONS COMPLETE passed=10' in log and 'FAIL ' not in log
        log = (Path(os.environ['APPDATA']) / appid / 'Local Store/RVision.log').read_text(encoding='utf-8-sig')
        (folder / 'runtime.txt').write_text(log, encoding='utf-8')
        assert log.count('init ok ' + VERSION) == 2 and log.count('tick 181') == 2
        result['status'] = 'PASS'
    finally:
        desc.unlink(missing_ok=True)
        save(folder / 'result.json', result)
    print('MERGE OPTIONS PASS: exact production bytes, 20 checks', flush=True)


def audit():
    proof = validate_build()
    assert not (OUT / 'verified.json').exists(), 'Do not overwrite acceptance evidence'
    review = load('merged_stair_audit', MOD / 'build/stair-review/analyze.py').audit(OUT / 'capture')
    residual = load('merged_stair_residual', MOD / 'build/stair-review/residual_audit.py').audit(OUT / 'capture')
    save(OUT / 'pixels.json', review)
    save(OUT / 'residual.json', residual)
    assert len(review['pairs']) == 8
    assert all(p['changed_outside_cut_air'] == 0 and p['changed_material_pixels'] == 0 and p['old_black_air'] > 0 and p['new_black_air'] == 0 for p in review['pairs'])
    assert all(p['cut_air_overlay_mismatch'] == 0 for p in review['pairs'] if p['variant'] == 'off')
    assert all(p['target_positive']['pixels'] == p['target_positive']['final_output_unchanged_from_old'] and p['common_air_final_output_changes'] == 0 and p['common_air_delta_changes'] == 0 for p in residual['pairs'])
    assert max(p['cut_air_overlay_max_delta'] for p in review['pairs']) <= 1
    checks = read(OUT / 'checks-result.json')
    capture = read(OUT / 'capture/evidence/result.json')
    options = read(OUT / 'options/result.json')
    assert len(checks) == 6 and sum(c['passed'] for c in checks) == 183 and all(c['exit'] == 0 for c in checks)
    assert len(capture['checks']) == 96 and all(c['ok'] for c in capture['checks']) and not capture.get('error')
    assert read(OUT / 'capture/last-run.json')['exit'] == 0
    assert options['status'] == 'PASS' and options['sha256'] == proof['candidate_swf']
    assert len(options['runs']) == 2 and all(r['exit'] == 0 and r['checks'] == 10 for r in options['runs'])
    save(OUT / 'verified.json', {'status': 'PASS_WITH_RETAINED_REFERENCE_DIAGNOSTICS',
         'sha256': proof['candidate_swf'], 'version': VERSION, 'functional_checks': 299,
         'pixels': {key: review[key] for key in ['passed', 'failed', 'isolation_passed', 'isolation_failed']},
         'limitation': 'Constant-bright reference residuals retained; no new performance or full-network claim',
         'evidence': {name: sha(OUT / name) for name in ['build-complete.json', 'merge-inputs.json',
                      'checks-result.json', 'capture/evidence/result.json', 'capture/last-run.json',
                      'options/result.json', 'pixels.json', 'residual.json']}})
    print('MERGE PIXELS: black bars removed, material/outside unchanged; strict diagnostics retained:', review['passed'], review['failed'], review['isolation_passed'], review['isolation_failed'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'build', 'checks', 'capture', 'options', 'audit'])
    action = parser.parse_args().action
    {'prepare': prepare, 'build': build, 'checks': run_checks, 'capture': run_capture, 'options': run_options, 'audit': audit}[action]()
