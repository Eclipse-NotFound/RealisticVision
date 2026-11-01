"""Freeze only owned evidence, never runtime assets or copied player data."""
from pathlib import Path
import gzip,hashlib,json
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shot-light-output';DEST=MOD/'knowledge/experiments/shot-light-20261101'
assert not DEST.exists(),'Never overwrite frozen evidence'
assert (OUT/'final-checks.json').is_file(),'Complete receipt before archiving'
assert (OUT/'09-geometry-timing/detailed-analysis.json').is_file()
assert (OUT/'10-direct-checks/validation.json').is_file()
assert (OUT/'14-projectile-circle-stress/validation.json').is_file()
DEST.mkdir(parents=True);(DEST/'.gitattributes').write_bytes(b'* -text whitespace=cr-at-eol\n')
origins={}
def retain(p):
 raw=p.read_bytes();compressed=p.suffix in ('.as','.py','.log') or len(raw)>100000
 rel=p.relative_to(OUT).as_posix()+('.gz' if compressed else '')
 target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(gzip.compress(raw,mtime=0) if compressed else raw)
 assert (gzip.decompress(target.read_bytes()) if compressed else target.read_bytes())==raw
 origins[rel]={'source':p.relative_to(MOD).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'compressed':compressed}
for name in ['inputs.json','stub-inputs.json','generated-runner.py','final-checks.json']:
 if (OUT/name).is_file():retain(OUT/name)
for name in ['baseline','lighting-baseline','candidate','raster-candidate','geometry-candidate','direct-candidate','direct-full-candidate','direct-circle-candidate']:
 for p in sorted((OUT/name/'src').rglob('*.as')):retain(p)
 if (OUT/name/'sources.json').is_file():retain(OUT/name/'sources.json')
for run in sorted(p for p in OUT.iterdir() if p.is_dir() and p.name[:2].isdigit()):
 for p in sorted(run.iterdir()):
  if p.is_file() and (p.suffix in ('.json','.log','.as') or p.name.endswith('.compiler.xml') or p.name in ('test.xml','application.xml')):retain(p)
 for sub in ['rv-src','lighting-src','lighting-build']:
  for p in sorted((run/sub).rglob('*')):
   if p.is_file() and (p.suffix in ('.as','.json','.log') or p.name.endswith('.compiler.xml')):retain(p)
 e=run/'evidence';result=e/'result.json'
 if result.is_file():retain(result)
 else:
  partial=sorted(e.glob('result-*.json'),key=lambda p:int(p.stem.split('-')[1]))
  if partial:retain(partial[-1])
 for p in sorted(e.glob('*.png')):retain(p)
(DEST/'origins.json').write_text(json.dumps(origins,ensure_ascii=False,indent=2)+'\n','utf8',newline='\n')
(DEST/'README.md').write_text('''# 开火照明调查证据

结论与限制见[报告](../2026-11-01-shot-light.md)。
`origins.json` 记录原件路径、SHA256、大小及压缩标志；gzip 解压后逐字节核对。
保留失败运行、候选及原生计时；未包含游戏资源、存档或配置种子。
原件仍位于 `build/shot-light-output`，复现工具位于 `build/shot-light`。
环境快照只说明端点；性能结论依赖同进程配对，不能把某轮绝对耗时套用到玩家前台。
''','utf8',newline='\n')
print(json.dumps({'files':len(origins),'bytes':sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file())}))
