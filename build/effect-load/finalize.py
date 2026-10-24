from pathlib import Path
import json,shutil,subprocess,re,hashlib,statistics
import package as p
MOD,OUT=p.MOD,p.OUT
ARCHIVE='knowledge/experiments/effect-load-v0339-20261024';REPORT='knowledge/experiments/2026-10-24-effect-load.md'
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8-sig'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
 receipt=read('deployment/receipt.json');assert receipt['result']=='PASS'
 proof=read('verified.json');perf=read('performance.json');manifest=read('production-final/manifest.json');decision=read('performance-decision.json');assert decision['accepted']
 dest=MOD/ARCHIVE;assert not dest.exists();dest.mkdir(parents=True)
 for name in ['reproduction-01','candidate-01','edges-01','functional-01','native-01','native-02','native-03','parent-01','production-final','development-check','deployment']:
  for f in (OUT/name).rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   rel=f.relative_to(OUT/name)
   if rel.parts[0] in ['mods','Rooms','data','music','snd','runtime','runtimes']:continue
   if f.suffix not in ['.json','.log','.txt','.as','.png'] and not(name=='production-final' and f.name=='RealisticVisionMod.swf'):continue
   if f.name in ['lang.xml','launcher_text.xml'] or f.name.startswith('text_'):continue
   target=dest/name/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
 for name in ['inputs.json','performance.json','performance-decision.json','verified.json','development.patch']:shutil.copyfile(OUT/name,dest/name)
 (dest/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8')
 pins={f.relative_to(dest).as_posix():sha(f) for f in dest.rglob('*') if f.is_file()};p.run.save(dest/'archive.json',pins)
 lines=['被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching；remains-mod-memory','技能归属：用户级与Remains工作区级','测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision','',
 '# D43：密集特效的多余遮罩开销','',f'已部署 **{p.VERSION}**，{manifest["bytes"]}B，SHA256 `{manifest["swf"]}`。D42准确生产源派生，仅替换RV。','',
 '用户反馈敌人、子弹和弹道较多时，遮罩内外都明显卡顿。D42的applyWorldVisual在判断全亮前已按每个移动包围盒创建/刷新/模糊位图。100/500移动视觉对象的隔离复现确认数量上升带来额外开销，500个全亮对象在30次更新内累计1065个区域栅格。','',
 '候选先按每帧视野版本缓存实际子格的全亮/全暗/混合分类。完整支持区全黑时直接用空遮罩；全亮且足够远离滤镜边界时保留原生绘制；混合、房间边界和较宽滤镜均回退原算法。仍每帧检查对象及真实包围盒，不减刷新频率，不删除动画，不改弹体物理或原生探索。','',
 '## 同输入局部开销','',
 '两版本在同一AIR进程内交替处理完全相同的位置、旋转和视野。以下只计独立视觉遮挡函数，不是完整FPS；绘图对比在计时外。','',
 '|模式|区域|对象数|D42均值ms|候选均值ms|区域栅格D42/候选|','|---|---|---:|---:|---:|---|']
 for line in (OUT/'candidate-01/result.txt').read_text(encoding='utf-8').splitlines():
  if line.startswith('LOAD ROW '):
   x=json.loads(line[9:]);lines.append(f'|{x["mode"]}|{["全亮","全暗","密集交界"][x["state"]]}|{x["count"]}|{statistics.mean(x["baseline"]):.2f}|{statistics.mean(x["candidate"]):.2f}|{x["rasters"][0]}/{x["rasters"][1]}|')
 lines+=['','全亮/全暗显著减少不必要的位图；密集交界保持原渲染，新增分类有少量成本，不声称所有负载都变快。','',
 '## 原生六敌战斗','',
 '两轮分别交换新旧顺序，每轮12窗口，每窗240样本；完整已启用组合，off仅关闭RV。六名真实UnitMerc使用smg10，原生子弹、粒子、伤害和击退继续运行，无逐帧传送。首轮步行夹具因六敌将玩家推出单敌路线而失败，未用于性能结论；随后改为不驱动方向键、自然受击的站立战斗。原生世界与随机发射持续变化，配对均值不是确定性因果；全局进程仅启停采样，运行时只看自有实例与内存。','',
 '|轮次|模式|版本|平均帧间隔ms|P95|max|RV更新均值ms|','|---|---|---|---:|---:|---:|---:|']
 for x in perf:lines.append(f'|{x["trial"]}|{x["mode"]}|{x["variant"]}|{x["interval"]["mean"]}|{x["interval"]["p95"]}|{x["interval"]["max"]}|{x["update"]["mean"]}|')
 lines+=['',decision['reason'],'',
 '## 功能与边界','',
 '1131项/组：360帧密集视觉严格像素相等、360帧房间边缘/六档模糊严格相等、311项原生特效与狮鹫恢复/遮挡检查、64组实际父层墙面/地板/逻辑及设置极值、36项准确包设置保存与两进程恢复。密集基线夹具退出请求后多回调两次，前360组及额外结果均通过；边缘夹具已及时移除帧监听。部分可见激光PNG已目检，可见段仍显示。','',
 '完整战斗24窗全部完成。最大长帧、其它模组开销及密集交界成本仍存在；未声称原版流畅度或玩家精确场景已验。开发树保留authority显示适配，编译仅语法检查，本次发布不含该接口。共享知识两层查询partial且无直接匹配，不等于无相关经验；没有操作玩家实例或真实存档。','',
 '## 部署与回退','',f'本机持续授权下安装并验证新版初始化、ModSettings注册、tick1/181/361。备份 `{receipt["backup"]}`；回退须先核对当前仍为本轮新指纹，再恢复该文件，避免覆盖后续更新。宿主、配置、其它模组保护指纹未变。用户正常保存并重启生效。','',
 f'[验证证据](effect-load-v0339-20261024/verified.json) · [部署回执](effect-load-v0339-20261024/deployment/receipt.json)。','']
 (MOD/REPORT).write_text('\n'.join(lines),encoding='utf-8',newline='\n')
 memory=f'> 2026-10-24 **D43 v0.33.9已部署**：先分类全亮/全暗支持区，避免独立特效的多余区域位图；混合/边界/宽滤镜仍走原算法。1131项/组、24原生六敌战斗窗与正式启动通过。SHA {manifest["swf"]}，{manifest["bytes"]}B；准确生产源build/effect-load-output/production-final/src，不含authority。局部全亮/暗开销明显下降，密集交界和整体长帧仍有边界。[报告](../{REPORT})。\n\n'
 journal=f'## 2026-10-24 — D43密集特效开销修复\n\n- 全亮前已生成遮罩的顺序导致多余位图。改为保守的完整支持区分类，保留原生动画与边缘算法。\n- 1131项/组、24原生六敌战斗窗通过，已部署{p.VERSION}，SHA {manifest["swf"]}。\n- [报告](../{REPORT})保留局部收益、两轮整体数据、步行夹具失败与回退路径；外部WIP保留。\n\n'
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for name,entry in [('MEMORY.md',memory),('journal.md',journal)]:
  path=MOD/'state'/name;base=subprocess.check_output(['git','show','HEAD:state/'+name],cwd=MOD).decode('utf-8');work=path.read_text(encoding='utf-8-sig')
  def apply(s):
   if name=='journal.md':return entry+s
   s=re.sub(r'- 当前安装D42 v0.33.8；[^\n]+','- 当前安装D43 v0.33.9；独立特效全亮/全暗区域跳过位图生成，遮挡与墙面保留；准确源build/effect-load-output/production-final/src，不含authority。性能边界见顶部报告。',s,count=1)
   s=s.replace('## 4. 正在进行与停点\n\n','## 4. 正在进行与停点\n\n- D43已完成，当前无待跑测试；后续以D43准确生产源为基线。下方为历史停点。\n\n',1)
   s=s.replace('当前D42 v0.33.8需用户正常保存并重启加载','当前D43 v0.33.9需用户正常保存并重启加载')
   return s.replace('\n\n','\n\n'+entry,1)
  path.write_text(apply(work),encoding='utf-8',newline='\n');(owned/name).write_text(apply(base),encoding='utf-8',newline='\n')
 path=MOD/'decisions/decisions.md';s=path.read_text(encoding='utf-8-sig');i=s.index('## D');s=s[:i]+'## D43：独立视觉先做保守的全亮/全暗分类\n\n- 完整支持区证明一致才跳过位图，混合边界与宽滤镜保留旧算法；不降低动画或视野刷新。\n- 已部署v0.33.9；局部收益、倒序原生复测和限制见[报告](../'+REPORT+')。\n\n'+s[i:];path.write_text(s,encoding='utf-8',newline='\n')
 print('D43 report/archive ready',len(pins))
if __name__=='__main__':main()
