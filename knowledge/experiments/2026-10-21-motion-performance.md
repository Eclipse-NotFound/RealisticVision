被测技能：remains-runtime-debug / remains-auto-testing / remains-mod-build / remains-release-gate / remains-swf-patching
技能归属：Remains 工作区 `.agents/skills`
测试工作区：D:/Program Files/Steam/steamapps/common/Remains

# D33 高速移动与战斗性能（合入 D34）

状态：2026-10-21 16:07:44 **已部署 v0.33.1-motion-performance**，正式路径复验通过。用户反馈两模式均卡顿；沿用“不改变视觉效果”的要求，按 GOVERNANCE §6 完成本机部署。减轻了部分开销，但偶发长帧仍存在。

## 来源及改动

调查起点为 D32 v0.32.3，76314B81…AF5C46B7。调查期间另一会话安装 D34 v0.33.0，8D4A1963…10C55BF1；最终候选以 `build/vision-settings-output/candidate/src` 的已验收源为基线，完整保留亮度、分模式柔化和视距倍率设置。

新增两处优化：

1. `RVWallSurface.buildContourClip` 按线性像素顺序扫描，跨瓦片时才重读高度；连续矩形用 `Vector.<int>` 保存，alpha、地形或视口变化正确失效。矩形顺序、覆盖范围和高度分类保持相同。
2. `RealisticVisionMod.joinClassicWalls` 在四角和所有实际边修正均为零时跳过重复写入 64 像素；原位图已含完全相同的整数值。

不减少更新频率、分辨率或柔化质量。不改变原生亮度、探索、敌人资格、念力守卫；阶梯顶部空气判定与防溢出保留。墙边常亮默认关闭，保存值保留。未发布 authority 工作没有带入生产候选。

## 归因与没有采用的版本

`motion-performance-output/profile-04`：在 192×75 场景中，current 无单位的更新均值约 31.5ms；120 帧墙面累计约 2.0s，其中轮廓构建约 0.93s。96 单位时 applyMask 累计约 0.65s，实际 maskGraphics 仅约 27–39ms。classic 96 单位更新约 61.5ms，applyVisionClassic 累计约 5.35s。表明先优化墙面重复计算与 classic 重复写入较有依据，不能由此归因用户全部卡顿。

- 早期 Object 矩形缓存通过像素检查，但 `trial-03` 中三个默认场景最大值回退，未发布。
- `scan-trial-01` 只线性扫描不缓存，平均收益较小；保留为比较，不作为当前发布候选。
- 紧凑整数向量缓存用于最终合并测试。减少对象存活是实现事实；GC 是否造成某一次停顿尚未直接证明。
- 旧 `motion-performance-output/production` 是过时 v0.32.4，缺 D34 且有长帧回退，禁止部署。

## 完成的功能验证

以下均针对 `motion-performance-output/merged-settings` 新组合：

| 证据目录 | 结果 | 覆盖 |
|---|---:|---|
| checks-01 / ViewportChecks | 192 组通过 | 两模式、常亮开关、视口移动和缩放，最终像素严格一致 |
| checks-01 / EquivalenceChecks | 68 项通过 | 材质/alpha变化、半高墙、透明重叠、变换、光照与房间重置 |
| checks-01 / MaskChecks | 16 项通过 | 单位资格、遮罩及释放 |
| settings-checks | 90+16+21 项通过 | D34 设置规则、柔化、共享探索 |
| verify-final | 32 个原生检查点通过 | 更新后宿主中，雾层、墙面、当前视野、探索、敌人资格/遮罩及合成图严格一致 |
| production / first、restored | 36 项通过 | 准确生产字节的11项设置入口、改键、开关与四个参数跨进程保存 |

最终计 471 项/组。较早宿主上的 verify-01 另有32点通过，未重复计数。生产包仅含六个正式类，不含 fe 存根、authority 或测试驱动。生产源与测试源只差版本标记；验证来源和指纹由 `verified.json` 锁定。

## 同输入移动对照

`merged-settings/trial-01`：两版本同进程交替顺序，每场景预热 30 帧、测量 120 帧；每步移动 12px。单位密集组为 96 个显示测试单位。数值是 **RV 更新加离屏雾层绘制**，不是整个游戏帧耗时或 FPS。

| 场景 | 均值旧→新(ms) | P95旧→新 | 最大值旧→新 | >50ms帧旧→新 |
|---|---:|---:|---:|---:|
| current 无单位 | 35.98→30.81 | 59→54 | 78→97 | 15→7 |
| current 96单位 | 43.35→37.46 | 63→57 | 117→101 | 29→8 |
| classic 96单位 | 65.28→55.25 | 115→101 | 135→328 | 81→81 |
| current 96单位、常亮开 | 69.27→64.50 | 111→108 | 147→142 | 88→90 |

