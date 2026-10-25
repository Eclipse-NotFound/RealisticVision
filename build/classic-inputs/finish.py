"""Preserve D50 evidence and its exact pending state; do not deploy."""
from pathlib import Path
import ast, hashlib, json, shutil, subprocess, sys

MOD = Path(__file__).resolve().parents[2]
GAME = MOD.parents[1]
OUT = MOD / 'build/classic-inputs-output'
DEST = MOD / 'knowledge/experiments/classic-inputs-d50-20261025'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=MOD)


assert git('rev-parse', 'HEAD').decode().startswith('932330b')
assert not git('diff', '--cached', '--name-only').strip()
expected = {
    'release/RealisticVisionMod.swf': '638e2d408e2cf46683c41114f75773829a1b4417d74bffe9d08855a4fe343710',
    'release/config.txt': '5136ee1923a77f5f10eab1b3994b64cbd67b09d687a7e829fb1e81d2e79a3c7f',
    '../../pfe.swf': 'a796827173af7d6fab9885fb66ecc62182ab5335918a30c7cce4c44914a238b7',
}
assert all(sha(MOD / p) == h for p, h in expected.items())
sys.path.insert(0, str(GAME / 'mods/ModLoader/tools'))
from test_registry import Registry, Registration
assert not [r for r in Registry().status() if 'RealisticVision' in r['owner']
            and r['state'] in ('waiting', 'running', 'needs-check')]

finished = {'local-01': 0, 'native-01': 0, 'combat-01': 0, 'all-local-01': 0,
            'all-native-functional-02': 0, 'all-transitions-01': 1, 'all-transitions-02': 0}
for name, code in finished.items():
    assert json.loads((OUT / name / 'last-run.json').read_text())['exit'] == code
    assert not (OUT / name / 'test.xml').exists()
assert not (OUT / 'all-native-01/last-run.json').exists()
assert not (OUT / 'all-native-01/test.xml').exists()
assert not (OUT / 'all-combat-01').exists()

