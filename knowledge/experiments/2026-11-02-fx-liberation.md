# RV v0.34.0-fx-liberation：半分辨率雾场 + 遮罩门控 + 无损候选合并（已部署）

被测技能：remains-mod-build / remains-auto-testing / remains-runtime-debug / remains-release-gate
技能归属：Remains 工作区
测试工作区：D:/Program Files/Steam/steamapps/common/Remains

# 背景

用户批准"以极小视觉微差换取大幅度帧率解放"方案（[设计文档](../../design/framerate-liberation-plan.md)），授权实施。方案四支柱：A 雾场半分辨率、B 敌人遮罩门控与肢体继承、C 射线粗化（并入 A）、D 无损底座合并。

# 实现内容

生产基线 = `build/landmem-fix-20261102/src`（v0.33.17-locmem；见下"中途合并事件"）。产物源码 `build/perf-20261102/src`，6 个生产类，无 authority/存根。

1. **Phase 1 无损候选移植**（自普查会话 v0.33.17-exact-render 包，逐块核对原文后应用）：
   - coverage-fast：`refreshMask` 覆盖分类角落单像素早退 + 原生 any-alpha 查询（31/33/37 轮 720 帧严格相等验证）；
   - classic-repaint-v2：视口/亮度/柔化/画质/逻辑模式不变时跳过重复显示重画（48/52/54 轮收益验证）。
   - **遵从普查会话"两项暂不纳入组合"结论**：贴图上传门控（paletteMap，62/64/66 性能方向不稳定）与固定字段记录（63/66）**未纳入**本包。
2. **Phase 2 雾场半分辨率管线**：`FOG_SUB`/`MASK_SUB` 静态常量（8）→ 实例变量 `fogSub`（全 137+31 处用法逐一转换，`MASK_SUB==FOG_SUB` 单格网假设保持）；`fog_vision_quality=0` 时 fogSub=4（字段像素量 −75%），显示层 `scaleX/Y=Tile.tileX/fogSub` 自动 2x 双线性拉伸；`applyVisionScale()` 统一重建模糊半径（cfgSoft/4÷5、maskBlur×fogSub/8）、经典矩阵与单元格矩形；`wallEdgeLight` 硬编码 `/5` 采样换算改为 fogSub 派生；角点采样偏移内联化（世界坐标不变：0.5 与 fogSub−0.5）。
3. **Phase 3 遮罩门控**（`enemy_mask_fast=1` 默认）：
   - `enemyState` 房内路径走完全部瓦片累计加权可见比例（亮=1/混合=0.5/暗=0），≥80% 判全可见（摘遮罩+关 cacheAsBitmap 原生直绘）、≤15% 判全隐，仅临界带保留动态软遮罩；tile 级 fallback 路径同语义；门控关闭时保持原早退语义。
   - `applyWeaponVisual` state=1 快速路径：全可见单位的武器摘共享遮罩/关缓存（回到部分可见时 revision=-1 强制重拷）。
   - 狮鹫手臂（visualGrifArm）与全可见单位长枪出框改走 `fxCenterLit` 中心点二值（枪体中心亮→不建 world 记录，避免与武器遮罩逐帧互抢；暗→空遮罩）。
4. **Phase 4 配置预设**：`vision_quality_preset` 0=极速（默认，三项全快）/1=平衡（雾全分辨率+其余快）/2=原版（三项走 v0.33 原路径）；单项键 `fx_vision_quality`/`fog_vision_quality`/`enemy_mask_fast` 显式出现时覆盖预设对应项。config 模板字节级追加四键中的三个新键（421B）。

# 中途合并事件（重要）

首轮候选基于 `fx-fast-20261102/src`（v0.33.16）构建并完成 4 轮 A/B 后，发现并行会话已于 01:28 部署 **v0.33.17-locmem**（跨楼层记忆修复，roomMem/rangeMem 改 Location 对象弱键）。为避免回退用户已获修复，以 landmem 源为基线**重放全部编辑**（diff 显示 locmem 改动与本轮编辑区零重叠；cfg 字段声明补丁 `add_cfg_fields.py`）；合并版重新编译为 48,554B 并以**部署字节**复验两轮（fxlib05/06）。locmem 的 `roommem restore` 日志路径保留。

