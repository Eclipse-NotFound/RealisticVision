"""Archive D34 evidence and stage only this task's state additions."""
from pathlib import Path
import difflib, json, shutil, subprocess
import run
MOD,OUT=run.MOD,run.OUT
def git(*args,**kw):return subprocess.run(['git',*args],cwd=MOD,check=True,**kw)
def main():
    assert not (MOD/'knowledge/experiments/2026-10-21-vision-settings.md').exists(), 'Already archived; do not rewrite frozen evidence or duplicate state'
    receipt=json.loads((OUT/'deployment/receipt.json').read_text(encoding='utf-8'))
    proof=json.loads((OUT/'verified.json').read_text(encoding='utf-8'))
    assert receipt['result']=='PASS' and run.p.sha(MOD/'release/RealisticVisionMod.swf')==proof['swf']
    run.save(OUT/'frozen.json',{'version':run.p.VERSION,'swf':proof['swf'],'status':'DEPLOYED'})
    dest=MOD/'knowledge/experiments/vision-settings-v0330-20261021';dest.mkdir(exist_ok=True)
    for name in ['verified.json','build.json','baseline.json','classes.txt','classes-stderr.txt']:
        shutil.copyfile(OUT/name,dest/name)
    shutil.copytree(OUT/'native-final/evidence',dest/'native',dirs_exist_ok=True)
    for record in proof['checks']+[proof['native']]+proof['options']:
        source=MOD/record['log'];shutil.copyfile(source,dest/source.name)
    for name in ['receipt.json','formal-output.txt','formal-runtime.txt']:
        shutil.copyfile(OUT/'deployment'/name,dest/name)
    # Retain earlier functional runs and the initial native capture, separately.
    prior=dest/'initial';prior.mkdir(exist_ok=True)
    for f in (OUT/'native').glob('pfe-*.txt'):shutil.copyfile(f,prior/f.name)
    shutil.copyfile(OUT/'native/result.json',prior/'native-result.json')
    shutil.copyfile(OUT/'options/result.json',prior/'options-result.json')
    cards=''
    for i in [0,1,4,5]:
        mode='仿原版' if i<4 else '平滑阴影'
        cards+='<h2>'+mode+' / 位置 '+str(i%2+1)+'</h2><div class="row">'
        for key,label in [('default','默认'),('soft','柔化尺度40像素'),('range3','短视距夹具×3')]:
            cards+='<figure><img src="native/'+key+'-'+str(i)+'.png"><figcaption>'+label+'</figcaption></figure>'
        cards+='</div>'
    html='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>RV 0.33.0 视野设置</title><style>body{font:16px/1.6 system-ui;background:#161b24;color:#eee;margin:28px}h1{margin-bottom:8px}.row{display:flex;gap:16px}figure{margin:0;flex:1;min-width:0}img{width:100%}figcaption{color:#b9c9da}table{border-collapse:collapse}td,th{padding:8px 18px;border:1px solid #445}@media(max-width:900px){.row{display:block}}</style><h1>RealisticVision 0.33.0 · 已部署</h1><p>白色表示无遮挡，黑色表示阴影。下图是独立测试的雾层，非玩家存档截图。8组默认与恢复默认的最终图均严格相同。</p><table><tr><th>设置</th><th>范围</th><th>默认</th></tr><tr><td>已探索区域亮度</td><td>0—1</td><td>0.35（保留已有保存值）</td></tr><tr><td>最大视距倍率</td><td>0.5—3</td><td>1</td></tr><tr><td>平滑阴影渐变宽度</td><td>0—60像素柔化尺度</td><td>20</td></tr><tr><td>仿原版额外柔化</td><td>0—40像素柔化尺度</td><td>0</td></tr></table><p>倍率按房间默认视距计算，墙门仍遮挡；亮度和柔化不扩大探索或敌人可见性。原版模式、基地透传、原生亮度记录保持原规则。柔化尺度不是严格的10%—90%边界宽度。</p>'''+cards+'</html>'
    (dest/'comparison.html').write_text(html,encoding='utf-8')
    report='''被测技能：remains-mod-memory、remains-mod-build、remains-auto-testing、remains-runtime-debug、remains-release-gate、remains-swf-patching、diagnosing-bugs
技能归属：Remains工作区；diagnosing-bugs为用户级
测试工作区：D:/Program Files/Steam/steamapps/common/Remains

# D34：视野显示与最大距离设置

2026-10-21，用户确认房间视距倍率0.5–3、默认1，以及分模式柔化并保留原生墙内渐变。已部署v0.33.0-vision-settings。原“记忆区暗度”实际是亮度，修正反向文案并保留dim键及保存值；新增soft_current、soft_classic、viewscale。原版模式/总开关/基地透传、原版visi/t_visi/地图传送/AI字段不作修改。

## 实现与兼容

- 默认亮度0.35、current柔化尺度20px、classic附加柔化0px、视距倍率1。设置即时保存，原地重算而不重置房间，避免丢失子格探索。空/非有限配置回落默认，超范围钳制；中英俄菜单均有说明。
- current仅调显示滤镜；classic附加柔化后重新接回原墙场。敌人使用独立逻辑输入。自定义classic记忆亮度时，基准逻辑遮罩与可调显示分开计算，不将高亮记忆区送入敌人遮罩。
- 距离的全亮半径与最大半径同步缩放，动态读取房间参数。倍率不是1时，在模组内采样角点光照，沿原版的步进及减法遮光规则；不调用原版lighting写入。原生已有亮度继续保留。扩展记忆随房间保留，世界重置清空。
- 生产源从已部署D32准确六类源派生，保留D31性能与D32阶梯修复；不混入authority工作。并行D33运动性能候选未在本次安装，未来合并须保留本次设置，不可覆盖较新的release。

## 验证

251条断言：90设置与默认等价、16原柔化回归（含1000条射线）、21共享探索、88原生训练房、36准确生产包两进程设置/快捷键/心跳。原生测试有两模式×常亮开关×两位置；8组默认和恢复默认最终雾层均逐像素相同。高亮记忆与额外柔化不改变逻辑位图/探索数组；倍率放大能看到更多无遮挡格、无法穿墙；原版字段和距离值不变。人工已探索夹具验证亮度从全黑到明亮且FOV仍不可见。房间往返保留扩展墙光记忆。

正式路径独立AppID、独立桌面启动：新版init、ModSettings注册、tick1/181/361均通过；只关闭本轮实例、移除本轮描述符。包仅六类，无fe存根/测试探针/authority。具体字节与原始日志见[证据目录](vision-settings-v0330-20261021/verified.json)。

## 边界及真实过程

- 本次是功能及像素验收，没有测完整战斗FPS，也没有验证所有玩家存档/所有联机组合。大视距、宽柔化和自定义classic亮度会增加工作量，不承诺免费获得更大范围。
- 原生墙内算法保留，包括D30已记录的开启常亮时隐藏参考层1/255取整差；本次默认等价使用D32完整最终图，未将历史残差抹成全绿。
- 早期组件按offline登记，曾与RConnect性能轮重叠，对方独占检查拒绝了那轮，未产生有效性能数据。已改所有AIR组件使用game占用；原始登记保留。
- 新启动器接入首轮缺application.xml、catalog，随后探针名不满足Mod后缀；均在启动前报错，补齐隔离副本和入口名后成功。不改正式名单，不以命令退出0代替检查输出文件。
- 共享知识两层检索为partial，有无关来源不可读；性能方法沿KB-000056边界，不据此声称全库无经验。

## 部署与回退

新包SHA256：`NEW_SHA`，40,371B。旧D32：`76314B819151FBA6F67F6D740B21030A9EEC8359AF4C9C9DDEB83D4CAF5C46B7`。
备份：`BACKUP`。只有当前release仍为本次新SHA时才可将该备份恢复到release/RealisticVisionMod.swf；遇到更新版本先核对合并，不覆盖。真实用户配置与存档没有写入。已有游戏须保存并正常重启。

精确生产源：`build/vision-settings-output/candidate/src`；构建/测试工具：`build/vision-settings`。部署回执见[receipt.json](vision-settings-v0330-20261021/receipt.json)。
'''.replace('NEW_SHA',proof['swf'].upper()).replace('BACKUP',receipt['backup'])
    (MOD/'knowledge/experiments/2026-10-21-vision-settings.md').write_text(report,encoding='utf-8')
    # Apply the same reviewed settings delta to development main, retaining authority.
    for rel,fn in [('RealisticVisionMod.as',run.p.main_source),('modlocales/vision/RVLocaleMessages.as',run.p.locale_source)]:
        target=MOD/'src'/rel;old=target.read_text(encoding='utf-8-sig');new=fn(old)
        target.write_text(new,encoding='utf-8')
    # Do not stage the other task's existing .gitignore / state edits.
    additions={'.gitignore':'\nbuild/vision-settings-output/\nbuild/backups/before-vision-settings-*/\n',
      'state/MEMORY.md':'> 2026-10-21 **D34 v0.33.0已部署**：已探索区亮度、分模式柔化与0.5–3倍房间视距；默认画面与D32严格相同，251项通过，正式路径init/设置注册/tick1/181/361通过。SHA '+proof['swf'].upper()+'。准确源build/vision-settings-output/candidate/src，不含authority及未发布D33候选；后续性能合并不可覆盖设置。详见[报告](../knowledge/experiments/2026-10-21-vision-settings.md)。\n\n',
      'state/journal.md':'## 2026-10-21 D34 视野设置已部署\n- 用户确认：记忆亮度、分模式柔化、房间视距倍率0.5–3。默认保持，扩大距离仍经遮挡；AI/原版地图传送记录不写。\n- 完成：251项功能/像素检查、两进程设置与正式启动；保留已部署阶梯与性能、authority WIP和并行D33。\n- 证据/回退：[设置报告](../knowledge/experiments/2026-10-21-vision-settings.md)。大视距/柔化成本未作完整FPS结论，用户正常重启生效。\n\n'}
    for rel,extra in additions.items():
        base=git('show','HEAD:'+rel,capture_output=True).stdout.decode('utf-8-sig')
        target=MOD/rel;working=target.read_text(encoding='utf-8-sig')
        if rel=='.gitignore':staged=base+extra;updated=working+extra
        else:
            pos=base.index('\n')+1;staged=base[:pos]+'\n'+extra+base[pos:]
            pos=working.index('\n')+1;updated=working[:pos]+'\n'+extra+working[pos:]
        target.write_text(updated,encoding='utf-8')
        digest=git('hash-object','-w','--stdin',input=staged.encode('utf-8'),capture_output=True).stdout.decode().strip()
        git('update-index','--cacheinfo','100644,'+digest+','+rel)
    status=MOD/'state/vision-settings-2026-10-21.md'
    status.write_text('# D34 视野设置已部署\n\n'+report[report.index('2026-10-21，'):report.index('## 实现与兼容')]+'\n详见[完整报告](../knowledge/experiments/2026-10-21-vision-settings.md)。\n',encoding='utf-8')
    git('add','src/RealisticVisionMod.as','src/modlocales/vision/RVLocaleMessages.as','build/vision-settings','knowledge/experiments/2026-10-21-vision-settings.md','knowledge/experiments/vision-settings-v0330-20261021','state/vision-settings-2026-10-21.md')
    print('D34 evidence archived; only owned state deltas staged')
if __name__=='__main__':main()
