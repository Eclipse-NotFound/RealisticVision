from pathlib import Path
import json,shutil,subprocess,re,hashlib,statistics
import package as p
MOD,OUT=p.MOD,p.OUT
ARCHIVE='knowledge/experiments/effect-load-v0339-20261024';REPORT='knowledge/experiments/2026-10-24-effect-load.md'
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def copy_evidence(source,target,names):
 for name in names:
  base=source/name
  if base.is_file():
   dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base,dest);continue
  for f in base.rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   rel=f.relative_to(base)
   if rel.parts[0] in ['mods','Rooms','data','music','snd','runtime','runtimes']:continue
   if f.suffix not in ['.json','.log','.txt','.as','.png'] and not(name=='production-final' and f.name=='RealisticVisionMod.swf'):continue
   if f.name in ['lang.xml','launcher_text.xml'] or f.name.startswith('text_'):continue
   dest=target/name/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
def main():
 receipt=read('deployment/receipt.json');assert receipt['result']=='PASS'
 proof=read('verified.json');perf=read('performance.json');manifest=read('production-final/manifest.json');decision=read('performance-decision.json');assert decision['accepted']
 dest=MOD/ARCHIVE;assert not dest.exists();dest.mkdir(parents=True)
 names=['candidate-01','candidate-02','candidate-03','edges-01','functional-01','functional-02','functional-03','native-01','native-02','native-03','native-04','native-05','native-06','idle-01','safe-01-parent','safe-02-parent','production-final','development-check','deployment','group-steps','inputs.json','performance.json','performance-decision.json','dependency-transition.json','verified.json','development.patch']
 names += [f.name for f in OUT.glob('gate-*.log')]
 copy_evidence(OUT,dest,names)
 copy_evidence(MOD/'build/effect-load-output',dest/'rejected-v1',['candidate-01','native-01','native-02','native-03','performance.json','performance-decision.json','verified.json'])
 copy_evidence(MOD/'build/effect-load-v2-output',dest/'rejected-v2',['candidate-01','performance-decision.json'])
 (dest/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8')
 pins={f.relative_to(dest).as_posix():sha(f) for f in dest.rglob('*') if f.is_file()};p.run.save(dest/'archive.json',pins)
 lines=['被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching；remains-mod-memory','技能归属：用户级与Remains工作区级','测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision','',
 '# D43：密集特效遮罩的单次采样优化','',f'已部署 **{p.VERSION}**，{manifest["bytes"]}B，SHA256 `{manifest["swf"]}`。由D42准确生产源派生，仅替换RV。','',
 '用户反馈敌人、子弹和弹道较多时，无论是否被遮挡都会卡顿。D42在判断特效全亮/全暗前，已经生成或更新区域位图、模糊图及输入副本，完全可见的动画也付出了遮罩成本。','',
 '最终候选在原有采样中判断完整支持区是否一致：classic直接复用threshold返回的匹配数，current检查已写入的原始小位图。全暗使用原有空遮罩；全亮且有足够滤镜支撑时直接按原生绘制。只有混合、房间边界或宽滤镜需要继续生成模糊图和辅助形状。保留区域原始采样缓存，不宣称消除全部区域缓存；不重复classic逻辑采样，不降低刷新频率，不修改子弹物理、动画、探索和敌人判定。','',
 '## 被否决的候选与环境异常','',
 '- v1逐格提前分类：1131项/组功能通过，但两轮classic平均帧间隔分别83.383→87.688ms、79.964→81.992ms，均不利，未部署。','- v2整块提前分类：360帧像素一致，但混合区域仍重复采样，未进入正式性能验收或部署。','- v3第一次构建局部变量重名，编译失败后改名，失败目录保留。第一轮密集夹具完成360帧严格对照，但达到180秒进程上限，退出124；不作为最终性能依据。原生测试一次启动前可用内存约4.13GiB，被既有5GiB门槛阻止，未启动AIR；原始前置快照保留。','- 一次功能运行在构建完成前被调用，因build.json未生成而退出，未启动AIR；之后等待构建成功再运行。','',
 '## 同输入局部开销','',
 '两版本同一AIR进程内交替处理相同位置、旋转、视野。下表只计独立视觉遮挡函数，绘图对比在计时外，不是完整游戏FPS。每组30样本；100/500为人工移动视觉对象，不代表真实战斗子弹数量。','',
 '|模式|区域|对象数|D42均值ms|候选均值ms|D42/候选P95|','|---|---|---:|---:|---:|---|']
 at=lines.index('## 同输入局部开销')
 lines[at:at]=[
  '- v3 native-01在600秒上限前只完成8窗，classic不完整，退出124；保留原始结果，不计入最终性能结论。idle-01负载诊断的实际历时约44秒，不冒充严格3秒采样，也不用于性能验收。',
  '- native-02/03启动检查曾把Minecraft Java服务器误当作模组构建而退出，未启动AIR。已按进程可执行文件与完整参数区分；不关闭该服务，其CPU累计时间与内存列为背景数据，不能据进程存在断言卡顿原因。真正的Flex/FFDec和外部AIR仍阻止性能测试。',
  '- native-04两次在AIR前因可用内存低于5GiB中止；未降低启动门槛。最终性能轮还要求采样期间至少3GiB可用内存。functional-02曾因共享测试占用等待超时、尚未启动AIR，随后在单一登记的顺序验证组中继续。',
  '- 父层检查的环境包装脚本曾因字符串替换误中嵌入文本而出现语法错误，尚未启动该检查；改为仅在最后入口插入。safe-01-parent随后在第七组中途达到300秒上限，退出124。safe-02-parent复用74项相同冻结文件，等待上限600秒；不把前轮部分通过当作完整验收。',
  '- 顺序验证组转入native-04时，两个测试包装器重复传递timeout导致启动前TypeError，未启动AIR；改为显式参数签名。随后RConnect按用户另一项指令由DF0F更新至78C roomfix5，因此保留native-04未运行状态，另建native-05和functional-03。未将旧测试重标为新组合。',
  '- 早期失败/部分轮使用ABE2宿主；最终native-03/05/06及functional-03采用已更新的A796宿主。native-03为RC DF0F、native-05/06为RC 78C；准确差异见dependency-transition.json。每轮均在各自同一进程内轮换D42与候选；不把跨宿主、跨组合、跨时段变化直接归因RV。',
  '- 对方报告宿主A796颜色修复已验证；本侧独立核对实际文件指纹及新宿主功能。native-03实际加载ModLoader BD71（v2.4），不含FrameRecorder；native-05/06则加载新部署的2050，实际包含并运行记录器。不能把新记录器作为早期轮次变慢的原因；输入及telemetry.json均已额外绑定。',
  '- 组内一次汇总因其它目录的同名package模块混入而失败；改为按绝对路径加载本轮模块后重新只读汇总，保留原游戏结果。',
  '- native-05只读取得测试进程策略ControlMask=0、StateMask=0，表示仍由系统管理，不能据此证明具体CPU频率或降速原因。随后参照已核对原报告指纹的KB-000071 r1，native-06仅给自建测试进程设置并读回HighQoS（1/0），生产启动器、玩家进程、电源计划均未改。进程退出后该设置结束。固定百万次运算置于采样窗口前后，24个校验和均437500，耗时2–4ms。与普通轮次的绝对差异不是本轮严格A/B/A因果证明。',
  '- 进程策略读取与设置依据微软[GetProcessInformation](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocessinformation)和[PROCESS_POWER_THROTTLING_STATE](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-process_power_throttling_state)。这里只约束测试环境，不把测试调度策略算作SWF性能修复。','']
 for line in (OUT/'candidate-03/result.txt').read_text(encoding='utf-8').splitlines():
  if line.startswith('LOAD ROW '):
   x=json.loads(line[9:]);a=x['baseline'];b=x['candidate'];lines.append(f'|{x["mode"]}|{["全亮","全暗","密集交界"][x["state"]]}|{x["count"]}|{statistics.mean(a):.2f}|{statistics.mean(b):.2f}|{sorted(a)[int(.95*(len(a)-1))]}/{sorted(b)[int(.95*(len(b)-1))]}|')
 lines+=['','## 原生六敌战斗','',
 '最终每轮12窗口，每窗120样本；完整已启用组合，off仅关闭RV。六名真实UnitMerc使用smg10，场景原生单位总数约151，并非只有六个单位。原生子弹、粒子、伤害和击退继续运行，无方向键驱动或逐帧传送。交换新旧顺序复测时单独列出，不能跨轮挑选有利数据。loc.firstObj总数包含多种对象，不称为子弹数；最大弹体数量保留在原始结果。原生世界和随机发射持续变化，同轮配对也不等于确定性重放。','',
 '|轮次|模式|版本|平均帧间隔ms|P95|max|RV更新均值ms|','|---|---|---|---:|---:|---:|---:|']
 for x in perf:lines.append(f'|{x["trial"]}|{x["mode"]}|{x["variant"]}|{x["interval"]["mean"]}|{x["interval"]["p95"]}|{x["interval"]["max"]}|{x["update"]["mean"]}|')
 lines+=['',decision['reason'],'',
 '## 功能与边界','',
 f'{proof["checks"]}项/组：360帧密集视觉严格像素相等，360帧房间边缘/六档模糊严格相等，311项原生特效与狮鹫恢复/遮挡检查，64组实际父层墙面/地板/逻辑及设置极值，36项准确包设置保存与两进程恢复。完整原生战斗{proof["native_windows"]}窗完成。','',
 '未声称达到关闭模组的整体流畅度或消除全部长帧。受控轮current最长218ms中RV更新7ms、classic最长285ms中RV更新5ms，其余时间不在RV更新函数内；这只定位计时范围，尚不能排除其绘制/分配的后续影响。用户精确存档现场未复现。开发树authority改动仅保留并做语法检查，本次六类生产包不含该接口。共享知识两层查询仍为partial，后续读回并应用KB-000071 r1；来源不足不等于没有经验。无玩家实例或真实存档写入。','',
 '## 部署与回退','',f'持续授权下安装并验证新版初始化、ModSettings注册、tick1/181/361。备份 `{receipt["backup"]}`；回退须先核对当前仍为本轮新指纹，再恢复备份，避免覆盖后续更新。宿主、配置及其它模组保护指纹未变。需正常保存并重启游戏。','',
 '[验证证据](effect-load-v0339-20261024/verified.json) · [部署回执](effect-load-v0339-20261024/deployment/receipt.json)。','']
 (MOD/REPORT).write_text('\n'.join(lines),encoding='utf-8',newline='\n')
 memory=f'> 2026-10-24 **D43 v0.33.9已部署**：在独立特效的原有采样中判断全亮/全暗，跳过不需要的模糊及辅助图，不重复classic采样；边界与宽滤镜沿用原算法。{proof["checks"]}项/组、{proof["native_windows"]}原生六敌战斗窗与正式启动通过。SHA {manifest["swf"]}，{manifest["bytes"]}B；准确源build/effect-load-v3-output/production-final/src，不含authority。两版失败方案与环境异常保留；受控测试RV更新current约少20%、classic约少6%，完整帧基本持平，最长帧未解决，测试调度策略未部署。[报告](../{REPORT})。\n\n'
 journal=f'## 2026-10-24 — D43密集特效单次采样优化\n\n- 否决逐格/整块预分类的重复成本，最终在原有采样内分类全亮/全暗，保留边缘算法与原生动画。\n- {proof["checks"]}项/组、{proof["native_windows"]}原生战斗窗通过，已部署{p.VERSION}，SHA {manifest["swf"]}。\n- [报告](../{REPORT})含完整性能数据、失败候选、测试异常和回退；外部WIP保留。\n\n'
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for name,entry in [('MEMORY.md',memory),('journal.md',journal)]:
  path=MOD/'state'/name;base=subprocess.check_output(['git','show','HEAD:state/'+name],cwd=MOD).decode('utf-8');work=path.read_text(encoding='utf-8-sig')
  def apply(s):
   if name=='journal.md':return entry+s
   s=re.sub(r'- 当前安装D42 v0.33.8；[^\n]+','- 当前安装D43 v0.33.9；独立特效单次采样跳过全亮/全暗区域多余模糊，遮挡与墙面保留；准确源build/effect-load-v3-output/production-final/src，不含authority。性能边界见顶部报告。',s,count=1)
   s=s.replace('## 4. 正在进行与停点\n\n','## 4. 正在进行与停点\n\n- D43已完成，当前无待跑测试；后续以D43准确生产源为基线。下方为历史停点。\n\n',1)
   return s.replace('\n\n','\n\n'+entry,1)
  path.write_text(apply(work),encoding='utf-8',newline='\n');(owned/name).write_text(apply(base),encoding='utf-8',newline='\n')
 path=MOD/'decisions/decisions.md';s=path.read_text(encoding='utf-8-sig');i=s.index('## D');s=s[:i]+'## D43：独立特效复用原有采样分类\n\n- 全亮/全暗区域跳过模糊与辅助图，混合边界和宽滤镜保留旧算法；不降低动画或视野刷新。\n- 已部署v0.33.9；被否决候选及完整性能边界见[报告](../'+REPORT+')。\n\n'+s[i:];path.write_text(s,encoding='utf-8',newline='\n')
 print('D43 report/archive ready',len(pins))
if __name__=='__main__':main()