with Registration(owner='RealisticVision / D50 保存证据',
                  purpose='非游戏；功能完成，独立计时按用户选择暂缓',
                  run_dir=OUT, evidence=DEST / 'archive.json', wait=900) as rec:
    assert not DEST.exists()
    DEST.mkdir(parents=True)
    pins = {}
    for top in [*finished, 'all-native-01', 'candidates', 'group-steps']:
        folder = OUT / top
        for p in folder.rglob('*'):
            if not p.is_file():
                continue
            rel = p.relative_to(folder)
            keep = (p.suffix == '.as' or len(rel.parts) == 1 and p.suffix in ('.json', '.log', '.txt')
                    or 'evidence' in rel.parts and p.suffix in ('.json', '.png')
                    or top == 'candidates' and p.suffix == '.json')
            if keep:
                q = DEST / p.relative_to(OUT)
                q.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, q)
                pins[q.relative_to(DEST).as_posix()] = sha(q)
    for name in ['inputs.json', 'PERFORMANCE-PAUSED.json']:
        shutil.copyfile(OUT / name, DEST / name)
        pins[name] = sha(DEST / name)
    (DEST / '.gitattributes').write_text(
        '** -text\n*.log -whitespace\n*.txt -whitespace\n*.as -whitespace\n*.json whitespace=cr-at-eol\n',
        encoding='utf-8', newline='\n')
    pins['.gitattributes'] = sha(DEST / '.gitattributes')
    receipt = {'formalUnchanged': expected, 'adopted': False, 'status': 'pending-performance',
               'functional': {'rawLocal': 6529, 'rawNative': 64, 'allLocal': 6529,
                              'allNative': 64, 'allTransitions': 59397},
               'rawCombatPairedIntervals': 2148, 'allCombatRan': False,
               'failedFixtureRetained': 'all-transitions-01',
               'userChoice': '保留试玩，先做代码和画面检查', 'activeOwnedGameTests': 0}
    (DEST / 'finish.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    pins['finish.json'] = sha(DEST / 'finish.json')
    (DEST / 'archive.json').write_text(json.dumps(pins, indent=2) + '\n', encoding='utf-8')

    head = '> 2026-10-25 **D50功能完成，独立计时暂缓，正式仍D44**：classic私有插值raw候选6529+64检查通过，亮度0.6普通房间战斗均值51.89→50.79ms，current52.87→53.48ms；单轮小收益未采用。all再缓存私有墙场，6529局部+64原生+59397临界尺寸/设置/模式/换房检查严格相同，尚无性能数据。用户选择保留player-1/player-2、先做代码和画面检查；暂停独立计时，不关试玩。所有自有AIR退出。详见[报告](../knowledge/experiments/2026-10-25-classic-inputs.md)，证据classic-inputs-d50-20261025。'
    stop = '- D50：raw/all均待判定，未部署；用户明确保留试玩、只做代码和画面检查，独立计时暂停标志build/classic-inputs-output/PERFORMANCE-PAUSED.json。不要重跑已结束all-plan或覆盖all-native-01；all-native-functional-02只做像素，不可用于计时。四尺寸转换测试已通过，新路径仅小房间且主要用于非默认亮度。待用户明确恢复独立性能测试后，重新核对试玩/登记/包组合，在新目录测all并复验。正式准确源仍D44；目标未完成。下方为历史停点。'
    journal = '''## 2026-10-25 — D50私有插值画面通过，独立性能暂缓

- 从准确D44生产源独立派生raw/all，普通房间按原查询代复用私有原始/可见性/墙场，公开查询范围和顺序不变；current及大图没有新算法，主要适用于亮度不等于0.35。
- raw局部6529/原生64通过，完整14入口+RV子域12窗2148有效间隔：classic51.89→50.79ms、P95 73→70；current52.87→53.48ms。单轮小收益不足采用，不能与D49不同机器负载拼数字。
- all局部6529、原生64、4尺寸×16组合×32帧59397项严格相同。首个扩展夹具29698项后因基线大图读取缺少cam报1069；只补测试World.cam/Location.space后新目录通过，失败证据保留。
- all-native-01因两份试玩仍运行在启动前退出；用户明确保留试玩、先查代码和画面。functional-02只比较冻结字节画面，标禁止性能用途；独立性能入口保留环境门控并新增本轮暂停标志。所有自有AIR/临时描述符已退出，不关闭两份试玩。
- 正式638E/config5136/rootA796不变，4项外部authority WIP保留；未改src/release、未部署、无出站消息。报告knowledge/experiments/2026-10-25-classic-inputs.md。待用户恢复独立计时后新目录验证all完整战斗，整体目标仍未完成。

'''
    owned = OUT / 'owned-state'
    owned.mkdir(exist_ok=True)
    for name in ['MEMORY.md', 'journal.md']:
        base = git('show', 'HEAD:state/' + name).decode('utf-8')
        live = (MOD / 'state' / name).read_text(encoding='utf-8')

        def transform(s):
            if name == 'journal.md':
                return journal + s
            at = s.index('> 2026-10-25 **D49')
            s = s[:at] + head + '\n\n' + s[at:]
            old = '- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。D45尚在验证，正式安装未改，性能边界见顶部报告。'
            new = '- 当前安装D44 v0.33.10；准确生产源build/combat-render-output/production-final2/src，排除authority。D50候选功能通过，独立性能按用户选择暂缓；正式安装未改，详见顶部报告。'
            assert s.count(old) == 1
            s = s.replace(old, new)
            pos = s.index('\n\n', s.index('## 4. 正在进行与停点')) + 2
            return s[:pos] + stop + '\n\n' + s[pos:]

        (owned / name).write_text(transform(base), encoding='utf-8', newline='\n')
        (MOD / 'state' / name).write_text(transform(live), encoding='utf-8', newline='\n')
    for p in (MOD / 'build/classic-inputs').glob('*.py'):
        ast.parse(p.read_text(encoding='utf-8'))
    subprocess.run(['git', 'add', '--', '.gitignore', 'build/classic-inputs',
                    'knowledge/experiments/2026-10-25-classic-inputs.md'], cwd=MOD, check=True)
    subprocess.run(['git', 'add', '-f', '--', str(DEST)], cwd=MOD, check=True)
    for name in ['MEMORY.md', 'journal.md']:
        digest = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'], cwd=MOD,
                                         input=(owned / name).read_bytes()).decode().strip()
        subprocess.run(['git', 'update-index', '--cacheinfo', '100644,' + digest + ',state/' + name], cwd=MOD, check=True)
    for rel, h in pins.items():
        assert hashlib.sha256(git('show', ':' + (DEST / rel).relative_to(MOD).as_posix())).hexdigest() == h, rel
    assert sorted(line.split() for line in git('diff', '--numstat').decode().splitlines()) == sorted([
        ['24', '0', 'src/RVAuthorityView.as'], ['2', '0', 'state/MEMORY.md'],
        ['4', '0', 'state/journal.md'], ['15', '0', 'tests/authority/AuthorityViewChecks.as']])
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=MOD, check=True)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    rec.outcome = 'passed'
    rec.note = '证据和状态已保存；候选未部署，独立性能按用户选择暂缓'
