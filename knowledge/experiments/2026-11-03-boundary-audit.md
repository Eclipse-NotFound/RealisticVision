被测技能：diagnosing-bugs（2026-10-08.1）；remains-runtime-debug / remains-mod-memory（2026-10-27.1）；remains-knowledge-contribution
技能归属：C:/Users/hello/.agents/skills/diagnosing-bugs；Remains/.agents/skills 下对应工作区技能
测试工作区：D:/Program Files/Steam/steamapps/common/Remains（RealisticVision）

# 边界开火/敌人活动卡顿：既有证据复核与方案修订

日期：2026-11-03。任务是调查并制定优化方案。本轮仅核对源码、重算既有数据、查看已有截图和写文档；没有启动游戏、编译候选、部署或改变设置。以下数字来自旧测试，不是新增运行结果。方案见 [boundary-fire-stutter-plan](../../design/boundary-fire-stutter-plan.md)。

## 1. 输入与冻结

- 正式 SWF：v0.34.4-door-smooth，49,080B，SHA256 `2D5360864ABD7A6E6115FBE6C362CD0ED5F0665A8D336513DF6E711B3F064407`。
- 安装模板 config：SHA256 `73B83AB5E60E1CC71367DD7F725DE7D2E4C9BCC36F045F43EF530A53BCEBC3DE`。模板含 `fog_vision_quality=0`、`vision_quality_preset=0`、`enemy_mask_fast=1`、`fx_vision_quality=0`、`motionstep=4.0`；不代表 Local Store 的实际设置。
- 主源码：`build/perf-20261102/src/RealisticVisionMod.as`，SHA256 `133BD23611C245275546D8088F80FE3D27DE214C6E99AAB66DA1A0E1FFD85C0E`；与 `build/boundary-c1-output/baseline/src/RealisticVisionMod.as` 字节指纹相同，且与 C1 inputs.json 一致。只核对了该主文件，不冒称全部源码树已逐字比对。
- 原始输入：`build/fire-exhaustive-output/{c1grid-01c,c1grid-02,c1grid-diag-01,c1grid-diag-02}/` 下的 evidence/result.json、analysis.json、CombatRenderProbeMod.as、三版本主源码及 SWF。
- 复核工具：[audit_evidence.py](boundary-audit-20261103/audit_evidence.py)；输出：[audit.json](boundary-audit-20261103/audit.json)。保存 4 轮、24 窗摘要、原件路径/指纹、计数分母、场景和 SWF 比较结果；脚本仅读原件，输出写到本报告附件目录。

## 2. 已确认的证据边界

### 配置初始化没有对齐

冻结生产主源码的构造器为空（507–510）；startup 才调用 loadConfig 和 applyVisionScale（526–527）。loadConfig 优先读本端存储，完成后才把 fogSub 从初值 8 改为配置要求的 4/8，并重建派生滤镜/矩阵（554–559、674–695）。

C1 驱动 `CombatRenderProbeMod.as:175–178` 直接 new 实例并 resetRoom，硬设 dim=.6、soft_current=25；没有 startup/loadConfig/applyVisionScale 调用，也没有 fogSub 赋值。四份驱动及注入源码都已检查。因此该夹具按源码运行在初始 8 子格，而非安装模板解析后的 4 子格；仅声称它是旧测试路径的源码结论，本轮没有再启动运行时读取字段。

这不否定候选间已有图像检查，但使“11.9ms/次就是当前游玩配置成本”的推断失去依据。所有优化都需先通过真实配置解析，再记录生效字段，不能只手改 fogSub。

### 预热与采样分母不同，父子耗时不能相加

驱动常量为 SAMPLE_COUNT=360、WARMUP_COUNT=90、PROFILE=false。清空 profile/calls 的逻辑受 PROFILE 控制，末尾却无条件导出，所以每窗 applyVision 调用数为 450，positions/frames 仅 360。位置相邻差实际分母是 359 次转换，不是 360 次位移机会。

原记录以 360 帧身体轨迹对照含预热的 450 帧 FOV 总数，不能称“一一对应”。重载轮有 198–366 次 computeFov/450 帧；246–343 是按版本把两窗平均后的范围，应避免当逐窗极值。

用同一窗全部 450 帧的 rv 累计作分母，`applyVision + updateWallSurface` 的占比如下。fillFogCache 内嵌于 applyVision，未重复加入；这只说明 RV 函数执行构成，不是 GPU 或完整帧成本。

| c1grid-02 窗 | 版本 | FOV 次数（450 帧） | 身体位移转换（359 次） | 场显示+墙体 / RV | 部分可见敌人最大值 |
|---|---|---:|---:|---:|---:|
| 0 | vector | 198 | 255 | 83.5% | 0 |
| 1 | candidate | 337 | 335 | 83.7% | 0 |
| 2 | normal | 287 | 299 | 84.4% | 0 |
| 3 | normal | 205 | 235 | 81.9% | 0 |
| 4 | candidate | 349 | 349 | 85.7% | 0 |
| 5 | vector | 366 | 359 | 87.1% | 0 |

fillFogCache 单次平均 11.72–12.14ms 仍可由原数据复算，但必须带上述配置、预热和场景条件。隐藏对象处理包含世界特效处理，后者包含单对象遮罩及 refreshMask；这些也是嵌套耗时，不可简单相加。

### 发射、命中与活动不能混为一谈

