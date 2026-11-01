# 正式 combo-v4 性能切口普查

本目录只生成独立计数版，不提供部署候选。准确生产源来自
`build/mask-budget-output/production-combo-v4/src`；安装指纹 AEA30314…9AA557。

`prepare.py` 首次冻结当前宿主、启用组合和准确生产源，禁止覆盖已有输出。
`run.py` 核对并复用 `build/maximized-flow/run.py` 的隔离、静音、登记和退出实现；
实际生成的运行器、测试源与所有字节指纹保存在新的输出目录。
`instrument.py` 只加计数；不跳帧、改遮罩、隐藏特效或改判定。

诊断包含两模式各固定/受控位置扫动，共四窗；每窗45预热+180采样。
玩家位置扫动不等同方向键物理跑步。六名狮鹫、原生轻机枪/SMG和所有原生
弹体/粒子照常运行。函数包装和计数有额外开销，不能用它验收提速。

```text
python -X utf8 build/performance-survey/prepare.py
python -X utf8 build/performance-survey/run.py 01-census --full --solo --sweep --both --no-cpu --private-visible --maximize
python -X utf8 build/performance-survey/history.py
python -X utf8 build/performance-survey/analyze.py 02-census
```

运行期间不打开进度JSON；只在结束后分析结果。旧最大化/裁切/共享掩膜等
失败证据继续保留；统计“少做了多少工作”不等于完整帧已经更快。

本轮01因探针仍校验旧实验输出目录而保存失败；已修正检查目标，未删除保护。
02用 `--reuse-from=01-census` 复用相同RV字节及源，四窗720采样帧完成，
716完整帧间隔。74769次显示对象处理未发现同帧重复，移动current输入比较
97.56%相同，classic固定/移动99.37%/99.57%相同。墙轮廓重建均为0。
这些是下一步原型的工作量依据，不代表已实现提速。本轮没有生产改动或部署。

`archive.py` 单次冻结终态证据，不收集游戏资源和玩家存储，拒绝覆盖已有归档。
结果与限制见 `knowledge/experiments/2026-11-01-performance-survey.md`。
