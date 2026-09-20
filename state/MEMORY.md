# RealisticVision —— 开发记忆入口

> 更新：2026-09-20。current跑动停顿/像素感调查完成，实验未合入正式源码或部署；正式仍v0.28.2（含念力热修复）。范围见../AGENT_SCOPE.md。

## 1. 这个模组是什么

三态视野：未探索全黑、视野内可见、记忆区变暗并隐藏敌人。含墙门遮挡、部分敌人裁剪、念力宽限、营地透传；vanilla / classic / current三模式。入口RealisticVisionMod，源码src/RealisticVisionMod.as；仅根目录1.02宿主已安装本模组loader。

## 2. 用户偏好与协作约定

- D22明确确认：墙按原版黑芯/基础亮面/渐变，只压暗原光；原版维护visi/t_visi与地图/传送判定。地板保留模式区别。
- 用户先定位小墙块“阴影位置偏移、不贴墙”，再指出“墙边亮带、拐角接缝”；看过诊断页后明确“按候选修复”，随后明确“请部署”。本次发布授权已执行，不需重复确认。
- 先同场景原版/旧版对照、实际AIR复现；既查墙内也查墙/地板交界。纯阴影比较必须同输入。原版宽亮面不自动收窄，原截图准确存档仍需目检。
- 不写其他模组；不用Ghost、不新增委托。MSW既有WIP stash保留。血条不强制visible=true，由visDetails重算；不恢复记忆播种、墙面受光传播旧方案。
- 2026-09-19另一任务发布的念力热修复a583f1a守卫已随v0.28.2保留；本次阴影发布另有本任务明确授权。

## 3. 当前状态

- 正式v0.28.2，源码提交37c25ba：D24用中心可见性统一墙的记忆压暗及地板边界，保住D23投影位置。墙底图保持原版原尺寸，内角共享角值；current渲染不变。已有念力守卫完整保留。
- 接缝8/8、墙形39项、小墙10方向通过。小墙端点误差0.25px；完整1.02训练房同输入下classic额外墙边跳变166/84→11/4，current纯阴影整图差0；墙面无抬亮、黑芯0，地板内部格线最大相邻差6。
- 39项中的弱光混合样本按中心权重独立计算（23.22→实测23），其余38项语义不变；未放宽接缝/端点/全记忆阈值。新增弱光墙缓存最大alpha差2，离临界取整带的敌人分类差0。
- 测试SWF：build/RealisticVisionMod_test.swf，18,877字节，SHA A8A7DAE9A755ACD7FC93101003AACE2C8CF2A0FF6A507318B3B7A7CAADB685E2；FFDec只有RealisticVisionMod，无嵌入fe.*。源码SHA E5B19E618CE5A09256281700C6EFC80DCB5EB9543E16A42654B49E35E0119D35。
- 正式release已替换为上述A8A7…85E2，与已验测试SWF完全一致；config保留current/dim=.35/debug=0，SHA 5136EE1923A77F5F10EAB1B3994B64CBD67B09D687A7E829FB1E81D2E79A3C7F。根pfe.swf保持5300EC48…241E7。
- 新备份build/release_backup_v0280_grabfix1_before_v0282_20260919.swf，旧SHA E4E5ED82D5E65201A57A712F7BEBC6FDB499E7822C131B414A67700107401969。需要回滚时复制到release/RealisticVisionMod.swf并重启，不覆盖此前备份。
- 独立正式路径实例rv-deploy-smoke-v0282-20260919-232730：六loader均init returned、RV新版标记/设置注册成功、22条心跳至3781；3次F12实际进入cycleMode。自有PID24556已关闭，测试描述符已删除。用户实例未操作，需保存并正常重启生效。

## 4. 正在进行与卡点

