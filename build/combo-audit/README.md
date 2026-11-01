# v0.33.15 combo-v4 审核工具

用途：只在本模组新建副本中重放真实轻机枪，审核生产源；不构建到release、不改真实pfe存储。结果与局限见 `knowledge/experiments/2026-11-01-combo-audit.md`。

- `prepare.py`：首次冻结D56与v4的准确生产源/原包，记录输入。已执行，不能再次覆盖。
- `run.py`：沿D58专用驱动派生。必须用新目录名；唯一AIR ID、私有桌面、静音、独占登记。`--reuse-from`复用冻结的测试代码、依赖模组及宿主，宿主仅覆盖新建副本。计时不是正式字节直接运行；生产源加public访问/计数器/诊断开关的差异需保留。
- `native_check.py`：只读核对已有FFDec导出的75个主入口/主循环方法体。当前安装已变C6，不能盲目重跑固定8321检查；`native-source/checked.json`是本轮冻结宿主的依据。
- `SavedFireProbe.as`：真实存档副本、原生LMG、受控六狮鹫或零敌人。`--solo`仅清除随机怪；零敌人还须 `--zero-enemies`。相邻窗不重载地图，随机数/动态世界有自然差异，必须往返比较。
- `AuditChecks.as`：计时后才执行的合成几何与受控原生单位反例；08另以D56独立对象作图像参照。不要将清缓存重绑快照自动当正确基准。
- `collect.py`：重新检查真实开火、窗口active、每间隔一次World.step、分段总和，区分完整计时与后置检查失败。
- `archive.py`：一次冻结报告证据，排除存档、重复媒体及其他模组二进制。已经冻结时不得覆盖。

实际序列（以下为运行参数记录，不应全部重跑）：

| 目录 | 参数重点 |
|---|---|
| 01-large-pair | `--candidate --pair --sweep --solo --private-visible --native-screen --full --plain` |
| 02-small-pair-checks | 同01，去native-screen，增加`--reuse-from=01-large-pair --audit-checks --native-timing`；后置PNG路径失败 |
| 03-large-diagnostic | `--v4-only --diagnostic --sweep --solo --private-visible --native-screen --full --plain --native-timing` |
| 04-large-solo | 同03，将diagnostic换为`--zero-enemies --idle-pair --audit-checks` |
| 05-large-noeffects | 同03，将diagnostic换为`--noeffects-pair --reuse-from=03-large-diagnostic` |
| 06/07 | 宿主漂移检查阻止启动；没有计时 |
| 08-audit-only | `--candidate --audit-only --audit-checks --sweep --solo --private-visible --full --plain --reuse-from=01-large-pair` |
| 09-large-fog | 同03，将diagnostic换为`--fog-diagnostic --reuse-from=03-large-diagnostic` |

所有计时默认warmup90 + sample180、current、dim=.6、soft_current=25、wallbright=false；其他模组随冻结名单，LAD按此前约定排除。窗口原生激活仅在私有桌面；01–04每帧调用activate，05之后仅inactive时调用，差异计入报告边界，不能跨轮直接排名。撤罩、跳过特效或隐藏fog都改变画面，只用于归因。
