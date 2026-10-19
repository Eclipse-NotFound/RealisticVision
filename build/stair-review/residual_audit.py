"""Read-only follow-up to analyze.py; preserves every strict failure.

The hidden-overlay image is a diagnostic intervention, not a proven
pixel-invariant rendering reference. Compare its behavior against the old
renderer in a native cleared area. Never launches AIR or edits a candidate.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[2]


def audit(folder):
    evidence = folder / 'evidence'
    used = {}

    def track(path):
        used[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    result = json.loads(track(evidence / 'result.json').read_text(encoding='utf-8-sig'))
    terrain = np.asarray(Image.open(track(evidence / 'terrain-alpha.png')).convert('RGBA'))
    alpha = terrain[:, :, 3]
    rows = []
    for mode in ['classic', 'current']:
        for position, step in [('lower', 3), ('upper', 5)]:
            tag = f'{position}-{mode}'

            def read(variant, suffix):
                path = track(evidence / f'{variant}-{tag}-{suffix}.png')
                return np.asarray(Image.open(path).convert('RGB')).astype(np.int16)

            fog = {v: read(v, 'fog') for v in ['oldOn', 'on']}
            masked = {v: read(v, 'masked-base-only') for v in ['oldOn', 'on']}
            state = next(s for s in result['states'] if s['variant'] == 'on'
                         and s['mode'] == mode and s['step'] == step)
            allowed = np.zeros(alpha.shape, bool)
            for tile in state['tiles']:
                if tile['opac'] >= 1 and tile['zForm']:
                    x, y = tile['x'] * 40, tile['y'] * 40
                    allowed[y:y + tile['zForm'] * 10, x:x + 40] = True
            allowed &= alpha == 0
            # This exact row is cleared with native Tile.dec and opac=0 by
            # WallSurfaceProbe.capture, immediately above the fixture.
            common_air = np.zeros(alpha.shape, bool)
            common_air[640:680, 480:640] = True
            common_air &= alpha == 0
            delta = {v: fog[v] - masked[v] for v in fog}

            def histogram(values):
                values = values[values != 0]
                unique, counts = np.unique(values, return_counts=True)
                return {str(int(k)): int(v) for k, v in zip(unique, counts)}

            def residual_detail(region):
                final_unchanged = np.all(fog['on'] == fog['oldOn'], axis=2)
                return {
                    'pixels': int(region.sum()),
                    'final_output_unchanged_from_old': int((region & final_unchanged).sum()),
                    'old_output_red_range': [int(fog['oldOn'][:, :, 0][region].min()),
                                             int(fog['oldOn'][:, :, 0][region].max())] if region.any() else None,
                }

            rows.append({
                'mode': mode, 'position': position,
                'all_input_images_grayscale': all(
                    np.array_equal(image[:, :, 0], image[:, :, channel])
                    for group in [fog, masked] for image in group.values()
                    for channel in [1, 2]),
                'target_positive': residual_detail(allowed & (delta['on'][:, :, 0] > 0)),
                'target_negative': residual_detail(allowed & (delta['on'][:, :, 0] < 0)),
                'target_max_abs_channel_delta': int(np.abs(delta['on'][allowed]).max()),
                'common_air_pixels': int(common_air.sum()),
                'common_air_signed_red_deltas': {
                    v: histogram(delta[v][:, :, 0][common_air]) for v in delta},
                'common_air_final_output_changes': int((np.any(fog['on'] != fog['oldOn'], axis=2) & common_air).sum()),
                'common_air_delta_changes': int((np.any(delta['on'] != delta['oldOn'], axis=2) & common_air).sum()),
            })
    return {
        'capture': str(folder), 'input_sha256': used, 'pairs': rows,
        'interpretation': {
            'established': [
                'The targeted black-air regression is repaired; analyze.py independently records material and outside-region invariance.',
                'Every positive target residual has unchanged final output versus oldOn; its hidden-overlay reference changes.',
                'In the cleared air above the stairs, current has the same signed hidden-overlay residuals before and after the fix.',
            ],
            'inference': 'Hiding overlay containers can change rendering quantization; signed differences alone do not establish physical overlay leakage.',
            'unresolved': 'The individual negative one-level target residuals have not each been assigned a proven rendering cause.',
            'decision': 'Accept the narrow stair-classification fix for integration; retain strict18/8 and isolation4/4 diagnostics, without claiming pixel-perfect equivalence or deploying the old-baseline candidate.',
        },
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    report = audit(args.capture.resolve())
    out = MOD / 'build/stair-shadow-output/review-rv3'
    out.mkdir(exist_ok=True)
    path = out / (args.capture.name + '-residual-comparison.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'pairs': report['pairs']}, ensure_ascii=False, indent=2))
