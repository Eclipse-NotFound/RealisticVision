# RealisticVision —— Agent 工作范围

> 完整治理规则见工作区根目录 `GOVERNANCE.md`（权限模型、知识库、参考区、游戏文件修改、外置记忆协议、同步与镜像）。
> 本文件只记录本模组的参数与特例。开始开发：读本文件 → 读 `state\MEMORY.md`（记忆入口）。

## 项目参数

| 项 | 值 |
|---|---|
| project | RealisticVision |
| workspace | mods/RealisticVision/ |
| repository | 本目录为独立 git 仓库 |
| 运行时入口 | release/RealisticVisionMod.swf（入口类 `RealisticVisionMod`，`public static init(main)`） |
| 记忆入口 | state/MEMORY.md |

## 本模组特例（相对 GOVERNANCE 的偏离/补充）

- `release\config.txt` 是运行时配置（路径硬编码于模组源码 `File.applicationDirectory.resolvePath("mods/RealisticVision/release/config.txt")`，勿移动）。
- 构建走存根 SWC 路线（acompc 产 GameStubs.swc + amxmlc external 链接；存根只留 build\ 绝不随 release 发布），细节见 `remains-mod-build` 技能。
