# 菜单改键统一部署（2026-10-15）

已安装并验证。用户在统筹会话01a13f40-6ca2-7872-9f9a-c1e453e80745明确选择“安装剩余六个（推荐）”。本记录只确认改键部署，不发布源码目录其他实验。

- 正式文件：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/release/RealisticVisionMod.swf
- 安装SHA256：`E99608088A8B00B4442BC3AEF52D8035336F0123EA5A96D55503C90B1F6E0808`
- 原文件SHA256：`B7695DF82AA45FDB783C4EB88AFFCB0C34A7674E3A052D2FD128867172A83A49`
- 精确备份：D:/Program Files/Steam/steamapps/common/Remains/mods/ModLoader/build/backups/before-keybind-clients-20261015-214440-393ca9a3/RealisticVision/RealisticVisionMod.swf
- 源候选：D:/Program Files/Steam/steamapps/common/Remains/mods/RealisticVision/build/keybind-output/candidate/RealisticVisionMod.swf

安装时间：2026-10-15T21:44:41.4244524+08:00。正式ModLoader BD71、FA B330与七客户端共同读回验证：首进程175项、重启171项；本模组改键按钮、精确组合、显示宽高、跨进程保存和默认恢复通过。各客户端更深入的实际动作验证保留在keybind-integration-2026-10-15.md，不把联合计数当作全部战斗或DLC验收。

统一回执：../../ModLoader/build/out/keybind-client-installation/deployment.json；稳定证据及说明：../../ModLoader/state/keybind-integration-2026-10-15.md。回退在游戏退出后调用ModLoader/build/deploy-keybind-clients.ps1 -Action Rollback，先核对六个目标仍为此次指纹，禁止覆盖后续部署。若出现更晚安装，应按更新的部署回执协调回退，不直接复制旧备份。

源码中未发布的B、墙面/曳光或灯光优化保持各自WIP所有权；后续版本须保留本轮按键适配器和菜单。此部署未改用户真实存储与加载清单，没有强制重启玩家实例，重启游戏后生效。