- 最新用户要求详细探查current跑动阴影停顿/像素感。报告2026-09-20-current-motion-investigation.md、证据current-motion-20260920/、可重复build/motion-tests/已完成；不是新的发布授权，也未合入实验源码。
- 确定原因：真实stage30Hz，三帧FOV+下一帧显示约10Hz；仅改每帧FOV会饿死显示（60步0更新）。5px二值采样+max(raw,blur)形成台阶；角点历史0/7误写0/1产生亮点，单变量实验未见阴影内异常808→0。
- 缓存遮光数据与基线单墙/完整训练房各24帧逐像素一致。同进程交替复测，重算17–20ms→约12ms；缓存+每帧同步90/90更新，均摊约13–14ms，仍需降成本和实战验收。全图2.5px台阶约减半但P95 55ms；边界四点积分改善小；取消硬钳制漏光，均不能直接采用。
- 修复与正式部署均已完成。修复报告2026-09-19-classic-wall-seam-fix.md；部署回执2026-09-19-v0282-deployment.md及deployment-v0282/，对照页已更新发布状态，原候选验收数据/指纹保留。
- 已淘汰只改地板衔接（端点退至19.25px）和“格角记忆+中心记忆”双重压暗（一个方向偏4px）。最终classic墙基底不预乘角记忆；只用中心可见性乘原光，地板校正共享边曲线。
- 正常startup及模式入口已补验；未重放用户精确存档、相机/移动历史或六模组共同战斗，不能声称原截图每个观感及实战性能已验收。

## 5. 已知问题

- classic仍有40px粗格掠角（一个水平角与连续切线差21px）、薄墙可见侧约20px渐变；原版宽亮面保留。
- 完整48×25房间30次强制重建：旧464/521ms，新655/697ms；约增加6ms/次，静止调用约3.4–3.8ms。是单次绘图采样，不是帧率；优化已降低早期候选墙缓存开销，长期实战性能待验。
- current目标区既有边界差139/149未扩修。F12的saveConfig SecurityError:fileWriteResource在部署冒烟再次出现3次，模式入口仍执行、配置指纹不变；这是既有持久化问题，重启仍默认current。狮鹫internal手臂限制、SATS记忆扫描/抓暗敌瞬间报警等旧问题保留。
- 同尺寸resetRoom清黑共用三图与fogBlurPending、透明RGBA规范为0等既有修复不能回退。新可见性边框复制边缘样本，墙遮挡层延伸过裁切边界，避免亮缝。

## 6. 下一步

1. 若继续实现current候选：先修角点历史与显示饥饿，再缓存遮光/减少全亮区域和未变墙体的重复工作，协调地板显示与单位掩膜。实验变体只是调查，不能直接部署。
2. 抗锯齿另做连续轮廓覆盖率/边缘距离原型；当前四点积分负结果、全图翻倍成本和无钳制漏光已有证据。需验门水破墙、换房、缩放、探索边缘、敌人裁剪与完整战斗，不把固定步回放叫实际FPS。
3. 保留D22、classic v0.28.2与a583f1a；不自动关闭用户游戏。旧念力与墙影回滚点均保留，详见journal与部署报告。

## 7. 深入了解与复验

- current调查：2026-09-20-current-motion-investigation.md；current-motion-20260920/comparison.html可逐帧播放。motion-tests/README含10变体、小夹具红信号、完整游戏与同进程交替基准。性能编译必须debug=false/optimize=true；旧debug构建及截图回放耗时不能直接当正式FPS。bench初次仅解析CR失败，已从完整日志恢复11例，不算重跑。
- 本轮修复报告2026-09-19-classic-wall-seam-fix.md、证据classic-seams-v0282/、D24；正式部署报告2026-09-19-v0282-deployment.md及deployment-v0282/。前轮诊断2026-09-19-classic-wall-seams.md及classic-seams-20260919/是失败候选历史，不覆盖。
- 小墙历史2026-09-12-classic-wall-edge-offset.md / classic-edge-v0281/ / D23；原版墙形2026-09-10-wall-shadow-v0280-validation.md / D22。念力正式部署与回滚有journal自包含记录。
- 入口build/wall-tests/README.md：run.mjs、--edges、--seams；完整run-game.mjs --training --seams，基线加--revision ee7988c，顺序运行；inspect-seams.py --baseline与--repair；新归档make-seam-fix-evidence.mjs。旧probe仅用于旧revision。
- 构建只用build/build_test.bat；旧build.bat/build.sh会写release且含旧路径。SDK D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk；Java D:/Program Files/Adobe Animate 2024/jre；FFDec同tools/ffdec/ffdec.jar。
- AIR需独立app id/资源副本，禁止写真实pfe存档。完整导出限时150秒；出现CAPTURED仍须核对进程成功退出与测量器通过。Pillow Python：C:/Users/hello/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe。
