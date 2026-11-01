from pathlib import Path
import json,hashlib
MOD=Path(__file__).resolve().parents[2];OUT=MOD/'build/eye-boundary-output'
receipt=json.loads((OUT/'deployment.json').read_text('utf8'))
assert hashlib.sha256((MOD/'release/RealisticVisionMod.swf').read_bytes()).hexdigest()==receipt['sha256']
entry='''> 2026-11-02 **v0.34.3-eye-boundary 已部署**：修普通弹体注册点进暗区后整条亮处尾迹提前消失；Bullet/SmartBullet/PhisBullet 改空间软遮罩并刷新动态外框，Part 保持快速路径。视野从真实玩家眼部发出，按眼部位移刷新，墙角分类不再跨不同起点复用。771项受控检查与正式候选原生加载/运行通过；未重测密集战斗帧率。49,048B / `0861FB64…6DD2E30B`；config与宿主未改。源 `build/eye-boundary-output/candidate/src`，可审阅补丁 `build/eye-boundary/production.patch`，备份 `build/backups/before-eye-boundary-20261102-073730`。**保存并重启游戏生效**。[报告](../knowledge/experiments/2026-11-02-eye-boundary.md)。

'''
p=MOD/'state/MEMORY.md';s=p.read_text('utf8');assert 'v0.34.3-eye-boundary 已部署' not in s
pos=s.index('\n')+1;s=s[:pos]+'\n'+entry+s[pos:]
old='- 当前安装 **v0.33.17-locmem**'
s=s.replace(old,'- 历史安装 **v0.33.17-locmem**',1)
s=s.replace('## 3. 当前状态\n','## 3. 当前状态\n\n- 当前安装 **v0.34.3-eye-boundary**，49,048B / `0861FB64…6DD2E30B`；准确生产源 `build/eye-boundary-output/candidate/src`，保留 v0.34.2 的门区、激光与跨地图记忆修复。771项针对性检查及正式包冒烟通过；无需追加未请求的性能普查。本轮已结束，等待正常重启后的实际游玩反馈。详情见顶部新条目。\n',1)
p.write_text(s,'utf8',newline='\n')
p=MOD/'state/journal.md';s=p.read_text('utf8');header='''## 2026-11-02 — v0.34.3-eye-boundary：弹迹提前消失与眼部视点修复

- 用户报告普通子弹提前被阴影遮住、可视区域与眼睛不对齐。基于正式v0.34.2冻结修复，保留并发authority开发线。
- 弹体全图形裁剪与动态外框；眼部显示部件坐标驱动射线/刷新，取消跨眼点墙角缓存复用。771项受控检查、正式候选原生加载/运行通过，未测完整战斗帧率；工具失败及修正如实留存。
- 已部署49,048B / 0861FB64…6DD2E30B，配置不变，备份before-eye-boundary-20261102-073730；全部本轮测试退出。玩家保存重启生效，无待执行的agent测试。
- [报告与边界](../knowledge/experiments/2026-11-02-eye-boundary.md)，准确源build/eye-boundary-output/candidate/src，审阅补丁build/eye-boundary/production.patch。

'''
p.write_text(header+s,'utf8',newline='\n')
print('Memory and journal updated; installed hash checked.')
