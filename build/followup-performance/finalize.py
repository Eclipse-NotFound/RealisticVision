"""Archive actual D38 evidence and update only this task's state changes."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import package as p
OUT,MOD=p.OUT,p.MOD
ARCHIVE='followup-performance-v0335-20261022'
REPORT='2026-10-22-followup-performance.md'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def triple(s):return '/'.join(str(s[k]) for k in ['mean','p95','max'])
def main():
 receipt=read('deployment/receipt.json');proof=read('verified.json');perf=read('performance.json');manifest=read('production/manifest.json')
 assert receipt['result']=='PASS' and proof['status']=='PASS' and receipt['new']==manifest['swf']
 assert read('development-check/result.json')['compiled']
 archive=MOD/'knowledge/experiments'/ARCHIVE;archive.mkdir(exist_ok=False)
 names=['profile-00-visible','exact-01-parent','exact-01b-parent','timing-01-visible','exact-02-parent','timing-02-visible','exact-03-parent','timing-03-visible','checks-final','wide-final-parent','exact-final-parent','timing-final-visible','native-final','weapon-final','production','development-check','deployment']
 files=[]
 for name in names:
  for f in (OUT/name).rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   if f.suffix in ['.json','.log','.png'] or (f.suffix=='.txt' and ('Checks' in f.name or 'Harness' in f.name or f.name in ['classes.txt','formal-runtime.txt','formal-output.txt'])):files.append(f)
 files += [OUT/'inputs.json',OUT/'verified.json',OUT/'performance.json',OUT/'selected.json',OUT/'development.patch']
 files += list((OUT/'production/src').rglob('*.as'))
 for name in ['wide-final-parent','exact-final-parent']:files.append(OUT/name/'RecoveryFrameProbeMod.as')
 for f in files:
  dest=archive/f.relative_to(OUT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);assert sha(dest)==sha(f)
 (archive/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8',newline='\n')
 (archive/'archive.json').write_text(json.dumps({f.relative_to(OUT).as_posix():sha(f) for f in files},indent=2)+'\n',encoding='utf-8',newline='\n')
 paired=[];benefits={}
 for c in perf['paired']:
  a,b=c['update'];u,v=c['total'];gain=100*(a['mean']-b['mean'])/a['mean'];benefits.setdefault(c['case']['mode'],[]).append(gain)
  paired.append(f"| {c['case']['mode']} / {c['case']['dim']} | {triple(a)} | {triple(b)} | {triple(u)} | {triple(v)} | {gain:.1f}% |")
 combat=[]
 for c in perf['combat_pooled']:combat.append(f"| {c['mode']} / {c['variant']} | {triple(c['interval'])} | {c['interval']['over50']}/240 | {triple(c['update'])} |")
 gaintext='；'.join(f'{mode}约{min(v):.1f}%～{max(v):.1f}%' for mode,v in benefits.items())
 report=f'''被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching
技能归属：用户级与Remains工作区级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# 2026-10-22 继续保持画面的性能优化

用户要求继续优化，目标是开启两个模式时接近原版流畅度。以已部署D37 v0.33.4、187D287B…4111272的准确六类生产源为基线，D38最终选择candidate-04，并部署{p.VERSION}。没有从含独立authority的开发树整包发布。

## 归因与改动

分段插桩的两侧都是相同D37，192×75场景、96人工单位，每组120更新。classic亮度0.35组classicLogicRegion累计约1322/1381ms、3038次调用；helper的updateContour约596/552ms。current的updateWallSurface约1382/1278ms，其中rebuildSupport236/220、buildContourClip269/265ms。嵌套函数累计时间不能相加，也不是完整帧耗时。

1. classic将新查询区域按4×4格对齐，附近敌人与武器复用已生成的精确逻辑采样。原来的采样、墙角修正、支持边距和当前代失效保持；新单位和同帧再次移动仍即时查询。不增加视野或探索。
2. 两模式的墙面支持范围按连续行段扩展同样的一格采样边距，生成支持矩形时一并生成外侧补集。两个遮罩复用同一补集几何，省去重复全行扫描及排序。真实材质仍每次读取比较，原地破墙和透明凹口即时更新；半高阶梯、墙芯、渐变和常亮规则保持。

单独候选01的无插桩配对更新均值classic约降16%～21%，current未修改；候选03墙面行段方案两模式约降3%～8%。候选02只缓存非零支持范围，没有稳定收益，已舍弃。最终04只合01与03，下面用最终同一轮数据评价，不叠加不同轮收益。

## 正确性

本轮{proof['checks']}项/组通过：完整原逻辑场及移动单位1536、设置90、运动16（含1000射线）、共享探索21、helper像素68、变化格与多次查询3072、实际父子显示层级图像96、真实childObjs武器52、准确生产字节两进程设置36。另有12原生射击窗口。检查计数不是独立缺陷数。

96组实际视口图像与D37逐像素一致，涵盖两模式、常亮开关、亮度0/0.35/0.6/1、柔化0/40、视距0.5/1/3、缩放0.5/0.75/1/1.25及默认约0.658333。继承D37的保留父子层级取图，finally恢复原父层/索引，未使用像素容差。其软件显示层验收不等于GPU/系统DPI全部认证。

真实武器测试沿用D35泄露反例与完整所选组合，候选泄露像素为0。重新挂载复用原生vis，不声称覆盖所有其他模组装饰。源码审查确认FOV、原生visi/t_visi、AI/地图/传送、设置和共享探索代码无新修改；相关历史算法证据复用D37，不虚增本轮专测计数。

exact-01-parent初次失败是继承工具按候选01～04编号跳过lazy完整场生成，比较了尚未填的缓存。修正为所有本轮候选在验证时都先补齐双方逻辑场，并只比较可查询区域；新exact-01b-parent32点通过。原失败保留，不覆盖，不计入通过项。实际单位遮罩仍在运行路径独立比较；LazyClassic/DirtyClassic保留历史全图算法作为oracle。

## 同输入性能

每组每版120样本，同进程交替，无插桩、无逐帧截图。单位ms，均值/P95/最大。RV更新CPU工作与完整游戏帧间隔分开；更新+draw的draw是独立软件绘制，不是GPU耗时。

| 模式/亮度 | D37更新 | D38更新 | D37更新+draw | D38更新+draw | 更新均值降低 |
|---|---|---|---|---|---|
{chr(10).join(paired)}

最终同输入更新均值下降：{gaintext}。P95、最大值完整照录，平均降低不表示每个长帧消失；不跨轮挑选有利数字。

## 原生战斗观察

同一CS大场景，记忆亮度0.6、current柔化25，按每模式off/A/B/B/A/off交替；有实际原生攻击与弹丸，每窗120采样，各版本每模式合计240帧。off是同场原生渲染，不是无任何模组的纯游戏。世界持续演进，窗口差异不是确定性因果收益，不能外推为全组合或联机FPS。

| 模式/版本 | 帧间隔均值/P95/最大(ms) | 超50ms帧 | RV更新均值/P95/最大(ms) |
|---|---|---|---|
{chr(10).join(combat)}

本轮没有测出稳定的整帧改善：classic平均35.171→35.462ms，current34.821→35.279ms；classic超50ms帧10→9，current3→6。classic模组更新12.896→12.946ms基本持平，current12.125→11.688ms略降。off/current出现400ms孤立峰值，不能靠它抬高的均值宣称达到原版，也不能把小幅窗口差异直接归因于本改动。该战斗场景的结果不同于96人工单位同输入压力场景；真实战斗改善尚未得到证实。

实际画面保持和同输入开销下降支持保留本轮优化，但用户所求的战斗流畅度仍需后续验证；不承诺所有场景已达到原版。完整组合只用于武器功能回归，联机压力未重跑。

计时环境与原始样本见[performance.json]({ARCHIVE}/performance.json)。最终计时检查未记录其他AIR/JVM，最低可用内存均超过3GiB；秒级采样不排除短进程及系统负载。所有AIR/JVM按官方共享测试登记顺序、独立应用ID/存储、私有桌面运行；未操作玩家游戏或真实存档。经验检索partial，已回读KB-000056，不将来源缺失解释为全库无经验。

## 部署与恢复

准确包{manifest['bytes']}B，六类，SHA256 `{receipt['new']}`。根application.xml→pfe.swf及loader清单核对后只替换RV。正式路径独立init、ModSettings注册、tick1/181/361通过；宿主、其他模组和真实配置指纹保持，自己的测试进程与描述符已清理。用户保存并正常重启游戏后生效。

备份 `{receipt['backup']}` 是D37，SHA187D287B…4111272。回滚前核对当前RV仍为本轮SHA，再原子恢复该备份并重启；如有后续新安装先核对，不覆盖。部署器有失败回滚，本轮未触发。准确生产源在本证据production/src及build/followup-performance-output/production/src，开发树authority与四项外部WIP保留。

完整证据索引：[archive.json]({ARCHIVE}/archive.json)。仅此次冻结源与同一SHA对应验收；旧候选与旧正式版本不得覆盖当前安装。
'''
 (MOD/'knowledge/experiments'/REPORT).write_text(report,encoding='utf-8',newline='\n')
 brief=f'> 2026-10-22 **D38 v0.33.5已部署**：classic按4×4格复用精确逻辑采样；两模式墙面支持区/补集一次生成。同输入更新下降{gaintext}，4987项/组、12原生射击窗及正式init/注册/tick1/181/361通过。准确包{receipt["new"][:8].upper()}…{receipt["new"][-8:].upper()}（{manifest["bytes"]}B）；[报告](../knowledge/experiments/{REPORT})含完整帧间隔和长帧边界。生产源build/followup-performance-output/production/src，无authority；D37备份保留，正常重启生效。'
 journal=f'''## 2026-10-22 — D38继续保持画面的性能优化

- 实现：classic4×4格批量生成精确逻辑采样；墙面支持区和正向补集一次生成，两个mask复用。画质/刷新/逻辑视野不减；设置、阶梯、防溢出和武器遮挡保留。
- 证据：4987项/组，96组父层图像严格相等，12原生战斗窗；同输入更新下降{gaintext}。战斗为非确定性观察，完整P95/长帧及off距离见[报告](../knowledge/experiments/{REPORT})。
- 部署：{p.VERSION}，{receipt['new']}，{manifest['bytes']}B，正式init/注册/tick1/181/361通过；备份{receipt['backup']}。只改RV，外部四项WIP保留。
- 淘汰：支持形状缓存候选02无稳定收益。01初次验证工具编号分支错误，修正后另名复验；最终04合01与03。全部本轮测试已退出，用户正常重启生效。

'''
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for rel in ['state/MEMORY.md','state/journal.md']:
  path=MOD/rel;working=path.read_text(encoding='utf-8-sig');head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=MOD).decode('utf-8')
  def change(s):
   if rel.endswith('journal.md'):return journal+s
   s=s.replace('# RealisticVision —— 开发记忆入口\n\n','# RealisticVision —— 开发记忆入口\n\n'+brief+'\n\n',1)
   start=s.index('- 当前安装D37 ');end=s.index('\n',start)
   s=s[:start]+f'- 当前安装D38 v0.33.5（{receipt["new"][:8].upper()}…{receipt["new"][-8:].upper()}）；精确采样复用与墙面行段优化。准确源build/followup-performance-output/production/src和knowledge/experiments/{ARCHIVE}/production/src，不从含authority的HEAD整包部署。'+s[end:]
   start=s.index('- D37实现、验证、部署已完成');end=s.index('\n',start)
   return s[:start]+'- D38实现、验证、部署已完成；全部本轮测试实例退出。最终candidate-04合01+03，02无稳定收益已淘汰；同输入开销继续降低，仍不承诺所有战斗达到原版。exact-01-parent为继承工具错误，修正后另名复验，不重跑覆盖历史。authority仍独立未发布。'+s[end:]
  path.write_text(change(working),encoding='utf-8',newline='\n');(owned/path.name).write_text(change(head),encoding='utf-8',newline='\n')
 with (MOD/'decisions/decisions.md').open('a',encoding='utf-8',newline='\n') as f:
  f.write('\n\n## D38：复用精确遮挡采样与墙面补集\n\n2026-10-22。基于D37准确生产源，classic将按需逻辑场查询对齐4×4格供相邻单位复用，原采样/支持边距/失效保持；墙面连续行段生成支持区时同步生成正向补集，避免重复扫描和排序。材质仍每次核对，不降画质/刷新/视距。候选02仅缓存支持形状无稳定收益，舍弃；最终04合01与03。4987项/组、96严格父层图像和12原生射击窗后部署v0.33.5；性能及长帧边界见2026-10-22-followup-performance.md。生产不含authority。\n')
 print('D38 archive/report/state ready:',len(files),'files')
if __name__=='__main__':main()
