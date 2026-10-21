被测技能：remains-mod-memory、remains-mod-build、remains-auto-testing、remains-runtime-debug、remains-release-gate、remains-swf-patching、diagnosing-bugs
技能归属：Remains工作区；diagnosing-bugs为用户级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains

# D34：视野显示与最大距离设置

2026-10-21，用户确认房间视距倍率0.5–3、默认1，以及分模式柔化并保留原生墙内渐变。已部署v0.33.0-vision-settings。原“记忆区暗度”实际是亮度，修正反向文案并保留dim键及保存值；新增soft_current、soft_classic、viewscale。原版模式/总开关/基地透传、原版visi/t_visi/地图传送/AI字段不作修改。

## 实现与兼容

- 默认亮度0.35、current柔化尺度20px、classic附加柔化0px、视距倍率1。设置即时保存，原地重算而不重置房间，避免丢失子格探索。空/非有限配置回落默认，超范围钳制；中英俄菜单均有说明。
- current仅调显示滤镜；classic附加柔化后重新接回原墙场。敌人使用独立逻辑输入。自定义classic记忆亮度时，基准逻辑遮罩与可调显示分开计算，不将高亮记忆区送入敌人遮罩。
- 距离的全亮半径与最大半径同步缩放，动态读取房间参数。倍率不是1时，在模组内采样角点光照，沿原版的步进及减法遮光规则；不调用原版lighting写入。原生已有亮度继续保留。扩展记忆随房间保留，世界重置清空。
- 生产源从已部署D32准确六类源派生，保留D31性能与D32阶梯修复；不混入authority工作。并行D33运动性能候选未在本次安装，未来合并须保留本次设置，不可覆盖较新的release。

## 验证

251条断言：90设置与默认等价、16原柔化回归（含1000条射线）、21共享探索、88原生训练房、36准确生产包两进程设置/快捷键/心跳。原生测试有两模式×常亮开关×两位置；8组默认和恢复默认最终雾层均逐像素相同。高亮记忆与额外柔化不改变逻辑位图/探索数组；倍率放大能看到更多无遮挡格、无法穿墙；原版字段和距离值不变。人工已探索夹具验证亮度从全黑到明亮且FOV仍不可见。房间往返保留扩展墙光记忆。

正式路径独立AppID、独立桌面启动：新版init、ModSettings注册、tick1/181/361均通过；只关闭本轮实例、移除本轮描述符。包仅六类，无fe存根/测试探针/authority。具体字节与原始日志见[证据目录](vision-settings-v0330-20261021/verified.json)。

## 边界及真实过程

- 本次是功能及像素验收，没有测完整战斗FPS，也没有验证所有玩家存档/所有联机组合。大视距、宽柔化和自定义classic亮度会增加工作量，不承诺免费获得更大范围。
- 原生墙内算法保留，包括D30已记录的开启常亮时隐藏参考层1/255取整差；本次默认等价使用D32完整最终图，未将历史残差抹成全绿。
- 早期组件按offline登记，曾与RConnect性能轮重叠，对方独占检查拒绝了那轮，未产生有效性能数据。已改所有AIR组件使用game占用；原始登记保留。
- 新启动器接入首轮缺application.xml、catalog，随后探针名不满足Mod后缀；均在启动前报错，补齐隔离副本和入口名后成功。不改正式名单，不以命令退出0代替检查输出文件。
- 共享知识两层检索为partial，有无关来源不可读；性能方法沿KB-000056边界，不据此声称全库无经验。

## 部署与回退

新包SHA256：`8D4A19634770ACCA0B66C8C684955855EF4725E80FBDFF329451D69710C55BF1`，40,371B。旧D32：`76314B819151FBA6F67F6D740B21030A9EEC8359AF4C9C9DDEB83D4CAF5C46B7`。
备份：`build\backups\before-vision-settings-20261021-151427-0f4bec\RealisticVisionMod.before.swf`。只有当前release仍为本次新SHA时才可将该备份恢复到release/RealisticVisionMod.swf；遇到更新版本先核对合并，不覆盖。真实用户配置与存档没有写入。已有游戏须保存并正常重启。

精确生产源：`build/vision-settings-output/candidate/src`；构建/测试工具：`build/vision-settings`。部署回执见[receipt.json](vision-settings-v0330-20261021/receipt.json)。

收尾按绝对路径边界和保留源SHA逐文件核对，清理102份重复运行素材，共217,328,880B；生产源、候选包、截图、日志、配置及回退备份保留。清单见[cleanup.json](vision-settings-v0330-20261021/cleanup.json)。旧测试副本复跑前须按保留源哈希恢复素材，不覆盖历史证据。
