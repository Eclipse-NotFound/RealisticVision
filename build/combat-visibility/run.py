"""D36: isolated native weapon visibility and performance investigation."""
from pathlib import Path
import sys, json, re, shutil, subprocess, argparse
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]; GAME=MOD.parents[1]; OUT=MOD/'build/combat-visibility-output'
sys.path.insert(0,str(MOD/'build/motion-performance'))
import run as r
r.OUT=OUT
BASE=MOD/'build/regression-recovery-output/production-singlepass/src'

def build(name, full=False):
    folder=OUT/name; assert not folder.exists();folder.mkdir(parents=True)
    with r.Registration(owner='RealisticVision / D36 武器遮挡',purpose=name+' build',run_dir=folder,evidence=folder/'build.json',wait=300) as rec:
        r.runtime(folder)
        s=(MOD/'build/frame-performance/FrameProbe.as').read_text(encoding='utf-8-sig')
        s=s.replace('FrameProbe','CombatVisibilityProbeMod').replace('/RealisticVision/build/frame-performance-output/','/RealisticVision/build/combat-visibility-output/')
        s=s.replace('makeUnits(w);canvas=', 'inspectWeapons(w);return;makeUnits(w);canvas=')
        s=s.replace('      private function makeUnits(w:*):void{',(HERE/'inspect.as.inc').read_text(encoding='utf-8')+'\n      private function makeUnits(w:*):void{')
        entry=folder/'CombatVisibilityProbeMod.as';entry.write_text(s,encoding='utf-8')
        r.runner.compile(entry,folder/'mods/CombatVisibilityProbe/release/CombatVisibilityProbeMod.swf',[folder],definitions=['-define=CONFIG::largeScene,false','-define=CONFIG::verifyPixels,false','-define=CONFIG::liveFrames,false'])
        inv=json.loads(subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--list','--json','--no-ui'],capture_output=True,text=True,encoding='utf-8-sig',timeout=45).stdout)
        r.save(folder/'inventory.json',inv)
        selected=[]
        if full:
            for item in inv['mods']:
                if item['enabled'] and item['entry']!='RealisticVisionMod':
                    shutil.copytree(GAME/'mods'/item['directory']/'release',folder/'mods'/item['directory']/'release')
                    selected.append(item['entry'])
        selected.append('CombatVisibilityProbeMod')
        catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
        (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nCombatVisibilityProbe|CombatVisibilityProbeMod|1|0|0\n',encoding='utf-8')
        p=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only',','.join(selected),'--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8-sig',timeout=45)
        assert p.returncode==0,p.stdout+p.stderr
        for v in ['baseline','candidate']:
            source=BASE if v=='baseline' or not (OUT/'candidate/src').exists() else OUT/'candidate/src'
            r.public(source,folder/(v+'-src'))
            r.runner.compile(folder/(v+'-src/RealisticVisionMod.as'),folder/(v+'.swf'),[folder/(v+'-src')],stubs=True)
        r.save(folder/'build.json',{'files':{str(p.relative_to(folder)):r.sha(p) for p in folder.rglob('*') if p.is_file() and p.suffix in ['.swf','.as','.txt','.xml']}})
        rec.outcome='passed'

def functional(name):
    folder=OUT/name
    assert not (folder/'last-run.json').exists()
    pins=json.loads((folder/'build.json').read_text())['files']
    assert all(r.sha(folder/k)==v for k,v in pins.items())
    with r.Registration(owner='RealisticVision / D36 武器功能复现',purpose=name,run_dir=folder,evidence=folder/'evidence/result.json',wait=300) as rec:
        r.save(folder/'launch-state.json',r.environment())
        code,log=r.air(folder,'pfe.swf',rec,180)
        print(log[-6000:])
        assert code==0 and 'FRAME COMPLETE' in log and 'FAIL ' not in log
        rec.outcome='passed';rec.note='驱动完成；症状判定看result；不是性能计时资格'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run']);p.add_argument('name');p.add_argument('--full',action='store_true');a=p.parse_args()
    if a.action=='build':build(a.name,a.full)
    else:functional(a.name)
