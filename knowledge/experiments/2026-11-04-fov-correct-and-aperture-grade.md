# 门/窗视野边界 + 贴墙视野泄漏：两批实施（v0.34.9-fov-correct / v0.35.0-aperture-grade）

2026-11-04。按 [方案](../../design/door-window-boundary-plan.md) 实施批次 1 与批次 2。
本报告记录**改了什么、证据是什么、没验到什么**。运行时加载**未能在本会话沙箱内验证**
（见 §5），这是本轮最重要的边界，不能当成"已通过"。

---

## 1. 批次 1：v0.34.9-fov-correct（只修正确性）

| 编号 | 改动 | 代码位置（`RealisticVisionMod.as`） | 配置键（默认） |
|---|---|---|---|
| C-Eye-1 | 新增 `visionEye`（每帧一次的眼点缓存）+ `sanitizeEye`（按**当前姿态**的 `scX/scY` 把眼点夹回实心自由格）+ `eyeCellFree` | 新增函数，插在 `playerVisionEye` 之后；`onFrameInner`/`computeFov` 两处调用改为 `visionEye` | `eye_clamp=1` |
| C-Eye-2 | `castRay` 起点格若 `opac>=1` → 整条射线返回 -1 | `castRay`，DDA 之前 | `eye_guard=1` |
| C-Ap-1 | 墙可见性传播只作用于 `opac>=1`（透光门窗按自身 `lit` 归类） | `computeFov` 的传播循环 | `solid_promote=1` |
| C-Ray-1 | 目标格 `opac` 只扣一次（循环内已扣过就不再扣） | `castRay` 目标采样处 | `ray_target_once=1` |
| C-Ray-2 | 子格射线的视野半径守卫 | `recalcTile` | `ray_radius=0`（**默认关**，见 §4） |
| P0-D | `fovdbg` 诊断：眼点/起点格 `(opac,phis,zForm)`/盒子/2 格环 `fov` 写 `RVision.log`（需 `debug=1`；眼点在不透明格必写，其余 30 帧最多一行） | 新增 `logFovDebug`，`computeFov` 末尾调用 | `fovdbg=0` |

**与方案的偏离（3 处，均有理由）**

1. `eye_guard` 从"起点格计入遮挡"收窄为"起点格**实心**则整条射线作废"。
   原因：0<opac<1 的起点格（水/`Area.tileop`）在 v0.34.8 里被整块跳过是**与原生一致**的语义
   （原生 `Location.lighting` 同样从 `i=1` 起步、不采样眼点格）；改成扣减会让整间水房视野变暗、
   并可能整间掉进 `FOV_DIM` 平顶 —— 那是回归，不是修复。
2. `eyeCellFree` 相应只把 `opac>=1` 判为不合法（站水里不再被"请出去"）。
3. `ray_radius` 默认 **0**。方案里它是"P3 可选"：原生 `visi` 在视野半径外是"只升不降的棘轮"，
   场外本来会保留亮度；RV 半径外改黑反而偏离原版观感。先把代码备好、默认不动。

## 2. 批次 2：v0.35.0-aperture-grade（口径统一）

| 编号 | 改动 | 代码位置 | 配置键（默认） |
|---|---|---|---|
| C-Ap-4 | 角点采样把该瓦片的射线亮度量化进 `cornerReuseFlags` 的 bit8-15；`fillLitTile` 带 `litF`，`f = falloff*litF`、`lDist1` 内的整块填充改为 `(1-litF)*255`；复用帧也能还原 | `fillFogCache` 角点循环 + `fillLitTile` | `lit_fastpath=1` |
| C-Ap-2 | 新增 `surfaceAlpha`/`fillApertureTile`：0<opac<1 的瓦片**叶面**改用与墙同族的四角双线性（同一个原生 `visi` 场） | `fillFogCache` 新分支 + 两个新函数 | `aperture_surface=1` |
| C-Ap-3 | 门景不再是常量下限：`floorEff = doordim - (doordim-dim)*min(1,(1-falloff)*doorgrade)` | `recalcTile` 的 `doorView` 分支 | `doorgrade=1`（0=旧行为） |
| C-Ap-5 B1 | 门景锥内（8 邻有 `FOV_DIM`）的墙改用 `doorViewAlpha`（与门后地板同源） | `fillWallTile` 开头 + `inDoorCone`/`doorViewAlpha` | `door_wall_merge=0`（**默认关**，见 §4） |

**与方案的偏离（2 处）**

1. **C-Ap-2 不再乘透射率**（方案草案里写 `gv *= (1-opac)`）。这是修正：
   `opac` 是"挡住多少光"，不是"看起来多透明"；门板/玻璃对观察者是**看得见的实体**。
   原生 `Location.lighting` 里门瓦片自身角点的射线在到达角点前就停了，所以原生门板同样是亮的。
   乘透射率会得到"门板 204、门后 38"的反向结果 —— 方案 §F-4b 批评的正是这种反向。
2. **C-Ap-5 的"角值补偿"（方案 C-Ap-5 A）未实施**。理由：C-Ap-2 让叶面与相邻墙共用同一组角值，
   交界已经数值连续（实测 raw 落差 59→0）；再对墙做 `gv/(1-opac)` 补偿会**偏离原生**，
   属于"为了消除一个原生也有的暗环而改口径"。

## 3. 离线证据（不启动游戏）

工具：`tools/door-fov-20261104/model.py`（v0.34.8 算术模型，已扩展批次 1/2 的口径开关）、
`tools/fov-fix-20261104/checks.py`、`checks_b2.py`。全部断言可复算：

