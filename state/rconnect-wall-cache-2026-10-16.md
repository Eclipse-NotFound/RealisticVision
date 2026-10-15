# RConnect 联测：墙面比较缓存（未部署）

用户在 RConnect 主会话明确批准 `mods/RConnect/design/a33-rv-wall-comparison-proposal.md` 所述局部优化、测试、与 RV 协调及合格后部署。RV 会话 `01a088fa-b17e-7fc1-85bc-b767327bf4fd` 已只读确认准确生产线并交出该文件和 AIR 测试窗口；没有覆盖其它工作或旧候选。

仅修改 `src/RVWallSurface.as`：保留每帧高度、已探索、亮度采样及绘制，将三组字符串签名改为持久数值缓存。中途回调异常保留 dirty 状态，NaN 比较沿用原字符串行为，换房、视口和 reset 使缓存失效。设置、视野、亮度规则、回调顺序和绘制频率不改。

- 正式版本仍为 v0.31.1，SHA `baa48289d9cf86f64cff53b4734032ad29c89c3ac1704db2d89038d4b8db4275`。
- 源码基线为 `build/wall-options-output/candidate/src`，原 helper SHA `d5142d3d9d9885b804628cf7ac12c4fa9320c48c33dd62bf1101759dc8a2b7fd`；保留改键、多语言和 CS 兼容，未带入 authority WIP。
- 候选在 `../RConnect/build/m52/a33-rv-wall-01`，版本 v0.31.2-wall-cache-candidate，SHA `5470892dada3154b466ee75adbd68ecb81f97ae00ca19c4e1e77b573a6414ab3`。只有 helper 和入口版本与准确生产基线不同。
- 新旧实际 AIR 绘图/回调顺序/重绘次数/几何/异常恢复/NaN 对照 491 项及已有 BoundaryChecks 27 项通过。源与结果在候选的 `checks/`。
- 原生训练房金属 76 项、岩壁 77 项状态检查通过；两模式、常亮开关、上下眼位的 32 对整幅画面/雾层逐像素相同。检查同进程、相同原生场景和路线，诊断构建仅将 private 暴露供既有探针读取。结果在候选的 `native-scene/{metal,rock}/`，不把这项渲染对照当作完整战斗验收。
- 配 RConnect fix33 的无采样密集运行 `6518802013`：主 25/0、加 43/7，七窗 58–68 帧/8秒，P95 152–195ms。仍未达到 80 帧/8秒门槛，**不部署**。原房敌人/入口的跨轮随机差异尚在，不能据旧轮数值宣称严格等工作量的收益。

测试结束即清理重复运行资产，保留冻结源、驱动、日志、失败和 PNG；安装、配置和真实存档未写。RConnect 正在继续编码耗时与密集采样，并负责最终联合门禁。如后续合格，回退点须备份当前 BAA48289 墙面版，不能沿用旧 E996 改键备份或旧联合回退。

实际修改和部署由 RConnect 主会话 `01a086bb-378c-7f60-b8e1-50d90ffa0996` 统一接续。不要运行旧 wall-options 的 prepare/build 覆盖历史候选。