# 验证数据（fire-exhaustive 链，三版本同进程回文：normal=combo-v4 冻结源 / candidate=本包 / vector=时任正式版；current 模式，每轮 718 完整间隔/版本，benchmark-eligible 除注明）

|轮次|场景|对照|基线均值/P95/最大/>100|候选均值/P95/最大/>100|RV 基线→候选|
|---|---|---|---|---|---|
|fxlib01|固定|vs v0.33.16-fx-fast|36.58/60/181/6|**35.06/52/129/4**|1.35→1.48|
|fxlib01|固定|vs combo-v4|43.72/76/335/15|**35.06/52/129/4**|3.48→1.48|
|fxlib02|移动正序|vs fx-fast|33.33/42/106/1|33.88/50/102/1|0.92→0.97|
|fxlib03|移动反序|vs fx-fast|34.05/42/112/2|**33.33/40/90/0**|0.96→0.68|
|fxlib05|固定（部署字节）|vs v0.33.17-locmem|33.99/45/133/1|**33.47/41/99/0**|1.00→0.66|
|fxlib06|移动（部署字节）|vs locmem|33.31/41/79/0|33.33/41/96/0|1.16→0.99|

- 固定站位：对历任正式版均值 −1.5%~−4.2%、P95 −9%~−13%、>100ms 帧减半或清零、最大尖峰下降；RV 调用 −34%。
- 移动：与历任持平（±0.6ms 内，历轮噪声带；普查会话同链未改算法对照也见 ±3ms）。
- fxlib04-visual（--visual，因并行 AIR 进程在场标 non-benchmark）：截图 PIL 校验——候选固有暗区泄漏 27/36036=**0.07%**（与已验收 fx-fast 同级；另一窗 910 点与现任 872 点对称，为不同时间窗枪口焰瞬态）；亮区结构重合 83.3%/91.6%（现任自身 86.9%/93.5%，同量级）；无空帧/破图。
- 官方 ModLoader 隔离副本冒烟（两轮）：launcher 回读 RealisticVisionMod `将加载` SHA 一致；`init ok v0.34.0-fx-liberation`、ModSettings 注册、tick 1–901、requested==ok。

# 部署与回退

- 正式：`release/RealisticVisionMod.swf` 48,554B SHA256 `638AB1B0079D50126933AD14581FEB577382E401D080E247D5F8CAB5DAE807C8`；`release/config.txt` 421B `73B83AB5…BCEBC3DE`（BOM/CRLF 保持，`fx_vision_quality=0` 后字节级插入 `fog_vision_quality=0` / `enemy_mask_fast=1` / `vision_quality_preset=0`）。
- 回退备份：`build/backups/before-fxlib-20261102-014500`（locmem SWF 35243D0F + 旧 config 13F5AB06）。**重启游戏生效**。
- 不回滚文件也可用 `vision_quality_preset=2` 回三项原路径、`=1` 回雾全分辨率（下一房间生效；玩家运行时配置 `%APPDATA%\pfe\Local Store\RealisticVision_config.txt` 无新键时默认预设 0）。

# 视觉取舍清单（用户已接受）

半分辨率雾边缘羽化略粗（10px 子格 + 双线性 + 模糊后动态中难辨）；≥80% 可见敌人不再有边界虚化（更利于索敌）；≤15% 可见敌人直接隐藏；手臂/长枪按中心点二值，跨边界失去羽化渐变（与 fx-fast 特效同语义）。

# 边界与坑

