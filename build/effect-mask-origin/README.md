# D56：轻机枪持续射击

已部署v0.33.11-effect-clip；结论与完整数字见 `../../knowledge/experiments/2026-10-29-effect-mask-origin.md`。

最终采用 `grid_current`：current保留原遮罩采样格，缩小每个独立特效的显示范围，真实输入变化时重新绑定目标遮罩；classic沿已安装路径。准确私有生产源在 `../effect-mask-origin-output/production/src`，不能用含authority开发接口的HEAD整包替代。

- `prepare*.py` 是已经执行的单次历史生成器，不能覆盖旧目录重跑。
- `check.py` 比较人工动态位图。`--fresh-current-reference`在current按原算法每帧重建参考，classic保留跨帧缓存；只用于功能，不将其CPU时间作性能排名。
- `run.py` 捕获同批原生特效并回放；像素轮换会解除mask关联，不能验收连续关联缓存。计时窗不会逐帧解除。
- `native_run.py` 完整原生扫射，实际最大化尺寸、私有桌面可见、静音、唯一存档副本；`--reuse-from`先核对源再复用对应SWF和依赖。
- `package.py` 构建准确包、核对六个类并验证两进程设置。`smoke.py`已执行于production-smoke-29，不重跑覆盖。
- `deploy.py`已完成本机定向替换，先验证证据/并发指纹，再备份、原子替换及失败回滚。
- `integrate.py`将验证的修改同步开发源码，保留authorityView写入；不重跑覆盖已同步源。

所有失败方案均为实验记录，禁止安装。后续测试使用新名称并经共享登记。源码、生成夹具与二进制采用内容去重归档，原路径到内容的映射见归档的object-map.json；存档副本不进归档。
