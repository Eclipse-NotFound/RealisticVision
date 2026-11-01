被测技能：diagnosing-bugs（2026-10-08.1）；remains-runtime-debug / remains-auto-testing / remains-release-gate（2026-10-27.1）；remains-mod-build；remains-mod-memory
技能归属：用户级 C:/Users/hello/.agents/skills/diagnosing-bugs；其余为本区 .agents/skills
测试工作区：D:/Program Files/Steam/steamapps/common/Remains

# v0.34.3：弹体边界裁剪与玩家眼部对齐

2026-11-02 已本机部署。用户报告：子弹尚有亮处动画却被提前遮罩；阴影视线与画面眼部不一致。

## 原因与修复

- v0.34.2 的 `applyWorldVisuals` 将普通 Bullet / SmartBullet / PhisBullet 与 Part 都交给 `fxCenterLit`。实际只检测 `vis.x/y` 注册点，不检查尾迹或图形占据范围。弹头已在暗侧而尾迹还在亮侧时，空 Shape 会让整条尾迹消失。原激光例外仅覆盖 `vis.laser`，不覆盖普通长弹迹。
- 三种弹体统一走现有空间软遮罩，保留 Part 火花、烟雾和弹壳的快速处理。动态弹体每次取实际外框，避免父对象不动、内部光束伸缩时复用旧外框。未改原生 visible、alpha、弹道或伤害。
- `computeFov` 原起点为 `(gg.X, gg.Y-gg.scY*.75)`；这是身体近似点。原生 `UnitPlayer` 有 `vis.osn.body.head.morda.eye`，本轮截图确认其中心落在显示眼部。转为角色父层世界坐标后供视野射线使用；不改游戏本体感知字段。
- 刷新条件改为眼部位移，站着转身、抬头低头也能触发刷新。保留已有位移阈值（当前模式默认4px，classic有3帧节奏），不声称零亚像素滞后。取点失败或小马图层隐藏时回退原起点。
- 墙角射线分类只能在眼部坐标相同的情况下复用；取消16px内沿用旧起点分类，避免旧墙角阴影抵消眼部定位修复。

准确生产源：`build/eye-boundary-output/candidate/src`，从当前 v0.34.2 的 `build/perf-20261102/src` 冻结派生。保留此前 locmem、门区、激光修复；未合入 `src/` 下 authority 开发线。可审阅增量 `build/eye-boundary/production.patch`，基线源指纹 `baseline-source.json`。

## 实证

独立随机 AIR ID、后台桌面、静音、共享登记；只加载本轮探针，未加载光与暗或其他玩法模组，未写玩家存档、配置或名单。

- `checks-06`：50项通过。原生玩家站立、左右朝向、三个头部角度；截图红圈为旧点、绿圈为新点。旧点偏离约17.19–22.15游戏像素；目检新点位于眼部。实际 `computeFov` 起点与显示部件几何一致；原地转身触发刷新。
- `checks-07`：771项通过（包含前项与隐藏小马图层回退）。current/classic、4/8子格、5个弹体位置，共20组对照。原生 Bullet 实例配可计数白条，经真实 dispatch 路径：弹头x=310/340、边界x=300时，旧版亮侧计数0，候选保留320/200像素；测量暗侧x≥350均0。这里远暗侧零像素不代表禁止原有边缘双线性柔化。
- 三种原生弹体 × 快速/原画质 × 60步持续绑定、同坐标改变自身几何，合计360步、720项检查。短图形位于暗侧时隐藏，增长到亮侧时露出应见部分，暗侧仍为0。它是受控绘制循环，不是360个原生战斗帧。
- `smoke-01`：未经 public 化或插桩的正式候选，经当前 ModLoader 加载；requested/ok一致、`init ok v0.34.3-eye-boundary`、tick 1/181、75个原生活动采样窗无错误。部署使用同一份文件。
- 本轮实际看过眼部定位及弹迹输出PNG。没有用户原存档的逐帧重放，也未重测密集战斗帧率；恢复弹体软遮罩及移动眼部重算可能增加密集射击/运动时的开销，不承诺保持此前全部性能收益。原生眼部动画路径可替换，代码每次重新解析；未认证全部特殊外观和变身姿态。

证据根目录 `build/eye-boundary-output/`，各轮 `evidence/result.json`、PNG、隔离启动记录、编译日志与存储日志保留。参考 KB-000108 r5：分开验证单次替换与持续绑定，验证输出也验证路径；本轮未作无损像素或性能收益声明。

## 失败与工具修正

- 初始系统 Python 缺 psutil，改用本机已有完整运行时；未安装新依赖。
- checks-01：测试入口未带 Mod 后缀，被启动器拒绝，未启动游戏。
- checks-02：受限进程不能创建测试桌面，未启动游戏；按运行器要求经批准使用普通用户上下文，仍是独立后台桌面。
- checks-03：测试驱动误把 MainMenu 逻辑对象当显示对象，#1069；修正菜单调用、原生 Bullet 构造参数。
- checks-04：过早冻结玩家动画且测试位图子格数与实际字段不一致，证据无效。改为原生初始化完成、明确站立姿态并同步 fogSub。
- checks-05：同一显示对象上一轮候选遮罩影响下一轮基线，导致基线假通过；先恢复本轮消费者，再做独立对照。checks-06通过；checks-07另测同候选持续绑定，不以卸罩对照替代该项。
- 修改测试脚本时，字面路径护栏把脚本中的SWF文件名误识别为直接写入；按已有授权登记5分钟、会话绑定的精确调用后执行。没有禁用保护或更改信任。

## 部署

- `release/RealisticVisionMod.swf`：49,048B，SHA256 `0861FB644AE951993FA7DA79A7E8E4B71B564F08C60881B5F151DD406DD2E30B`。
- 前版 `2F44DDD1844C7DAC7E8FFDE4EAFB256460F5FB6958675A07FB449477C4AC151F`；备份 `build/backups/before-eye-boundary-20261102-073730/`。
- config 保持 `73B83AB5E60E1CC71367DD7F725DE7D2E4C9BCC36F045F43EF530A53BCEBC3DE`，宿主未改。
- 替换前后均核对指纹；回读与smoke-01完全一致。本轮游戏实例均已退出，登记已结束。运行中的玩家游戏不操作，保存并重启后生效。
- 回滚仅在安装仍为本轮 SHA 时使用上述备份，不能覆盖并发更新。详细源指纹见 `build/eye-boundary-output/deployment.json`。
