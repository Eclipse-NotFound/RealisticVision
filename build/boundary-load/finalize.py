from pathlib import Path
import json,hashlib,shutil,subprocess
import package as p
MOD,OUT=p.MOD,p.OUT
ARCHIVE='knowledge/experiments/boundary-load-v0337-20261023'
REPORT='knowledge/experiments/2026-10-23-boundary-load.md'
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
def main():
 receipt=read('deployment/receipt.json');assert receipt['result']=='PASS'
 proof=read('verified.json');perf=read('performance.json');manifest=read('production/manifest.json')
 dest=MOD/ARCHIVE;assert not dest.exists();dest.mkdir(parents=True)
 names=['safe-exact-02-parent','safe-exact-03-parent','safe-extent-parent','stress-profile','stress-02-profile','stress-03-timing','native-final','weapon-final','render-checks','render-checks-02','production','deployment','development-check']
 for name in names:
  for f in (OUT/name).rglob('*'):
   # Preserve output and exact tested sources; omit duplicated hosts/assets/stores.
   if not f.is_file() or 'storage' in f.parts:continue
   relative=f.relative_to(OUT/name)
   if relative.parts[0] in ['mods','data','music','snd','runtime','runtimes']:continue
   if f.suffix not in ['.json','.log','.txt','.as','.png'] and not (name=='production' and f.name=='RealisticVisionMod.swf'):continue
   target=dest/name/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
 for name in ['candidate-00','candidate-01','candidate-02','candidate-03','production-input']:
  shutil.copytree(OUT/name/'src',dest/name/'src')
 for name in ['inputs.json','selected.json','performance.json','performance-decision.json','verified.json','development.patch']:
  shutil.copyfile(OUT/name,dest/name)
 (dest/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8')
 pins={f.relative_to(dest).as_posix():sha(f) for f in dest.rglob('*') if f.is_file()}
 (dest/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
 lines=['被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching；remains-mod-memory',
 '技能归属：用户级与Remains工作区级','测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision','',
 '# 2026-10-23 多明暗边界与敌人遮罩：D41 v0.33.7','',
 f'已部署 **{p.VERSION}**，{manifest["bytes"]} B，SHA256 `{manifest["swf"]}`。基线为D39 `83d8e590…205c7e65`；没有引入D40未发布候选或authority。用户确认两种模式都有卡顿，按本机持续授权完成验证、备份和正式路径复验。','',
 '## 定位与实现','',
 '边界移动会使视野输入变化，部分可见单位增多会叠加逐单位遮罩工作；没有敌人时墙面/雾层更新也占明显时间。因此不能把全部卡顿归于敌人遮罩。此次固定192×75原生地图做0/24/96个测试单位和静止/两档脚本位移对照；数量、位置、移动和墙面状态有各自影响，未复现用户精确存档，也没有独立测出“边界条数→耗时”的曲线。','',
 '- 两模式：输入位图仍当帧更新，只在区域或位图对象改变时重建遮罩图形。身体、血条与独立武器遮罩共享更新后的像素引用，避免重复图形及武器复制。',
 '- classic：查询重叠区域时，只渲染其中未缓存部分的包围矩形，保留4×4格批处理和两格采样边缘；已发布过的区域不重复复制。',
 '- current：清理上一轮确实写过的视野矩形，免于反复清理整个大地图位图；切房/分配变化、静止原生墙光变化使范围失效，下次完整清理。镜头跳转清除旧矩形。',
 '- 不降低分辨率或刷新频率，不改光线算法、探索、可见阈值和原生visi/t_visi；墙芯、阶梯、防溢出、常亮选项与现有设置保留。RVWallSurface及另外四个生产辅助类字节源不变。','',
 '## 证据与正确性','',
 '747项/组：64组最终候选严格图像/逻辑/单位遮罩对照；6项镜头外墙光更新反例（含3组完整图像检查）；589项身体/血条/武器逐帧绘制检查（216次复用，同一applyMask方法指纹复用证据）；52项原生武器泄露回归；准确生产字节两进程36项设置保存。另12个完整组合原生跑动射击窗口，每窗240个采样帧，均有持续贴地移动、折返、实际攻击和原生弹体。',
 '589项驱动第一轮#1009来自classic未分配测试用currentSight，修正夹具后另目录通过；失败保留。没有放宽像素容差。父层图像在classic全图诊断前截取，避免D40已发现的诊断副作用。镜头外反例人为设置共同输入并使用真实applyVision静止墙更新路径，然后检查旧像素清零；不修改正式游戏/存档。','',
 '## 同输入局部更新计时（毫秒）','',
 '每组每版本80样本、同进程交替顺序。脚本位移不是原生跑动；更新加雾层软件绘制不等于完整FPS。profile初筛中classic96单位慢移遮罩8.18→5.86ms，快移7.80→5.90ms；最终无分段探针结果如下。','',
 '|模式|测试单位数|脚本位移|更新均值 旧→新|更新P95 旧→新|更新+雾绘制均值 旧→新|','|---|---:|---:|---:|---:|---:|']
 for row in perf['paired']:
  c=row['case'];a,b=row['update'];x,y=row['updateDraw']
  lines.append(f'|{c["mode"]}|{c["count"]}|{c["speed"]}|{a["mean"]}→{b["mean"]}|{a["p95"]}→{b["p95"]}|{x["mean"]}→{y["mean"]}|')
 lines+=['','## 原生完整帧间隔（毫秒）','','方向键真实跑动与持续敌人射击，低开销观察；序列off/candidate/baseline/baseline/candidate/off，每模式各一轮。NPC/世界持续演进，不能当成确定性全帧因果实验。每行汇合两个窗口，共478个有后继帧的间隔。off仍启用其他选定模组，仅关闭RV。','',
 '|模式|版本|均值|P95|最大|超过100ms次数|RV更新均值|','|---|---|---:|---:|---:|---:|---:|']
 for row in perf['native']:
  a=row['interval'];lines.append(f'|{row["mode"]}|{row["variant"]}|{a["mean"]}|{a["p95"]}|{a["max"]}|{a["over100"]}|{row["update"]["mean"]}|')
 lines+=['',
 'classic平均帧间隔60.213→57.241ms、P95 81→74ms，但最大149→174ms，不能说所有长帧改善。current整体54.659→55.347ms、P95同为70ms，按基本持平处理；RV自身13.059→12.801ms的小幅下降不构成整体变快的证据。两模式仍慢于同场RV关闭约40ms，未达到接近原版的最终目标。接受本次有限优化是因为密集边界的同输入收益明确、classic整体方向一致、current整体未见实质回退且功能严格一致。',
 '尾部时间包括其他脚本、渲染、调度与驱动，不能据此认定GPU或GC。完整最慢帧及内存记录见performance.json；保留P95/最大值反例。未证明剩余卡顿的唯一根因，下一步应结合宿主绘制合批工作继续观察，不叠加未验候选。','',
 '## 部署与回退','',
 f'原生产基线和当前宿主BEFC均在部署前核对，正式目标仅`release/RealisticVisionMod.swf`。备份：`{receipt["backup"]}`。需要回退时只恢复该备份，先核对当前仍为本次安装哈希。',
 '正式路径独立新应用ID启动：新版本init、ModSettings设置注册、tick1/181/361通过；自己的测试进程与临时描述符清理，其他模组/宿主/配置保护指纹不变，玩家存储未写。已有游戏需正常保存并重启。构建源`build/boundary-load-output/production/src`，六类，无authority或测试存根。',
 f'本轮证据：[归档](boundary-load-v0337-20261023/verified.json)，[性能原始汇总](boundary-load-v0337-20261023/performance.json)，[部署回执](boundary-load-v0337-20261023/deployment/receipt.json)。',
 '', '技能回流：按正式测试登记等待并最小核对一次RConnect启动失败占用（air_started=false/准确PID均无）；通过recover释放，未结束其他测试。与CS按登记错开；未调用Ghost、未新建委托。发布门禁按2026-10-19.1执行，本轮无需再次确认；失败回滚路径已备妥但未主动制造部署故障。','']
 (MOD/REPORT).write_text('\n'.join(lines),encoding='utf-8',newline='\n')
 memory=f'> 2026-10-23 **D41 v0.33.7已部署**：复用身体/血条/武器遮罩图形，classic仅补算未缓存视野区，current局部清理并保留静止墙光失效。747项/组、12原生战斗窗与正式init/注册/tick1/181/361通过。准确包{manifest["swf"][:12]}…（{manifest["bytes"]}B），生产源build/boundary-load-output/production/src。密集移动更新classic约11%下降、current约3%–4%；完整帧classic60.2→57.2ms，current基本持平54.7→55.3ms，未达原版，长帧未全解。[报告](../{REPORT})。\n\n'
 journal=f'## 2026-10-23 — D41移动边界/敌人遮罩优化部署\n\n- 用户确认两模式都有；三项不降画质优化，747项/组及12原生方向键跑动射击窗口通过。局部收益与整体限度分开记录，current整体仍基本持平，classic最大帧仍有反例。\n- 已部署{p.VERSION}，SHA {manifest["swf"]}；D39回退备份{receipt["backup"]}，正式路径init/注册/tick1/181/361通过。\n- 仅RV本轮修改，authority四项外部WIP保留；[报告](../{REPORT})，后续不要混入D40未发布候选。\n\n'
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for name,insert in [('MEMORY.md',memory),('journal.md',journal)]:
  path=MOD/'state'/name;base=git('show','HEAD:state/'+name).decode('utf-8');working=path.read_text(encoding='utf-8-sig')
  def apply(text):
   return text.replace('\n\n','\n\n'+insert,1) if name=='MEMORY.md' else insert+text
  path.write_text(apply(working),encoding='utf-8',newline='\n');(owned/name).write_text(apply(base),encoding='utf-8',newline='\n')
 decision=MOD/'decisions/decisions.md';text=decision.read_text(encoding='utf-8-sig');entry='## D41：移动边界只更新像素，重叠逻辑区按未缓存部分补算\n\n- 保留每帧视野和原样光栅化，复用不变的mask图形；classic缩小新逻辑采样区，current局部清理保留全清理失效分支。\n- 采用三项组合并部署v0.33.7；747项/组通过，classic整体略改善、current基本持平，不宣称已达原版或解决全部长帧。\n- [证据](../'+REPORT+')；D40候选仍不发布。\n\n'
 marker=text.index('## D1：');decision.write_text(text[:marker]+entry+text[marker:],encoding='utf-8',newline='\n')
 print('D41 report/archive/state ready',len(pins))
if __name__=='__main__':main()
