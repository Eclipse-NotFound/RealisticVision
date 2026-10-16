被测技能：diagnosing-bugs 2026-10-08.1（C:/Users/hello/.agents/skills/diagnosing-bugs/SKILL.md）
技能归属：用户级；配合工作区 remains-mod-build、remains-auto-testing、remains-release-gate、remains-swf-patching、remains-mod-memory、remains-knowledge-contribution
测试工作区：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision

# D29：保持 D28 画面的墙面性能优化，已部署

用户本轮明确要求“在不影响视觉效果的前提下优化性能表现，并部署”。已安装 **v0.32.1-wall-performance，36,992B**，SHA256 `2E7150CF415355C2D7B809689AAC3C4CA0BACBB5F6D8770066A6E887D8907A10`。准确生产源 `build/wall-performance-output/candidate/src` 从 D28 冻结生产线派生；只替换墙面 helper 和版本号，保留改键、多语言、场景兼容及共享探索，未混入 authority WIP。部署与回退见 [回执](../../state/deployment-v0321-2026-10-16.md)。

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

16:06:22备份当前BAA版本后原子安装2E7150CF候选，独立正式启动通过；未覆盖配置。备份 `build/backups/before-wall-performance-20261016-160622-78a9d0/RealisticVisionMod.before.swf`，SHA256 `BAA48289D9CF86F64CFF53B4734032AD29C89C3AC1704DB2D89038D4B8DB4275`。回退只恢复这一份RV，不使用旧的CS/WB联合回滚脚本。AIR窗口已交还RConnect，后续联合验收由其在新安装指纹下继续。

工具入口 [build/wall-performance/README.md](../../build/wall-performance/README.md)。本轮实际使用诊断技能的假设—分段测量—严格差分—弃用无效方案流程；未修改技能。精确调用环境经验已归档 **KB-000102 r1**；首个知识写入因README来源越界失败，保留原区证据作为唯一来源后成功，未扩大来源边界。

## 环境问题：SWF 只读来源复制误拦

本轮冻结 CS 更新后的宿主时，含 `write_text` 与 SWF 字面路径的命令被 `binary-swf-use-release-pipeline` 拦截。该命令只读取正式宿主并写本模组测试副本；没有修改原宿主。未更换工具绕过，也未禁用/修改 hook。

已核对 `C:/Users/hello/.codex/hooks/zcode-migration/README.md`、`codex-guard.ps1` 及 CS 刚成功使用的 `build/generated/grant-v07-probe.json`。本客户端的事件为：`session_id` 等于当前线程 ID，`cwd` 为根目录 Windows 绝对路径，`tool_name` 为 `Bash`，`tool_input` 仅包含原始 `command`（本次命令未指定 workdir）。不能直接拿 functions.exec 的整个 JS 载荷或 exec_command 的 cmd 键代替。

依据用户本轮既有优化/部署授权，通过受审查的提权调用向现有授权台账追加一个当前会话、8分钟有效的精确摘要；写前比较台账原文，保留其他条目。摘要由现有 Get-GuardDigest 计算，`fdc4356d05efaeba400fbe5816d737a57d0e2c3e26f647a33525ed795480ec58`；同一条实际复制命令随后正常通过。事件在 `build/wall-performance-output/snapshot-grant-event.json`，新宿主指纹在 `runtime-inputs.json`。此为一次具体环境验证，不增加未来授权，不证明其他客户端或含 workdir 的适配形状相同。
