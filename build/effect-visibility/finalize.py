from pathlib import Path
import json,hashlib,shutil,subprocess,re
import package as p
MOD,OUT=p.MOD,p.OUT
ARCHIVE='knowledge/experiments/effect-visibility-v0338-20261023'
REPORT='knowledge/experiments/2026-10-23-effect-visibility.md'
def read(rel):return json.loads((OUT/rel).read_text(encoding='utf-8'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
def main():
 receipt=read('deployment/receipt.json');assert receipt['result']=='PASS'
 proof=read('verified.json');perf=read('performance.json');manifest=read('production-final/manifest.json')
 dest=MOD/ARCHIVE;assert not dest.exists();dest.mkdir(parents=True)
 names=['reproduction-01','functional-01','functional-02','functional-03','functional-final','functional-optimized','unit-render-01','safe-exact-parent','safe-final-parent','native-01','native-02','native-final','native-optimized','native-final-02','production-final','deployment','development-check']
 for name in names:
  for f in (OUT/name).rglob('*'):
   if not f.is_file() or 'storage' in f.parts:continue
   rel=f.relative_to(OUT/name)
   if rel.parts[0] in ['mods','Rooms','data','music','snd','runtime','runtimes']:continue
   if f.suffix not in ['.json','.log','.txt','.as','.png'] and not(name=='production-final' and f.name=='RealisticVisionMod.swf'):continue
   if f.name in ['lang.xml','launcher_text.xml'] or f.name.startswith('text_'):continue
   target=dest/name/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
 for name in ['inputs.json','performance.json','performance-decision.json','verified.json','development.patch']:shutil.copyfile(OUT/name,dest/name)
 (dest/'.gitattributes').write_text('* -text -diff\n',encoding='utf-8')
 pins={f.relative_to(dest).as_posix():sha(f) for f in dest.rglob('*') if f.is_file()};(dest/'archive.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
 lines=['被测技能：diagnosing-bugs；remains-runtime-debug；remains-auto-testing；remains-mod-build；remains-release-gate；remains-swf-patching；remains-mod-memory',
 '技能归属：用户级与Remains工作区级','测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision','',
 '# 2026-10-23 D42：暗区弹道与狮鹫肢体泄露','',
 f'已部署 **{p.VERSION}**，{manifest["bytes"]} B，SHA256 `{manifest["swf"]}`。仅替换RV，原D41安装6DBBAE60…作为回退基线；生产来源为D41准确快照，不含authority或D40未发布候选。','',
 '## 原因与处理','',
 '原生Bullet/PhisBullet/SmartBullet和Emitter生成的Part是独立场景对象，没有经过手持武器遮挡。UnitMerc的arm为internal字段，显示对象另挂在visObjs；旧scanArms靠64像素内隐藏/可见单位猜归属，每三帧处理，附近存在可见单位时会误放行。原生子武器虽已按身体处理，枪口伸出身体分类范围时仍可能泄露。',
 '修复按每个实际视觉的世界范围取原有逻辑视野，独立遮罩、共享同区域栅格，并每帧检查动画/挂载。移除模糊的近邻手臂猜测，只识别原生visualGrifArm类。可见身体上的敌方长枪也独立裁切；子弹按当前位置显示，射手在暗处并不会使进入视野的弹体消失。',
 '不改visible/alpha、位置、对象链、弹体step、碰撞、伤害、AI、原生visi/t_visi、地图或传送判定。完全可见内容维持原生绘制；完整支持区alpha全零才采用空遮罩，免去该特效的位图缓存。部分可见仍沿用原软边。切模式/房间、摘除和原生死亡隐藏均恢复或保留。',
 'Part没有可访问的射手归属，本次按世界位置处理原生临时粒子，包含相同类型的环境粒子；可见区不变，暗区粒子不再显示。已有外部mask优先，不覆盖其它模组自有遮罩；任意第三方特效子类和玩家精确存档未穷尽验证。','',
 '## 验证与失败记录','',
 '1000项/组：311项原生视觉检查（两模式、手臂/枪械/子弹/激光/火花/爆炸/弹壳，暗区归零、明区逐像素一致、部分显示、重入/死亡/移除/重设visible、身体亮而枪口暗）；589项原身体/血条/武器实际渲染检查；64组原生墙面/地板/逻辑与参数极值、镜头缩放严格一致；36项准确生产字节设置保存与跨进程恢复。589项之后只有world visual方法修改，applyMask和refreshMask按方法全文匹配复用证据。',
 '311项使用原生视觉和真实发射器，逻辑场可控以隔离遮罩；长枪案例额外设置原生武器位置并调用animate以覆盖身体外缘，不声称复现用户精确站位。实战另运行12个完整组合的方向键跑动/狮鹫射击窗口，每窗240采样帧。子弹进入视野的显示与射手身份无关由位置遮罩及重入检查覆盖。',
 '首次爆炸反例未执行原生粒子初始化，测试失败后补step；完全可见区强制缓存导致像素变化，改为明区透传；首次狮鹫战斗218/240贴地触发旧夹具220门槛，改为>=200；后续原生击退使Y偏离平台9.03px，超过旧步行夹具8px限制，最终仍逐帧限定同一平台一格40px并记录最大偏移，不用传送消除击退。另真实战斗发现撤销遮罩使显示列表缩短，修为逆序遍历。这些失败均保留。',
 '第一轮完整战斗中，修复本身新增开销，因此增加仅对全零栅格使用空遮罩的快路径。它检查完整支持区，避免遗漏原生发光外延；旧production是筛选中间产物，不部署。','',
 '开发树合入时，初次精确补丁因既有authority写入与逐帧守卫不同而停止，源码未被部分修改。按原接口适配这些显示写入后编译通过；开发树仅做语法检查，新增视觉与authority联机行为未验，不作为本次发布来源。','',
 '## 最终完整帧间隔（毫秒）','',
 '同进程各模式off/candidate/baseline/baseline/candidate/off，全部其它已启用模组保留，off仅关闭RV。每行两窗共478个间隔。原生世界持续变化且有暖机差异，不能把均值波动视为确定因果，也不能把局部RV更新换算FPS。','',
 '|模式|版本|平均帧间隔|P95|最大|>100ms次数|RV更新均值|','|---|---|---:|---:|---:|---:|---:|']
 for row in perf:
  a=row['interval'];lines.append(f'|{row["mode"]}|{row["variant"]}|{a["mean"]}|{a["p95"]}|{a["max"]}|{a["over100"]}|{row["update"]["mean"]}|')
 lines+=['','最终current平均帧间隔64.046→64.741ms，classic67.163→66.933ms，均值与旧版基本持平；RV自身更新分别增加约2.35/3.18ms。P95均较低，但classic最大帧161→317ms，不得据均值声称长帧已解决。接受本次正确性修复并如实保留额外成本；未达到关闭RV的流畅度。决定与原始指纹见performance-decision.json，不以功能绿灯代替性能判断。','',
 '## 部署、隔离与回退','',
 f'本机持续授权下通过门禁，备份`{receipt["backup"]}`，原子替换准确生产文件，正式路径新应用ID验证init/ModSettings注册/tick1/181/361。宿主、其它模组、配置和玩家存储保护指纹未改；自己的测试进程/描述符清理。已有游戏正常保存并重启生效。',
 '生产源`build/effect-visibility-output/production-final/src`；六个发布类，不含fe存根或authority。回退先核对仍是本轮新哈希，再恢复本轮备份；不覆盖后续更新。',
 f'[验证证据](effect-visibility-v0338-20261023/verified.json) · [部署回执](effect-visibility-v0338-20261023/deployment/receipt.json)。','',
 '技能回流：使用登记串行等待其它模组，独立隐藏桌面与唯一AIR存储；未用Ghost、未新增委托。确认了静态图片检查不能替代原生动态显示列表验证、全亮强制缓存会改变亚像素画面；失败记录及修正保留。','']
 (MOD/REPORT).write_text('\n'.join(lines),encoding='utf-8',newline='\n')
 memory=f'> 2026-10-23 **D42 v0.33.8已部署**：按世界位置裁切原生弹体/激光/粒子、狮鹫独立手臂和身体外敌方武器；明区原生绘制、全零支持区空遮罩。1000项/组及12完整组合跑动射击窗、正式init/注册/tick1/181/361通过。SHA {manifest["swf"]}，{manifest["bytes"]}B；准确源build/effect-visibility-output/production-final/src。尚未达原版流畅度、第三方自有遮罩优先。[报告](../{REPORT})。\n\n'
 journal=f'## 2026-10-23 — D42弹道与狮鹫手臂/武器遮挡修复\n\n- 原生独立特效遗漏、近邻猜归属和身体外枪口漏裁切；改为每帧按世界位置裁切，共享栅格，明区透传，全黑空遮罩。原生逻辑/伤害/动画不改。\n- 1000项/组、12完整组合战斗窗及正式路径启动通过；部署{p.VERSION}，SHA {manifest["swf"]}，备份{receipt["backup"]}。\n- [报告](../{REPORT})记录性能开销、失败修正与边界。四项authority WIP保留，生产源不含authority。\n\n'
 owned=OUT/'owned-state';owned.mkdir(exist_ok=False)
 for name,insert in [('MEMORY.md',memory),('journal.md',journal)]:
  path=MOD/'state'/name;base=git('show','HEAD:state/'+name).decode('utf-8');working=path.read_text(encoding='utf-8-sig')
  def apply(text):
   if name=='journal.md':return insert+text
   text=text.replace('狮鹫internal手臂、','')
   text=re.sub(r'- 当前安装D41 v0.33.7；[^\n]+','- 当前安装D42 v0.33.8；原生特效与狮鹫独立视觉按位置裁切。准确生产源build/effect-visibility-output/production-final/src；不含authority。性能仍未达到关闭RV，详见顶部报告。',text,count=1)
   text=text.replace('## 4. 正在进行与停点\n\n','## 4. 正在进行与停点\n\n- D42已完成验证、部署及收尾，当前无待跑RV实例；以下均为历史停点，不自动重跑。后续反馈以D42准确生产源为基线，不能混入D40候选或authority。\n\n',1)
   text=text.replace('## 6. 下一步\n\n','## 6. 下一步\n\n- 当前D42 v0.33.8需用户正常保存并重启加载。原生特效与狮鹫泄露已修复；后续长帧仍需实测归因。下方旧版本行动仅留历史，不据此回退当前安装。\n\n',1)
   text=text.replace('- 最新发布：state/deployment-v0323-', '- 历史D32发布：state/deployment-v0323-',1)
   return text.replace('\n\n','\n\n'+insert,1)
  path.write_text(apply(working),encoding='utf-8',newline='\n');(owned/name).write_text(apply(base),encoding='utf-8',newline='\n')
 decision=MOD/'decisions/decisions.md';text=decision.read_text(encoding='utf-8-sig');i=text.index('## D')
 entry='## D42：独立特效与狮鹫肢体按世界位置遮挡\n\n- 不通过邻近单位猜归属、不按射手隐藏整条弹道；复用原视野栅格，独立mask，原生动画和逻辑照常。\n- 明区透传以保留亚像素画面；全零支持区空遮罩；部分可见保持软边。保留外部自有mask。\n- 已部署v0.33.8；1000项/组与12原生射击窗通过。[证据](../'+REPORT+')。\n\n'
 decision.write_text(text[:i]+entry+text[i:],encoding='utf-8',newline='\n')
 print('D42 archive/report/state ready',len(pins))
if __name__=='__main__':main()
