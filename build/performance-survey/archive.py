"""Archive the completed census without game assets or player storage."""
from pathlib import Path
import gzip
import hashlib
import json

MOD = Path(__file__).resolve().parents[2]
OUT = MOD / 'build/performance-survey-output'
DEST = MOD / 'knowledge/experiments/performance-survey-20261101'
assert not DEST.exists(), 'Frozen evidence must not be overwritten'
assert json.loads((OUT / '02-census/last-run.json').read_text('utf8'))['exit'] == 0
assert json.loads((OUT / '01-census/last-run.json').read_text('utf8'))['exit'] == 1
DEST.mkdir(parents=True)
(DEST / '.gitattributes').write_bytes(b'* -text whitespace=cr-at-eol\n')
origins = {}


def retain(source, target, compressed=False):
    raw = source.read_bytes()
    path = DEST / target
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = gzip.compress(raw, mtime=0) if compressed else raw
    path.write_bytes(saved)
    assert (gzip.decompress(path.read_bytes()) if compressed else path.read_bytes()) == raw
    origins[target] = {'source': source.relative_to(MOD).as_posix(),
                       'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                       'compressed': compressed}


for name in ['inputs.json', 'history.json', 'generated-runner.py']:
    retain(OUT / name, name)
for source in sorted((OUT / 'baseline/src').rglob('*.as')):
    retain(source, 'baseline-src/' + source.relative_to(OUT / 'baseline/src').as_posix() + '.gz', True)
for run in ['01-census', '02-census']:
    folder = OUT / run
    for name in ['after.json', 'before.json', 'build.json', 'environment.json', 'last-run.json',
                 'resource-policy.json', 'running.json', 'selection.json', 'analysis.json', 'census.json']:
        if (folder / name).exists():
            retain(folder / name, run + '/' + name)
    for name in ['air-output.log', 'rv.compile.log', 'rv.compiler.xml', 'CombatRenderProbeMod.as']:
        if (folder / name).exists():
            retain(folder / name, run + '/' + name + '.gz', True)
    for source in sorted((folder / 'evidence').glob('*')):
        if source.name == 'result.json' or source.suffix == '.png':
            compressed = source.suffix == '.json'
            retain(source, run + '/evidence/' + source.name + ('.gz' if compressed else ''), compressed)
    for source in sorted((folder / 'rv-src').rglob('*.as')):
        rel = source.relative_to(folder / 'rv-src').as_posix()
        if run == '01-census':
            assert source.read_bytes() == (OUT / '02-census/rv-src' / rel).read_bytes()
        else:
            retain(source, run + '/rv-src/' + rel + '.gz', True)

(DEST / 'origins.json').write_text(json.dumps(origins, ensure_ascii=False, indent=2) + '\n', 'utf8', newline='\n')
(DEST / 'README.md').write_text('''# 性能普查证据

01因输出目录校验仍指向旧实验而失败；02修正探针保存路径，复用相同RV字节与源后完成。
两份探针、日志和退出记录均保留；02记录两模式各固定/受控移动，共720采样帧。
计时含诊断开销，不能据此声称某个优化带来提速；正式安装没有改变。

原始字节保留，不做换行归一化；较大的原始JSON、AS源和日志使用gzip压缩。
origins.json记录原路径、未压缩SHA256和大小；manifest.json核对归档文件。
01与02的rv-src已经逐文件比较相等，只收录02的一份。其余生成字节指纹在build.json。
未收录游戏资源、玩家存档或隔离应用存储。未保留中途结果快照，终态result包含四窗完整数据。
场景PNG仅供现场核对，不是候选逐像素等价验收。
''', 'utf8', newline='\n')
manifest = {p.relative_to(DEST).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(DEST.rglob('*')) if p.is_file()}
(DEST / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8', newline='\n')
print('Archived', len(manifest), 'files;', sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()), 'bytes')
