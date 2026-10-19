"""Summarize completed, uninstrumented D31 paired timings and window evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics

OUT = Path(__file__).resolve().parents[1] / 'frame-performance-output'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def stats(values):
    assert values and all(isinstance(v, (int, float)) and v >= 0 for v in values)
    ordered = sorted(values)
    return {'n': len(values), 'mean': statistics.mean(values),
            'median': statistics.median(values),
            'p95': ordered[int(.95 * (len(values) - 1))], 'max': max(values)}


def analyze(name):
    folder = OUT / name
    result_path = folder / 'evidence/result.json'
    result, build, last = (read(p) for p in
                          [result_path, folder / 'build-inputs.json', folder / 'last-run.json'])
    assert last['exit'] == 0 and not result.get('error'), 'Run did not complete successfully'
    assert not any(build[k] for k in ['profile', 'verify', 'live']), 'Not a paired timing run'
    assert len(result['cases']) == 4 and result['checks'] == [], 'Incomplete or pixel-verified run'
    rows = []
    for case in result['cases']:
        updates, draws = case['updates'], case['draws']
        assert len(updates) == len(draws) == 2
        assert all(len(series) == 120 for series in updates + draws)
        total = [[a + b for a, b in zip(updates[i], draws[i])] for i in range(2)]
        row = {'spec': case['spec']}
        for metric, values in [('updates', updates), ('draws', draws), ('total', total)]:
            row[metric] = [stats(v) for v in values]
            row[metric + '_mean_reduction_percent'] = 100 * (
                1 - row[metric][1]['mean'] / row[metric][0]['mean'])
        row['total_paired_absolute_difference_ms'] = stats([abs(b - a) for a, b in zip(*total)])
        row['candidate_faster_pairs'] = sum(b < a for a, b in zip(*total))
        row['equal_pairs'] = sum(b == a for a, b in zip(*total))
        # Both orderings remain visible instead of attributing timer noise to code.
        row['total_by_order'] = {
            'baseline_first': [stats(v[0::2]) for v in total],
            'candidate_first': [stats(v[1::2]) for v in total],
        }
        rows.append(row)
    environment = read(folder / 'environment.json') if (folder / 'environment.json').exists() else []
    other = {(p['pid'], p['name']) for sample in environment for p in sample['processes']
             if p['pid'] != last['pid']}
    output = {
        'run': name, 'scene': result['scene'],
        'data_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest(),
        'source_manifest': build, 'last_run': last,
        'units': 'milliseconds; RV update and offscreen fog draw, not complete game frame time',
        'p95_rule': 'sorted(values)[floor(.95 * (n - 1))]',
        'total_rule': 'each matching update and draw sample added before computing statistics',
        'rows': rows,
        'environment': {
            'samples': len(environment), 'sampling_interval_seconds': 10,
            'minimum_available_gib': min((x['available_bytes'] / 1024**3 for x in environment), default=None),
            'maximum_available_gib': max((x['available_bytes'] / 1024**3 for x in environment), default=None),
            'other_air_java': [{'pid': pid, 'name': proc} for pid, proc in sorted(other)],
            'limitation': 'AIR/Java observations cannot exclude short-lived or other process contention',
        },
    }
    dest = OUT / ('analysis-final.json' if name == 'final-large-trial' else name + '-analysis.json')
    dest.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(dest)
    for row in rows:
        print(json.dumps({k: row[k] for k in ['spec', 'updates', 'total', 'total_mean_reduction_percent']}, ensure_ascii=False))
    print(json.dumps(output['environment'], ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='final-large-trial')
    analyze(parser.parse_args().name)