重载窗 `sampleNativeEnemyShotsLowerBound=371–397` 来自武器 kol_shoot 的正差下界；驱动本身注明不是精确总发射数。它不记录弹体命中、玩家受击或击退，原先“371–397 次命中/踉跄”表述应撤回。bodyMoved 支持身体确实移动，不能唯一归因到命中；重载轮没有逐帧眼点/原因记录。

diag-02 窗 1–5 的 liveEye 采样跨度为零，能排除这些窗口里的射击眼点抖动。它与重载轮不是相同布局和玩家轨迹，所以不能借它排除所有武器姿态，也不能用另一次的原因计数补齐重载轮缺失证据。

### 不是同一场景，也不是敌人自主跨界复现

四轮 scene.nativeUnits 分别为 12/6/9/17，再额外生成 6 敌；重载每窗总单位数为 12。不得把“新增 6 敌”写成全场只有 6 敌。

两张旧截图已目检：01c 是低矮横廊，02 是高挑破墙空间，边界形状明显不同；scene 的出生点/地面高度也不同。同一个 loc1_3 字符串不证明同一随机地图。原生持续世界在窗口间不重置，因此也不能假定窗口间输入天然相等。

驱动每帧固定所生成敌人的位置，定期请求其 attack，玩家持续开火；它不是“玩家停火、一个敌人自主活动”的场景。重载六窗部分可见敌人全为零，完全没有验证敌人本体软遮罩跨界假设。

### A/A 是同源重编译，不是同字节

c1grid-02 的 normal/vector 主文件逐字相同，但 rv.swf 为 `A312B33D…18D34A69`，vector.swf 为 `4B61D9C5…32943D`。不能称同字节 A/A；字节差本身也不证明算法不同。本轮没有逆向二进制差异原因。后续控制组直接复制同一编译产物，省去这项歧义。

## 3. 保留的结论与降级的结论

- **保留**：C1 图像结果 JSON 记录 623 项通过、raster 集合 baseline 12/candidate 6；仍是该夹具覆盖范围内的等价证据，不扩成所有显示输入的证明。原性能方向不稳定，未部署状态合理。
- **保留**：当前弹体全几何路径及均匀区域早退；场/墙体在重载夹具里占主要 RV 执行成本。两条均有源代码或原数据支持。
- **降级为候选**：受击位移是两种用户症状的共同主因；所有开火卡顿只在跨界弹体出现；C1 增加的全部时间均由粗格放大导致。缺少对齐场景、事件和配置的因果对照。
- **纠正**：跨界不代表每帧必定分配/模糊/重画；现有实现已含多层复用。刷新等待 2–3 帧在原测试 30fps 下约 67–100ms，不能写成固定 50ms 或承诺仅几像素误差。
- **方案变化**：先配置对齐，区分边界在屏/弹体支持区混合、固定眼点/受击位移、敌人不开火活动/开火，再选择保真优化。C4 降频不再是默认首选，画质和逻辑时序取舍留给用户。

## 4. 未验项、工具限制与处理

1. 未新增真人或隔离运行复现；没有用户精确存档、时间段、当前实际配置与加载组合。已知安装版本不能证明正在运行的游戏已重启到该版本。
2. 一条包含本端配置、application.xml 和 UnitPlayer 参考源码的只读查询被 PreToolUse 的 `Protected target (read-only-reference)` 拦截；同一精确调用走 require_escalated 后仍被拦。未关闭钩子或换工具绕读。该批内容未取得，因此不从缺失推断配置不存在，也未独立核实本体受击代码。
3. shared_knowledge 已回读 KB-000106 r1、KB-000123 r5、KB-000056 r1；补充两层查询返回 partial 且有不可读专题/原区。无命中不是没有经验。本轮发现属于已知“实际参数/事件语义/同输入”规则在旧夹具中的具体偏差，留模组记录，未重复建通用知识卡。
4. 首次通过 PowerShell 管道写中文方案遇到 UnicodeEncodeError；写入目标被截空后，立即按预先 SHA256 校验，从当前已提交原件恢复，再由 UTF-8 文件字节替换并回读。未丢失原方案；后续文档修改采用 apply_patch，未改终端/系统编码。
5. 不修改或清理遗留 `.dshclaim`；所记 PID 37008 本轮查询未发现存活进程，仍以文件指纹防止覆盖并发编辑。既有 authority 源码、测试和其他未提交报告均保留。

## 5. 技能方法与本次产物

实际使用：外置记忆定位生产快照；diagnosing-bugs 将推测转成可证伪对照；runtime-debug 区分对象链/显示、事件语义与完整帧；knowledge-contribution 把尚未稳定的模组结论留本模组。没有技能行为修改，也不宣称自动选择或运行时测试覆盖全面通过。

[已落盘→既有] KB-000106/123/056 与 C1 原报告提供参数、计时和回放边界。[本次产物] 现行方案、本报告、离线复核脚本及数据、MEMORY/journal 接续、原报告末尾更正。全局台账只登记这份合并报告，不逐项另建技能报告。

收尾核对：24 窗及 623 项旧检查的摘要已成功重算，全部记录的输入指纹再次匹配；方案/报告本地链接无缺失，UTF-8 内容无替换字符。全局测试报告台账已查重追加并回读，状态为待吸收；这不代表新一轮游戏验证通过。

下一可执行步骤：方案 P0-a 及 S0/S1/S2；敌人单独活动另以 S3/S4 验证。本轮交付为调查与方案，不声称卡顿已经修复。
