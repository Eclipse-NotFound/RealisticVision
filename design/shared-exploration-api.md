# 可选探索记忆接口 v1

2026-09-20，用户授权为 RConnect 增加协作接口，并明确不得形成硬性依赖。RV 不引用、不加载、不启动 RConnect；未调用接口时保留自身视野行为。

运行时在 `World.w.main` 发布名为 `RVExplorationAPI` 的不可见 `RVExplorationCarrier`，其公开 `api:Object` 包含：

| 成员 | 契约 |
|---|---|
| `version` | 数值 1 |
| `active(loc:Object):Boolean` | 当前房间由 RV current/classic 渲染时为 true；禁用、vanilla、基地透传等返回 false。 |
| `capture(loc:Object):Array` | active 时导出本地探索，其他情况返回 null，调用方使用原版适配。 |
| `merge(loc:Object, rows:Array):Boolean` | 只接受当前实例的当前房间和完整合法数据；按最大亮度与子格并集保留共享记忆。false 表示尚未准备或参数不合法。 |

调用方必须动态探测版本与函数是否存在，不能引用 `RealisticVisionMod` 或载体的 AS3 类型。使用原生显示树和普通 Object/Array/Function 传递，避开兄弟加载域的自定义类身份问题。Sprite 是封闭类，载体使用显式 `api` 公共属性，不能直接向普通 Sprite 临时赋属性。

`rows.length == loc.spaceY`；每行按 x 递增，每格 17 个小写十六进制字符：首字符是原版光照 0–15 的量化值，随后 16 个字符描述 8×8 子格曾见位。子格编号 `b = sy*8+sx`，第 `floor(b/4)` 个字符的 `1 << (b%4)` 表示曾见。尺寸上限 200×200。调用方负责网络房间身份/代际验证；接口还会检查传入 loc 与 World.w.loc/curLoc 是同一实例。整包验证通过后才写入记忆。

RV 分别保留本地和共享探索。共享层按 Location 对象隔离，不进入原有按 id 存储的个人 `roomMem`，避免共享数据污染同名新地图。current 合并子格、classic 合并瓦片记忆；墙面合并显示光照。亮度遵循本机配置，原版 visi/t_visi、FOV/currentSight 与瞬移/悬停判定保持本地。共享墙光也不扩大单位裁剪所用的 currentSight。

共享层在模式切换、关闭共享接收和断开连接后保留；读档/新世界按 RV 原有 resetOff 生命周期清除，不另建磁盘探索存档。接收开关归调用方控制。RV 总开关/vanilla 透传时，由调用方绘制原版共享记忆；再开启 RV 时恢复已有共享层。没有本接口的旧 RV 不保证新共享渲染，但不影响 RConnect 在未安装 RV 的原版环境独立运行。

测试入口：`build/shared-exploration/run_checks.py`；它只在测试副本中开放 private，运行 SoftHarness 与 SharedExplorationHarness。正式 SWF 只链接游戏存根，不能把测试公开字段版本、测试夹具或 fe.* 存根一起发布。
