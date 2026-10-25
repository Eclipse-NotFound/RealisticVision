"""Archive completed D52 trials and stage only this task's state changes."""
from pathlib import Path
import ast,hashlib,json,shutil,subprocess,sys,time

MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1]
OUT=MOD/'build/candidate-comparison-output'
DEST=MOD/'knowledge/experiments/candidate-comparison-d52-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=MOD)
assert git('rev-parse','HEAD').decode().startswith('dd1bffe')
assert not git('diff','--cached','--name-only').strip()
expected={'release/RealisticVisionMod.swf':'638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710',
          'release/config.txt':'5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f'}
assert all(sha(MOD/p)==digest for p,digest in expected.items())
summary=json.loads((OUT/'summary.json').read_text())
assert len(summary['runs'])==2 and not summary['adopted']
for name in ['comparison-01','comparison-04']:
    folder=OUT/name
    assert json.loads((folder/'last-run.json').read_text())['exit']==0
    assert not (folder/'test.xml').exists()
    assert json.loads((folder/'analysis.json').read_text())['verified']
for name in ['comparison-02','comparison-03']:
    assert not (OUT/name/'last-run.json').exists()
    assert not (OUT/name/'running.json').exists()
for name in ['comparison-01','comparison-02','comparison-03','comparison-04']:
    folder=OUT/name
    for rel,digest in json.loads((folder/'build.json').read_text())['files'].items():
        assert sha(folder/rel)==digest, (name,rel)
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
from test_registry import Registry,Registration
assert not [row for row in Registry().status() if 'RealisticVision' in row['owner'] and row['state'] in ('waiting','running','needs-check')]
# Allow explicitly identified older queued groups to finish before archival IO.
older=set(sys.argv[1:]);deadline=time.monotonic()+900
if older:print('Waiting for earlier test reservations before archival IO',flush=True)
while older:
    older={row['id'] for row in Registry().status() if row['id'] in older and row['state'] in ('waiting','running','needs-check')}
    if not older:break
    assert time.monotonic()<deadline, 'Earlier tests remain; archival IO has not started'
    time.sleep(5)
