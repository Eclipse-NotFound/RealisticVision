# RealisticVision —— 开发记忆入口

> 更新：2026-09-19。v0.28.2 classic接缝修复已完成源码、隔离回归与测试构建，未部署。正式仍为另一获授权任务发布的v0.28.0-grabfix.1。范围见../AGENT_SCOPE.md。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current三模式。入口RealisticVisionMod，源码src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组loader。

## 2. 用户偏好与协作约定

- D22明确确认：墙按原版黑芯/基础亮面/渐变，只压暗原光；原版维护visi/t_visi与地图/传送判定。地板保留模式区别。
- 用户先定位小墙块“阴影位置偏移、不贴墙”，再指出“墙边亮带、拐角接缝”；看过诊断页后明确“按候选修复”。本轮授权是修复，未追加阴影候选部署授权。
- 先同场景原版/旧版对照、实际AIR复现；既查墙内也查墙/地板交界。纯阴影比较必须同输入。原版宽亮面不自动收窄，原截图准确存档仍需目检。
- 不写其他模组；不用Ghost、不新增委托。MSW既有WIP stash保留。血条不强制visible=true，由visDetails重算；不恢复记忆播种、墙面受光传播旧方案。
- 2026-09-19另一任务已获用户“允许”并部署念力热修复，其a583f1a守卫必须保留；该授权不扩展到本次阴影候选发布。

## 3. 当前状态

- 源码候选v0.28.2：D24用中心可见性统一墙的记忆压暗及地板边界，保住D23投影位置。墙底图保持原版原尺寸，内角共享角值；current渲染不变。已有念力守卫完整保留。
- 接缝8/8、墙形39项、小墙10方向通过。小墙端点误差0.25px；完整1.02训练房同输入下classic额外墙边跳变166/84→11/4，current纯阴影整图差0；墙面无抬亮、黑芯0，地板内部格线最大相邻差6。
- 39项中的弱光混合样本按中心权重独立计算（23.22→实测23），其余38项语义不变；未放宽接缝/端点/全记忆阈值。新增弱光墙缓存最大alpha差2，离临界取整带的敌人分类差0。
- 测试SWF：build/RealisticVisionMod_test.swf，18,877字节，SHA A8A7DAE9A755ACD7FC93101003AACE2C8CF2A0FF6A507318B3B7A7CAADB685E2；FFDec只有RealisticVisionMod，无嵌入fe.*。源码SHA E5B19E618CE5A09256281700C6EFC80DCB5EB9543E16A42654B49E35E0119D35。
- 正式release为v0.28.0-grabfix.1，SHA E4E5ED82D5E65201A57A712F7BEBC6FDB499E7822C131B414A67700107401969；config仍current/dim=.35/debug=0，SHA 5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F。本轮未改正式文件。
- 念力热修复独立提交a583f1a并正式路径验证；其vanilla/基地/配置安全房间透传条件未混入阴影部署。本候选含该源码修复。

## 4. 正在进行与卡点

- 本轮修复、测试构建与对照已完成；不是部署状态。证据见knowledge/experiments/2026-09-19-classic-wall-seam-fix.md及classic-seams-v0282/comparison.html。
- 已淘汰只改地板衔接（端点退至19.25px）和“格角记忆+中心记忆”双重压暗（一个方向偏4px）。最终classic墙基底不预乘角记忆；只用中心可见性乘原光，地板校正共享边曲线。
- 未重放用户精确存档和移动历史，不能声称截图每个观感都已消失。正常startup、快捷键、六模组实战仍属后续部署门禁范围。

## 5. 已知问题

- classic仍有40px粗格掠角（一个水平角与连续切线差21px）、薄墙可见侧约20px渐变；原版宽亮面保留。
- 完整48×25房间30次强制重建：旧464/521ms，新655/697ms；约增加6ms/次，静止调用约3.4–3.8ms。是单次绘图采样，不是帧率；优化已降低早期候选墙缓存开销，长期实战性能待验。
- current目标区既有边界差139/149未扩修。F12的saveConfig SecurityError:fileWriteResource、狮鹫internal手臂限制、SATS记忆扫描/抓暗敌瞬间报警等旧问题保留。
- 同尺寸resetRoom清黑共用三图与fogBlurPending、透明RGBA规范为0等既有修复不能回退。新可见性边框复制边缘样本，墙遮挡层延伸过裁切边界，避免亮缝。

## 6. 下一步

1. 用户确认部署时走release-gate，先备份当前v0.28.0-grabfix.1，再用本候选构建；不得覆盖已有唯一备份。重点补正常启动、模式切换、原存档目检和共同战斗性能。
2. 保留本次阴影修复和a583f1a念力守卫。若要改变原版自身宽亮面，先具体对照，不擅自缩窄D22渐变。
3. 旧念力回滚点build/release_backup_v0280_before_grabfix_20260919.swf（57FA90F813C267C1BB0BC4B4AAB536257CF10EDCD20E7E38BDA93E9B3AA9B6E0），旧墙版本回滚点release_backup_v0271_before_v0280_20260910.swf（9423F7D727191C0F090EDD0C2E50D43339643F70F69E9D0F05C33114AE86A56D）均保留。

## 7. 深入了解与复验

- 本轮报告2026-09-19-classic-wall-seam-fix.md、证据classic-seams-v0282/、D24；前轮诊断2026-09-19-classic-wall-seams.md及classic-seams-20260919/是失败候选历史，不覆盖。
- 小墙历史2026-09-12-classic-wall-edge-offset.md / classic-edge-v0281/ / D23；原版墙形2026-09-10-wall-shadow-v0280-validation.md / D22。念力正式部署与回滚有journal自包含记录。
- 入口build/wall-tests/README.md：run.mjs、--edges、--seams；完整run-game.mjs --training --seams，基线加--revision ee7988c，顺序运行；inspect-seams.py --baseline与--repair；新归档make-seam-fix-evidence.mjs。旧probe仅用于旧revision。
- 构建只用build/build_test.bat；旧build.bat/build.sh会写release且含旧路径。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk；Java D:/Program Files/Adobe Animate 2024/jre；FFDec同tools/ffdec/ffdec.jar。
- AIR需独立app id/资源副本，禁止写真实pfe存档。完整导出限时150秒；出现CAPTURED仍须核对进程成功退出与测量器通过。Pillow Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。
