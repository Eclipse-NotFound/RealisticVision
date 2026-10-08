# RealisticVision — 视野与探索迷雾

[English](README.md) · **简体中文**

没去过的地方隐藏在黑暗中，眼前区域清晰可见，离开后只留下较暗的地形记忆；墙后的敌人不会继续显示。适合喜欢潜行与探索感的玩家。

**[下载 v0.30.1 — RealisticVision_v0.30.1.zip](https://github.com/Eclipse-NotFound/RealisticVision/releases/download/v0.30.1/RealisticVision_v0.30.1.zip)** · [发布说明 / 其他版本](https://github.com/Eclipse-NotFound/RealisticVision/releases)

点击上方链接下载成品。也可以打开发布页，展开 **Assets（下载文件）**，选择同名文件；**Source code** 和绿色 **Code → Download ZIP** 是源码，不能直接安装。

## 会带来什么变化

- 未探索、当前可见、已探索但看不见三种状态。
- 墙体破坏、门和玻璃会影响视线；记忆区保留场景和物品，不保留敌人。
- 可切换原版与两种模组视野模式，调整记忆亮度。
- 可配合 RConnect 接收队友探索记录，需双方各自设置。

## 安装

适用于 **Windows / Remains 1.02**。

1. 保存并退出游戏。Steam 库中右键 Remains → **管理 → 浏览本地文件**，打开含 `pfe.swf` 和 `application.xml` 的游戏文件夹。
2. 第一次装本系列模组，先完成 [ModLoader 首次安装](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.zh-CN.md#first-install)；它包含一次性游戏补丁和模组扫描器。已装好的玩家可跳过。
3. 解压下载的 ZIP，把里面的 **`mods` 文件夹合并到游戏文件夹**，不要套成 `mods/mods`。 首次安装时，将 `default-config/RealisticVision/config.txt` 复制到 `mods/RealisticVision/release/config.txt`；升级时不要覆盖原配置。
4. 双击游戏目录下的 **`mods/ModLoader/RemainsModScanner.exe`**，等待完成后关闭提示，再按平常方式启动游戏。

放对后应能找到：`mods/RealisticVision/release/RealisticVisionMod.swf`。进入可探索区域后应能看到视野变化；F11 可对比开关效果。

[图示文件结构、更新与恢复方法](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.zh-CN.md)

## 第一次怎么玩

| 按键 / 入口 | 用途 |
|---|---|
| F11 | 开启/关闭视野效果 |
| F12 | 在原版、经典和当前视野模式之间切换 |
| 哔哔小马 → 设置 → 模组 → 视野系统 | 调整亮度等选项 |

模式名称只在切换时短暂显示。模式与开关会保存；游戏内保存的设置会覆盖安装包配置模板，所以通常直接在设置页调整即可。

## 更新、停用与适用范围

更新前保存退出，备份 `mods/RealisticVision`，再合并新版文件、运行扫描器并重启；保留自己的配置。临时停用时，可把该模组文件夹移到 `mods` 之外备份，再扫描并重启。

本指引对应 v0.30.1 / Remains 1.02。营地等安全区可能保留原版显示。记忆亮度不会让隐藏敌人现身；复杂场景的性能仍会受机器与其他模组影响。

## 遇到问题

先检查：文件夹是否放对、是否运行过扫描器、是否完全退出并重启。通用问题见[安装与排错指南](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.zh-CN.md#troubleshooting)。

仍有问题，请到[问题反馈](https://github.com/Eclipse-NotFound/RealisticVision/issues)说明：游戏版本、本模组版本、其他已装模组、操作步骤、预期结果与实际结果；能附截图或报错原文更好。不要上传个人存档，除非排查时确有需要。

<details>
<summary>开发资料（普通安装无需阅读）</summary>

本页按可下载的发布包编写，仓库源码可能更靠前。实现见 [src](src/)；历史设计、验证和版本记录保留在项目目录中。

</details>

[查看全部模组及玩法介绍](https://github.com/Eclipse-NotFound/ModLoader/blob/master/README.zh-CN.md#choose-mods) · [首次安装指南](https://github.com/Eclipse-NotFound/ModLoader/blob/master/docs/INSTALL.zh-CN.md)

这是玩家制作的非官方模组项目，需要自行拥有游戏。
