"""Record verified release evidence; stage only this task's memory additions."""
from pathlib import Path
import hashlib,json,shutil,subprocess
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/wall-performance-output'
EV=MOD/'knowledge/experiments/wall-performance-v0321-20261016'
receipt=json.loads((OUT/'deployment/receipt.json').read_text())
proof=json.loads((OUT/'final-checks.json').read_text())
assert receipt['result']=='PASS' and proof['status']=='PASS'
new=proof['candidate_sha256'].upper();old=receipt['old_sha256'].upper();backup=receipt['backup']
assert hashlib.sha256((MOD/'release/RealisticVisionMod.swf').read_bytes()).hexdigest()==receipt['new_sha256']
target=MOD/'state/deployment-v0321';target.mkdir(exist_ok=True)
for name in ['receipt.json','preflight.json','formal-runtime.txt','formal-output.txt']:
    shutil.copyfile(OUT/'deployment'/name,target/name)
for p in target.glob('*.txt'):
    p.write_text('\n'.join(line.rstrip() for line in p.read_bytes().decode('utf-8').replace('\r','').splitlines()).rstrip()+'\n',encoding='utf-8')
shutil.copyfile(OUT/'final-checks.json',target/'final-checks.json')
report=MOD/'knowledge/experiments/2026-10-16-wall-performance.md'
previous=report.read_text(encoding='utf-8')
environment=previous[previous.index('## 环境问题：'):]
report.write_text(f'''被测技能：diagnosing-bugs 2026-10-08.1（C:/Users/hello/.agents/skills/diagnosing-bugs/SKILL.md）
技能归属：用户级；配合工作区 remains-mod-build、remains-auto-testing、remains-release-gate、remains-swf-patching、remains-mod-memory、remains-knowledge-contribution
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# D29：保持 D28 画面的墙面性能优化，已部署

用户本轮明确要求“在不影响视觉效果的前提下优化性能表现，并部署”。已安装 **v0.32.1-wall-performance，36,992B**，SHA256 `{new}`。准确生产源 `build/wall-performance-output/candidate/src` 从 D28 冻结生产线派生；只替换墙面 helper 和版本号，保留改键、多语言、场景兼容及共享探索，未混入 authority WIP。部署与回退见 [回执](../../state/deployment-v0321-2026-10-16.md)。

视觉基准为 D28 v0.32.0（65B6BF90…46BE7217），并非浏览器停留的 D27 页面。保留原生墙芯和渐变、亮边随视野、防溢出；“已探索墙边常亮”仍可选、默认关闭，已有保存值继续生效。

## 实现与取舍

每帧仍核对几何、探索、光照、前景材质及镜头。墙形不变时复用各墙边的采样位置和权重，按原来的整数取整与最大值规则更新光照；仅清理有采样的格点，复用数值缓冲区后批量写入位图。常亮墙面的局部图只在墙形或材质变化时重绘，移动地板雾与原雾继续更新。

没有改变 STEP、模糊强度、采样位置、亮度范围或刷新节奏；不写原生 visi/t_visi，不扩大逻辑视野、探索或敌人资格。精确差分以 D28 自身为基准，未使用其对更早墙面的1–3级轮廓容差。

最初的整图向量转换方案没有收益：同轮 classic 默认10.75→11.15ms，current12.08→12.18ms；分段计时指向整图遍历抵消了逐像素调用收益，已弃用。去掉该遍历后，阴影场更新阶段约节省0.3–0.5ms；再缓存常亮材质图。扩大到240帧后出现默认组峰值增高，未能唯一归因；最终改为复用光照数组，避免每次变化都分配整张向量。各阶段原始结果保留，不跨轮挑数比较。

## 验证

最终 **336 项通过**：严格差分68、恢复/凹口26、设置8、柔化与射线16、共享探索21、原生金属88、原生岩壁/半高墙89、准确生产字节两进程20。额外 **16组原生雾层图的变化像素数全部为0，最大差0**。图像不是空白场，均包含0–255范围；代表图已目检。没有声称所有真实存档、任意材质或全部亚像素输入都被穷尽。

| 范围 | 验证内容 |
|---|---|
| 人工真实AIR差分 | 动态光照、NaN恢复、探索开关、半高墙、原地破坏、透明/重叠/隐藏/带颜色变换材质、视口变化、0.75/1/1.25/1.5倍缩放及重置，输出严格一致 |
| 原生房间 | 金属与岩壁两场景、两模式、常亮开/关、上下两位置；六段路线的原生记录、FOV、探索和敌人分类不变；16组最终雾层图严格一致 |
| 功能隔离 | 1000条缓存/实时射线，门/水/破墙即时更新、敌人遮蔽、共享探索与本地判定分离 |
| 生产字节 | 同一36992B SWF两进程验证默认关闭、即时保存/重读、模式及快捷键页、tick181；FFDec完整6类，无fe.*存根或authority类 |
| 正式启动 | 从根application.xml指向的pfe.swf及正式release加载；新版init、ModSettings注册、tick1/181/361通过，测试PID55800退出、描述符删除 |

数据与源指纹见 [final-checks.json](wall-performance-v0321-20261016/final-checks.json)、[pixels.json](wall-performance-v0321-20261016/pixels.json)、[计时原始样本](wall-performance-v0321-20261016/benchmark-raw.json)。源码与各最终测试副本只存在访问级别/隔离配置路径的预期差异，自动核对通过；没有拿中间候选结果替代最终产物。

## 性能结果与边界

同一进程四组轮换，正式优化编译、不插分段计时探针，每模式每组240帧。以下是 **RV更新 + 雾层绘图**，不含原生物理、网络和战斗，不可换算完整FPS。两次原生场景截图另外执行，未混入计时。

| 模式/常亮 | D28均值 → 新版 | P95旧 → 新 | 最大值旧 → 新 | 均值降幅 |
|---|---:|---:|---:|---:|
| classic 关闭 | 18.73 → 18.05ms | 27 → 25ms | 37 → 32ms | 3.6% |
| current 关闭 | 20.89 → 19.72ms | 25 → 24ms | 51 → 37ms | 5.6% |
| classic 开启 | 32.21 → 30.17ms | 46 → 42ms | 116 → 96ms | 6.3% |
| current 开启 | 35.44 → 32.28ms | 43 → 39ms | 93 → 75ms | 8.9% |

本轮四组均值、P95和最大值都下降；开启常亮仍有75–96ms的长帧，不能说卡顿已消除。不同轮绝对耗时变化较大，只按同轮配对判断收益。最终默认组的下降较小，结论是减少了一部分重复渲染工作，不是全面性能问题已解决。大型连续场景、真实玩家存档和高负载联机不在此轮性能覆盖中。

RConnect提供的历史2da241821f组合仍有七个密集窗口低于80帧/8秒；该信息是协作回报，本轮没有复跑该联机门槛，也不归因于RV。共享vis/hpbar的MirrorHitUnit重复处理只是线索，本轮未更改其对象语义。

## 运行环境、失败记录与部署

与CS/RConnect协调后串行使用隐藏AIR，唯一应用ID、独立存储；没有操作玩家实例或写真实pfe存档。测试宿主已冻结为CS 0.7.0安装后的根2A466248…，组合指纹见runtime-inputs.json；测试素材副本只加载探针。正式路径启动使用当前完整安装。部署仅更换RV，宿主、清单、配置和其他模组共18个保护指纹在前后核对一致。

最终240帧基准首轮因旧探针的300次Timer上限而中止（bench-final），不是游戏或候选超时；保留失败JSON，修正基准上限为700后重跑。一次编译后的状态打印因相对路径异常而失败，编译本身成功，修正绝对输出路径后通过。FFDec无法建立其日志锁，但返回0并完整列出6类；未把此警告误判为SWF损坏。

16:06:22备份当前BAA版本后原子安装2E7150CF候选，独立正式启动通过；未覆盖配置。备份 `{backup}`，SHA256 `{old}`。回退只恢复这一份RV，不使用旧的CS/WB联合回滚脚本。AIR窗口已交还RConnect，后续联合验收由其在新安装指纹下继续。

工具入口 [build/wall-performance/README.md](../../build/wall-performance/README.md)。本轮实际使用诊断技能的假设—分段测量—严格差分—弃用无效方案流程；未修改技能。精确调用环境经验已归档 **KB-000102 r1**；首个知识写入因README来源越界失败，保留原区证据作为唯一来源后成功，未扩大来源边界。

'''+environment,encoding='utf-8')
(MOD/'state/deployment-v0321-2026-10-16.md').write_text(f'''# RealisticVision v0.32.1 部署回执

2026-10-16 16:06:22（Asia/Shanghai）。用户明确要求不改变视觉效果地优化并部署；已完成。

- 安装：`release/RealisticVisionMod.swf`，v0.32.1-wall-performance，36,992B。
- SHA256：`{new}`。
- 来源：`build/wall-performance-output/candidate/RealisticVisionMod.swf`；源目录为同级`src`，从D28冻结生产线派生，不含authority工作。
- 336项、68组人工像素差分与16组原生雾层逐像素一致。准确生产字节两进程20项通过；正式路径init、设置注册、tick1/181/361通过。测试PID55800关闭、描述符清理。
- 只替换RV；根pfe2A466248…、CS70C06879…、WBDF9AA072…、LAD514A7671…和清单/配置等18项指纹未变。正式校验保存于[receipt.json](deployment-v0321/receipt.json)。
- 常亮默认关闭，保留既有保存值；墙芯、渐变、防溢出及原视野/探索规则保持。平均渲染开销比D28减少约4%–9%，非完整FPS；高负载联机未在本轮验收。

## 单模组回退

备份：`{backup}`，SHA256 `{old}`。核对当前安装仍为上方2E7150CF、备份仍BAA后，只将备份恢复至`release/RealisticVisionMod.swf`，再保存并正常重启游戏。若之后已有新部署，先重新核对，不盲目覆盖。不要执行此前CS/WB联合回滚。

用户游戏未被关闭；下一次正常重启才会加载新版本。细节见[实验报告](../knowledge/experiments/2026-10-16-wall-performance.md)。
''',encoding='utf-8')
summary=f'> 2026-10-16 16:06:22 D29 **已部署**：v0.32.1-wall-performance，36,992B，SHA256 `{new}`。保持D28原生墙芯/渐变和防溢出；常亮默认关闭并保留保存值。复用墙边采样、光照缓冲区与常亮墙面图；336项、68组人工差分与16组原生雾层严格相同，准确生产字节及正式路径启动通过。相比D28同进程平均渲染开销减少约4%–9%，非完整FPS，长帧/密集联机仍有边界。仅改RV，authority WIP保留。详见[报告](../knowledge/experiments/2026-10-16-wall-performance.md)和[回退记录](deployment-v0321-2026-10-16.md)。'
def memory(s):
    lines=s.splitlines()
    idx=next(i for i,l in enumerate(lines) if l.startswith('> 2026-10-16 D28候选完成'))
    lines[idx]=summary;s='\n'.join(lines)+'\n'
    start=s.index('- D28候选完成：');end=s.index('\n',start)
    s=s[:start]+'- D29已部署2E7150CF…8907A10：336项通过、16组原生雾层差0。保持D28视觉；正式路径新版init/设置注册/tick1/181/361通过。当前无RV测试实例，AIR已归还RConnect。'+s[end:]
    start=s.index('- D28准确生产源在');end=s.index('\n',start)
    s=s[:start]+'- D29准确生产源与已部署字节在build/wall-performance-output/candidate；脚本入口build/wall-performance/README.md。禁止用含authority的HEAD整包部署，禁止重建覆盖冻结候选。D28旧候选/实验保留。'+s[end:]
    start=s.index('- D28默认路径平均');end=s.index('\n',start)
    s=s[:start]+'- D29最终同进程240帧：关闭常亮classic18.73→18.05ms、current20.89→19.72ms；开启32.21→30.17ms、35.44→32.28ms。P95和峰值本轮均下降，开启仍有75–96ms长帧；不能换算完整战斗FPS。真实大图/玩家存档与密集联机未验。'+s[end:]
    start=s.index('1. D28候选未部署');end=s.index('\n3. 后续优先',start)
    s=s[:start]+f'1. D29已按本轮授权部署，用户保存并正常重启生效；无需重复部署或等待新授权。\n2. 本次仅用`{backup}`回退至BAA；核对指纹后只恢复RV。详情见deployment-v0321-2026-10-16.md。'+s[end:]
    s=s.replace('保留D28视觉目标、D22记录隔离','保留D29严格等价于D28的视觉目标、D22记录隔离')
    s=s.replace('## 7. 深入了解与复验\n','## 7. 深入了解与复验\n\n- D29最新入口：knowledge/experiments/2026-10-16-wall-performance.md、state/deployment-v0321-2026-10-16.md、build/wall-performance/README.md；KB-000102记录本轮精确调用护栏经验。\n')
    return s
