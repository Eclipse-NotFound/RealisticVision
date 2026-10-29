# D57 六敌交战诊断

正式保持D56 v0.33.11；本目录三个候选均未获稳定完整战斗收益，不部署。
报告：`knowledge/experiments/2026-10-29-enemy-combat.md`。
冻结证据：`knowledge/experiments/enemy-combat-d57-20261029/`。

入口 `run.py` 使用唯一AIR ID、共享登记、静音与独立桌面。以正式生产源的
冻结副本为基线，不编译开发HEAD。所有输出名称必须新建，prepare脚本是
单次历史生成器；不要重跑来覆盖候选或旧证据。

本轮最终驱动：原生 `mainMenuOff()` 摘菜单；原生更新前固定狮鹫位置，
使身体/手臂/武器同步；开火数为采样期kol_shoot正差值下界。
参数 `--candidate --source=effect_alloc --sweep --solo --private-visible
--native-screen --full --plain --both --native-timing` 是21轮条件；
22加 `--reverse --reuse-from=21-allocation-combat`。solo移除随机原生单位，
仍生成六狮鹫。不可当零敌人或纯自主AI。

`--memory --short --plain --both --native-timing` 是19归因路径，不传candidate。
净内存变化不等于分配量；嵌套阶段不能相加。`--render-phases` 的RENDER后
区间包含调度等，不能解释成GPU独占。

`check.py`/`MaskRenderChecks.as` 验证身体候选；`alpha_check.py` 验证透明
内容裁切；`alloc_check.py` 验证去掉未使用m3及首像素判定。正式像素证据
09/13/20分别1531/722/723项，14原生同批60帧。功能通过不表示性能通过。

`finish.py` 只归档，不部署或提交。源码和测试SWF按内容去重，object-map
映射原路径；大原始JSON无损gzip，compressed-map记录压缩前后哈希。
播放器存档、Local Store、种子和重复运行素材不入库。22次实验含3次编译前
失败、多个像素反例及未修正驱动，只有报告指定的68窗用于纠正后的交战统计。
