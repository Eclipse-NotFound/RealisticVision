# D55：相同原生特效批次回放

入口为 `run.py` 与 `SavedReplayProbe.as`。初建用的 `prepare.py`、`Replay.as.inc` 保留历史，不能重跑覆盖后续修订；`stable*.py` 和 `prepare_native.py` 同样只允许首次生成。

基线固定为 D44 准确生产源 `build/combat-render-output/production-final2/src`，正式包仍 v0.33.10。所有实验写 `build/effect-replay-output/<新名称>`，共享测试登记、唯一 AIR ID、独立存储、静音及私有桌面运行。私有存档种子只读复用 D54，不能提交或写回玩家目录。

## 对照边界

- 原生轻机枪开火270帧后取当前存活的 Part/Bullet，暂停原生世界，用原生动画帧和固定位置曲线回放；不是精确重演玩家弹道，也不是完整游戏 FPS。
- 保留原显示层顺序、矩阵、颜色及原素材，验证原生对象寿命没有继续。每窗同样60帧输入，预热60、采样120，末帧无后续间隔不计。120帧上限仅用于回放阶段。
- `--validate` 比较60帧，不计性能；在两种实现间暂时卸下各自遮罩，但保留各自跨帧缓存。必须记录优化阳性，不能每帧销毁缓存后声称已检查时间复用。
- `--diagnostic` 的 fixed 对照取消位置运动，仍播放动画；它输入不同，只能用于归因，不能冒充优化。
- 前后存在其他 AIR 时帧计时只作诊断，功能检查仍可用。清理仅结束自己登记的实例。

## 工具

- `check.py <新名称> --stable --stable-v4`：1081项，含动态视野、静态视野中的移动、两模式、实际父显示树缩放/平移、多个柔化设置。`--explain` 保存失败对象与低分辨率样本差异，不能据此独占归因 GPU 或缓存机制。
- `run.py <新名称> --candidate --stable-v4 --plain --full --native-screen --private-visible [--validate]`：同批原生动画回放。另有 `--identity`，使用并核对 D47 冻结候选；`--identity-blit`只处理单个位图子对象。两者均未采用。
- `native_run.py <新名称> --candidate --plain --full --native-screen --private-visible --solo --sweep`：D54已纠正的真实原生扫射驱动，默认绑定 stable-v4；`--identity-blit`选另一候选，`--reuse-18`检查源相同后复用18轮字节。19用`--both --reverse`反转两模式对照。
- `native_check.py`：已准备的后续原生全类型回归入口，仅生成文件不等于已运行。

本轮21次运行已结束。stable-v4没有完整扫射收益；identity与identity-blit有最终像素反例，均未采用。候选及实验 SWF 不能安装。完整数据见`knowledge/experiments/2026-10-28-effect-replay.md`及对应归档。`finish.py`只为本轮收尾运行一次，`register_report.py`追加台账且查重。
