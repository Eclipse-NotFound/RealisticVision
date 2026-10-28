"""One-shot D53 evidence archival; preserve unrelated authority changes."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1];OUT=MOD/'build/solo-fire-output'
DEST=MOD/'knowledge/experiments/solo-fire-d53-20261028'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('804b659')
assert not git('diff','--cached','--name-only').strip()
formal={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710','release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f'}
assert all(sha(MOD/p)==h for p,h in formal.items())
runs=['full-profile-03','full-split-05','early-dark-full-06','full-bursts-07','full-bursts-reverse-08']
windows=frames=shots=0
for name in runs:
 f=OUT/name;assert json.loads((f/'last-run.json').read_text())['exit']==0 and not(f/'test.xml').exists()
 assert not json.loads((f/'environment.json').read_text())['performanceEligible']
 for rel,h in json.loads((f/'build.json').read_text())['files'].items():assert sha(f/rel)==h,(name,rel)
 data=json.loads((f/'evidence/result.json').read_text());windows+=len(data['cases'])
 for c in data['cases']:
  if 'idle' not in c['variant']:assert c['attacks']>10 and c['maxProjectiles']>0
  frames+=sum('nextInterval' in v for v in c['frames']);shots+=c['attacks']
assert (windows,frames,shots)==(32,7168,3060)
assert json.loads((OUT/'early-dark-pixels-01/validation.json').read_text())=={'passed':True,'exit':0,'checks':361}
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'));from test_registry import Registration,Registry
assert not [r for r in Registry().status() if r['owner'].startswith('RealisticVision / D53') and r['state'] in ('waiting','running','needs-check')]
with Registration(owner='RealisticVision / D53 保存证据',purpose='归档，未部署；等待确认实际游玩入口',run_dir=OUT,evidence=DEST/'archive.json',wait=900) as rec:
 assert not DEST.exists();DEST.mkdir(parents=True);pins={}
 names=runs+['full-profile-01','full-profile-02','full-split-04','early-dark-pixels-01','candidates']
 for name in names:
  folder=OUT/name
  if not folder.exists():continue
  for p in folder.rglob('*'):
   if not p.is_file():continue
   rel=p.relative_to(folder)
   keep=p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix=='.json'
   keep=keep or p.name in ('rv.swf','candidate.swf','EffectLoadChecks.swf','CombatRenderProbeMod.swf') or name=='candidates' and p.suffix=='.json'
   if keep:
    q=DEST/p.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
 failures={'full-profile-01':'SoundMixer import missing; compile failed, no AIR','full-profile-02':'AIR completed but shots=0; rejected by postvalidation; not performance evidence','full-split-04':'Read-only media hardlink denied before AIR; fresh 05 requested normal escalation'}
 (DEST/'failures.json').write_text(json.dumps(failures,indent=2)+'\n',encoding='utf-8');pins['failures.json']=sha(DEST/'failures.json')
 receipt={'formalUnchanged':formal,'windows':windows,'intervals':frames,'shots':shots,'adopted':False,'deployed':False,'performanceEligible':False,'pending':'User confirmation of formal launcher vs B190 actual reproduction environment','rootHostSha256':sha(GAME/'pfe.swf')}
 (DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');pins['finish.json']=sha(DEST/'finish.json')
 (DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
 (DEST/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
 header='> 2026-10-28 **D53单人轻机枪调查，未修复/未部署，正式仍D44**：按用户current/LMG补32窗、7168完整间隔、3060次真实开火；均有B190并行，帧数据仅诊断。early-dark候选361严格图像/13281阳性通过，无明确整帧收益，未采用。首次开火先开RV93ms、换新进程先关RV仍87ms，支持继续定位非RV的首次开火环节，不足以认定加载/绘制根因。训练房未稳定复现持续明显卡顿。已询问实际入口：正式v0.33.10还是独立B190 v0.30.2，尚待答复；未改试玩。全部本轮自有AIR退出，四项外部WIP保留。[报告](../knowledge/experiments/2026-10-28-solo-fire.md)，工具build/solo-fire。'
 journal='''## 2026-10-28 — D53轻机枪实际开火与冷启动停顿调查

- 用户补充武器轻机枪、current。修复测试夹具原生等级限制，加入发射计数，失败01/02/04保留。32有效窗口、7168完整间隔、3060次攻击；两份B190并行，全部performanceEligible=false，不作为独立性能排名。
- 当前参数dim0.6/soft25。计算与绘制拆分只提供特效遮罩线索；禁鼠标无收益，撤罩不进入候选。early-dark通过361严格图像、13281次阳性，但无明确整帧收益，未采用。
- 首次开火先开RV93ms，反向新进程先关RV仍87ms；138ms峰值在未开枪的视野初始化。未证明音频/GPU/GC或具体资源加载根因。训练房持续射击未稳定重现明显卡顿，不能否认用户现场症状。
- 只读确认B190磁盘RV独立v0.30.2，正式为D44；player-1保存enabled=0，不能仅凭旧包归因。已询问实际启动入口，尚无回复。没有改联机目录/真实存档、关闭试玩或发出协调消息。
- 正式638E/config5136不变，自有AIR/描述符退出，authority四项WIP保留。报告knowledge/experiments/2026-10-28-solo-fire.md；目标未完成，接续应匹配实际环境，不继续堆未经整帧证明的微优化。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
 for name in ['MEMORY.md','journal.md']:
  base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
  def transform(s):
   if name=='journal.md':return journal+s
   pos=s.index('\n\n')+2;return s[:pos]+header+'\n\n'+s[pos:]
  (owned/name).write_text(transform(base),encoding='utf-8',newline='\n');(MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
 for p in (MOD/'build/solo-fire').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 subprocess.run(['git','add','--','.gitignore','build/solo-fire','knowledge/experiments/2026-10-28-solo-fire.md'],cwd=MOD,check=True)
 subprocess.run(['git','add','-f','--',str(DEST)],cwd=MOD,check=True)
 for name in ['MEMORY.md','journal.md']:
  h=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=MOD,input=(owned/name).read_bytes()).decode().strip();subprocess.run(['git','update-index','--cacheinfo','100644,'+h+',state/'+name],cwd=MOD,check=True)
 assert sorted(line.split() for line in git('diff','--numstat').decode().splitlines())==sorted([['24','0','src/RVAuthorityView.as'],['2','0','state/MEMORY.md'],['4','0','state/journal.md'],['15','0','tests/authority/AuthorityViewChecks.as']])
 for rel,h in pins.items():assert hashlib.sha256(git('show',':'+(DEST/rel).relative_to(MOD).as_posix())).hexdigest()==h,rel
 subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
 print(json.dumps(receipt,ensure_ascii=False));rec.outcome='passed';rec.note='实验已归档；未解决/未部署，等待确认实际入口'
