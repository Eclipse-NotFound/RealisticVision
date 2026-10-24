"""Archive D48 only, after prior registered tests, keeping raw bytes and WIP."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys,time
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/shared-mask-output';GAME=MOD.parents[1]
DEST=MOD/'knowledge/experiments/shared-mask-d48-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('8d8e2ff')
expected={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f','../../pfe.swf':'a796827173af7d6fab9885fb66ecc62182ab5335918a30c7cce4c44914a238b7'}
assert all(sha(MOD/p)==digest for p,digest in expected.items()),'Installation changed'
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registry,Registration
active=[r for r in Registry().status() if r['state'] in ('waiting','running','needs-check')]
assert not [r for r in active if 'RealisticVision' in r['owner']],'Owned tests still active'
older={r['id'] for r in active};deadline=time.monotonic()+900
if older:print('Wait for previously registered tests before IO-intensive archive: '+','.join(sorted(older)),flush=True)
while older:
 rows=Registry().status();older={r['id'] for r in rows if r['id'] in older and r['state'] in ('waiting','running','needs-check')}
 if not older:break
 assert time.monotonic()<deadline,'Archive deferred; prior tests still active'
 time.sleep(5)
with Registration(owner='RealisticVision / D48 证据收尾',purpose='原始证据与索引校验；非额外游戏测试',run_dir=OUT,evidence=DEST/'archive.json',wait=900) as rec:
 assert not DEST.exists();DEST.mkdir(parents=True)
 paths=[OUT/'asset-deduplication-01.json',OUT/'pixel-failures.json']
 names=['shared-pixels-01','shared-native-01','shared-combat-01','reference-pixels-01','reference-v2-pixels-01','shared-v2-pixels-01','shared-v2-native-01','shared-v2-combat-01']
 for name in names:
  folder=OUT/name
  assert json.loads((folder/'last-run.json').read_text())['exit']==(1 if name.startswith('reference') else 0)
  assert not (folder/'test.xml').exists(),name
  for p in folder.rglob('*'):
   if not p.is_file():continue
   rel=p.relative_to(folder)
   if p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix in ('.json','.png'):paths.append(p)
 for name in ['candidates','group-steps']:
  paths.extend(p for p in (OUT/name).rglob('*') if p.is_file() and p.suffix in ('.as','.json','.log'))
 pins={}
 for p in paths:
  rel=p.relative_to(OUT);target=DEST/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);pins[rel.as_posix()]=sha(target)
 attributes=DEST/'.gitattributes';attributes.write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(attributes)
 receipt={'formalUnchanged':expected,'activeOwnedGameTests':0,'archivedFiles':len(pins),'adopted':False,'sharedChecks':1249,'sharedV2Checks':1249,'referenceVariantsPixelFailureCountEach':24,'cleanCombatPairedIntervals':2148,'firstCombatDiagnosticOnly':True}
 (DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');pins['finish.json']=sha(DEST/'finish.json')
 (DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 head='> 2026-10-25 **D48结束，正式仍D44**：共享4×4格模糊场的shared/shared-v2各通过361+888项，但直接引用大位图的reference两版均在帧164出现24像素差异，淘汰。首轮计时受自有去重IO干扰，仅诊断；shared-v2干净12窗current68.08→70.00ms、classic71.89→71.51ms且最大408ms，无稳定收益，不采用。所有本轮AIR/队列结束。下一步检查ensureFog/RVWallSurface每帧重复设置相同显示属性是否造成大雾层重建，不叠加本轮候选。详见[报告](../knowledge/experiments/2026-10-25-shared-mask.md)，证据shared-mask-d48-20261025。'
 stop='- D48已结束，无RV游戏实例/排队；所有共享场候选不采用，准确正式源仍D44。新方向：ensureFog重复写scrollRect/colorTransform/blendMode和RVWallSurface重复挂air/base mask及setChildIndex；只是源码发现，性能原因未证实。下一轮从D44独立验证同值设置跳过，保留第三方状态变化恢复和实际画面。D48原图/错误/受干扰计时均保留，不重跑旧目录。下方为历史停点。'
 journal='''## 2026-10-25 — D48共享模糊场无稳定收益，保留像素反例

- 从准确D44派生shared局部复制与reference共享填充；classic只用原查询已补算区域，不扩大显示查询。shared的361图像/阳性17478次及888原生检查通过。
- 加强动态root/子滤镜与缓存偏好后，reference在帧164出现24像素差异；缓存键分离后的reference-v2同样失败。shared-v2保持局部绘图，361/阳性16596次与888原生检查通过；不放宽像素容差，未证实内部舍入机制。
- 首轮12窗因自有已结束素材去重IO重叠（484261674B/3.23秒）标仅诊断，失败边界如实保留。随后干净shared-v2十二窗current68.08→70.00ms、classic71.89→71.51ms，尾部不利，全部候选不采用/不部署。没有把局部计算或P95单项当整体流畅度。
- 正式RV638E…3710/config5136…A3C7F/rootA796…238B7不变，主源码与四项外部WIP保留。所有AIR/描述符/登记已结束，无出站消息；收到CS时段请求后不追加游戏，证据归档等待既有测试。
- 下一步从D44检查ensureFog及RVWallSurface重复同值显示设置，验证是否造成额外合成，不叠加失败共享场。报告knowledge/experiments/2026-10-25-shared-mask.md，证据shared-mask-d48-20261025，工具build/shared-mask；整体目标未完成。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
 for name in ['MEMORY.md','journal.md']:
  base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
  def transform(s):
   if name=='journal.md':return journal+s
   at=s.index('> 2026-10-25 **D47');s=s[:at]+head+'\n\n'+s[at:]
   at=s.index('## 4. 正在进行与停点');pos=s.index('\n\n',at)+2;return s[:pos]+stop+'\n\n'+s[pos:]
  (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
 for p in (MOD/'build/shared-mask').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 assert not git('diff','--cached','--name-only').strip()
 subprocess.run(['git','add','--','.gitignore','build/shared-mask','knowledge/experiments/2026-10-25-shared-mask.md'],cwd=MOD,check=True)
 subprocess.run(['git','add','-f','--',str(DEST)],cwd=MOD,check=True)
 for name in ['MEMORY.md','journal.md']:
  digest=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=MOD,input=(owned/name).read_bytes()).decode().strip()
  subprocess.run(['git','update-index','--cacheinfo','100644,'+digest+',state/'+name],cwd=MOD,check=True)
 for rel,digest in pins.items():assert hashlib.sha256(git('show',':'+(DEST/rel).relative_to(MOD).as_posix())).hexdigest()==digest,rel
 left=git('diff','--numstat').decode()
 assert sorted(line.split() for line in left.splitlines())==sorted([['24','0','src/RVAuthorityView.as'],['2','0','state/MEMORY.md'],['4','0','state/journal.md'],['15','0','tests/authority/AuthorityViewChecks.as']]),left
 subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
 print(json.dumps(receipt,ensure_ascii=False),flush=True);rec.outcome='passed';rec.note='仅原始证据和索引字节校验完成，非新增游戏验证；所有候选不采用'