四组均值减少 6.88%–15.36%，P95均下降；**不能说所有长帧消失或最大值全面改善**。classic 的 328ms 包含更新 74ms、绘图 254ms；相同位置基线更新 94ms、绘图 7ms。以下补充单活跃版本原生循环；不能把绘图停顿直接归因于某函数，也不能由这些有限窗口排除偶发回退。

测量窗口±1秒共83次环境采样，未观察到其它 AIR/Java，最低可用内存 5.488GiB；启动满足≥6GiB。采样不能排除所有系统负载。完整指纹与统计见 `trial-01/analysis.json`。

## 原生射击驱动与失败记录

历史 D32 `live-02/03/04` 没有实际攻击；仅可用作移动观察。D34 合并 `live-01` 前两窗出现弹丸，随后不持续；`live-02` 没有选到持枪目标；`live-03` 测试武器ID错误。均不能用作完整战斗验收。

修正后的驱动通过原生 UnitRaider 构造、putLoc/addObj 与当前武器 attack 来产生射击，不以 UnitDamager 陷阱替代持枪敌人。每 6 步扣一次扳机以释放非自动武器 t_auto，敌人无敌只用于维持负载。每窗必须有攻击和 Bullet 对象。玩家每步12px往返，原生世界循环持续；按 baseline/candidate/candidate/baseline 顺序覆盖两模式。随机场景/战斗演进仍限制因果比较。

`merged-settings/live-04` 最终8窗全部完成，每窗120正式样本，22–37次攻击，最多2–3个同时存在的 Bullet；原生 raider1 使用 smg10。每模式/版本合并两窗，统计如下：

| 模式 | RV更新均值旧→新(ms) | RV更新P95 | RV更新最大值 | 整帧间隔均值 | 整帧间隔P95 | 整帧间隔最大值 |
|---|---:|---:|---:|---:|---:|---:|
| current | 19.53→19.83 | 23→23 | 33→30 | 48.40→45.04 | 64→58 | 95→138 |
| classic | 50.07→40.92 | 85→69 | 105→112 | 76.09→68.86 | 113→108 | 221→215 |

classic 的更新均值约减少18.3%，current 在这段短距离往返里基本持平。整帧间隔包含原生逻辑、绘图与系统调度；两组敌人攻击次数和时序不同，不能把间隔变化直接换算成纯模组 FPS 收益。current 的138ms长帧仍存在，而其RV更新最高30ms；未确定其余开销来源。全程未观察其它 AIR/Java，最低可用内存4.557GiB，不视为无系统干扰的证明。

发布判断：保留画面和逻辑、配对常规开销及P95下降、真实射击窗口无功能故障，适合安装为增量优化；没有认证全场景长帧改善，也没有达成稳定30 FPS。下一次实测若仍卡顿，应围绕完整组合的长帧分段归因，不再把平均值降低当作问题全部消失。

所有失败/暂缓记录保留，不覆盖原证据。`packed-trial-01` 在低内存门控处退出，没有启动 AIR；不能算性能失败或通过。早期 `trial-01/02` 有其它 AIR/Java 干扰，只作探索线索。

## 运行与发布边界

测试使用启动器选组、唯一 AIR ID、独立存储和 HiddenProcess 后台桌面。编译与游戏占用均通过共享登记排队，未停止其他会话或玩家游戏。桌面创建经正常权限申请完成，没有前台回退。原生性能测试通常只选 ContinuousScene 与测试驱动，不代表全模组/联机混战验证。

工具：`build/motion-performance/README.md`。本轮查用共享经验 KB-000056（测量边界）与 KB-000071（后台调度）；可复用战斗负载核验另记入公共 discovery。未修改正式技能。

## 部署与回退

- 准确包：`build/motion-performance-output/merged-settings/production/RealisticVisionMod.swf`，40,686字节。
- SHA256：`F2B8A973D9D2A374C9BD8F5DA9D29040266954C8F139B8C85BFA0AAAA749A561`。
- 只替换 `release/RealisticVisionMod.swf`；17项宿主、描述符、清单、配置及其他模组指纹前后相同。
- 正式宿主：`7D423BD7B7DD7D2B997E692BD1E22EF520879CD42387C14653C116C15385BCD4`；新版 init、ModSettings 注册、tick 1/181/361通过。
- 独立测试PID 112036已关闭，临时描述符删除，未操作玩家存储。
- 回退备份：`build/backups/before-motion-performance-20261021-160744-56a353/RealisticVisionMod.before.swf`，对应旧D34 `8D4A1963…10C55BF1`。需回退时先确认安装仍为本轮F2B8A，按登记仅恢复此文件并复验，不能覆盖未来较新安装。
- 机器回执：`build/motion-performance-output/merged-settings/deployment/receipt.json`；门禁证据：同目录上级 `verified.json`。失败回滚路径已实现，本轮无需触发回滚。
- 已有游戏须正常保存退出后重启。没有对外推送或发布。