- 仅 current 模式整窗计时（用户主用）；classic 收益主要来自 classic-repaint-v2（普查会话 48/52/54 数据），本包未单独整窗计时 classic。preset=1/2 逻辑分支简单未单独计时。
- fxlib01–04 为合并 locmem 前字节；05/06 为部署字节。合并无逐帧成本（locmem 仅对象键替换）。
- 工具坑：PowerShell `Get-Content` 把无 BOM UTF-8 源按 GBK 读会**静默损坏全部中文注释**——源码批量改动一律 Python 显式 encoding；`run.py --help` 会被当运行名误建目录（已清理，未启动游戏）；adl64.exe 在游戏根目录（`runtimes/air/win64` 是其 runtime 参数而非其位置）；mxmlc 需在 `flexsdk/frameworks` 工作目录运行（localFonts.ser 相对路径）。
- 与并行会话共享 fire-exhaustive-output：本轮占用 fxlib* 目录与 fxlib/locmem 槽位，未触碰普查会话任何目录；其 76 轮结论（贴图门控/固定字段不稳定、重叠合罩反例）已吸收进本包取舍。

# 证据

- 输出：`build/fire-exhaustive-output/fxlib01-fixed` … `fxlib06-merged-moving`、`fxlib04-visual/evidence/scene-0..5.png`
- 候选槽位：`build/fire-exhaustive-output/fxlib/src`（=部署源）；现任对照槽 `locmem/src`
- 实验：`build/perf-20261102/`（src/out/转换脚本/visual_check.py/smoke_official.py/deploy.py/locmem.diff）

# v0.34.1-door-coverage 修复

用户真机报告：透光门后可视效果未覆盖炮塔。根因=v0.34.0 门控把 FOV_DIM（透光门/水泄漏区，子格按门景亮度写入 currentSight）混合包围盒按 ≥80% 加权比例提升为全可见，摘遮罩直绘导致门景暗度渐变丢失。

修复（源 build/perf-20261102/src，部署 48,731B DAC7CB25…4AD6E0C9，备份 uild/backups/before-doorfix-20261102-054200，config 未改）：
1. enemyState 房内路径：dimTiles 计数，bbox 含 FOV_DIM 瓦片时禁 ≥0.8 提升（≤15% 隐藏不受影响）；
2. fallback 路径：同语义（bbox 扫 FOV_DIM）；
3. 手臂与全可见单位长枪：中心瓦片 FOV_DIM 时回退 pplyWorldVisual 软遮罩；**粒子/子弹保持亮/隐二值**（首版粒子也回退，fxlibdoor01 同轮 +1.19ms，且粒子语义非主诉，收窄为手臂/长枪）。

|轮次|候选均值/P95/>100|v0.34.0 现任|说明|
|---|---|---|---|
|fxlibdoor01（粗版，粒子也回退）|34.84/53/3|33.65/47/3|门少房型|
|fxlibdoor02（收窄部署版）|35.57/55/2|33.79/47/2|门多+敌常在门区=最坏场景，软遮罩开销回归为语义代价；无门场景零影响（判断 O(1)）|

官方冒烟：init ok v0.34.1-door-coverage、设置注册、tick 1–901。真机门后炮塔视觉待用户重启核对。


# v0.34.2-laser-shadow 修复

用户真机报告：激光炮塔的光束不会受到阴影的遮盖。根因（反编译 Bullet.as:208-229）：激光弹=Bullet 类实例（fx-fast 二值名单内），vis 内 `laser` 子对象按射程拉伸（`vis.laser.scaleX=距离/100`）；fxCenterLit 只看 vis 原点（炮塔口），起点亮→整段直绘——长条几何无法用原点代表，属 v0.33.16 中心点二值固有局限，密集游玩后暴露。

修复（部署 48,757B `2F44DDD1…4AC151F`，备份 `before-laserfix-20261102-054800`，config 未改）：applyWorldVisuals dispatch 判别 `Object(obj.vis).laser == null`——激光弹回 `applyWorldVisual` 逐对象软遮罩；其余弹体保持二值。一次动态属性查询，普通枪弹/火花零影响；真实激光场景每炮塔在场 1-2 发，软遮罩开销可忽略。

|轮次|候选均值/P95/>100/RV|v0.34.1 现任|说明|
|---|---|---|---|
|fxlib342-01|34.06/45/2/0.80|33.93/45/0/0.71|噪声带（LMG 场无激光对象）|

官方冒烟：init ok v0.34.2-laser-shadow、设置注册、tick。真机激光穿阴影待用户重启核对。
