"""Registered, isolated boundary trials; production is read-only here."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, re, shutil, subprocess, sys

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
GAME = MOD.parents[1]
OUT = MOD / 'build/boundary-opt-20261103'
BASE = MOD / 'build/perf-20261102/src'
PIN = '2d5360864abd7a6e6115fbe6c362cd0ed5f0665a8d336513df6e711b3f064407'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


r = load('boundary_runtime', MOD / 'build/motion-performance/run.py')
from test_resources import snapshot, comparison_environment


def instrument(source):
    source = r.fp.instrument(source, ['prepareOcclusion', 'computeFov', 'fillFogCache',
        'applyVision', 'updateWallSurface', 'hideEnemies', 'applyWorldVisuals',
        'applyWorldVisual', 'refreshMask', 'recalcTile'])
    pos = source.index('{', source.index('public class')) + 1
    source = source[:pos] + '\npublic var audit:Object={};\n' + source[pos:]
    def hit(anchor, name):
        nonlocal source
        assert source.count(anchor) == 1, anchor
        source = source.replace(anchor, 'audit["'+name+'"] = int(audit["'+name+'"])+1;\n'+anchor)
    hit('         var lit:Number = 1;\n         var leaked:Boolean = false;', 'rays')
    hit('         if(bdb==null){bdb=new BitmapData(totx,toty,true,0);rec.m2e=bdb;}', 'mixedChecks')
    hit('            bdb.applyFilter(bd,bd.rect,this.fogPoint,blur);', 'blur')
    hit('         rec.lastFov = this.fovVersion;', 'rasterRefresh')
    hit('         if(raster==null){raster={worldRaster:true', 'rasterRequests')
    return source


def prepare():
    assert r.sha(MOD/'release/RealisticVisionMod.swf') == PIN, 'Re-freeze new installation'
    OUT.mkdir(exist_ok=True)
    if not (OUT/'baseline').exists():
        shutil.copytree(BASE, OUT/'baseline/src')
        shutil.copyfile(MOD/'release/RealisticVisionMod.swf', OUT/'baseline/installed.swf')
        config = Path(os.environ['APPDATA'])/'pfe/Local Store/RealisticVision_config.txt'
        if not config.exists(): config = MOD/'release/config.txt'
        shutil.copyfile(config, OUT/'baseline/RealisticVision_config.txt')
        r.save(OUT/'inputs.json', {'installed': PIN, 'configOrigin': str(config),
            'config': r.sha(config), 'source': {p.relative_to(BASE).as_posix(): r.sha(p)
                                             for p in BASE.rglob('*.as')}})
    pins = json.loads((OUT/'inputs.json').read_text('utf8'))
    assert all(r.sha(OUT/'baseline/src'/p)==h for p,h in pins['source'].items())


def link_or_copy(source, target):
    # Filesystem policies may disallow hardlinks; a private copy is equivalent.
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)
    return str(target)


def runtime(folder):
    folder.mkdir(parents=True)
    (folder/'evidence').mkdir()
    for p in GAME.iterdir():
        if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):
            if p.name == 'pfe.swf': shutil.copyfile(p,folder/p.name)
            else: link_or_copy(p,folder/p.name)
    shutil.copytree(GAME/'Rooms',folder/'Rooms',copy_function=link_or_copy)
    shutil.copyfile(GAME/'application.xml',folder/'application.xml')
    cfg = folder/'mods/RealisticVision/release/config.txt'
    cfg.parent.mkdir(parents=True)
    shutil.copyfile(OUT/'baseline/RealisticVision_config.txt',cfg)


def run(args):
    prepare()
    folder = OUT/args.name
    assert not folder.exists(), 'Use a new run name'
    runtime(folder)
    probe = 'BoundaryExactProbeMod' if args.checks else 'BoundaryPerfProbeMod'
    source = (HERE/(probe+'.as')).read_text('utf8')
    source = source.replace('const PROFILE:Boolean=true', 'const PROFILE:Boolean='+str(args.profile).lower())
    source = source.replace('const PAIRED:Boolean=false', 'const PAIRED:Boolean='+str(args.paired).lower())
    source = source.replace('const REVERSE:Boolean=false', 'const REVERSE:Boolean='+str(args.reverse).lower())
    source = source.replace('const MOVING:Boolean=false', 'const MOVING:Boolean='+str(args.moving).lower())
    (folder/(probe+'.as')).write_text(source,'utf8')
    r.runner.compile(folder/(probe+'.as'),folder/('mods/BoundaryProbe/release/'+probe+'.swf'),[folder])
    sources = [('baseline',OUT/'baseline/src')]
    if args.candidate: sources.append(('candidate',OUT/args.candidate/'src'))
    for name, src in sources:
        r.public(src,folder/(name+'-src'))
        p = folder/(name+'-src/RealisticVisionMod.as')
        if args.profile: p.write_text(instrument(p.read_text('utf8')),'utf8')
        r.runner.compile(p,folder/(name+'.swf'),[p.parent],stubs=True)
    if not args.candidate: shutil.copyfile(folder/'baseline.swf',folder/'candidate.swf')
    catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True)
    (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text('utf-8-sig')+'\nBoundaryProbe|'+probe+'|1|0|0\n','utf8')
    selection=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',probe,'--no-ui','--report',str(folder/'selection.json')],capture_output=True)
    assert selection.returncode==0,selection.stdout+selection.stderr
    r.save(folder/'build.json',{'args':vars(args),'host':r.sha(folder/'pfe.swf'),
        'baseline':r.sha(folder/'baseline.swf'),'candidate':r.sha(folder/'candidate.swf'),
        'probe':r.sha(folder/('mods/BoundaryProbe/release/'+probe+'.swf'))})
    with r.Registration(owner='RealisticVision / boundary optimization',purpose=args.name,
        resource='game',run_dir=folder,evidence=folder/'evidence/result.json',wait=300) as rec:
        before=snapshot();r.save(folder/'before.json',before)
        owned_process = r.HiddenProcess
        def launch(*positional, **keywords):
            process = owned_process(*positional, **keywords)
            r.save(folder/'resource-policy.json',process.resource_policy)
            return process
        r.HiddenProcess = launch
        try:
            code,log=r.air(folder,'pfe.swf',rec,420)
        finally:
            r.HiddenProcess = owned_process
        after=snapshot();r.save(folder/'after.json',after)
        print(log[-2200:],flush=True)
        assert code==0 and ('BOUNDARY EXACT COMPLETE' if args.checks else 'BOUNDARY PERF COMPLETE') in log and 'FAIL ' not in log
        assert 'ModLoader[ok_'+probe+']' in log
        rec.outcome='passed';rec.note='Isolated native trial completed; performance conclusions in report'
        data=json.loads((folder/'evidence/result.json').read_text('utf8'))
        env=comparison_environment('benchmark',before,after,
            json.loads((folder/'resource-policy.json').read_text('utf8')))
        if not args.checks and any(max(c['intervals'])>5000 for c in data['cases']):
            env['performanceEligible']=False
            env['reasons'].append('Multi-second interruption observed; retain raw data, do not claim frame-time gains')
        r.save(folder/'environment.json',env)
        if args.checks:
            print(json.dumps(data),flush=True)
            return
        for c in data['cases']:
            xs=sorted(c['intervals']); us=c['updates']
            print(c['scenario'],c['variant'],'n',len(xs),'mean',round(sum(xs)/len(xs),3),
                'p95',xs[int(.95*(len(xs)-1))],'max',max(xs),'rv',round(sum(us)/len(us),3),
                'shotsLower',c['shotsLower'],'counts',c.get('audit'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--profile',action='store_true')
    p.add_argument('--paired',action='store_true');p.add_argument('--reverse',action='store_true')
    p.add_argument('--candidate');p.add_argument('--checks',action='store_true')
    p.add_argument('--moving',action='store_true');run(p.parse_args())
