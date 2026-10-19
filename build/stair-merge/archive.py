"""Archive immutable merge checks and deployment receipts without rerunning AIR."""
from pathlib import Path
import merge

OUT = merge.OUT
DEST = merge.MOD / 'knowledge/experiments/stair-performance-v0323-20261019'
STATE = merge.MOD / 'state/deployment-v0323'


def copy(source, target):
    data = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == data, 'Do not overwrite evidence: ' + str(target)
    else:
        with target.open('xb') as stream:
            stream.write(data)
    assert merge.sha(source) == merge.sha(target)


def main():
    proof = merge.validate_build()
    receipt = merge.read(OUT / 'deployment/receipt.json')
    assert receipt['result'] == 'PASS' and receipt['new_sha256'] == proof['candidate_swf']
    assert receipt['test_process_closed'] and receipt['test_descriptor_removed']
    assert merge.sha(merge.MOD / receipt['backup']) == merge.OLD
    for name in ['merge-inputs.json', 'build-complete.json', 'verified.json', 'classes.json',
                 'checks-result.json', 'pixels.json', 'residual.json']:
        copy(OUT / name, DEST / name)
    for folder in ['checks', 'regression', 'options']:
        for path in (OUT / folder).iterdir():
            if path.suffix in ['.txt', '.json']:
                copy(path, DEST / folder / path.name)
    for path in (OUT / 'capture/evidence').iterdir():
        if path.suffix in ['.png', '.json']:
            copy(path, DEST / 'capture' / path.name)
    for name in ['last-run.json', 'game.log']:
        copy(OUT / 'capture' / name, DEST / 'capture' / ('game.txt' if name == 'game.log' else name))
    for path in OUT.glob('*-environment-*.json'):
        copy(path, DEST / 'environment' / path.name)
    for path in (OUT / 'deployment').iterdir():
        if path.suffix in ['.json', '.txt']:
            copy(path, STATE / path.name)
    print('MERGE EVIDENCE ARCHIVED: ' + str(DEST), flush=True)


if __name__ == '__main__':
    main()
