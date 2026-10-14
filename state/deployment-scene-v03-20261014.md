# v0.30.4-scene 安装记录

用户在ContinuousScene任务授权必要兼容更新。本次大图仅按需复制currentSightData：场变化置空，粗判可见单位首次需要时才getVector；同帧复用。小图、FOV、共享探索、遮罩规则保持。

安装2026-10-14 23:10:26，25512B，SHA256 89B391BCE114534D6F2C0147BD4B136602168EE4362AA36F6F0C37ECD47173B5。源自0735491及ContinuousScene/build/compat_prepare.py，未包含HEAD的authority接口或RVAuthorityView及其检查WIP。

42项源码夹具（Soft16/Shared21/SceneSight5）、同字节全模组大场景48项、安装后原生启动15项通过。证据、计时对照和限制见../ContinuousScene/knowledge/experiments/preload-v03-20261014.md（相对mods目录）。当前大图完整行走55ms中位/p95 73ms，未稳定30帧；未验证联机或密集长时战斗。

release/config.txt仍5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F。备份ContinuousScene/build/backups/upgrade-v03-20261014-231026/RealisticVisionMod.swf，原SHA ED76EC15666FD8CD50ACF0149F7EC32F2602D2E68D753580A0EC5814B95A2E99。整体回退ContinuousScene/build/rollback-v03.ps1，保留共享清单/配置/存档。需重启生效。
