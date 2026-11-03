#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated hidden-window load test for a candidate RealisticVisionMod.swf.

Copies the host entry SWFs/XML + Rooms into build/fov-fix-20261104/smoke-<name>/,
installs the candidate as mods/RealisticVision/release/RealisticVisionMod.swf with a
**test-only** config (enabled=1, unique storage id), then runs adl64 in a unique
application id so the mod's RVision.log lands in a private Local Store that this
script reads and reports.

Never touches the installed release/, the user's Local Store, saves or config.

usage: python smoke.py v0349 [--timeout 90]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
GAME = MOD.parents[1]
OUT = MOD / 'build/fov-fix-20261104'
HOST_ENTRY = 'pfe.swf'


def copy_game(folder):
    folder.mkdir(parents=True, exist_ok=True)
    pat = re.compile(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf'
                     r'|(text_.*|lang|launcher_text)\.xml')
    for p in GAME.iterdir():
        if p.is_file() and pat.fullmatch(p.name):
            shutil.copyfile(p, folder / p.name)
    shutil.copytree(GAME / 'Rooms', folder / 'Rooms', dirs_exist_ok=True)
    shutil.copyfile(GAME / 'application.xml', folder / 'application.xml')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('variant')
    ap.add_argument('--timeout', type=int, default=120)
    args = ap.parse_args()

    cand = OUT / args.variant / 'RealisticVisionMod.swf'
    if not cand.exists():
        raise SystemExit('missing candidate swf: %s' % cand)
    folder = OUT / ('smoke-' + args.variant)
    if folder.exists():
        shutil.rmtree(folder)
    print('staging isolated root', folder.relative_to(MOD))
    copy_game(folder)

    release = folder / 'mods/RealisticVision/release'
    release.mkdir(parents=True)
    shutil.copyfile(cand, release / 'RealisticVisionMod.swf')
    cfg_src = MOD / 'release/config.txt'
    cfg = cfg_src.read_text('utf-8')
    assert 'enabled=1' in cfg, 'template must already be enabled for the smoke'
    (release / 'config.txt').write_text(cfg, 'utf-8')

    catalog = folder / 'mods/ModLoader'
    catalog.mkdir(parents=True, exist_ok=True)
    supported = (GAME / 'mods/ModLoader/supported-mods.txt').read_text('utf-8-sig')
    (catalog / 'supported-mods.txt').write_text(supported, 'utf-8')

    sel = subprocess.run([str(GAME / 'mods/ModLoader/RemainsModLauncher.exe'),
                          '--root', str(folder), '--only', 'RealisticVisionMod',
                          '--no-ui', '--report', str(folder / 'selection.json')],
                         capture_output=True, text=True)
    print('launcher exit', sel.returncode)
    if sel.returncode:
        print(sel.stdout, sel.stderr)
        return 2

    app_id = 'rv-fovfix-smoke-' + uuid.uuid4().hex
    desc = folder / 'test.xml'
    desc.write_text(
        '<application xmlns="http://ns.adobe.com/air/application/30.0"><id>' + app_id +
        '</id><versionNumber>1.0</versionNumber><filename>RVFovFix</filename>'
        '<initialWindow><content>' + HOST_ENTRY + '</content><visible>false</visible>'
        '<width>1280</width><height>720</height><renderMode>direct</renderMode>'
        '</initialWindow></application>', encoding='utf-8')
    log = folder / 'air-output.log'
    # The DSH sandbox denies %APPDATA% to this process tree, and AIR resolves
    # File.applicationStorageDirectory through %APPDATA%: redirect it to a
    # workspace-local store so the mod's RVision.log lands inside the workspace.
    store = folder / 'appdata'
    store.mkdir(exist_ok=True)
    env = dict(os.environ)
    env['APPDATA'] = str(store)
    env['LOCALAPPDATA'] = str(store)
    try:
        with log.open('w', encoding='utf-8') as fh:
            proc = subprocess.Popen([str(GAME / 'adl64.exe'), '-runtime',
                                     str(GAME / 'runtimes/air/win64'), str(desc), '-nodebug'],
                                    cwd=folder, stdout=fh, stderr=subprocess.STDOUT,
                                    env=env,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                code = proc.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                code = 124
    finally:
        desc.unlink(missing_ok=True)

    rvlog = store / app_id / 'Local Store' / 'RVision.log'
    if not rvlog.exists():
        rvlog = Path(os.environ['APPDATA']) / app_id / 'Local Store' / 'RVision.log'
    text = rvlog.read_text('utf-8', errors='replace') if rvlog.exists() else ''
    air = log.read_text('utf-8', errors='replace')
    print('adl exit', code, '| RVision.log', 'present' if rvlog.exists() else 'MISSING')
    print('--- air tail ---')
    print(air[-1500:])
    print('--- RVision.log ---')
    print(text[-1500:])

    checks = {
        'init_ok': 'init ok v0.34.9-fov-correct' in text,
        'tick': 'tick ' in text,
        'no_error': 'onFrame error' not in text and 'ERROR' not in text,
        'modloader_ok': 'ModLoader[ok_RealisticVisionMod]' in air,
    }
    report = {'variant': args.variant, 'appId': app_id, 'adlExit': code,
              'swf': json.loads((OUT / args.variant / 'build.json').read_text('utf-8'))['swf'],
              'checks': checks, 'passed': all(checks.values())}
    (folder / 'smoke.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                                       encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
