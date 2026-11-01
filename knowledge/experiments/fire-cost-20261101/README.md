# 开火成本调查证据

完整说明见 [调查报告](../2026-11-01-fire-cost.md)。
`origins.json` 记录每份原件的SHA256、大小及是否压缩；gzip固定mtime=0，解压逐字节回验。
这里只保留本模组生成的代码、诊断日志、数值结果和失败图片，未打包游戏资源/存档。
原始运行仍留 `build/fire-cost-output`；源码生成器留 `build/fire-cost`。
`before/after/environment` 只说明端点资源状态；不能代替全程独占或稳定负载证明。
失败运行不删除；完成情况与不采用的原因以报告逐项说明为准。
