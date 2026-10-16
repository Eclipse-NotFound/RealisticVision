# 构建目录清理与素材恢复

2026-10-16，按用户要求清理本模组积累的无用文件。删除了1,397份内容相同的测试运行素材副本和12份Python字节码，共1,409个文件。文件路径的逻辑大小合计3,011,619,522字节；扣除原先已有硬链接的重复计数，独立文件大小为2,088,775,421字节，约2.09GB。

源码、编译产物、独有测试数据、原始日志/截图、knowledge/对照页、当前release及全部回退备份保留。每个被删除的素材都有SHA256相同的本地恢复来源，共53份；没有新增硬链接。删除前后核对1,427个源码、证据、安装和备份指纹均通过。磁盘空闲量同期还有其他变化，不能把整个磁盘的变化都归因于此次清理。

清单与结果：[plan.json](../state/cleanup-2026-10-16/plan.json)、[receipt.json](../state/cleanup-2026-10-16/receipt.json)。计划中的保护指纹对应清理发生时的状态，后续正常编辑源码或记忆后会有预期差异。

以下冻结输入继续保留原址，后续开发不要把它们当作重复缓存删除：

- `wall-restore-output/game-rock/`：D28冻结的声音、贴图、语言、Rooms与旧宿主。
- `wall-performance-output/runtime-inputs/pfe.swf`：D29实测宿主。
- `wall-options-output/game-rock/pfe.swf`、`motion-test-output/game/pfe.swf`：其他不同指纹的历史宿主。
- 各候选/基线的`src`、已冻结模组SWF和`backups/`：生产来源、对照和回退。

部分旧实验目录不再直接包含完整游戏素材。重跑其`run-game`前，从RealisticVision目录用Codex runtime Python恢复所需目录，例如：

```text
python -B -X utf8 build/cleanup_runtime_duplicates.py restore --prefix build/wall-performance-output/game-reuse/
```

恢复仅复制缺失的文件，校验来源和目标指纹，不覆盖已有不同内容；不影响正式游戏。字节码由Python自动再生成。清理脚本用`plan`生成计划，必须显式选择`apply`才删除；本次计划和回执禁止覆盖，不要重复执行历史清理。
