# D32：将阶梯修复合入已安装的性能版本

用户明确要求把另一对话阶梯黑条修复候选合并部署。基线固定为D31已安装DECCA3E0…C4A0B10CA；仅将D30已审查的`contourRole`高度判断合入，版本为v0.32.3-stair-performance。不能直接用旧D30的325A整包替换，也不能编译含authority的HEAD部署。

输出固定在`build/stair-shadow-output/merged-v0323/`，保留所有已有D30、D31证据。`merge-inputs.json`固定六类源：主文件仅版本标记变化，helper与已审查D30完全一致，其余四类字节不变。`build-complete.json`记录准确生产字节、测试构建和原生输入指纹。

2026-10-19 15:26:52已部署准确包76314B81…AF5C46B7（37,775B）；299项功能检查及正式启动通过。回执见`state/deployment-v0323-2026-10-19.md`，归档见`knowledge/experiments/stair-performance-v0323-20261019/`。以下为已完成步骤的复现说明，不要重跑冻结目录。

从游戏根用Codex runtime Python执行，已完成的阶段与证据不可覆盖：

```text
mods/RealisticVision/build/stair-merge/merge.py prepare
mods/RealisticVision/build/stair-merge/merge.py build
mods/RealisticVision/build/stair-merge/merge.py checks
mods/RealisticVision/build/stair-merge/merge.py capture
mods/RealisticVision/build/stair-merge/merge.py options
mods/RealisticVision/build/stair-merge/merge.py audit
mods/RealisticVision/build/stair-merge/deploy.py prepare
mods/RealisticVision/build/stair-merge/deploy.py deploy
mods/RealisticVision/build/stair-merge/archive.py
```

编译和AIR按RConnect主会话明确交接安排；启动前至少6GiB可用物理内存，唯一AppID、隐藏实例和独立存储。`checks`运行44项阶梯专项与139项回归；`capture`执行96项原生训练房检查及8组图像；`options`以准确生产字节运行两进程20项设置/改键/保存恢复。没有性能计时或刷新降级。

像素门槛沿用D30已审查边界：黑条消失、实体材质与半高格空气以外零变化、关闭常亮时与保留mask的原雾一致。开启常亮的隐藏层参考仍可能有1/255差异，严格失败数据必须保留；不能把该参照当作已证实不会影响合成取整的标准。`audit`记录严格结果和已有残差解释的再核对；不将参考差异涂绿。

FFDec已对准确生产字节枚举6类，无fe存根、探针或authority；只读枚举退出0，AppData日志锁警告保留。部署脚本仅更新RV，冻结保护指纹并备份原DECCA；正式独立启动失败只回退本模组。用户存档/配置和其它会话进程不操作。完成后立即交回窗口，更新本轮回执与记忆。
