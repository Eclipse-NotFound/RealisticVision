"""Freeze D51 functional evidence and preserve the user's timing pause."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/ray-clearance-output'
DEST=MOD/'knowledge/experiments/ray-clearance-d51-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('5ba0ee2')
assert not git('diff','--cached','--name-only').strip()
expected={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710',
 'release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f',
 '../../pfe.swf':'a796827173af7d6fab9885fb66ecc62182ab5335918a30c7cce4c44914a238b7'}
assert all(sha(MOD/p)==h for p,h in expected.items())
for name,code in [('rays-01',1),('rays-02',0),('native-large-01',0)]:
 assert json.loads((OUT/name/'last-run.json').read_text())['exit']==code
 assert not(OUT/name/'test.xml').exists()
 build=json.loads((OUT/name/'build.json').read_text());assert all(sha(OUT/name/p)==h for p,h in build['files'].items())
sourcepins=json.loads((OUT/'inputs-v2.json').read_text())['candidate']
assert all(sha(OUT/'candidate-v2/src'/p)==h for p,h in sourcepins.items())
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registry,Registration
assert not [r for r in Registry().status() if 'RealisticVision' in r['owner'] and r['state'] in ('waiting','running','needs-check')]
with Registration(owner='RealisticVision / D51 保存证据',purpose='非游戏；功能证据归档，性能仍暂缓',run_dir=OUT,evidence=DEST/'archive.json',wait=900) as rec:
 assert not DEST.exists();DEST.mkdir(parents=True);pins={}
 for top in ['candidate','candidate-v2','rays-01','rays-02','native-large-01']:
  folder=OUT/top
  for p in folder.rglob('*'):
   if not p.is_file():continue
   rel=p.relative_to(folder)
   if p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix in ('.json','.png'):
    q=DEST/p.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
 for name in ['inputs.json','inputs-v2.json','PERFORMANCE-PAUSED.json']:
  shutil.copyfile(OUT/name,DEST/name);pins[name]=sha(DEST/name)
 (DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
 receipt={'formalUnchanged':expected,'adopted':False,'status':'pending-performance','rayChecks':134827,'rayComparisons':21129,
  'nativeChecks':64,'nativeFastHits':368918,'performanceEvidence':False,'activeOwnedGameTests':0,'userChoice':'保留试玩，只做代码和画面检查'}
 (DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');pins['finish.json']=sha(DEST/'finish.json')
 (DEST/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
 head='> 2026-10-25 **D51功能完成，性能仍暂缓，正式仍D44**：独立候选candidate-v2用原遮光快照证明空矩形后省略逐格射线，墙/门/水/异常值回退；21129条射线及134827项检查、192×75原生64次严格画面全部通过。原生回放快速路径368918次、循环33896533→29561650，只是步骤计数，未证明帧率收益。用户保留试玩的选择有效，无独立计时/部署。自有AIR均退出。详见[报告](../knowledge/experiments/2026-10-25-ray-clearance.md)，证据ray-clearance-d51-20261025。'
 stop='- D51与D50均功能通过、性能待定，未合并或部署。用户保留试玩、只做代码和画面检查的选择继续有效；两个输出目录均有PERFORMANCE-PAUSED.json。D51准确候选build/ray-clearance-output/candidate-v2/src，首稿未测试即因行宽改变风险淘汰。rays-01为夹具中断不对称失败，rays-02及native-large-01已结束且严格通过。没有可采用的D51时间数据；恢复独立计时后先核对环境/组合，再用无测试计数的生产源对D44做完整战斗复验。目标未完成。下方为历史停点。'
 journal='''## 2026-10-25 — D51空矩形射线候选功能通过，性能待定

- 从准确D44独立派生，按原遮光快照计数正值/非有限值，仅零矩形跳过原逐格遍历；不改刷新、视野或动画。首稿同长度不同行宽有静态边框风险，未测试即换candidate-v2，保留源和说明。
- rays-02五尺寸六类地图21129射线结果相同，134827项通过。rays-01只对候选施加中断，导致一项不对称比较失败；修正夹具后通过，候选源码不变。含门/水/墙/异常值、非批处理、坐标不匹配、中断和换房。
- 原生192×75、8组、96合成单位64次原始场/逻辑/整雾严格相同，实际加载与源指纹通过。快速路径368918次，旧循环33896533→29561650；这是功能计数，不能当性能收益。试玩保留，无独立性能数据。
- D50仍独立待判定，两候选不合并。用户性能暂停保持；自有AIR和描述符退出，无出站消息。正式638E/config5136/rootA796不变，4项authority外部WIP保留。报告knowledge/experiments/2026-10-25-ray-clearance.md；整体战斗流畅度目标未完成。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
 for name in ['MEMORY.md','journal.md']:
  base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
  def transform(s):
   if name=='journal.md':return journal+s
   pos=s.index('> 2026-10-25 **D50');s=s[:pos]+head+'\n\n'+s[pos:]
   old='D50候选功能通过，独立性能按用户选择暂缓；正式安装未改，详见顶部报告。'
   assert s.count(old)==1;s=s.replace(old,'D50/D51独立候选功能通过，完整性能按用户选择暂缓；正式安装未改，详见顶部报告。')
   pos=s.index('\n\n',s.index('## 4. 正在进行与停点'))+2;return s[:pos]+stop+'\n\n'+s[pos:]
  (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
 for p in (MOD/'build/ray-clearance').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 subprocess.run(['git','add','--','.gitignore','build/ray-clearance','knowledge/experiments/2026-10-25-ray-clearance.md'],cwd=MOD,check=True)
 subprocess.run(['git','add','-f','--',str(DEST)],cwd=MOD,check=True)
 for name in ['MEMORY.md','journal.md']:
  digest=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=MOD,input=(owned/name).read_bytes()).decode().strip()
  subprocess.run(['git','update-index','--cacheinfo','100644,'+digest+',state/'+name],cwd=MOD,check=True)
 for rel,h in pins.items():assert hashlib.sha256(git('show',':'+(DEST/rel).relative_to(MOD).as_posix())).hexdigest()==h,rel
 assert sorted(line.split() for line in git('diff','--numstat').decode().splitlines())==sorted([['24','0','src/RVAuthorityView.as'],['2','0','state/MEMORY.md'],['4','0','state/journal.md'],['15','0','tests/authority/AuthorityViewChecks.as']])
 subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
 print(json.dumps(receipt,ensure_ascii=False),flush=True);rec.outcome='passed';rec.note='功能证据及自身状态已保存；性能暂停，未部署'
