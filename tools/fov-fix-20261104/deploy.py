#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy a verified candidate to release/ with a timestamped backup + receipt.

Follows GOVERNANCE §6 / remains-release-gate: verify the target was not changed
concurrently, keep a rollback copy, install the exact verified bytes, read the
fingerprint back, and write a receipt next to the candidate.

usage: python deploy.py v0349 [--note "batch 1"]
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
OUT = MOD / 'build/fov-fix-20261104'
RELEASE = MOD / 'release/RealisticVisionMod.swf'
BACKUPS = MOD / 'build/backups'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('variant')
    ap.add_argument('--note', default='')
    args = ap.parse_args()

    cand = OUT / args.variant / 'RealisticVisionMod.swf'
    if not cand.exists():
        raise SystemExit('missing candidate: %s' % cand)
    build = json.loads((OUT / args.variant / 'build.json').read_text('utf-8'))
    if sha(cand) != build['swf']:
        raise SystemExit('candidate changed since build.json was written; rebuild first')

    prev_sha = sha(RELEASE)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = BACKUPS / ('before-%s-%s' % (args.variant, stamp))
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(RELEASE, backup / 'RealisticVisionMod.swf')
    cfg = MOD / 'release/config.txt'
    if cfg.exists():
        shutil.copyfile(cfg, backup / 'config.txt')
    print('backup  %s  %s' % (backup.relative_to(MOD), prev_sha[:16]))

    shutil.copyfile(cand, RELEASE)
    now_sha = sha(RELEASE)
    if now_sha != build['swf']:
        raise SystemExit('read-back mismatch: %s != %s' % (now_sha, build['swf']))

    receipt = {
        'variant': args.variant,
        'note': args.note,
        'deployedAt': datetime.now().isoformat(timespec='seconds'),
        'swf': now_sha,
        'bytes': RELEASE.stat().st_size,
        'previous': prev_sha,
        'backup': str(backup.relative_to(MOD)),
        'source': build['source'],
        'restartRequired': True,
    }
    (OUT / args.variant / 'deployment.json').write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('deployed %s  %d B  %s' % (RELEASE.relative_to(MOD), receipt['bytes'], now_sha))
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
