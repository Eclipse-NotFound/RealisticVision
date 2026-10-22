"""Archive evidence and update only this task's state after deployment."""
from pathlib import Path
import json,shutil,subprocess,hashlib
import package as p
OUT,MOD=p.OUT,p.MOD
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
 receipt=json.loads((OUT/'deployment/receipt.json').read_text());assert receipt['result']=='PASS'
 proof=json.loads((OUT/'verified.json').read_text());perf=json.loads((OUT/'performance.json').read_text())
 archive=MOD/'knowledge/experiments/combat-visibility-v0333-20261022';archive.mkdir(exist_ok=False)
 files=[]
 for name in ['repro-full-01','regress-full-01','regress-full-02','regress-full-03','profile-01','checks-01','exact-01','timing-01','timing-02','combat-02','production','development-check','deployment']:
  for f in (OUT/name).rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   if f.suffix in ['.json','.log','.png'] or (f.suffix=='.txt' and ('Checks' in f.name or 'Harness' in f.name or f.name in ['batch.txt','classes.txt','formal-runtime.txt','formal-output.txt'])):files.append(f)
 files += [OUT/'verified.json',OUT/'performance.json']
 for f in files:
  q=archive/f.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,q);assert sha(f)==sha(q)
 (archive/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8')
 pins={f.relative_to(OUT).as_posix():sha(f) for f in files}
 (archive/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
 rows=[]
 for c in perf['paired']:
  a,b=c['total'];rows.append('| '+c['case']['mode']+' '+str(c['case']['dim'])+' | '+ '/'.join(str(a[k]) for k in ['mean','p95','max'])+' | '+ '/'.join(str(b[k]) for k in ['mean','p95','max'])+' |')
 report=f'''被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching
技能归属：用户级与Remains工作区级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# 2026-10-22 武器泄露与战斗开销修复

用户反馈v0.33.2在战斗仍有轻微卡顿，且记忆区域有独立武器露出。本轮准确生产基线7852F61E…BE86764；实际配置current、dim约0.6、soft_current25、viewscale1、wallbright0。未写玩家配置或存档，未操作玩家实例。采用登记、独立AIR ID、私有桌面；测试开始时玩家运行的功能复现不作为计时。后续确认玩家实例退出才采集性能。

## 根因与修复

原生UnitRaider.currentWeapon位于childObjs，由Unit.step更新，并不在Location.firstObj。旧版只扫描房间链，因此真实身体有mask而武器无mask；完整安装组合最小复现两模式各6帧均泄露806像素。候选每帧沿单位真实附件处理Weapon，复用所属单位已算出的状态，武器拥有独立Shape，避免与身体争用同一mask。只在遮罩输入更新时复制graphics；不再给这些武器重新分类或等三帧扫描。原生已隐藏状态、死亡和模式恢复独立处理。

计时归因中current的软遮罩后处理在120帧累计414–476ms。批量paletteMap和threshold替换两次getVector、逐像素循环与setVector，保留完全相同的整数透明度映射。未降低分辨率/更新频率，未变更探索、墙影、视距及地板柔化；RVWallSurface生产源指纹不变。

## 实证与边界

- 完整组合真实武器52项：两模式泄露像素806→0；隐藏/恢复、同场更新、重新挂载、原生hidden、死亡、停用、换房通过。原生武器本次remVisual/addVisual复用了同一vis，测试仅验证重新挂载，不冒充替换新对象的实测。重建不同vis的释放分支有代码但未由这次原生动作触发。
- 1536项显示/逻辑缓存与破墙；90项设置；16项运动/射线（含1000射线）；21项共享探索；65组批量位图（全256透明度和64模糊场）严格相等。
- 大图192×75、96单位：32检查点的雾图、墙图、逻辑场、单位mask及合成图严格相同。此前普通人工Unit未带真实武器，不能覆盖此次附件缺陷；本轮另有真实武器测试补上。
- 准确生产包两进程36项设置/改键保存通过。总计1848项/组检查，另有8个真实射击窗口，每窗120采样，原生攻击与弹丸均存在。
- 没有玩家截图对应存档/移动历史，不声称整张用户图复原；软取图不是GPU呈现认证。UnitMerc的internal arm、任意模组装饰和名称提示不在此次武器像素认证范围。没有改变念力玩法。

## 性能

无插桩/无逐帧取图的同进程交替对照，每组每版120帧。下表是RV更新加独立雾图draw，单位ms；不是完整FPS。[汇总](combat-visibility-v0333-20261022/performance.json)、[原始样本](combat-visibility-v0333-20261022/timing-02/evidence/result.json)和[环境采样](combat-visibility-v0333-20261022/timing-02/environment.json)均保留。秒级观察无其他AIR/JVM，不排除短进程和其他系统负载。

| 模式/记忆亮度 | D35均值/P95/最大 | D36均值/P95/最大 |
|---|---|---|
{chr(10).join(rows)}

current两组均值降低约2.5%–2.7%；classic增加0.73–0.78ms（约1.1%–1.6%），包含每帧新增的真实附件处理。P95并非全面改善，四组最大值均上升；不能声称消除了长帧或证明其根因已修复。保留候选的依据是武器错误被实际修正、current平均开销小幅下降且画面不变；本次性能优化只是有限改进。

真实战斗A/B/B/A每模式4窗，原生世界继续演进，非确定性重放；只能辅助观察，不将独立窗口差值视为精确收益。整帧尖峰与RV独占更新分开记录，不承诺所有卡顿消失。

真实战斗current两窗RV平均更新约19.60ms，基线约19.63ms，基本持平；classic约37.55ms，基线约37.35ms。此次没有证明真实战斗中的卡顿已明显改善。完整组合用于武器功能复验；战斗计时仅CS与动态RV，不能外推为完整模组组合的FPS。

## 失败和中断保留

regress-full-01的app:写PNG被AIR拒绝，改为受限本实验nativePath；regress-full-02驱动访问classic不存在的currentSight触发1009，补齐仅测试的控制场后regress-full-03通过。不是生产崩溃。timing-01因工具会话更新中断停在case1，运行器和子进程均退出后按官方登记恢复；半轮数据作废，timing-02完整重测。排队过程中遇到CS中断登记，核对无存活进程后调用recover时该记录已被对方恢复，未做二次写入或停止他方进程。

## 部署

持续本机授权，发布门禁通过后只替换RV。版本v0.33.3-combat-visibility，42400B，SHA256 `{receipt['new']}`。正式路径独立启动确认init、新版本、设置注册及tick1/181/361；保护指纹和真实配置前后相同。备份 `{receipt['backup']}` 为D35；回滚需核对当前仍为本轮包，再原子恢复此备份，正常重启生效。

准确生产源 `build/combat-visibility-output/production/src`，仅六类、无authority或fe.*存根。开发src同步本轮变更并保留既有authority记账，单独编译确认语法，未把该独立接口带入安装；它的新增武器协作行为未在本轮联机验收。四项外部WIP保留。

本轮技能实证为可复现视觉错误、真实附件测试缝隙、严格像素与计时分离、登记等待和一次中断核对、准确包部署；不覆盖只读无法复现分支或所有客户端环境。经验查询返回partial（无关写作原件缺失）；已回读KB-000106，复用实际配置覆盖和测量边界，不解释为完整经验库均已搜索。
'''
 reportpath=MOD/'knowledge/experiments/2026-10-22-combat-visibility.md';reportpath.write_text(report,encoding='utf-8')
 brief=f'> 2026-10-22 **D36 v0.33.3已部署**：原生手持武器漏扫childObjs导致记忆区泄露，现按所属单位每帧裁切并独立遮罩；806泄露像素归零，1848项和8原生射击窗通过。current软遮罩改批量处理，画面严格相同；实际耗时和长帧边界见[报告](../knowledge/experiments/2026-10-22-combat-visibility.md)。准确包AB461FF3…2F23871（42400B），生产源build/combat-visibility-output/production/src，无authority。正式init/设置注册/tick1/181/361通过；备份D35见deployment/receipt.json。'
 journal=f'''## 2026-10-22 — D36武器泄露与遮罩批量处理

- 根因与实现：手持武器在Unit.childObjs而不在房间链；按主人状态每帧处理、独立Shape共享像素，保留原生隐藏/死亡及恢复。current逐像素软遮罩转换改为相同映射的批量位图处理。
- 证据：1848项/组及8原生射击窗，真实武器806→0；设置/墙影/逻辑图严格一致。性能范围和峰值照录，不承诺完全无卡顿；玩家截图存档、内部arm/标签及联机authority未验。
- 已部署：{receipt['new']} / 42400B；正式路径init、设置注册、tick1/181/361通过。备份{receipt['backup']}；只改RV，四项外部WIP保留。
- 源与边界：[报告](../knowledge/experiments/2026-10-22-combat-visibility.md)，build/combat-visibility/README.md。准确源production/src，不从含authority的HEAD整包安装。timing-01中断作废，timing-02为完整对照，所有本轮测试进程已退出。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
 for rel in ['state/MEMORY.md','state/journal.md']:
  path=MOD/rel;working=path.read_text(encoding='utf-8-sig');head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=MOD).decode('utf-8')
  def change(s):
   if rel.endswith('journal.md'):return journal+s
   s=s.replace('# RealisticVision —— 开发记忆入口\n\n','# RealisticVision —— 开发记忆入口\n\n'+brief+'\n\n',1)
   s=s.replace('- 当前安装D35 v0.33.2（7852F61E…BE86764）；D34全部设置、D32阶梯与防溢出、D33有效缓存保留。正式源/包：build/regression-recovery-output/production-singlepass；不从含authority的HEAD整包部署。','- 当前安装D36 v0.33.3（AB461FF3…2F23871）；武器附件遮挡与批量软遮罩处理。保留D35全部设置/墙面与既有优化。准确生产源build/combat-visibility-output/production/src；不从含authority的HEAD整包部署。')
   s=s.replace('- D35实现、验证、部署已完成；所有RV实例已退出。candidate至candidate-v5为历史失败/过渡方案，不部署、不重跑覆盖。authority仍为独立未发布工作。','- D36实现、验证、部署已完成；所有本轮RV测试实例已退出。武器泄露复验归零；current平均开销略降，但实战更新基本持平、长帧未稳定改善。D35的candidate至candidate-v5和D36的timing-01为历史失败/过渡证据，不部署、不重跑覆盖。authority仍为独立未发布工作。')
   return s
  path.write_text(change(working),encoding='utf-8');(owned/path.name).write_text(change(head),encoding='utf-8')
 decision=MOD/'decisions/decisions.md'
 with decision.open('a',encoding='utf-8') as f:f.write('\n\n## D36：真实武器附件遮挡与批量软遮罩\n\n2026-10-22。以D35准确生产线修复；手持武器沿Unit.childObjs每帧读取，独立Shape共享既有软遮罩内容，保留原生隐藏与生命周期。current的逐像素透明度转换改原生批量位图调用；65组与原生32点严格比较通过才部署。性能收益仅指同输入RV更新和雾图绘制，峰值及真实战斗边界见本轮报告；不降低画质、刷新频率或视距。生产不带authority接口。\n')
 print('Archived',len(files),'files; report and owned state written')
if __name__=='__main__':main()
