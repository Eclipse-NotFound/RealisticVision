# 墙边常亮选项与独立边界修复

本工具只构建候选、运行独立 AIR 实例，不写 `release/` 或玩家存储。功能决定见 D27；最终结果见 `knowledge/experiments/2026-10-15-wall-bright-option.md`。

## 来源

候选固定基线为本模组 `build/wall-surface-output/baseline/src`，主源码 SHA256 为 `6979263b178b4deedf563a88c560614bd867d4fad89d806484b5a5b851c0d446`。基线改变时先核查安装版本，不能修改 pin 来跳过检查。

本轮收尾时菜单改键已安装，当前正式指纹为 E9960808…1F6E0808。`prepare.py` 另外固定已发布改键构建的三个源码文件，主源码指纹 83F27414…BD3F58C8；首次取源仅允许精确匹配的 `build/keybind-output/src`，其后使用本轮 `installed-keys/src` 快照。不能因为旧文档还写“候选”就覆盖这个已安装功能。

`prepare.py` 在此生产线上叠加 D26 和 D27，复制当前 `RVWallSurface.as` 与新语言条目。`--integrate-main` 仅用于第一次整合，已经执行，不得重复执行。候选保留已发布改键，仍不包含 HEAD 中尚未发布的 authority 改动；主开发源码编译产物不能当作本轮部署包。

## 命令

从模组目录运行，Python 使用本机 Codex runtime，开启 `-X utf8`。构建器复用 `build/wall-surface/run.py` 的 Flex/AIR 工具发现和独立实例管理。

```text
python -X utf8 build/wall-options/prepare.py
python -X utf8 build/wall-options/repro.py
python -X utf8 build/wall-options/repro.py --repaired
python -X utf8 build/wall-options/verify.py checks
python -X utf8 build/wall-options/verify.py game-rock
python -X utf8 build/wall-options/verify.py game
python -X utf8 build/wall-options/verify.py bench
python -X utf8 build/wall-options/verify.py build
python -X utf8 build/wall-options/evidence.py
```

性能回放与其它测试顺序执行。`profile.py` 仅在输出目录的副本中插入分段计时，定位开销；它产生的 SWF 不交付。

归档前单独只读核对候选 SWF、正式 SWF 和根 pfe.swf 的 SHA256，将结果保存到 `build/wall-options-output/binary-fingerprints.json`。键依次为 `build/wall-options-output/candidate/RealisticVisionMod.swf`、`release/RealisticVisionMod.swf`、`installed_pfe`。二进制指纹检查与归档写入分开，避免保护规则误把读取 SWF 的归档命令识别为修改游戏文件。

## 验证含义

- `repro.py` 用 f72c25f 中的旧实现复现透明凹口被方格墙影压黑，预期应用退出 1；脚本确认这是预期失败后退出 0。`--repaired` 要求常亮关闭时同一凹口正确显示。
- `BoundaryChecks` 覆盖两功能独立、开关、实际 alpha、墙芯、未探索背面、半高墙、破损、视口和分块边界。
- `DrawOnceChecks` 与 `reference/RVWallSurface.as` 中冻结的逐块重复绘制版本比较真实 AIR 像素，验证绘制优化不改变画面。该参考文件仅供测试。
- `SettingsChecks` 调用真实设置项及读写配置代码；测试副本的两处存储路径定向到本测试目录，正式源码保留原路径。旧配置缺键默认开启，非法值不改变默认值。
- `SoftHarness` 和 `SharedExplorationHarness` 保留已有逻辑视野、柔化和共享探索回归。
- 完整宿主副本按 baseline/off/on × classic/current 六组跑相同路线，检查原版光照、FOV、探索和敌人分类；逐段返回 AIR 事件循环，避免把整场测试挤在一次事件中。捕获世界图、阴影图和最终 Stage 图。
- 岩壁场景是原生训练房换用 G 材质并设置一处半高墙，不是用户截图存档复刻。重绘后补相机更新，世界图和最终 Stage 图分别保留。
- 每个 AIR 实例使用唯一应用 ID，窗口隐藏，退出后清理描述符；只终止本次创建的进程。测试资源使用明确路径守卫的本模组输出目录。
- `evidence.py` 只有在场景全部通过后才归档；开关不得改变前景 alpha=0 处的亮度，深墙芯必须全黑，修复不得影响远处地板。

配置键为 `wallbright=1/0`，设置项“已探索墙边常亮”。关闭只改变墙面亮度，两模式仍始终修复墙边阴影。

本轮不覆盖用户精确存档、全部材质、大型连续场景或全模组战斗。计时是更新与绘图开销，不能换算完整游戏 FPS。
