# v0.30.0 候选：可选共享探索 API

2026-09-20，RConnect 共享探索任务按用户明确授权修改本模组：各端独立开关、关闭后保留，共享显示遵循 RV 自身规则，不引入相互硬性依赖。当前仅候选，未替换正式 release。

新增 `RVExplorationCarrier`，在 main 显示树公开 `active/capture/merge` 普通对象回调。RConnect 只按名称动态探测；RV 没有 RConnect import/加载/网络代码。格式与调用规则见 [API 契约](../../design/shared-exploration-api.md)。共享历史与本人探索分别存储，按 Location 实例隔离，current 保留 8×8 子格边界，classic 按瓦片记忆；墙面光只改变绘制，不改变单位 currentSight 或原版 visi/t_visi。退出接收、断线和模式切换保留；新世界按原生命周期清除。

## 实测

- 原 SoftHarness：16 PASS，包含 1000 条缓存/实时射线、部分门/水变化、同尺寸换房、模式切换、掩膜边界与柔化回归。
- SharedExplorationHarness：21 PASS。实际调用公开接口并采样 fogCache/classicMemoryRaw/currentSight：共享子格在 dim=.35 时 alpha=166、dim=.8 时 alpha=51；相邻未探索子格保持 255，classic 记忆色随配置改变。共享前后本地 fov/explored/seenSub 与 currentSight 不变；共享墙光也不扩张单位视线。模式切换保留，同名新 Location 隔离，返回原 Location 恢复，resetOff 清理。
- 独立测试完全没有 RConnect；新 RV 普通候选又随 RConnect 在真实游戏双实例 `e6c6df2924` 完成 104 PASS，确认兄弟加载域之间回调实际可用。普通候选组合启动 `510c982aa5` 初始化/连接/心跳通过。
- 本模组本地夹具证据：shared-exploration-v0300/SoftHarness.log、SharedExplorationHarness.log；复现脚本 build/shared-exploration/run_checks.py。联机结果及指纹汇总位于 RConnect 的 knowledge/experiments/m31-validation-evidence.json。

第一轮公开接口用普通 Sprite 临时写 api，实机报 #1056。改为显式声明 public api 的载体类后通过；没有部署失败版本。测试源仅在独立输出副本将 private 暂改 public，正式源码没有开放内部数组。

普通候选 `build/shared-exploration/RealisticVisionMod.swf`：22310 字节，SHA256 `ce3abb8d1321df4f2a6e1053ecbb44aabff66a6e27f81b517d3a341b3a8dfb5b`。FFDec 类列表只有 RealisticVisionMod 与 RVExplorationCarrier，未嵌入 fe.* 存根、测试夹具或 RConnect 类。

## 边界与同期改动

原 v0.29.0 的性能/所有狭缝/用户具体存档边界仍在，未把夹具断言当成长时间全模组战斗验收。共享记录没有新增磁盘持久化；原版透传时由调用方负责共享绘制，接口也可在没有调用者时一直空闲。

工作树同期存在另一任务的 ModSettings 注册迁移，已经由该任务独立提交为 eb92773。候选按包含这段迁移的实际工作树编译，未回滚迁移；本任务接口叠加其后提交。另以 992622b 规范该部分暂存留下的九处 CRLF，使功能差异可正常审阅，空白忽略检查确认无语义改动。正式部署前仍需核对最新源/产物，正式安装以原 v0.29.0 部署回执为准。