| 断言 | 结果 |
|---|---|
| F-1a 站立（眼点在自由格）墙后点亮 | **0 格** |
| F-1b 坐姿（眼点在墙瓦片内）复现"墙后视野" | **45 格**（v0.34.8 语义） |
| C-Eye-1 站立/坐姿钳制后 | 眼点回到自由格、墙后 **0 格** |
| F-6 木门目标格 | `0.05 → 0.2` |
| F-6 窗目标格 | `0.6 → 0.8`（0.6 原先恰好贴 `litmin`） |
| F-3/C-Ap-1 木门叶面 | `[16..29] → [38]`（恢复门景口径） |
| C-Ray-2 半径外"曾见"子格 | `47 → 0`（默认关，仅验证代码正确） |
| C-Ap-4 窗后 300px 内 | `0 → 51`（`(1-0.2)*255`） |
| C-Ap-4 开放区（lit=1） | **逐位不变** |
| C-Ap-2 门板/墙交界 raw 落差 | `59 → 0` |
| C-Ap-2 门板取值 | `[38] → [42,97,151,206]`（与墙同族的角点梯度 = 原生门板观感） |
| C-Ap-3 门后光轴取值数 | `1 → 22`；远端 71 / 近端 50（解析式 69，差 2） |
| C-Ap-5 门景锥内墙 | `249 → 38`；锥外逐位不变 |

`checks.py` 9/9 通过，`checks_b2.py` 9/9 通过。

## 4. 默认值的取舍（为什么两处默认关）

- `ray_radius=0`：场外变黑与原版"棘轮保留"观感不同，方案本身也只把它列为可选。
- `door_wall_merge=0`：它会把门景锥内的墙提到与地板同亮度（亮一大片），观感变化最大，
  且本会话无法真机验证。用户可改一行 `door_wall_merge=1` 重启后比较。

## 5. 未验证项（边界，不伪报通过）

- **运行时加载未验证**。`adl64.exe` 在本会话能启动并报错（探针：`application descriptor not found`），
  但完整 AIR 应用（pfe.swf）在沙箱内**无法初始化**：本会话进程树对 `%APPDATA%` 的写入被拒绝
  （`Set-Content` 探针直接返回"访问被拒绝"），而 AIR 的 `File.applicationStorageDirectory` 就在那里；
  即使把子进程的 `APPDATA` 重定向到工作区，`Local Store` 仍未被创建、`air-output.log` 为空。
  与 2026-11-04 早先记录一致：**游戏测试需要 full-access（正常完整性）上下文**。
  ⇒ 首个真实加载会是用户的这次重启。若 `RVision.log` 的 `init ok` 行不是 `v0.35.0-aperture-grade`，
  或出现 `onFrame error`，按 §6 回滚。
- **观感未验证**：门板变暗、窗后变暗一层、门后渐变、坐姿视野中心下移 ≈20px —— 这些都需要真机看。
- **性能未测**：本轮改动都在 `needFov` 帧内（`computeFov`/`fillFogCache`），
  C-Eye-1 多 1~7 次 `getTile`/帧、C-Ap-4 多 1 次数组读/瓦片、C-Ap-2 每个透光瓦片多 4 次 `explorationLight`。
  **不作任何帧率声明**；沿用"训练室计时落在 A/A 噪声带内就不能宣称收益"的纪律。
- **共享探索数据**：C-Ap-1 会让"透光瓦片不再被传播点亮" ⇒ `captureExploration`/`beginCapture` 的
  `visi` 采样与 `fov` 标记可能略有变化；本轮未核对共享探索的跨会话等价性。

## 6. 部署与回滚

| 批次 | 字节 | SHA256 | 备份 |
|---|---|---|---|
| v0.34.9-fov-correct | 50,835 | `7be181636a53c6e71f48d328da15cc036511f7cb728f3d503a77747d361bdaac` | `build/backups/before-v0349-20261104-061848/` |
| **v0.35.0-aperture-grade（现行）** | **51,634** | **`c97a6f6cc0289a0aa4ddc9484c81fdc02ff9025b52c0d5976c5a6e69a624d76e`** | `build/backups/before-v0350-20261104-062257/` |

- 施工源：`build/fov-fix-20261104/v0349/src`、`build/fov-fix-20261104/v0350/src`（从 v0.34.8 冻结源派生）。
- `release/config.txt` 追加了 10 个新键（默认值 = 本轮行为），文件原有字节未改（GBK 段保持原样）。
- 回滚：把上表备份里的 `RealisticVisionMod.swf` 覆盖回 `release/`，重启游戏。
  也可只关单项：`eye_clamp/eye_guard/solid_promote/ray_target_once/aperture_surface/lit_fastpath/doorgrade/door_wall_merge = 0`。

## 7. 用户侧验收（3 分钟）

1. 重启游戏，看 `%APPDATA%\pfe\Local Store\RVision.log` 首行应为
   `init ok v0.35.0-aperture-grade settings=ModSettings-v1 …`；有 `tick` 行即为在跑。
2. 贴墙/坐姿贴着墙看：不该再"越过墙看到后面"。
3. 一扇关着的木门前停一下：门板应有雾（不再是通透的洞），门后有一层由近到远的渐变。
4. 走到有窗的房间：窗后的亮度应比 v0.34.8 略暗一层（窗不再是"完全不存在"）。
5. 若某项不合口味：只关那一项（如 `doorgrade=0` 回到平顶门景），重启即可，无需重编译。

## 8. 下一步

- 真机反馈后决定：`door_wall_merge` 是否开启、`doorgrade` 取 0/0.5/1、`lit_fastpath` 的暗化是否可接受。
- 有 full-access 上下文时补做：官方 ModLoader 冒烟（init/设置注册/tick）+ C-A/A 性能对照 + 共享探索等价性核对。
- 开发树 `src/` 仍未移植（cs-window / clip-hyst / clip-pad / 本轮两批），审阅源在 `build/fov-fix-20261104/*/src`。
