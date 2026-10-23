# D41 移动明暗边界与敌人遮罩

冻结基线：D39生产六类，83D8…205C7E65；禁止直接编译含authority的开发树安装。

1. `prepare.py`、`candidates.py`、`candidate03.py`只创建新目录，不覆盖历史。
2. `measure.py`沿用D40修正后的父层取图，stress区分数量/脚本位移，extent验证静止墙光写出视口后完整清理。像素与性能轮分开。
3. `render.py`检查动态BitmapData填充对身体/血条/独立武器的逐帧同步；首轮夹具错误保留，第二轮589项通过。
4. `native_walk.py --lean`使用真实方向键/射击、12窗口，原生世界非确定性；`weapon.py`保留旧漏武器正例。
5. `select.py`仅更新选定生产快照版本；`package.py`构建六类与真实设置两进程；`development.py`只把本轮差分应用开发树。
6. `review.py analyze`汇总，`accept.py`记录人工审视的有限收益与局限，`review.py verify`固定功能/字节/加载/依赖证据。
7. `deploy.py`通过正式登记，备份、原子替换、实际路径隔离启动及失败回滚；`finalize.py`归档报告/自身状态；`closeout.py`只暂存自己的变化，保留四项authority WIP。

所有AIR/编译用共享测试登记，独立应用ID/存储/隐藏桌面；不操作玩家游戏。输出位于忽略的`build/boundary-load-output`。不要重跑已存在目录。继承驱动部分登记标签含旧D35，实际版本由精确源和SHA确认。

沿用KB-000107 r2的取图/观察器限制，回读KB-000106 r1核对缓存分工；本轮新方法沉淀为KB-000108 r1（SHA 5c4529756c3f3f6ad9bf7e45672e433747ad9965dabb451246e516a36390f529）。查询有无关源不可读，不作全库穷尽声明。归档沿旧轮次以`-text -diff`保留原始CRLF/二进制证据，逐文件校验Git内字节；可编辑源码和报告仍正常检查差分。