with Registration(owner='RealisticVision / D52 保存证据',purpose='非游戏；32战斗窗核验与自身状态归档',run_dir=OUT,evidence=DEST/'archive.json',wait=900) as record:
    assert not DEST.exists();DEST.mkdir(parents=True);pins={}
    for name in ['classic','ray']:
        (OUT/'candidates'/name/'not-adopted.json').write_text(json.dumps({'adopted':False,'scope':'D52 48x25 six-enemy full-combination combat at memory 0.6','reason':'No consistent full-frame benefit across two orderings; preserve functional evidence.'},indent=2)+'\n',encoding='utf-8',newline='\n')
    source_reuse={}
    for top in ['candidates','comparison-01','comparison-02','comparison-03','comparison-04']:
        folder=OUT/top
        for p in folder.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(folder)
            if p.suffix=='.as' and top in ['comparison-02','comparison-03','comparison-04'] and len(rel.parts)>1:
                canonical=OUT/'comparison-01'/rel
                assert sha(p)==sha(canonical), 'Repeated source differs: '+str(p)
                source_reuse[p.relative_to(OUT).as_posix()]=canonical.relative_to(OUT).as_posix()
                continue
            if p.suffix=='.as' or len(rel.parts)==1 and p.suffix in ('.json','.log','.txt') or 'evidence' in rel.parts and p.suffix in ('.json','.png') or 'candidates'==top and p.suffix=='.json':
                q=DEST/p.relative_to(OUT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
    (DEST/'reused-sources.json').write_text(json.dumps(source_reuse,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');pins['reused-sources.json']=sha(DEST/'reused-sources.json')
    # Preserve exactly the bytes used in both timings; rebuilds are not byte-identical.
    for name in ['rv.swf','candidate.swf','ray.swf']:
        p=OUT/'comparison-01'/name;q=DEST/'frozen-test-bytes'/name;q.parent.mkdir(exist_ok=True)
        shutil.copyfile(p,q);pins[q.relative_to(DEST).as_posix()]=sha(q)
    for name in ['resumed.json','summary.json']:
        shutil.copyfile(OUT/name,DEST/name);pins[name]=sha(DEST/name)
    failures={'comparison-02':{'airStarted':False,'reason':'Recompiled same-source vision SWFs differ in bytes; repeat changed to frozen first-run binaries.'},
              'comparison-03':{'airStarted':False,'reason':'Forward-slash exclusion missed Windows probe path; use Path.parts to exclude only the intentionally changed probe.'}}
    (DEST/'preflight-failures.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');pins['preflight-failures.json']=sha(DEST/'preflight-failures.json')
    (DEST/'.gitattributes').write_text('** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',encoding='utf-8',newline='\n');pins['.gitattributes']=sha(DEST/'.gitattributes')
    receipt={'formalUnchanged':expected,'rootReadback':sha(GAME/'pfe.swf'),'adopted':False,'frames':6688,'windows':32,'activeOwnedTests':0,'userPauseRevoked':True}
    (DEST/'finish.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');pins['finish.json']=sha(DEST/'finish.json')
    (DEST/'archive.json').write_text(json.dumps(pins,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

    header='> 2026-10-25 **D52独立战斗复验完成，未采用，正式仍D44**：用户“可进行测试”已撤回此前性能暂停。D50 all及D51 v2两轮32窗、6688完整帧间隔，调换模式/候选次序并复用相同冻结字节；均未证明稳定完整战斗收益，不合并或部署。两次构建后预检失败均未启动AIR，修正后新目录通过；旧暂停标记改名保留。所有自有AIR与描述符退出，正式638E/config5136不变。详见[报告](../knowledge/experiments/2026-10-25-candidate-comparison.md)，证据candidate-comparison-d52-20261025。'
    stop='- D52：用户已恢复独立性能测试，旧暂停不再约束后续；32窗/6688间隔已完整核对。D50 all、D51 v2功能证据保留，但本轮无稳定整帧收益，未合并/部署，不再凭局部步骤减少推进。工具build/candidate-comparison，准确性能字节已冻存；comparison-02/03为启动前预检失败，01/04是有效样本。正式仍D44生产源，无authority。当前无RV实例或排队。整体卡顿未解决；下一步应先用可检验假设区分完整帧剩余的原生/绘制/调度开销，不继续堆未证实的微优化。下方均为历史停点。'
    journal='''## 2026-10-25 — D52恢复独立战斗测试，两个候选均未采用

- 用户明确“可进行测试”，撤回此前保留试玩导致的性能暂停；旧暂停文件改名留证。核对旧试玩已退出，按共享登记排队，无关闭他人实例/出站协调。
- 以准确D44为基线，独立对照D50 all和D51 v2，两轮32窗、6688有效完整间隔；六佣兵真实战斗，亮度0.6小房间，全组合。第二轮逆序并直接复用三份测试字节，全部其它加载SWF相同。两候选无稳定整体收益，未合并、未部署；已有严格视觉验证不冒充本轮重跑。
- comparison-02因同源重编译字节差异在AIR前停止；03因路径分隔符误判新探针同样未启动。修正后04完整通过，失败目录不覆盖。原始每窗数据、长帧与指纹全部保留。
- 正式638E/config5136不变，4项authority外部WIP保留；所有自有AIR/描述符退出。后续测试仍获用户授权，卡顿目标未完成。报告knowledge/experiments/2026-10-25-candidate-comparison.md。

'''
    owned=OUT/'owned-state';owned.mkdir(exist_ok=True)
    for name in ['MEMORY.md','journal.md']:
        base=git('show','HEAD:state/'+name).decode('utf-8');live=(MOD/'state'/name).read_text(encoding='utf-8')
        def transform(s):
            if name=='journal.md':return journal+s
            pos=s.index('> 2026-10-25 接续核对：');end=s.index('\n\n',pos)
            s=s[:pos]+header+s[end:]
            old='D50/D51独立候选功能通过，完整性能按用户选择暂缓；正式安装未改，详见顶部报告。'
            assert s.count(old)==1
            s=s.replace(old,'D50/D51已恢复独立战斗复验，未证实稳定整帧收益，未采用；正式安装未改，详见顶部D52报告。')
            pos=s.index('\n\n',s.index('## 4. 正在进行与停点'))+2
            return s[:pos]+stop+'\n\n'+s[pos:]
        (owned/name).write_text(transform(base),encoding='utf-8',newline='\n')
        (MOD/'state'/name).write_text(transform(live),encoding='utf-8',newline='\n')
    for p in (MOD/'build/candidate-comparison').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
    subprocess.run(['git','add','--','.gitignore','build/candidate-comparison','knowledge/experiments/2026-10-25-candidate-comparison.md'],cwd=MOD,check=True)
    subprocess.run(['git','add','-f','--',str(DEST)],cwd=MOD,check=True)
    for name in ['MEMORY.md','journal.md']:
        digest=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=MOD,input=(owned/name).read_bytes()).decode().strip()
        subprocess.run(['git','update-index','--cacheinfo','100644,'+digest+',state/'+name],cwd=MOD,check=True)
    for rel,digest in pins.items():assert hashlib.sha256(git('show',':'+(DEST/rel).relative_to(MOD).as_posix())).hexdigest()==digest,rel
    assert sorted(line.split() for line in git('diff','--numstat').decode().splitlines())==sorted([['24','0','src/RVAuthorityView.as'],['2','0','state/MEMORY.md'],['4','0','state/journal.md'],['15','0','tests/authority/AuthorityViewChecks.as']])
    subprocess.run(['git','diff','--cached','--check'],cwd=MOD,check=True)
    print(json.dumps(receipt,ensure_ascii=False),flush=True)
    record.outcome='passed';record.note='两轮32战斗窗及失败预检证据已保存；候选无稳定整体收益，未部署'
