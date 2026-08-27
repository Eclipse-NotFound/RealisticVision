# 实验：v0.24.6/0.24.7 自动化真机验证（2026-08-27）

## 目标

v0.24.6（两项修复）与 v0.24.7（五处性能优化）自 8/21 起一直"待用户实测"。
本轮用 remains-auto-testing 方法论做程序化真机验证：测试埋点 → 自动驱动
进游戏 → 日志关键词断言，把清单中可自动化的项先勾销，缩小用户手测范围。

## 环境与方法

- **埋点**：模组新增 `autotest` 配置键（默认 0，不影响正常游玩）。开启时：
  每 300 帧一行窗口统计 `auto st ...`（fov 重算三因计数 / 节流跳过 / 拆帧 /
  classic 门控 / 武器扫描 / 掩膜两分支 / 敌人三态 / 帧耗时 avg+max / err）；
  事件行（进房 / 念力抓放 / F11 F12 / 看门狗 / config 写结果）即时输出。
- **驱动**：复用 RConnect 自动化钩子（autoRole=host + autoGame=1 关菜单开新档，
  autoWalk=1 避墙漫游提供真实位移）；测试实例 app id `pferv1` + 临时描述符，
  存储天然隔离；模组日志 `%APPDATA%\pferv1\Local Store\RVision.log`。
- **构建**：flexsdk 在 `D:\RemainsMod\mods\Sandevistan\build\tools\flexsdk`，
  java 用 Animate 2024 自带 JRE（`D:\Program Files\Adobe Animate 2024\jre`）；
  ffdec 需 `java -jar ffdec.jar`（其 exe 启动器找不到该 JRE）。
  新增 `build/build_test.bat`（产物 build\RealisticVisionMod_test.swf，
  不直接覆盖 release）。

## 关键发现（按重要性）

### 1. Bug：classic 30Hz 门控因 frameCount 双递增失效（已修，v0.24.8）

`debugStep()` 历史上也 `frameCount++`，与 `onFrame()` 的 ++ 形成双递增：
frameCount 每渲染帧 +2、**奇偶恒定**（视进房时序而定）。v0.24.7 的 classic
门控 `(frameCount & 1) != 0 && !needFov` 因此恒全开**或**恒全关：

- 实测会话 A：`cls=150/0`（300 帧窗口全跑全图循环，优化完全无效）；
- 修复后：`cls=150/150` 精确对半（站立）/ `181/119`（移动，fov 帧全跑）。

连带影响：fov 30 帧兜底退化为每 15 帧（修后恢复 30）；structHash "每 2 帧"
恒每帧（修后恢复）；tick 心跳 1.5s（修后 3s）。武器扫描 `%3` 因 2 与 3 互素
侥幸保持每 3 帧语义。**修复 = 移除 debugStep 的 frameCount++**（一行），
所有 %N 门槛恢复设计语义。

### 2. v0.24.7 优化逐项验证（修复后构建，真机数据）

| 项 | 断言 | 结果 |
|---|---|---|
| ① fov 重算节流 | 移动时 fov 重算 / 被节流比 | classic 60:90、current 65:79（≈2.2-2.5× 降低，符合设计 ~3×） |
| ② 模糊+钳制拆帧 | blurD ≈ fov 帧数 | current blurD=70 ≈ fov=65 ✓ 每fov帧延迟次帧 |
| ③ classic 30Hz 门控 | cls 跳过/执行各半 | 修复前 150/0（恒不跳）→ 修复后 150/150 ✓ |
| ④ 武器扫描门控 | ws 执行 1/3 | 站立 100/200 ✓，移动 130/170（fov 帧加成）✓ |
| ⑤ classic 掩膜 classicRaw | mask Raw/Ray | random_mane 真实敌人 mask=50/0（零 raycast）✓ |

### 3. 性能基线（模组自身帧耗时 ms，48x25 房间）

| 模式 | 站立 avg/max | 移动 avg/max | 备注 |
|---|---|---|---|
| vanilla（透传） | 0.00/0 | — | 基线≈0 ✓ |
| classic | 0.28/5 | 0.43/6 | 修复门控后 |
| current | 0.45/16 | 2.24-2.40/29 | 移动峰值 29ms 是可感卡顿源 |

### 4. v0.24.6 侧证

random_mane 到达即遇敌：三态计数 e=0/0/2（两个部分可见敌人）持续多窗口、
掩膜正常挂载、武器扫描路径零错误、看门狗全程未触发（8 轮运行 err 恒 0）。

### 5. 环境发现（对后续自动化有用）

- **adl64 窗口不在前台时 FPS 趋零**：ENTER_FRAME 几乎不派发（8/18 实验
  "newGame 卡地形"的真正原因很可能就是这个——模组心跳停了但 RConnect 的
  real-time Timer 还在走，造成"驱动卡死"假象）。**自动化运行必须保持游戏
  窗口前台**（computer-use open_application activate 或用户配合）。
- **computer-use 键盘注入有效**：F11/F12 成功送达模组（8/18 用原始
  keybd_event/PostMessage 失败的问题被突破）；但 WASD 移动无效——游戏 Ctr
  虽走 stage KEY_DOWN 事件，前台被用户抢占后注入即失效（见 8/27 会话：
  用户正在用机器，不适合抢焦点）。移动数据改用 RConnect autoWalk 钩子获得。
- **RConnect autoTravelLand 到达即死**（跨模组，待报告）：hp=100 存活出发，
  random_mane / raiders 两图到达后 localPose 一律 lbl=die fr=14 卡死（非正常
  t_die 流程，不推进不复活）；begin 地不传送则一直存活（lbl=stay）。空槽位
  newGame(0,...) 实为加载 0 号槽（fe/World.as:823，nload=0 → game.init(data)），
  需配存档模板（本次用用户 3 月干净档 PFEgame1.sol 只读复制）。
- **saveConfig 在测试实例写盘失败**（待查）：F11/F12 后 config.txt 从未被
  重写（stat mtime 不变），catch 静默吞异常。v0.24.8 已在 catch 加 fileLog
  埋点（"auto config write error"），下次任一会话按 F 键即可拿到具体错误。

## 结论

- **v0.24.7 五项优化中 ①②④⑤ 按设计工作；③（classic 30Hz 门控）自发布起
  即失效（奇偶 bug），v0.24.8 修复并经真机对半交替数据验证。**
- 自动化可验证项已全部勾销；观感类（亮边/念力/部分可见观感/门/暗区武器/
  营地无雾/帧率手感）仍需用户游戏内确认（MEMORY §6 清单）。
- v0.24.8 = 修复 + autotest 埋点（默认关）+ 版本标记行 + saveConfig 错误日志。

## 运行记录

8 轮运行（run1-2 废弃于低帧率/死亡问题，run3 random_mane 敌人数据，
run5/6 存档模板试验，run7 classic+autoWalk，run8 current+autoWalk，冒烟 1 轮）。
原始日志存档：`logs-20260827/`（run8 RVision/RConnect + run3 ADL stdout）。
