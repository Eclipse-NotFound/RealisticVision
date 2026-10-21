# D35 下午性能回退调查

用户要求先回退。2026-10-21 22:17 已将准确 D32 v0.32.3 恢复到正式路径并复验。不要把 D33/D34 的历史发布记录当成当前安装依据。

最终：23:35 已部署 v0.33.2-settings-performance，41,630B，SHA7852F61E…BE86764。1731项及8个原生射击窗口通过；正式路径复验通过。准确生产源为 `production-singlepass/src`，当前安全回退备份为 `before-settings-recovery-20261021-233515-ab290b` 的D32。完整结果见本轮报告；回退/部署/状态收尾脚本为一次性冻结记录，不反复执行。

工具使用本机 Codex Python；所有 AIR 与编译均通过 ModLoader `Registration` 排队。AIR 仅用唯一应用 ID、独立存储、`HiddenProcess` 私有桌面。源和证据输出到 `build/regression-recovery-output/`，每次新目录；不重建历史目录。`src` 还有未发布 authority，不能整包编译用于部署。

- `rollback.py`：核对 F2B8A→76314 的精确指纹、备份并原子恢复、正式路径隔离启动；不是通用覆盖命令。
- `investigate.py build/run/analyze --name <新名> --left d32|d33 --right fixed...`：大图同输入交替对照。`--profile` 仅归因；`--verify` 另跑严格图像；`--live` 用已有原生持枪敌人驱动及实际攻击/弹丸断言。计时不能混用这三种模式。
- `checks.py build/run --name <新名> --source fixed...`：1536 项逐像素/按需遮挡、90 项设置、16 项柔化、21 项共享探索。仅用于测试的公有导出不进入正式包。
- `prepare.py`：第一版，只按需完成墙边子像素。`prepare_late.py`：增加局部原生位图合成，16 子像素取样缓冲、首帧初始化。`prepare_persistent.py`：分离显示与固定亮度的低分辨率样本。`prepare_singlepass.py`：一次地形扫描生成两份样本，分别保留最深邻居选择。
- `production.py`：准确六类生产包、两进程 36 项设置入口/保存验证；不部署。`review.py`钉住最终证据及宿主，`deploy.py`仅将准确D32安装更新为已验证包，启动失败自动恢复D32。`archive.py`将小体积原始证据归档；`cleanup.py`只删本轮与正式素材哈希相同的副本，保留源、包、唯一宿主和备份。

历史候选保留：`candidate` 的大图开销仍偏高；`candidate-v2` 的 1px 缓冲存在 1/255 误差；`candidate-v3` 扩展缓冲后暴露首次改亮度的空缓存；`candidate-v4` 已修正这些问题，但对 D32 的 60% 亮度基准仍多约 7% 更新耗时；`candidate-v5` 独立低分辨率缓存仍多约4%。`candidate-v6` 单遍历方案通过1663检查和32原生图像点，对D32四组更新加绘制均值下降3.8%～21.6%，current默认组最大峰值仍上升。以最终报告和冻结指纹决定可部署产物，不按版本字符串猜测。

最终轮：`checks-09`、`baseline-trial-05`（D32直接性能）、`final-native-01`（D33画面对照）、`final-combat-01`（D33原生射击）、`production-singlepass`。取图/归因轮不用于性能资格。`defer-next-test.json`可记录本任务主动让出的短时窗口，到期后仍须取得共享登记；不释放或抢占别人的测试。

逻辑缓存改为按查询区域完成。测试会主动补齐整间房所有可被敌人遮罩读取的像素再逐点比较；从不读取的房间外缓冲不构成功能契约。显示雾图、墙影与最终合成画面仍整图严格比较。早期全缓存比较失败与 1px 缓冲内实际取样误差分别记录，不能混为已通过。

收尾已删除649份同哈希运行素材（1,397,476,928B），恢复清单在output/cleanup.json及证据归档。重跑前逐项比较正式源哈希与清单，只有相同才可复制回对应隔离路径；来源变化须找准确旧备份或新建实验，不能绕过build.json指纹。release、唯一输入、生产源与回退包未删。
