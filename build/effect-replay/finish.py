"""Archive completed D55 evidence and stage only owned changes; no deployment."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/effect-replay-output'
DEST=MOD/'knowledge/experiments/effect-replay-d55-20261028'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,input=None):return subprocess.run(['git',*args],cwd=MOD,input=input,capture_output=True,check=True).stdout
assert git('rev-parse','HEAD').decode().startswith('42f8343')
assert not git('diff','--cached','--name-only').strip()
formal={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f'}
assert all(sha(MOD/p)==h for p,h in formal.items())
assert not git('diff','--','src/RealisticVisionMod.as').strip()
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import Registry
assert not [r for r in Registry().status() if r['owner'].startswith('RealisticVision / D55') and r['state'] in ('waiting','running','needs-check')]
runs=sorted(p for p in OUT.iterdir() if p.is_dir() and p.name.rsplit('-',1)[-1].isdigit())
assert len(runs)==21
summary={}
for folder in runs:
 assert not (folder/'test.xml').exists(),folder
 if (folder/'build.json').exists():
  for rel,h in json.loads((folder/'build.json').read_text()).get('files',{}).items():assert sha(folder/rel)==h,(folder.name,rel)
 row={}
 for name in ('validation.json','analysis.json','environment.json'):
  if (folder/name).exists():row[name]=json.loads((folder/name).read_text())
 if (folder/'evidence/result.json').exists():
  data=json.loads((folder/'evidence/result.json').read_text());cs=data.get('cases',[])
  row['native']={'windows':len(cs),'intervals':sum(sum('nextInterval' in f for f in c['frames']) for c in cs),'shots':sum(c['attacks'] for c in cs),'windowVisible':data.get('windowVisible'),'scene':data.get('scene')}
  row['replay']=data.get('replay');row['exactFrames']=data.get('exactFrames');row['optimizedCalls']=data.get('optimizedCalls');row['pixelFailure']=data.get('pixelFailure');row['error']=data.get('error')
  row['replayWindows']=[{k:c.get(k) for k in ('variant','maskCount','optimizedCalls','stableSavings','drawCalls')} for c in data.get('replayCases',[])]
 summary[folder.name]=row
assert summary['stable-v4-pixels-09']['validation.json']['checks']==1081
assert summary['stable-v4-replay-pixels-10']['exactFrames']==60
assert summary['stable-v4-native-timing-12']['native']['shots']==783
assert summary['stable-v4-native-timing-12']['analysis.json']['environment']['performanceEligible']
assert summary['identity-replay-counterexample-15']['pixelFailure']
assert not summary['identity-blit-pixels-21']['validation.json']['passed']
assert summary['identity-blit-pixels-16']['exactFrames']==60
assert sha(OUT/'identity-blit-native-timing-18/candidate.swf')==sha(OUT/'identity-blit-native-reverse-19/candidate.swf')
assert sum(summary[n]['native']['shots'] for n in ['stable-v4-native-timing-12','identity-blit-native-timing-18','identity-blit-native-reverse-19'])==3161
assert (OUT/'identity-replay-counterexample-15/evidence/failure-baseline.png').exists()
assert (OUT/'identity-replay-counterexample-15/evidence/failure-candidate.png').exists()
assert not DEST.exists();DEST.mkdir(parents=True);pins={}
for folder in runs+[OUT/'candidates']:
 for p in folder.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(folder)
  if any(v in rel.parts for v in ('storage','Local Store','player-seed','player-evidence')):continue
  keep=p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt')
  keep=keep or 'evidence' in rel.parts and p.suffix in ('.json','.png')
  keep=keep or p.name in ('rv.swf','baseline.swf','candidate.swf','EffectLoadChecks.swf','CombatRenderProbeMod.swf')
  if keep:
   q=DEST/p.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
original=MOD/'build/frame-attribution-output/candidates/identity'
for rel,h in json.loads((original/'manifest.json').read_text()).items():
 p=original/'src'/rel;assert sha(p)==h
 q=DEST/'candidates/identity-d47/src'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
receipt={'formalUnchanged':formal,'adopted':False,'deployed':False,'resolved':False,'allOwnedRunsFinished':True,'runs':summary,'rootHostSha256':sha(GAME/'pfe.swf'),'boundary':'Replay uses original visuals and deterministic trajectories, not recorded gameplay. Private-desktop visible is not foreground human verification. Native scenes regenerate random layouts.'}
(DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');pins['finish.json']=sha(DEST/'finish.json')
(DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
(DEST/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
header='> 2026-10-29 **D55同批特效回放完成，未采用/未部署，正式仍D44**：stable-v4通过1081项+原生60帧，重画2703→829，但完整扫射45.49→46.04ms未改善。identity-blit原生60帧通过、首轮current约快3.7%，反向current持平/classic变慢，扩展位图检查又在f121失败。原D47 identity也有原生47像素反例。21轮全部结束，完整扫射共24窗4296间隔/3161次开火；主src/release不改，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-28-effect-replay.md)，工具build/effect-replay。'
journal='''## 2026-10-29 — D55相同原生特效批次回放与缓存复用尝试（28日晚起）

- 固定原生lmg当前存活Part/Bullet，保留素材/层次/矩阵和动画、用确定性位置曲线回放；原生寿命冻结断言和输入指纹有效。是受控绘制回放，不是玩家弹道录制或完整FPS。
- stable初版全亮提前返回#1009；v2/v3在动态边界f121有像素差异。v4只在同视野代次和柔化设置内复用，1081项及原生60帧/3298阳性通过。
- 11同批计时重画2703→829，均值17.84→17.15ms但P95/最大更差；12原生14项组合6窗，D44 45.49/57/112ms，候选46.04/62/133ms，均值/P95/最大均未改善，不采用。环境合格仍不等于随机场景完全一致。
- D47全亮精确省略旧候选在新lmg回放f2出差异；后续反例记录和图片见归档。14因app资源URL截图写入失败，纠正为隔离目录nativePath后15保存；不是自动审批拒绝。没有因此放宽像素要求。
- 仅单个位图的identity-blit原生60帧/283阳性通过，18首轮current44.64→42.98ms；19复用相同字节反转次序，current47.10→47.04持平、classic49.49→51.25变慢。20夹具滤镜导入错误未启动AIR；21修正后f121出现动态边界像素反例，淘汰，不安装。
- 正式638E/config5136、主源码及玩家存档不改；本轮所有实例/登记已结束。接续先读保存的原生像素反例，查清全亮省略的绘制差异再考虑更小遮罩表示；不要重跑历史生成器或安装任何本轮测试SWF。

'''
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for name in ['MEMORY.md','journal.md']:
 base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
 def transform(s):
  if name=='journal.md':return journal+s
  pos=s.index('\n\n')+2;s=s[:pos]+header+'\n\n'+s[pos:]
  old='- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。最新D54已匹配正式入口、存档轻机枪和最大化窗口，确认持续特效遮罩额外成本，但候选均未形成可靠修复，未采用/部署；详见顶部D54报告。'
  new='- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。最新D55建立同批原生特效回放；stable-v4未获整帧收益，identity/identity-blit新增像素反例且后者复测收益不稳定，均未采用/部署；详见顶部D55报告。'
  assert old in s;s=s.replace(old,new)
  marker='## 4. 正在进行与停点\n\n';assert marker in s
  return s.replace(marker,marker+'- D55：本轮实验已结束，持续扫射问题仍未解决。保存的identity原生像素反例是后续检查入口；stable-v4整帧未获益，不要打包或部署。真实入口/武器/最大化条件已明确，无需再问；下方历史停点保留。\n\n',1)
 (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
for p in (MOD/'build/effect-replay').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
git('add','--','.gitignore','build/effect-replay','knowledge/experiments/2026-10-28-effect-replay.md')
git('add','-f','--',str(DEST))
for name in ['MEMORY.md','journal.md']:
 oid=git('hash-object','-w','--stdin',input=(owned/name).read_bytes()).decode().strip();git('update-index','--cacheinfo','100644,'+oid+',state/'+name)
expected={'src/RVAuthorityView.as':(24,0),'state/MEMORY.md':(2,0),'state/journal.md':(4,0),'tests/authority/AuthorityViewChecks.as':(15,0)}
actual={line.split('\t',2)[2]:tuple(map(int,line.split('\t')[:2])) for line in git('diff','--numstat').decode().splitlines()};assert actual==expected,actual
paths=list(pins);prefix=DEST.relative_to(MOD).as_posix()+'/'
raw=git('cat-file','--batch',input=('\n'.join(':'+prefix+p for p in paths)+'\n').encode());offset=0
for rel in paths:
 end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[1]==b'blob'
 size=int(header[2]);data=raw[end+1:end+1+size];offset=end+size+2;assert hashlib.sha256(data).hexdigest()==pins[rel],rel
assert offset==len(raw)
git('diff','--cached','--check')
print(json.dumps({'files':len(pins),'bytes':sum((DEST/p).stat().st_size for p in pins),'formalUnchanged':True,'resolved':False,'deployed':False,'runs':len(runs)},ensure_ascii=False))
