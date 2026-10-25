"""Frozen native pixel checks alongside retained play windows; never timing evidence."""
from pathlib import Path
import json, os, re, shutil, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import perf as d

r = d.r
OUT = d.OUT
MEDIA = {'sound.swf', 'sound_unit.swf', 'sound_weapon.swf', 'sprite.swf',
         'sprite1.swf', 'texture.swf', 'texture1.swf'}


def main():
    source = OUT / 'all-native-01'
    folder = OUT / 'all-native-functional-02'
    assert not folder.exists()
    frozen = json.loads((source / 'build.json').read_text(encoding='utf-8'))
    assert all(r.sha(source / p) == h for p, h in frozen['files'].items())
    with r.Registration(owner='RealisticVision / D50 仅画面验证',
                        purpose='用户保留试玩；冻结字节画面对照，不作性能判断',
                        run_dir=folder, evidence=folder / 'validation.json', wait=900) as rec:
        folder.mkdir(parents=True)
        (folder / 'evidence').mkdir()
        # Only immutable media share storage. Configuration, code and descriptors
        # remain independent copies. The interrupted attempt remains untouched.
        for relative in frozen['files']:
            src, dst = source / relative, folder / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            if relative in MEDIA:
                os.link(src, dst)
            else:
                shutil.copy2(src, dst)
        for name in ['build.json', 'selection.json', 'selection.log']:
            shutil.copy2(source / name, folder / name)
        r.save(folder / 'provenance.json', {
            'frozen_from': str(source), 'source_build_sha256': r.sha(source / 'build.json'),
            'purpose': 'functional pixels only; user explicitly retains player-1/player-2',
            'performance_evidence': False,
        })
        env = r.environment()
        r.save(folder / 'environment.json', env)
        assert env['available_bytes'] > 5 * 1024**3, env
        # Concurrency is intentional only for this non-timing check. The normal
        # performance runner's exclusive environment gate stays unchanged.
        code, log = r.air(folder, 'pfe.swf', rec, 600)
        count = len(re.findall(r'^PASS exact native frame ', log, re.M))
        selected = set(json.loads((folder / 'selection.json').read_text())['configuration']['selected'])
        requested = set(re.findall(r'ModLoader\[requested_(\w+)\]', log))
        loaded = set(re.findall(r'ModLoader\[ok_(\w+)\]', log))
        pins = all(r.sha(folder / p) == h for p, h in frozen['files'].items())
        passed = (code == 0 and count == 64 and 'FRAME COMPLETE' in log
                  and 'PRIVATE READY ' in log and 'FAIL ' not in log
                  and 'ModLoader[err_' not in log and selected == requested == loaded and pins)
        r.save(folder / 'validation.json', {
            'exit': code, 'checks': count, 'pass': passed, 'pins_match': pins,
            'selected': sorted(selected), 'performance_evidence': False,
            'retained_other_processes': env['processes'],
        })
        print(log[-1600:], flush=True)
        assert passed
        rec.outcome = 'passed'
        rec.note = '64项原生严格画面对照；试玩保留，本轮时间数据禁作性能证据'


if __name__ == '__main__':
    main()
