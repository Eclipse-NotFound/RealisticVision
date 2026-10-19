"""Independent D30 pixel audit. Reads a completed AIR capture; never runs AIR.

All allowed change regions come from native tile metadata and foreground alpha,
not the candidate's clipping implementation. Evidence stays in the owned review
directory. This does not establish the user's exact save/camera equivalence.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(folder):
    evidence = folder / 'evidence'
    result = json.loads((evidence / 'result.json').read_text(encoding='utf-8-sig'))
    terrain = np.asarray(Image.open(evidence / 'terrain-alpha.png').convert('RGBA'))
    height, width = terrain.shape[:2]
    report = {'capture': str(folder), 'fixture': result['fixture'],
              'result_sha256': digest(evidence / 'result.json'),
              'method': 'native tile heights plus terrain alpha; compare full rendered images',
              'checks': [], 'isolation_checks': [], 'pairs': []}
    checks = report['checks']
    checks.append({'name': 'AIR capture has no failing assertions',
                   'ok': bool(result['checks']) and all(c['ok'] for c in result['checks'])})
    for new, old in [('off', 'oldOff'), ('on', 'oldOn')]:
        for mode in ['classic', 'current']:
            for position, step in [('lower', 3), ('upper', 5)]:
                state = next(s for s in result['states'] if s['variant'] == new
                             and s['mode'] == mode and s['step'] == step)
                allowed = np.zeros((height, width), dtype=bool)
                top_distance = np.zeros((height, width), dtype=np.int16)
                for tile in state['tiles']:
                    if tile['opac'] < 1 or not tile['zForm']:
                        continue
                    x, y = tile['x'] * 40, tile['y'] * 40
                    allowed[y:y + tile['zForm'] * 10, x:x + 40] = True
                    for row in range(tile['zForm'] * 10):
                        top_distance[y + row, x:x + 40] = tile['zForm'] * 10 - row
                allowed &= terrain[:, :, 3] == 0
                tag = f'{position}-{mode}'
                paths = [evidence / f'{variant}-{tag}-fog.png' for variant in [old, new]]
                before, after = [np.asarray(Image.open(p).convert('RGB')).astype(np.int16) for p in paths]
                reference_path = evidence / f'{new}-{tag}-without-helper.png'
                reference = np.asarray(Image.open(reference_path).convert('RGB')).astype(np.int16)
                changed = np.any(before != after, axis=2)
                air_delta = np.max(np.abs(after - reference), axis=2)
                residual = (air_delta != 0) & allowed
                ry, rx = np.where(residual)
                material_distances = []
                for py, px in zip(ry, rx):
                    left, top = max(0, px - 50), max(0, py - 50)
                    sy, sx = np.where(terrain[top:py + 51, left:px + 51, 3] > 0)
                    if len(sx):
                        material_distances.append(float(np.sqrt(((sx + left - px) ** 2 +
                                                               (sy + top - py) ** 2).min())))
                pair = {'variant': new, 'mode': mode, 'position': position,
                        'allowed_air_pixels': int(allowed.sum()),
                        'changed_pixels': int(changed.sum()),
                        'changed_outside_cut_air': int((changed & ~allowed).sum()),
                        'changed_material_pixels': int((changed & (terrain[:, :, 3] > 0)).sum()),
                        'cut_air_mismatch_to_original_fog': int(((air_delta != 0) & allowed).sum()),
                        'max_air_delta_to_original_fog': int(air_delta[allowed].max()),
                        'signed_air_deltas': {str(int(v)): int(c) for v, c in zip(
                            *np.unique((after[:, :, 0] - reference[:, :, 0])[residual], return_counts=True))},
                        'residual_bbox': [int(rx.min()), int(ry.min()), int(rx.max()), int(ry.max())] if len(rx) else None,
                        'residual_distance_to_physical_top': [int(top_distance[residual].min()),
                                                             int(top_distance[residual].max())] if len(rx) else None,
                        'residual_distance_to_material': [min(material_distances), max(material_distances)] if material_distances else None,
                        'old_black_air': int((np.all(before == 0, axis=2) & allowed).sum()),
                        'new_black_air': int((np.all(after == 0, axis=2) & allowed).sum()),
                        'input_sha256': {p.name: digest(p) for p in paths + [reference_path]}}
                masked_path = evidence / f'{new}-{tag}-masked-base-only.png'
                if masked_path.exists():
                    masked = np.asarray(Image.open(masked_path).convert('RGB')).astype(np.int16)
                    overlay_delta = np.max(np.abs(after - masked), axis=2)
                    pair['cut_air_overlay_mismatch'] = int(((overlay_delta != 0) & allowed).sum())
                    pair['cut_air_overlay_max_delta'] = int(overlay_delta[allowed].max())
                    pair['input_sha256'][masked_path.name] = digest(masked_path)
                    report['isolation_checks'].append({
                        'name': f'{new} {tag} no overlay contribution in cut-away air',
                        'ok': pair['cut_air_overlay_mismatch'] == 0})
                report['pairs'].append(pair)
                for key in ['changed_outside_cut_air', 'changed_material_pixels',
                            'cut_air_mismatch_to_original_fog']:
                    checks.append({'name': f'{new} {tag} {key}', 'ok': pair[key] == 0})
    checks.append({'name': 'at least one captured regression is repaired',
                   'ok': any(p['changed_pixels'] > 0 for p in report['pairs'])})
    report['passed'] = sum(c['ok'] for c in checks)
    report['failed'] = len(checks) - report['passed']
    report['isolation_passed'] = sum(c['ok'] for c in report['isolation_checks'])
    report['isolation_failed'] = len(report['isolation_checks']) - report['isolation_passed']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('capture', type=Path)
    parser.add_argument('--detail', action='store_true', help='Write a separate detailed result, preserving the first strict result')
    args = parser.parse_args()
    report = audit(args.capture.resolve())
    out = MOD / 'build/stair-shadow-output/review-rv3'
    out.mkdir(exist_ok=True)
    path = out / (args.capture.name + ('-detailed' if args.detail else '') + '.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'passed': report['passed'],
                      'failed': report['failed'],
                      'isolation_passed': report['isolation_passed'],
                      'isolation_failed': report['isolation_failed'],
                      'pairs': [{k: v for k, v in p.items() if k != 'input_sha256'}
                                for p in report['pairs']]}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(report['failed']))
