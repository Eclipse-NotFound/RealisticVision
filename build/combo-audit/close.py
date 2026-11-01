"""Stage only this review's work; preserve the other chat's pending state edits."""
from pathlib import Path
import ast,hashlib,json,sqlite3,subprocess
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/combo-audit-output'
def git(*args,data=None):return subprocess.check_output(['git',*args],cwd=MOD,input=data)
assert git('rev-parse','HEAD').decode().strip()=='70bf9848e2070a25e7f0fdced96eade62c0be4a0'
assert not git('diff','--cached','--name-only').strip(), 'Do not mix staged work'
db=sqlite3.connect('file:'+str(GAME/'shared-knowledge/knowledge-validation/coordination/test-runs.sqlite3').replace('\\','/')+'?mode=ro',uri=True)
rows=[json.loads(x[0]) for x in db.execute('select payload from runs')];db.close()
mine=[r for r in rows if r['owner']=='RealisticVision / combo-v4审核']
assert len(mine)==9 and not [r for r in mine if r['state'] in ('waiting','running')]
for p in HERE.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
evidence=MOD/'knowledge/experiments/combo-audit-20261101'
for rel,digest in json.loads((evidence/'manifest.json').read_text()).items():assert hashlib.sha256((evidence/rel).read_bytes()).hexdigest()==digest,rel
assert hashlib.sha256((MOD/'release/RealisticVisionMod.swf').read_bytes()).hexdigest()=='aea303149b0a5d5a3072c610b3e95f4ad78963ea22ce123c6a3414e73b9aa557'
own=OUT/'owned-state';own.mkdir(exist_ok=False)
memory='''> 2026-11-01 **combo-v4审核完成，未部署修复**：正式RV仍47,534B / AEA30314…9AA557。准确生产源与D56仅主类变化，其他5文件相同；已冻结本轮两版源码。确认外框缓存漏scaleY/子几何（08独立D56 scaleY反例3840像素差）、fadeCount未初始化、关闭时alpha残留0.19921875。40窗7160完整间隔；最大化首轮off34.38/D5649.44/v444.73ms，后续有显著负载波动，不能套用旧小窗“问题均已处理”结论。零敌人扫射也变慢；跳过独立特效CPU3.49→0.80ms但整帧未改善；隐藏fog显示55.32→49.64ms、P95反变差，只有归因价值。5394ms无敌/无弹停顿中RV0ms、剩余阶段5330ms，极端长帧未精确定位。02后置PNG失败后04/08补验；06/07宿主8321→C6漂移被拦，08/09只在副本复用冻结8321；真实/种子CS nativeEnabled均false。所有自有AIR/登记结束。下一步优先修恢复/缓存正确性，再查阴影合成和单位软遮罩整体绘制，不能继续只靠FOV节流或把撤罩诊断当候选。[报告](../knowledge/experiments/2026-11-01-combo-audit.md)。'''
journal='''## 2026-11-01 — v0.33.15-combo-v4审核与最大化轻机枪归因

- 用户要求审核另一会话升级并详细调查开火卡顿，确认current+轻机枪+最大化。审核D56生产源→v4生产源；正式包AEA一致，未写release/src，保留外部未提交开发。
- 三项正确性缺陷：父transform不变不足以缓存动态外框；fadeCount首次undefined；恢复遗漏alpha。04/08真实宿主内受控反例，D56独立scaleY图像差3840；不将重绑快照的4560差误作回退幅度。
- 40窗7160完整间隔。首轮大窗off34.38/D5649.44/v444.73ms；零敌人扫射仍慢。单位遮罩和fog显示各有局部开销证据，但特效代码削减没有稳定整帧收益，且后段含绘制/等待/调度，不能称GPU独占。无敌无弹5394ms停顿中RV0ms，根因尚未全解。
- 02计时完成后PNG路径错误，登记失败保留，04/08补验；06/07因外部宿主更新在启动前被指纹门禁拦住，后两轮复用冻结副本。9项登记全部结束，未部署候选。报告knowledge/experiments/2026-11-01-combo-audit.md；证据combo-audit-20261101；工具build/combo-audit。

'''
for rel,block in [('state/MEMORY.md',memory),('state/journal.md',journal)]:
    p=MOD/rel;before=p.read_bytes();working=before.decode('utf-8-sig');base=git('show','HEAD:'+rel).decode('utf-8-sig')
    def add(s):
        if rel.endswith('MEMORY.md'):
            first,sep,rest=s.partition('\n');return first+'\n\n'+block+'\n\n'+rest.lstrip('\n')
        return block+s
    updated=add(working);staged=add(base)
    (own/(p.name+'.before')).write_bytes(before)
    assert p.read_bytes()==before
    p.write_text(updated,encoding='utf-8',newline='\n')
    blob=git('hash-object','-w','--stdin',data=staged.encode()).decode().strip()
    git('update-index','--cacheinfo','100644,'+blob+','+rel)
git('add','.gitignore','build/combo-audit','knowledge/experiments/2026-11-01-combo-audit.md','knowledge/experiments/combo-audit-20261101')
git('diff','--cached','--check')
print('Owned changes staged; other chat edits remain outside the index')
