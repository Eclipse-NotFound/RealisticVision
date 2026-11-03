#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the v0.34.9-fov-correct / v0.35.0-aperture-grade candidates.

Frozen lineage: the **deployed** v0.34.8-clip-pad production source
(build/boundary-opt2-20261104/production/src).  Nothing here writes release/ or
the user's config; deployment is a separate, explicit step.

Usage:
  python build.py --baseline                     # recompile the untouched v0.34.8 source
  python build.py --variant v0349                # build build/fov-fix-20261104/v0349
  python build.py --variant v0350
"""

from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
GAME = MOD.parents[1]
TOOLS = GAME / 'mods/Sandevistan/build/tools'
JAVA = Path('D:/Program Files/Adobe Animate 2024/jre/bin/java.exe')
SDK = TOOLS / 'flexsdk'
AIR = TOOLS / 'airsdk/frameworks/libs/air/airglobal.swc'
STUBS = MOD / 'build/GameStubs.swc'
OUT = MOD / 'build/fov-fix-20261104'
BASE_SRC = MOD / 'build/boundary-opt2-20261104/production/src'

# Deployed v0.34.8-clip-pad fingerprint, re-read at run time (never hard-asserted
# against a stale value: the plan's rule is "whoever changed it must say so").
DEPLOYED_SWF = MOD / 'release/RealisticVisionMod.swf'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compile_dir(src, out_swf):
    out_swf = Path(out_swf)
    out_swf.parent.mkdir(parents=True, exist_ok=True)
    config = out_swf.with_suffix('.compiler.xml')
    externs = [AIR, STUBS]
    config.write_text(
        '<flex-config><compiler><external-library-path>'
        + ''.join('<path-element>%s</path-element>' % p for p in externs)
        + '</external-library-path><source-path>'
        + ''.join('<path-element>%s</path-element>' % p for p in [src])
        + '</source-path><debug>false</debug><optimize>true</optimize>'
        + '<omit-trace-statements>false</omit-trace-statements><theme/></compiler>'
        + '<target-player>32.0</target-player><swf-version>32</swf-version>'
        + '<use-network>false</use-network>'
        + '<static-link-runtime-shared-libraries>true</static-link-runtime-shared-libraries>'
        + '</flex-config>', encoding='utf-8')
    result = subprocess.run(
        [str(JAVA), '-Dfile.encoding=UTF-8', '-jar', str(SDK / 'lib/mxmlc.jar'),
         '+flexlib=' + str(SDK / 'frameworks'), '-load-config=' + str(config),
         '-output=' + str(out_swf), str(Path(src) / 'RealisticVisionMod.as')],
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    out_swf.with_suffix('.compile.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise RuntimeError('compile failed: %s' % out_swf)
    print('Built %-52s %6d B  %s' % (out_swf.relative_to(MOD), out_swf.stat().st_size,
                                     sha(out_swf)[:16]))


def fingerprint_sources(src):
    return {p.relative_to(src).as_posix(): sha(p) for p in sorted(Path(src).rglob('*.as'))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', action='store_true')
    ap.add_argument('--variant')
    args = ap.parse_args()

    if not (SDK / 'lib/mxmlc.jar').exists():
        raise SystemExit('mxmlc missing at %s' % (SDK / 'lib/mxmlc.jar'))
    if not AIR.exists():
        raise SystemExit('airglobal missing at %s' % AIR)
    if not STUBS.exists():
        raise SystemExit('GameStubs.swc missing at %s' % STUBS)

    print('deployed v0.34.8 swf  %s  %d B' % (sha(DEPLOYED_SWF)[:16], DEPLOYED_SWF.stat().st_size))

    if args.baseline:
        dest = OUT / 'baseline'
        if not (dest / 'src').exists():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(BASE_SRC, dest / 'src')
        compile_dir(dest / 'src', dest / 'baseline.swf')
        (dest / 'build.json').write_text(json.dumps({
            'variant': 'v0.34.8-clip-pad (recompiled from frozen source)',
            'swf': sha(dest / 'baseline.swf'),
            'bytes': (dest / 'baseline.swf').stat().st_size,
            'source': fingerprint_sources(dest / 'src'),
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return

    if not args.variant:
        raise SystemExit('give --baseline or --variant')

    dest = OUT / args.variant
    src = dest / 'src'
    if not src.exists():
        raise SystemExit('missing candidate source tree: %s (copy it from baseline/src first)' % src)
    compile_dir(src, dest / 'RealisticVisionMod.swf')
    build = dest / 'build.json'
    data = json.loads(build.read_text('utf-8')) if build.exists() else {}
    data.update({
        'variant': args.variant,
        'swf': sha(dest / 'RealisticVisionMod.swf'),
        'bytes': (dest / 'RealisticVisionMod.swf').stat().st_size,
        'source': fingerprint_sources(src),
        'baseSource': fingerprint_sources(BASE_SRC),
    })
    build.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('wrote', build.relative_to(MOD))


if __name__ == '__main__':
    main()