entry='''## 2026-10-16 — D29墙面性能优化已部署

- 用户授权：保持既定视觉效果优化性能，并部署；复用既有授权，无重复确认。
- 实现：墙形采样缓存、复用光照数值缓冲、常亮墙面图缓存；不降刷新、保留D28墙芯/渐变与防溢出、默认关闭和原设置。全图转换无收益已弃用；扩大样本后针对分配改用缓冲复用，未武断归因峰值。
- 验证：336项、68组人工差分及16组原生雾层严格相同；正式优化编译的同进程240样本，默认均值约降低4%–6%、开启约6%–9%，P95/峰值此轮均降。非完整FPS，长帧与高负载联机未解决；详见2026-10-16-wall-performance报告和D29。
- 部署：准确生产包2E7150CF…8907A10（36992B）替换BAA，正式路径新版init、设置注册及tick1/181/361通过，测试退出。备份和单模组回滚见deployment-v0321-2026-10-16.md；其余18个保护指纹未变。主源码生产线62085FEF…C5EF81，未混入authority。
- 收尾：AIR已交回RConnect，源代码/工具/证据/回执一并提交；既有4个外部WIP保留。精确调用误拦方法已归档KB-000102 r1，未改变护栏或来源权限。

'''
owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
for path,transform in [('state/MEMORY.md',memory),('state/journal.md',lambda s:entry+s)]:
    file=MOD/path;file.write_text(transform(file.read_text(encoding='utf-8-sig')),encoding='utf-8')
    original=subprocess.check_output(['git','show','HEAD:'+path],cwd=MOD).decode('utf-8')
    data=transform(original).encode('utf-8');(owned/Path(path).name).write_bytes(data)
    blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=data,cwd=MOD).decode().strip()
    subprocess.check_call(['git','update-index','--cacheinfo','100644,'+blob+','+path],cwd=MOD)
print('Verified report, deployment receipt and owned memory changes recorded')
