"""Freeze completed experimental evidence, excluding game assets and saves."""
from pathlib import Path
import gzip
import hashlib
import json

MOD = Path(__file__).resolve().parents[2]
OUT = MOD / 'build/local-mask-regions-output'
DEST = MOD / 'knowledge/experiments/local-mask-regions-20261101'
assert not DEST.exists(), 'Do not overwrite frozen evidence'
runs = sorted(p for p in OUT.iterdir() if p.is_dir() and p.name[:2].isdigit())
assert (OUT / '09-three-way-short/last-run.json').exists(), 'Wait for the final owned test'
DEST.mkdir(parents=True)
(DEST / '.gitattributes').write_bytes(b'* -text whitespace=cr-at-eol\n')
origins = {}


def retain(source, target, compress=False):
    raw = source.read_bytes()
    path = DEST / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw, mtime=0) if compress else raw)
    assert (gzip.decompress(path.read_bytes()) if compress else path.read_bytes()) == raw
    origins[target] = {'source': source.relative_to(MOD).as_posix(),
                       'sha256': hashlib.sha256(raw).hexdigest(),
                       'bytes': len(raw), 'compressed': compress}


for name in ['inputs.json', 'generated-runner.py', 'resource-check.json', 'resource-check-v2.json', 'final-checks.json']:
    if (OUT / name).is_file():
        retain(OUT / name, name)
for variant in ['baseline', 'candidate', 'alpha-candidate']:
    for source in sorted((OUT / variant / 'src').rglob('*.as')):
        retain(source, variant + '/src/' + source.relative_to(OUT / variant / 'src').as_posix() + '.gz', True)
    if (OUT / variant / 'sources.json').is_file():
        retain(OUT / variant / 'sources.json', variant + '/sources.json')
for folder in runs:
    for source in sorted(folder.iterdir()):
        keep_xml = source.name.endswith('.compiler.xml') or source.name in ('test.xml', 'application.xml')
        if source.is_file() and (source.suffix in ('.json', '.log', '.as') or keep_xml):
            compress = source.suffix in ('.as', '.log')
            retain(source, folder.name + '/' + source.name + ('.gz' if compress else ''), compress)
    # Only generated mod/test sources; never descend into runtime, mods or store.
    for source_root in ['src', 'rv-src', 'candidate-src', 'vector-src']:
        for source in sorted((folder / source_root).rglob('*.as')):
            retain(source, folder.name + '/' + source.relative_to(folder).as_posix() + '.gz', True)
    evidence = folder / 'evidence'
    final = evidence / 'result.json'
    if final.exists():
        retain(final, folder.name + '/evidence/result.json.gz', True)
    else:
        snapshots = sorted(evidence.glob('result-*.json'), key=lambda p: int(p.stem.split('-')[1]))
        # Keep the last completed immutable snapshot and the six-window snapshot
        # actually inspected mid-run; do not imply that either is a final result.
        selected = {snapshots[-1]} if snapshots else set()
        selected.update(evidence.glob('result-6-*.json'))
        for source in sorted(selected):
            retain(source, folder.name + '/evidence/' + source.name + '.gz', True)
    for source in sorted(evidence.glob('*.png')):
        retain(source, folder.name + '/evidence/' + source.name)

(DEST / 'origins.json').write_text(json.dumps(origins, ensure_ascii=False, indent=2) + '\n', 'utf8', newline='\n')
(DEST / 'README.md').write_text('''# 精确区域遮罩与墙面 alpha 候选证据

完整结论见上级 2026-11-01-local-mask-regions.md。
01、02、05 是测试夹具失败；03、04、06、07 是通过的功能检查。
08 超时，只有部分窗口，不能作为部署性能证据。09 是相同字节的短窗反序复测。
resource-check.json 的逐进程 CPU 比率分母有误，仅整机 CPU 读数有效；
resource-check-v2.json 修正为每个 PID 自己的实际时间间隔，不能据此倒推 08 中途的负载来源。

AS 源、大 JSON 和日志保留原始字节后 gzip 压缩；origins.json 记原件指纹，
manifest.json 核对归档文件。没有收录游戏素材、玩家存档或测试应用存储。
场景 PNG 供现场核对，不能替代功能脚本的严格像素与输入对照。
''', 'utf8', newline='\n')
manifest = {p.relative_to(DEST).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8', newline='\n')
print('Archived', len(manifest), 'files;', sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()), 'bytes')
