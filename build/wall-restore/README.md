# D28 旧墙面渲染恢复

仅生成并验证 `v0.32.0-wall-restore-candidate`，不写正式 `release/`。设置保留“已探索墙边常亮”，源码和菜单默认均关闭；已有明确保存值继续生效。

来源由 `inputs.json` 固定：已安装 D27 的完整生产源、保留改键/语言/场景兼容的旧墙面参考、最终 helper。候选使用 `build/wall-options-output/candidate/src` 的生产线，不使用包含 authority 开发工作的 HEAD。旧墙面参考是 v0.30.1 的墙面算法叠加后续非墙面更新，不是整包回滚。

从本模组目录，用 Codex runtime Python 加 `-X utf8`：

```text
python -X utf8 build/wall-restore/prepare.py
python -X utf8 build/wall-restore/verify.py red
python -X utf8 build/wall-restore/verify.py checks
python -X utf8 build/wall-restore/verify.py game-rock
python -X utf8 build/wall-restore/verify.py game
python -X utf8 build/wall-restore/verify.py bench
python -X utf8 build/wall-restore/verify.py build
python -X utf8 build/wall-restore/production.py
python -X utf8 build/wall-restore/evidence.py
```

生产候选冻结后不要重新编译来替换待部署字节。后续功能应新建实验目录；不能修改输入指纹使历史候选跟随新 HEAD。`prepare.py` 检测 helper 或冻结来源改变会停止。

验证含义：

- `RestoreChecks` 在真实 AIR 上检查原墙像素、透明凹口、墙芯、常亮开关、0.75/1.25/1.5 倍缩放、破坏、块地图、重叠/隐藏/带颜色变换的前景与重置。`red` 要求 D27 在原墙像素保持项失败，证明检测到本轮要改的行为。
- `ContourCacheChecks` 对照冻结的全视口透明度版本；OFF 图像逐像素相等。ON 允许原生材质的 1 级取整，空气必须和 OFF 一致。参考文件永不进入生产 SWF。
- 原有柔化/逻辑视野与共享探索检查保持；设置检查运行真实读取与保存函数，路径仅在测试副本中指向自有目录。
- 原生游戏训练房按当前版关闭常亮、旧墙面、候选关闭、候选开启四组，同路线、两模式驱动。岩壁另外含原生 G 材质与半高墙。核对原版光照、FOV、探索和敌人分类，保存世界图、雾与最终 Stage。
- 计时同进程四组轮换，每模式各 120 次，含 RV 更新和雾层绘图；不含物理、截图编码、网络和战斗，不能换算完整 FPS。计时期间与 RConnect 协调暂停其它测试/编译。
- `production.py` 加载完全不改字节的交付 SWF，两进程检查默认关闭、开关、保存/恢复、模式与快捷键页、tick181。存根只编入探针。
- `evidence.py` 对照实际测试源和候选源，保留逐像素最大差、受影响数量和深墙点；不以均值掩盖边缘差异。原生凹凸边缘经不同向量裁切分区可能出现少量 1–3/255 的差异，必须同时报告数量。

全部 AIR 用唯一 ID、隐藏窗口、本模组内测试资源；只清理本次进程和描述符，不写真实 pfe 存储。重复素材仅在 SHA256 一致后与本模组冻结素材硬链接，共用输入只读，禁止原地补丁。不要运行旧 wall-options 的 prepare/build。

输出 `build/wall-restore-output` 已忽略；`*-full-alpha`、`*-sparse-alpha`、`*-terrain-cache` 是本轮淘汰的中间实测，保留原址。最终证据见 `knowledge/experiments/2026-10-16-wall-render-restore.md`。
