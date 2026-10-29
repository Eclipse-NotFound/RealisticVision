"""Archive D56 without duplicate sources or private saves; stage owned changes."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/effect-mask-origin-output';DEST=MOD/'knowledge/experiments/effect-mask-origin-d56-20261029'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().startswith('8d2711d') and not git('diff','--cached','--name-only').strip()
receipt=json.loads((OUT/'deployment/receipt.json').read_text());assert receipt['result']=='PASS'
assert sha(MOD/'release/RealisticVisionMod.swf')==receipt['new'] and sha(MOD/receipt['backup'])==receipt['old']
assert sha(MOD/'release/config.txt')==receipt['configUnchanged']
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registry
assert not [r for r in Registry().status() if r['owner'].startswith('RealisticVision / D56') and r['state'] in ('waiting','running','needs-check')]
runs=sorted(p for p in OUT.iterdir() if p.is_dir() and p.name.rsplit('-',1)[-1].isdigit());assert len(runs)==29
summary={};native_windows=intervals=shots=0
for folder in runs:
 assert not (folder/'test.xml').exists(),folder
 if (folder/'build.json').exists():
  for rel,h in json.loads((folder/'build.json').read_text()).get('files',{}).items():assert sha(folder/rel)==h,(folder.name,rel)
 row={}
 for name in ('validation.json','analysis.json','environment.json'):
  if (folder/name).exists():row[name]=json.loads((folder/name).read_text())
 if (folder/'evidence/result.json').exists():
  data=json.loads((folder/'evidence/result.json').read_text())
  row.update(replay=data.get('replay'),exactFrames=data.get('exactFrames'),optimizedCalls=data.get('optimizedCalls'),error=data.get('error'))
  cs=data.get('cases',[]);row['nativeWindows']=[{k:c.get(k) for k in ('variant','mode','attacks','maxParticles','maxProjectiles','retained')} for c in cs]
  if folder.name in ['grid-native-24','grid-native-reverse-25','current-final-native-27']:
   native_windows+=len(cs);intervals+=sum(sum('nextInterval' in f for f in c['frames']) for c in cs);shots+=sum(c['attacks'] for c in cs)
 summary[folder.name]=row
assert (native_windows,intervals,shots)==(30,5370,3874),(native_windows,intervals,shots)
assert summary['current-final-pixels-26']['validation.json']['checks']==721
assert summary['production-smoke-29']['validation.json']['passed']
assert sha(OUT/'grid-native-24/candidate.swf')==sha(OUT/'grid-native-reverse-25/candidate.swf')
spec=importlib.util.spec_from_file_location('d56_final_runtime',MOD/'build/motion-performance/run.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
assert not (OUT/'development-syntax-final.swf').exists()
r.runner.compile(MOD/'src/RealisticVisionMod.as',OUT/'development-syntax-final.swf',[MOD/'src'],stubs=True)
save(OUT/'integration-final.json',{'mainSource':sha(MOD/'src/RealisticVisionMod.as'),'syntax':sha(OUT/'development-syntax-final.swf'),'productionContainsAuthority':False,'note':'Development source retains authorityView writes and clarifies two-sample margin; production bytes unchanged.'})
assert not DEST.exists();DEST.mkdir(parents=True);pins={};objects={};mapping={}
def copy(p,rel):
 q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[rel]=sha(q);return rel
for p in (OUT/'production/src').rglob('*.as'):
 rel=copy(p,p.relative_to(OUT).as_posix());objects[(sha(p),p.suffix)]=rel
copy(OUT/'production/RealisticVisionMod.swf','production/RealisticVisionMod.swf')
objects[(sha(OUT/'production/RealisticVisionMod.swf'),'.swf')]='production/RealisticVisionMod.swf'
for folder in runs+[OUT/'candidates',OUT/'production',OUT/'deployment']:
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  if any(x in rel.parts for x in ('storage','Local Store','player-seed','player-evidence')):continue
  original=p.relative_to(OUT).as_posix()
  keep=p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt')
  keep=keep or 'evidence' in rel.parts and p.suffix in ('.json','.png')
  keep=keep or folder.name=='production' and p.suffix in ('.json','.log','.txt')
  binary=p.name in ('rv.swf','candidate.swf','EffectLoadChecks.swf','CombatRenderProbeMod.swf','ProductionSmokeMod.swf','CandidateOptionsProbe.swf','RealisticVisionMod.swf')
  if binary and p.name=='RealisticVisionMod.swf' and folder.name.startswith('production-smoke-'):
   assert sha(p)==receipt['new']
  elif binary and 'mods' in rel.parts and p.name not in ('CombatRenderProbeMod.swf','ProductionSmokeMod.swf'):binary=False
  if not (keep or binary):continue
  if p.suffix in ('.as','.swf'):
   key=(sha(p),p.suffix);stored=objects.get(key)
   if stored is None:stored=copy(p,'objects/'+key[0]+p.suffix);objects[key]=stored
   mapping[original]={'sha256':key[0],'stored':stored}
  elif original not in pins:copy(p,original)
for name in ['verified.json','integration.json','integration-final.json']:
 copy(OUT/name,name)
for name in ['first','restored']:
 copy(OUT/'production'/name/'storage/RVision.log','production/'+name+'/RVision.log')
save(DEST/'object-map.json',mapping);pins['object-map.json']=sha(DEST/'object-map.json')
save(DEST/'finish.json',{'adopted':'grid_current','deployed':True,'fullyResolved':False,'version':receipt['version'],'installedSha256':receipt['new'],'allOwnedRunsFinished':True,'nativeWindows':native_windows,'completeIntervals':intervals,'shots':shots,'runs':summary,'boundary':'Only current optimized; no full-FPS equivalence claim. Private-desktop tests and random native layouts.'});pins['finish.json']=sha(DEST/'finish.json')
(DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
save(DEST/'archive.json',pins)
header='> 2026-10-29 **D56 v0.33.11已部署**：current保留原采样格并缩小特效遮罩，真实内容变化时刷新目标关联；classic保持旧路径。发现旧跨帧关联残留，最终721项对照通过，准确包36设置及原生240帧/119次开火通过。三组current配对平均约低7%–12%，最终48.51→42.55ms、P95 65→56ms，仍有102ms长帧。准确包BD64B5BB…CE4A9AD（46441B），生产源build/effect-mask-origin-output/production/src，不含authority；旧638E已备份。29轮自有实例/登记全部结束，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-29-effect-mask-origin.md)。'
journal='''## 2026-10-29 — D56缩小current特效遮罩并部署v0.33.11

- 排除局部坐标、全暗位图隐藏、预绘后裁切和屏幕外跳过；无收益/有差异的分支均未合入。两帧反例发现重新绑定mask即可消除旧目标缓存残留，刷新版721项对照新鲜原算法通过。
- 在刷新关联基础上保留原5px采样格，将current单个特效的遮罩图形缩到目标外两个样本；父层非1:1整数/对象有滤镜则保留完整图形。classic共享刷新首轮略回退，最终限制为current，classic保留旧行为。
- 最终26检查721项（含父/目标alpha与模式/柔化/缩放）通过；current对新鲜完整原算法、classic对连续D44，像素严格相等。23同批回放19.63→17.17ms；24/25/27原生30窗5370间隔3874次开火，current平均分别约低7.4%、8.0%、12.3%。最终48.51→42.55ms/P95 65→56，长帧仍未全解，未达关闭RV流畅度。
- 准确包36设置通过；28探针退出重复回调#3200，修正探针后29以同一生产字节完成240帧/119次射击和9559次带遮罩粒子采样、静音、实际加载与干净退出。生产六类无authority/存根；正式08:16:28原子替换并回读BD64B5BB…CE4A9AD，旧638E备份保留，配置和其他模组未改。
- 生产源独立冻结，开发主源码合并时保留authorityView写入且单独编译；四项外部WIP未提交。29轮均退出。报告与去重证据见knowledge/experiments/2026-10-29-effect-mask-origin.md及effect-mask-origin-d56-20261029；不能安装其它历史候选。
- 纠正D55方法边界：轮换同一个原生对象会解除mask，保留数据缓存但不保留连续AIR关联状态；关联连续性需独立对象对照。下一步围绕密集敌人实际战斗的剩余长帧，不重复已淘汰候选或再询问已确定现场。

'''
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode();live=(MOD/'state'/name).read_text()
 def transform(s):
  if name=='journal.md':return journal+s
  pos=s.index('\n\n')+2;s=s[:pos]+header+'\n\n'+s[pos:]
  old='- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。最新D55建立同批原生特效回放；stable-v4未获整帧收益，identity/identity-blit新增像素反例且后者复测收益不稳定，均未采用/部署；详见顶部D55报告。'
  new='- 当前安装D56 v0.33.11-effect-clip，BD64B5BB…CE4A9AD；准确生产源build/effect-mask-origin-output/production/src，排除authority。current轻机枪持续扫射已改善，classic保持旧路径；仍有长帧和相对关闭RV的差距，详见顶部D56报告。'
  assert old in s;s=s.replace(old,new)
  marker='## 4. 正在进行与停点\n\n';assert marker in s
  return s.replace(marker,marker+'- D56已部署并结束本轮测试；用户保存重启生效。下一步测密集敌人原生战斗的剩余长帧，不把本轮7%–12%外推所有场景。生产私有源与开发authority线分开，四项外部WIP保留；下方是历史停点。\n\n',1)
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
for p in (MOD/'build/effect-mask-origin').glob('*.py'):ast.parse(p.read_text())
git('add','--','.gitignore','src/RealisticVisionMod.as','build/effect-mask-origin','knowledge/experiments/2026-10-29-effect-mask-origin.md');git('add','-f','--',str(DEST))
for name in ['MEMORY.md','journal.md']:
 oid=git('hash-object','-w','--stdin',input=(owned/name).read_bytes()).decode().strip();git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()};assert actual==expected,actual
prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in pins)+'\n').encode());offset=0
for rel in pins:
 end=raw.index(b'\n',offset);h=raw[offset:end].split();assert h[1]==b'blob';size=int(h[2]);data=raw[end+1:end+size+1];offset=end+size+2;assert hashlib.sha256(data).hexdigest()==pins[rel],rel
assert offset==len(raw);git('diff','--cached','--check')
print(json.dumps({'deployed':True,'files':len(pins),'sourceAndBinaryAliases':len(mapping),'uniqueObjects':len(objects),'bytes':sum((DEST/p).stat().st_size for p in pins),'runs':29,'outsideWipPreserved':True}))
