# 2026-11-04 CS×RV 大图移动工况实测：RV 真实成本与阶段 A 优化效果

## 一句话

在隔离沙箱里跑通"CS 连续大图 + 行走"后测到：**RV 在大图移动工况下自报 12.6ms/帧**（远高于此前静止场景的 3–4ms）；阶段 A 候选（W8+W7+W2+W1）把它降到 **9.95ms/帧（−21.2%）**，整帧均值 −3.4~−6.3ms、中位 −5.5ms、**>100ms 帧数 −28%**。三批交错实验里 **每个基线窗口都慢于每个候选窗口**（6/6、12 个 300 帧窗口）。

## 方法与装置

- 测试台：`build/cs-rv-20261104/`（并行子会话搭好）。隔离沙箱 = `mods/ContinuousScene/build/runtime-csrv` 的副本（宿主 `pfe.swf` A9B39CC7、CS 0.9.8 `285625F4`、13 个模组），每次运行**唯一 AIR app id**，驱动 `CsRvMoveProbeMod` 进入 `random_mane`、固定布局种子、往返行走（X 跨度验收 310px）、逐帧落盘帧间隔。
- 本次新增两个修正（否则跑不起来）：
  1. **`ModLoader` 清单**：`mods/loader-manifest.txt` 才是游戏读取的清单，`supported-mods.txt` 只是兼容表；新驱动必须用 `RemainsModLauncher.exe --root <runtime> --all --no-ui --report <runtime>/selection.json` 重新生成，否则驱动永远不会被 `requested`（本会话第一次 precheck 即因此空跑）。
  2. **驱动读 `rvAuditAPI` 的 #1069**：`MainFE` 是密封类，`main["rvAuditAPI"]` 在无该 API 的臂里直接抛错；已用 try/catch 包住。
  3. 另需 `psutil`：本机 PyPI 被代理拒（403），已在测试目录放一个 `psutil.py` 垫片（Win32 `GlobalMemoryStatusEx` + `tasklist`）。
- 臂：**Q = v0.35.0-aperture-grade 正式基线**（`C97A6F6C…`，冻结副本 `inputs/rv-v0350-release.swf`）；**P = 阶段 A 候选 v0.35.1-csoptA**（`out/candidate.swf`）。两臂同沙箱、同驱动、同配置模板（仅 `enabled/mode=current/cs_window=1/autotest=1/debug=0` 强制）、同种子、交错顺序 Q,P,P,Q。
- 每轮：boot → 新档 → `beginMission("random_mane")` → settle 6s → **移动窗口 60s** → 写 `result.json`（帧间隔数组）与 RV 自报 `auto st … ms=均值/峰值`。

## 结果

### RV 自报每帧 AS3 时间（`atMsSum/300`，同一沙箱、同图、交错）

| 批次 | 臂 | 窗口 1（f≈300） | 窗口 2（f≈600） |
|---|---|---|---|
| qp-01 | Q | 12.22 | 15.37 |
| qp-01 | Q | 10.57 | 12.95 |
| qp-01 | P | **8.54** | **11.90** |
| qp-01 | P | **8.40** | **11.29** |
| qp-02 | Q | 11.99 | 14.98 |
| qp-02 | Q | 10.79 | 12.91 |
| qp-02 | P | **8.72** | **10.53** |
| qp-02 | P | **8.97** | **11.60** |
| qp-03 | Q | 11.62 | 13.08 |
| qp-03 | Q | 11.18 | 13.91 |
| qp-03 | P | **8.43** | **11.48** |
| qp-03 | P | **8.99** | **10.51** |

- 窗口 1：Q 均值 **11.40**（范围 10.57–12.22） vs P 均值 **8.68**（8.40–8.99）→ **区间不重叠**。
- 窗口 2：Q 均值 **13.87**（12.91–15.37） vs P 均值 **11.22**（10.51–11.90）→ **区间不重叠**。
- 合并：Q **12.63ms/帧** → P **9.95ms/帧**，**−2.68ms（−21.2%）**。

### 整帧（完整 60s 窗口，含所有模组与渲染）

| 臂 | 均值 | 中位 | p95 | >100ms |
|---|---|---|---|---|
| Q（6 轮） | 95.55 / 92.67* | 85.5 | 183 | 174.5 |
| P（6 轮） | **89.23** | **80** | 176 | **126** |

\* 去掉 qp-01 首个 Q 轮的 109.93 冷启动离群值。

- 均值 **−6.3ms（−6.6%）**；去掉离群值 **−3.4ms（−3.6%）**。
- 中位 **85.5 → 80（−5.5ms，−6.4%）**；**>100ms 帧数 174.5 → 126（−27.8%）**。
- 三轮交错里每一对相邻 Q/P 都朝候选方向（4/4 pairs × 3 批）。

### 与模型对照（机制自证）

合成微基准预测的节省：W8 ≈1.68ms/帧 + W2 ≈0.26ms×0.6 + W7 ≈0.07ms + W1（突发）≈2.1–2.4ms/帧；实测 **−2.68ms/帧**，同量级且略高（W1 的突发帧贡献）。⇒ 微基准的排序与量级可用，且四项改动确实都生效（不是只生效一项）。

### 运行健康

- 24 轮（含 precheck）全部 `init ok` / `设置注册` / `tick` 正常；候选 6 轮 `err=0`，无 watchdog 自动停用。
- `xSpan=310`（每轮都真的走了）、`seedHook=true`；少数轮 `tileHash` 不同（战场破坏/门状态变化影响），故**跨批绝对帧时不作比较**，只用同批交错。

## 不能声称的

1. 这是**隔离沙箱**（隐藏窗口、`renderMode=direct`、1280×800、约 10–11fps）的数字，不是玩家真实前台帧率；沙箱里整帧被别处瓶颈主导（RV 省下 2.7ms 只体现为整帧 −3~−6ms）。
2. 沙箱配置模板是 `dim=0.35 / doordim=0.5`，玩家实际是 `dim=0.6 / doordim=0.85 / soft_current=25`；两臂同模板所以**相对差**成立，绝对 ms 不能直接搬到玩家机。
3. 只测了 current 模式；classic、`viewscale≠1`、CS 关闭的大图均未测。
4. **W6（雾层掩膜合成面积）** 仍未单独诊断：本次没有跑 C/D 诊断臂。整帧收益小于 RV 自身节省，说明瓶颈不在 RV AS3 内，但 W6 是否成立仍未知。
5. 未测开火/门开关的尖峰对比（W1 的突发场景只有间接证据：RV `msMax` Q 均值 96 → P 83，方向一致但样本少）。

## 复现

```powershell
cd mods\RealisticVision\build\cs-rv-20261104
python run_grid.py --batch qp-0X --order Q,P,P,Q --window-ms 60000 --settle-ms 6000 --timeout 260
# 证据：evidence/qp-0X-*/{result.json,summary.json,RVision.log,run.json}
```
前提：`runtime/mods/loader-manifest.txt` 已含 `CsRvMoveProbe|CsRvMoveProbeMod|1|0|0`（用 `RemainsModLauncher.exe --root <runtime> --all --no-ui --report …` 生成）。
