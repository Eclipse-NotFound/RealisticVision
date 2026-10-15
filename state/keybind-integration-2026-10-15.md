# RealisticVision 菜单改键

当前：最终候选组合验证通过，未部署。

- `realisticvision-hotkeys` 提供调试显示 F10、总开关 F11、渲染模式 F12；精确组合键、清除/恢复默认、冲突提示及即时本机保存，设置文件 `RealisticVision.hotkeys.json`。与联机的既有 F10 共用保留并标记。
- 输入框、原版改键、控制台和菜单期间让位。念力过滤改为跟随当前 `ctr.save().keyTele`，保持原版念力设置的权威性；不是第四个自有快捷键。
- 正式安装仍为 `0.30.5-scene` / SHA256 `B7695DF82AA45FDB783C4EB88AFFCB0C34A7674E3A052D2FD128867172A83A49`。候选基于 `build/wall-surface-output/baseline/src` 的精确生产源码，保留 ContinuousScene 0.5 兼容，不带 HEAD 墙面常亮候选或 authority WIP。
- 构建 `build/keybinds/build.py`；最终候选 `build/keybind-output/candidate/RealisticVisionMod.swf`，版本 `0.30.6-keybinds-candidate`，29098 B，SHA256 `e99608088a8b00b4442bc3aef52d8035336f0123ea5a96d55503c90b1f6e0808`。回执 `build/keybind-output/candidate.json`。选项面板和调试提示随当前绑定显示；八条新翻译同时进入messages.json正源与AS3目录，避免生成器覆盖。
- 同字节最终七模组346项组合通过（首进程175、重启171），包含本模组三按钮录入、精确匹配、显示宽高、跨进程保存和三项默认恢复；真实舞台事件实际切换总开关与渲染模式，旧F11和额外修饰键不触发。公共服务BD71B6F3…F4908B1的独立39项含中英俄和持续按住也通过。证据在ModLoader/build/out/menus/keybind-all-fit-20261015及keybind-core-fit-20261015。
- 首轮动作断言误读 app 目录旧 config 而失败；已改为检查实际 `applicationStorageDirectory/RealisticVision_config.txt`，原失败记录保留。编程事件经过实际游戏监听，未认证真人键盘或DLC/联机战斗。
- 本轮只改按键输入及新标签；现有墙面选项、authority、记忆/日志中的其他任务更新保持各自所有权。正式 release 与真实存档未动。
