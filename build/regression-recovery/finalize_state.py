"""Update D35 state without staging the pre-existing authority notes."""
from pathlib import Path
import json,re,subprocess
import investigate as inv

def main():
 receipt=json.loads((inv.OUT/'deployment/receipt.json').read_text());assert receipt['result']=='PASS'
 assert inv.r.sha(inv.MOD/'release/RealisticVisionMod.swf')==receipt['new']
 own=inv.OUT/'owned-state';own.mkdir(exist_ok=True)
 summary='> 2026-10-21 **D35先回退，再修复并部署v0.33.2**：22:17恢复下午前D32；23:35准确安装7852F61E…BE86764（41,630B）。自定义亮度不再重复整图合成/地形扫描；显示与逻辑隔离、设置、阶梯和防溢出保留。1731项检查及8个原生射击窗口通过，正式路径init/设置注册/tick1/181/361通过。D32配对四组更新加绘制均值低3.8%～21.6%，current默认组最大值仍83→125ms，不能承诺无卡顿。生产源build/regression-recovery-output/production-singlepass/src，不含authority；回退备份before-settings-recovery-20261021-233515-ab290b为D32。详见[报告](../knowledge/experiments/2026-10-21-settings-performance-recovery.md)。'
 journal='''## 2026-10-21 — D35先回退并修复非默认亮度的性能回退

- 用户明确先回退下午修改：22:17将F2B8A恢复D32 76314B81，正式路径复验通过，真实配置/存档未改。
- 根因：classic非35%记忆亮度递归完整渲染两次，用户实际约60%；此前默认值的性能收益不能覆盖此路径。改为一次地形遍历生成两组低图，固定逻辑高图按实际遮罩查询区完成，current复用距离衰减。
- 验证：1731项和8个原生射击窗口通过；显示整图、所有逻辑可读像素严格一致。D32直接配对均值低3.8%～21.6%，用户classic60%为66.692→64.133ms；current默认最大83→125ms、原生整帧仍有259ms尖峰，未声称卡顿全解。失败的1px缓冲、首帧空缓存及仍回退候选均保留。
- 部署：23:35:15准确v0.33.2 / 7852F61E083993E69431D5D8CA2FDF3C07D4068715946D04B3E796CECBE86764（41630B），仅RV，17项保护指纹及真实配置不变。独立正式init/设置注册/tick1/181/361通过，PID103276和描述符清理。备份build/backups/before-settings-recovery-20261021-233515-ab290b/RealisticVisionMod.before.swf为准确D32。
- 源与证据：[报告](../knowledge/experiments/2026-10-21-settings-performance-recovery.md)、build/regression-recovery/README.md、准确生产源build/regression-recovery-output/production-singlepass/src。共享登记排队；遗留他方实例仅由所属会话清理。并行authority四项WIP保留，用户正常保存并重启生效。

'''
 def memory(s):
  s=re.sub(r'^> 2026-10-21 22:17 \*\*D35.*\n\n','',s,flags=re.M)
  s=s.replace('# RealisticVision —— 开发记忆入口\n\n','# RealisticVision —— 开发记忆入口\n\n'+summary+'\n\n',1)
  s=s.replace('- 当前安装以顶部D33 v0.33.1为准；D34设置完整保留。正式源/包：build/motion-performance-output/merged-settings/production。','- 当前安装D35 v0.33.2（7852F61E…BE86764）；D34全部设置、D32阶梯与防溢出、D33有效缓存保留。正式源/包：build/regression-recovery-output/production-singlepass；不从含authority的HEAD整包部署。')
  s=s.replace('- D33本轮实现、验证与部署完成，无待跑RV实例。旧Object缓存和过时v0.32.4不可部署，不重跑冻结测试；authority仍为独立未发布工作。','- D35实现、验证、部署已完成；所有RV实例已退出。candidate至candidate-v5为历史失败/过渡方案，不部署、不重跑覆盖。authority仍为独立未发布工作。')
  s=s.replace('## 5. 已知问题与边界\n','## 5. 已知问题与边界\n\n- D35解决自定义亮度的重复计算回退；平均改善不能当作长帧全解。current默认大图最大83→125ms，射击整帧峰值259ms而RV更新最大26ms；具体慢帧与全组合长期联机尚未完全归因。\n',1)
  s=s.replace('- 用户正常保存并重启加载v0.33.1；若仍反馈高速/混战停顿，优先对完整组合的慢帧分段采样，保留画质及D34设置，不继续只按平均值优化。','- 用户正常保存并重启加载v0.33.2；若仍反馈高速/混战停顿，按实际保存的设置和完整组合慢帧采样，不仅测默认值或按平均值优化。D35安全回退基线为D32，路径见顶部报告。')
  s=s.replace('## 7. 深入了解与复验\n','## 7. 深入了解与复验\n\n- D35入口：knowledge/experiments/2026-10-21-settings-performance-recovery.md、build/regression-recovery/README.md。1731检查、8战斗窗、原始性能、失败与部署证据均保留；KB-000056用于测量方法。\n',1)
  return s
 for rel in ['state/MEMORY.md','state/journal.md']:
  p=inv.MOD/rel;old=p.read_text(encoding='utf-8-sig');head=subprocess.check_output(['git','show','HEAD:'+rel],cwd=inv.MOD).decode('utf-8')
  if rel.endswith('MEMORY.md'):
   assert summary not in old,'State already finalized; do not append twice'
   working,owned=memory(old),memory(head)
  else:
   previous='## 2026-10-21 — D35先回退下午改动并调查设置性能回退'
   if old.startswith(previous):old_clean=old[old.index('## 2026-10-21 — D33'):]
   else:old_clean=old
   working,owned=journal+old_clean,journal+head
  assert p.read_text(encoding='utf-8-sig')==old,'Concurrent state edit'
  p.write_text(working,encoding='utf-8');(own/p.name).write_text(owned,encoding='utf-8')
 print('Updated state; owned-state snapshots exclude pre-existing authority additions')

if __name__=='__main__':main()
