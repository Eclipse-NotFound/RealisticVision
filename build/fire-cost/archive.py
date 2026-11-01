"""Freeze completed evidence only; omit runtime assets, SWFs and player seeds."""
from pathlib import Path
import gzip, hashlib, json

MOD = Path(__file__).resolve().parents[2]
OUT = MOD/'build/fire-cost-output'
DEST = MOD/'knowledge/experiments/fire-cost-20261101'
assert not DEST.exists(), 'Never overwrite a frozen archive'
assert (OUT/'08-witness-moving/last-run.json').is_file(), 'Wait for the native comparison'
DEST.mkdir(parents=True)
(DEST/'.gitattributes').write_bytes(b'* -text whitespace=cr-at-eol\n')
origins = {}

def retain(source, target, compress=False):
    raw = source.read_bytes()
    target = str(target) + ('.gz' if compress else '')
    path = DEST/target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw,mtime=0) if compress else raw)
    assert (gzip.decompress(path.read_bytes()) if compress else path.read_bytes()) == raw
    origins[target] = dict(source=source.relative_to(MOD).as_posix(),
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), compressed=compress)

for name in ['inputs.json','optional-lad.json','generated-runner.py','final-checks.json']:
    if (OUT/name).is_file(): retain(OUT/name,name)
for root in [OUT/'baseline', *sorted((OUT/'candidates').iterdir())]:
    for source in sorted((root/'src').rglob('*.as')):
        retain(source,source.relative_to(OUT).as_posix(),True)
    if (root/'sources.json').exists():retain(root/'sources.json',(root/'sources.json').relative_to(OUT).as_posix())
for run in sorted(p for p in OUT.iterdir() if p.is_dir() and p.name[:2].isdigit()):
    for source in sorted(run.iterdir()):
        xml = source.name.endswith('.compiler.xml') or source.name in ('test.xml','application.xml')
        if source.is_file() and (source.suffix in ('.json','.log','.as') or xml):
            retain(source,source.relative_to(OUT).as_posix(),source.suffix in ('.as','.log') or source.stat().st_size>100000)
    for source_root in ['src','rv-src','candidate-src','vector-src']:
        for source in sorted((run/source_root).rglob('*.as')):
            retain(source,source.relative_to(OUT).as_posix(),True)
    evidence = run/'evidence'
    result = evidence/'result.json'
    if result.is_file():retain(result,result.relative_to(OUT).as_posix(),True)
    else:
        partial = sorted(evidence.glob('result-*.json'),key=lambda p:int(p.stem.split('-')[1]))
        if partial:retain(partial[-1],partial[-1].relative_to(OUT).as_posix(),True)
    for source in sorted(evidence.glob('*.png')):retain(source,source.relative_to(OUT).as_posix())
(DEST/'origins.json').write_text(json.dumps(origins,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
(DEST/'README.md').write_text('''# 开火成本调查证据

完整说明见 [调查报告](../2026-11-01-fire-cost.md)。
`origins.json` 记录每份原件的SHA256、大小及是否压缩；gzip固定mtime=0，解压逐字节回验。
这里只保留本模组生成的代码、诊断日志、数值结果和失败图片，未打包游戏资源/存档。
原始运行仍留 `build/fire-cost-output`；源码生成器留 `build/fire-cost`。
`before/after/environment` 只说明端点资源状态；不能代替全程独占或稳定负载证明。
失败运行不删除；完成情况与不采用的原因以报告逐项说明为准。
''','utf8',newline='\n')
print(json.dumps(dict(files=len(origins),bytes=sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file()))))
