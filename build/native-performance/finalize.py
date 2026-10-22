"""Archive D37's actual evidence and preserve unrelated authority work."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import package as p
OUT,MOD=p.OUT,p.MOD

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def triple(s):return '/'.join(str(s[k]) for k in ['mean','p95','max'])

def main():
 receipt=read('deployment/receipt.json');proof=read('verified.json');perf=read('performance.json');manifest=read('production/manifest.json')
 assert receipt['result']=='PASS' and proof['status']=='PASS' and receipt['new']==manifest['swf']
 assert read('development-check/result.json')['compiled']
 archive=MOD/'knowledge/experiments/native-performance-v0334-20261022';archive.mkdir(exist_ok=False)
 accepted=['checks-final','fov-12','memory-12','wide-final-visible','exact-final-visible','wide-final-parent','exact-final-parent','timing-final-visible','native-final','weapon-final','display-matrix-final','production','development-check','deployment']
 historical=['display-matrix','display-matrix-diagnostic','exact-wide-18','exact-wide-18b','focus-12-visible']
 files=[]
 for name in accepted+historical:
  for f in (OUT/name).rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   if f.suffix in ['.json','.log','.png'] or (f.suffix=='.txt' and ('Checks' in f.name or 'Harness' in f.name or f.name in ['classes.txt','formal-runtime.txt','formal-output.txt'])):files.append(f)
 files += [OUT/'verified.json',OUT/'performance.json',OUT/'selected.json',OUT/'development.patch']
 files += list((OUT/'production/src').rglob('*.as'))
 # Keep the small, exact capture oracle with its observed result.
 for name in ['wide-final-parent','exact-final-parent']:
  files.append(OUT/name/'RecoveryFrameProbeMod.as')
 for f in files:
  dest=archive/f.relative_to(OUT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f)
 (archive/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8',newline='\n')
 (archive/'archive.json').write_text(json.dumps({f.relative_to(OUT).as_posix():sha(f) for f in files},indent=2)+'\n',encoding='utf-8',newline='\n')
 paired=[]
 for c in perf['paired']:
  a,b=c['update'];u,v=c['total']
  paired.append(f"| {c['case']['mode']} / {c['case']['dim']} | {triple(a)} | {triple(b)} | {triple(u)} | {triple(v)} |")
 combat=[]
 for c in perf['combat_pooled']:
  combat.append(f"| {c['mode']} / {c['variant']} | {triple(c['interval'])} | {c['interval']['over50']}/240 | {triple(c['update'])} |")
 env={name:round(min(x['available_bytes'] for x in read(name+'/environment.json'))/1024**3,2) for name in ['timing-final-visible','native-final']}
 report=f'''被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching
技能归属：用户级与Remains工作区级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# 2026-10-22 两模式保持画面的性能优化

用户要求继续优化两种模式，目标接近原版渲染流畅度。D37基于正式D36 v0.33.3的准确六类生产源和AB461FF3…2F23871（42400B），最终选择candidate-12，部署为v0.33.4-native-performance。实际同场景战斗观察明显改善，但尚未达到原版水平；不把“更接近”写成目标完全完成。

## 改动与视觉约束

1. classic大房间只对实际视口及支持边距做显示合成；完整逻辑场单独按查询补齐。跳转镜头遇到原来跳过的渲染帧，仅用已有采样补绘，不推进原生光照、探索或淡出。
2. classic沿原有更新节奏核对原生亮度、记忆、探索及墙几何；只对改变的格子及3×3邻域重算昂贵的墙边灰度，solid改变才重建墙几何。
3. 墙材质复制计划按来源身份/矩形/位置复用；每帧仍复制和比较真实材质。重叠或不支持的变换继续原fallback，不延迟原地破墙。
4. FOV先全清，再遍历原视距的保守矩形与墙邻域；射线、圆距离和墙阻挡规则完全保留。
5. current缓存本地子格记忆的全无/混合/全有分类，任何本地写入立即失效；共享探索存在时保持原扫描。

未降低分辨率、刷新频率或视距；已探索亮度、分模式柔化、原生墙芯/渐变、阶梯、防溢出和常亮开关保留。D36真实childObjs武器遮挡保留。未修改原版AI、地图/传送判定及原生visi/t_visi。生产包不含独立authority开发。

## 验证及取图工具纠正

共{proof['checks']}项/组通过（不同驱动的检查计数，非独立缺陷数）：基础缓存1536、设置90、运动16（含1000射线）、共享探索21、helper位图68、变化格3072、FOV1152、子格记忆1920、独立取图36、两种取图各96检查点、真实武器52、准确生产包跨进程设置36。另有12个原生持续射击窗口，每窗120采样。源码逐份核对至最终生产包，版本号外无差异；开发树单独编译通过，未安装开发树。

两模式、常亮开关、记忆亮度0/0.35/0.6/1、柔化0/40、视距0.5/1/3、缩放0.5/0.75/1/1.25及默认约0.658333的组合，实际视口与D36严格逐像素相同；逻辑场/单位遮罩/移动/破墙亦核对。最终父子层级取图96检查点通过，未使用像素容差。真实武器复验保留旧D35的806泄露像素反例，本候选为0。该武器驱动的重新挂载复用了同一原生vis，不能声称验证了所有新vis替换与模组装饰。

早期沿用draw(fogVis,cameraMatrix)忽略根节点为scrollRect设置的位移，普通回放还漏掉实际scaleV并固定画布大小，错误比较了屏幕外区域。补上根矩阵后，独立Sprite反例仍揭示非整数缩放的栅格化差异：0.658333…时94个边缘像素、最大64/255；位置/包围盒相同，不代表逐像素相同。因此最终同步取图把fogVis暂挂到空父Sprite、按真实相机矩阵绘制父层，finally恢复原父层和索引。独立36项证明此路径与原父层绘制严格一致；整景再复验。此方法验证软件显示层，不等于GPU/操作系统DPI呈现认证。

旧取图轮的合成图和draw耗时不作为最终视觉/绘制结论；完整逻辑比较和纯更新计时各保留其原范围。candidate-06曾有真实的跳转补绘缺口，07已修复；不能把所有旧失败都归为取图问题。

## 同输入开销

每组每版120样本、同进程交替、无阶段插桩/无每帧截图。单位ms，均值/P95/最大。更新是RV独占CPU工作；更新+draw中的draw仍为组合矩阵的独立软件绘制，不是GPU帧耗时，不能换算完整游戏FPS。

| 模式/记忆亮度 | D36更新 | D37更新 | D36更新+draw | D37更新+draw |
|---|---|---|---|---|
{chr(10).join(paired)}

同输入更新均值：classic下降约26%～45%，current下降约24%。classic亮度0.35组的更新+draw最大值145→186ms，仍存在不利尖峰；不能把均值改善解释为所有长帧消失。绝对耗时受场景和机器负载影响，不跨不同轮次挑选有利样本。原始数据见[timing-final-visible](native-performance-v0334-20261022/timing-final-visible/evidence/result.json)。

## 实际原生射击与目标距离

192×75大场景、约56～57单位、Raider持smg10持续原生开火，有实际攻击和弹丸；按每模式off/A/B/B/A/off交替，共12窗口。每个模式/版本汇总240帧。off为同一ContinuousScene场景内的原生渲染，不是无任何模组的干净游戏；完整所选模组组合用于武器功能验收，不能把下表外推为全组合或联机FPS。原生世界持续演进，属于实战观察而非确定性同输入因果测量。

| 模式/版本 | 整帧间隔均值/P95/最大(ms) | 超50ms帧 | RV更新均值/P95/最大(ms) |
|---|---|---|---|
{chr(10).join(combat)}

current平均帧间隔45.87→37.48ms，off约33.30ms；classic66.85→40.75ms，off约33.35ms。候选相对off分别仍多约12.6%和22.2%，长帧也未完全回到off水平。classic超50ms由162/240降到33/240，current由34/240降到11/240。表内P95与最大值照录，不承诺每个用户场景都无卡顿。当前安装值得保留的依据是严格画面一致、同输入更新开销下降且实战整体更接近原版。

最终计时秒级环境采样无其他AIR/JVM，可用内存最低分别{env['timing-final-visible']}和{env['native-final']}GiB；不排除短进程及其他系统负载。前期机器可用内存降至约5.66GiB，旧6GiB门槛拒绝exact-wide-18且未启动AIR。根据已测内存回落，本轮启动下限改5GiB，最终性能审查另要求全程至少3GiB；没关闭玩家应用或改系统QoS。像素验证轮耗时不作收益。

## 历史尝试与运行纪律

01～04全图缓存探索，05编译失败；06跳转补绘缺口由07解决；08～12逐步叠加最终优化。13～17因错误取图尝试缩放回退，18保留整图缓冲的替代均未选择。最终C12未带这些回退，也未缩小原helper支持范围。display-matrix初次严格合成矩阵检查失败，diagnostic轮仅定位差异（其passed=24不是最终正确性验收），final36才验证保留父子层级方案。

所有AIR/JVM使用官方共享game登记、独立应用ID/存储与私有桌面；等待期间为其他模组让出资源。取消的自身等待进程由官方状态转暂缓；一次对waiting调用recover被拒，未强改登记或停止他方进程。未操作玩家游戏、存档或真实配置。旧SWF护栏曾拦截混合读取/写报告命令，改为正常独立只读核验，没有关闭护栏。

经验检索为partial，已读KB-000071与既有相机屏幕尺度结论；无关原件缺失，不解释为全库无经验。此前CS主循环协作回报未自行复查原日志，未用来填补本轮计时证据。

## 部署与恢复

按持续本机授权，只安装RV {manifest['bytes']}B，SHA256 `{receipt['new']}`。根application.xml→pfe.swf加载链与manifest已核对；正式路径独立启动确认新init、设置注册及tick1/181/361。宿主、其他模组及真实配置指纹前后保持；测试进程和临时描述符已清理。用户需保存并正常重启游戏才能加载新字节。

备份 `{receipt['backup']}` 为D36（AB461FF3…2F23871）。回滚前须核对正式仍是本轮187D287B…4111272，再原子恢复该备份并正常重启；若有更新安装先停止回滚、核对版本。部署失败分支自动回滚，本轮正式复验通过，未触发回滚。

准确生产源保存在本证据目录production/src以及build/native-performance-output/production/src。开发src含既有authority，不能整包替代正式六类产物；四项他方WIP保留。完整原始样本、截图、指纹及部署回执见[证据目录](native-performance-v0334-20261022/archive.json)。下一步若继续逼近原版，应优先追踪classic剩余更新帧与整体长帧，沿同场景off对照；不能以减少更新或牺牲边缘效果换成绩。
'''
 (MOD/'knowledge/experiments/2026-10-22-native-performance.md').write_text(report,encoding='utf-8',newline='\n')
 brief=f'> 2026-10-22 **D37 v0.33.4已部署**：保持D36画面，classic视口合成/变化格重算、材质复制计划复用、FOV保守遍历及current本地子格缓存。8191项/组、12原生射击窗、准确包设置与正式init/注册/tick1/181/361通过。战斗帧间隔classic66.85→40.75ms、current45.87→37.48ms，同场off约33.3ms，仍未完全达原版。准确包187D287B…4111272（43816B），冻结生产源见本轮证据production/src，无authority；[报告](../knowledge/experiments/2026-10-22-native-performance.md)详录取图纠正/长帧边界与D36备份。'
 journal=f'''## 2026-10-22 — D37保持画面的两模式性能优化

- 实现：classic显示按视口、变化格及邻域重算；每帧真实材质核对但复用复制计划；FOV保守范围；current已见子格分类缓存。默认、设置、共享探索、原墙芯/阶梯/防溢出及真实武器遮挡保留。
- 证据：8191项/组及12原生射击窗。取图先修正根节点/相机矩阵，再用保留父子层级96点严格复验；非整数缩放根矩阵栅格差异独立36项限定。不降低刷新/画质/视距。
- 性能：同输入更新classic约降26%～45%、current约24%；战斗帧间隔classic66.85→40.75、current45.87→37.48ms，同场off约33.3。仍有长帧，未达完全原版，非全模组联机验收。
- 部署：{receipt['new']}，{manifest['bytes']}B；正式路径新init/注册/tick1/181/361通过，备份{receipt['backup']}，只改RV。生产源归档production/src，开发authority与四项外部WIP保留。
- [完整报告](../knowledge/experiments/2026-10-22-native-performance.md)；候选12为最终，13～18为淘汰分支。全部本轮测试已退出，用户保存并正常重启生效。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for rel in ['state/MEMORY.md','state/journal.md']:
  path=MOD/rel;working=path.read_text(encoding='utf-8-sig');head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=MOD).decode('utf-8')
  def change(s):
   if rel.endswith('journal.md'):return journal+s
   s=s.replace('# RealisticVision —— 开发记忆入口\n\n','# RealisticVision —— 开发记忆入口\n\n'+brief+'\n\n',1)
   s=s.replace('- 当前安装D36 v0.33.3（AB461FF3…2F23871）；武器附件遮挡与批量软遮罩处理。保留D35全部设置/墙面与既有优化。准确生产源build/combat-visibility-output/production/src；不从含authority的HEAD整包部署。','- 当前安装D37 v0.33.4（187D287B…4111272）；两模式保持画面的性能优化，D36武器遮挡与全部设置/墙面保留。准确源build/native-performance-output/production/src及knowledge/experiments/native-performance-v0334-20261022/production/src；不从含authority的HEAD整包部署。')
   old='- D36实现、验证、部署已完成；所有本轮RV测试实例已退出。武器泄露复验归零；current平均开销略降，但实战更新基本持平、长帧未稳定改善。D35的candidate至candidate-v5和D36的timing-01为历史失败/过渡证据，不部署、不重跑覆盖。authority仍为独立未发布工作。'
   new='- D37实现、验证、部署已完成；所有本轮RV测试实例已退出。两模式更接近同场原生渲染，但平均帧间隔仍高约12.6%/22.2%（current/classic），长帧尚存。最终candidate-12；13～18为淘汰尝试。旧取图未算根位移/相机比例，最终父层取图已纠正并严格验收；勿重跑覆盖旧证据。authority仍为独立未发布工作。'
   return s.replace(old,new)
  path.write_text(change(working),encoding='utf-8',newline='\n');(owned/path.name).write_text(change(head),encoding='utf-8',newline='\n')
 with (MOD/'decisions/decisions.md').open('a',encoding='utf-8',newline='\n') as f:
  f.write('\n\n## D37：保持画面并逼近原生渲染开销\n\n2026-10-22。以D36准确生产线实施视口显示合成、classic变化格重算、材质复制计划复用、FOV保守范围和current本地子格分类缓存。逻辑场与显示场隔离，破墙/共享探索即时失效，画质、刷新与视距不减。最终candidate-12，经保留父子显示层级的严格像素比较才部署；13～18为淘汰分支。真实战斗对照明显改善但仍未达到同场off水平，具体均值、P95/最大值和超50ms比例见2026-10-22-native-performance.md。不把独立雾draw或非确定性窗口当完整FPS因果证明，生产不含authority。\n')
 print('D37 archive/report/state ready:',len(files),'files')

if __name__=='__main__':main()
