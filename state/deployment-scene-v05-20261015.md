# v0.30.5-scene 兼容部署记录

2026-10-15 16:18:17（UTC+8），按用户允许 RealisticVision、WallBlend 必要大场景兼容修改的授权，随 ContinuousScene 0.5 四目标更新安装。正式路径原生启动检查15/15通过，实例标识为 `pfe-modsettings-continuous-installed-20261015161849`。安装回执与验证摘要以[ContinuousScene部署回执](../../ContinuousScene/state/deployment-v05.json)为准。

| 项目 | 已安装值 |
| --- | --- |
| RV版本 | v0.30.5-scene |
| RV SHA256 | `B7695DF82AA45FDB783C4EB88AFFCB0C34A7674E3A052D2FD128867172A83A49` |
| 宿主SHA256 | `9987C696BEBBEB0626D8F73DA775CF867B2CED4FF626137FD9F161264270F938` |
| 冻结源码基线 | `0735491e49d0d286ea8847017ae2fb64067a3c71` |
| CS兼容源码包提交 | `0b34d7b`（ContinuousScene仓库，可复建入口） |

产物由上述已发布生产线叠加 ContinuousScene/build 的兼容生成脚本产生，冻结源码位于 ContinuousScene/build/generated/rv-production；不是本模组HEAD的直接构建。保留此前视野向量按需复制，本轮修正大场景镜头范围与刷新，并在保留全图逻辑扫描和即时门/水/破墙变化的前提下，减少重复数组访问与纯查询。普通房间、classic及AI视野规则保留。没有发布独立authority接口，也没有把RVAuthorityView及其检查、记忆中的其它未提交开发内容并入产物；后续切勿以HEAD未经核验直接覆盖当前安装。

验证范围：

- RV独立42/42：Soft 16、SharedExploration 21、SceneSight 5，证据 `ContinuousScene/knowledge/experiments/evidence/rv-v05-20261015-143227`。这是冻结候选源只开放测试访问并配游戏存根的夹具，并非直接加载已安装产物；不代替真实宿主组合验证。
- 最终9987C696宿主组合：Experience 111/111、Factory 34/34及内容/像素审计10/10、完整Lab 68/68通过；两轮独占无插桩Perf完成。正式原生启动15/15检查另见部署回执verification。
- 测试证据、像素判定边界和保留失败见[主报告](../../ContinuousScene/knowledge/experiments/experience-v05-20261015.md)。残余长帧和较高进程内存仍存在，不宣称达到原版稳定流畅；未认证多小时、全部战况、完整联机或DLC。

运行配置、清单、正式工厂XML和玩家存档不由本次兼容记录改动。备份由 ContinuousScene 统一管理：`ContinuousScene/build/backups/upgrade-v05-20261015-161817307-8a1b6645`，安装前RV为v0.30.4-scene（`89B391BCE114534D6F2C0147BD4B136602168EE4362AA36F6F0C37ECD47173B5`）。

回退只经 `ContinuousScene/build/upgrade-v05.ps1 -Action Rollback`，按本次四目标回执和指纹恢复；不得使用旧v0.3回退或单独复制历史产物覆盖同期Map1、WB0.5.3及RC/MSW更新。部署/回退后需玩家保存并正常重启，既有运行进程不会自动换版本。本条更新部署状态，原记忆与日志内容完整保留。
