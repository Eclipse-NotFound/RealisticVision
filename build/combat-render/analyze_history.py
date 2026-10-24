"""Offline evidence analysis only: never imports the AIR/build runner."""
from pathlib import Path
import hashlib,json,re

MOD=Path(__file__).resolve().parents[2]
SOURCE=MOD/'build/effect-load-v3-output/native-06'
TARGET=MOD/'knowledge/experiments/combat-render-d44-20261025/native06-lifetime-analysis.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert not TARGET.exists(),'Preserve prior evidence'
    build=json.loads((SOURCE/'build.json').read_text())
    pins={k.replace('\\','/'):v for k,v in build['files'].items()}
    inputs=['RecoveryFrameProbeMod.as','candidate-src/RealisticVisionMod.as']
    for name in inputs:assert sha(SOURCE/name)==pins[name],name
    probe=(SOURCE/inputs[0]).read_text(encoding='utf-8-sig')
    rv=(SOURCE/inputs[1]).read_text(encoding='utf-8-sig')
    # New independent RV instance per window; constructor only calls super.
    assert 'liveMod=new cls();' in probe and 'if(++liveAge<150)return;' in probe
    assert probe.count('liveMod.onFrameInner();')==1
    assert re.search(r'public function RealisticVisionMod\(\)\s*\{\s*super\(\);\s*\}',rv)
    assert 'public var worldPass:int = 0;' in rv
    assert rv.count('this.worldPass++;')==1
    assert rv.count('this.hideEnemies(w,loc,needFov);')==1
    assert rv.count('this.applyWorldVisuals(w,loc);')==1
    assert 'if(this.worldPass%60==0)' in rv and 'if(this.worldPass-int(raster.used)>120)' in rv
    assert 'raster.used=this.worldPass;' in rv
    first_possible=next(n for n in range(1,241) if n%60==0 and n-1>120)
    data=json.loads((SOURCE/'evidence/result.json').read_text())
    cases=[]
    for i,c in enumerate(data['cases']):
        if c['variant']!='candidate':continue
        frames=[f for f in c['frames'] if 'nextInterval' in f]
        assert max(f['age'] for f in c['frames'])==149
        longest=max(frames,key=lambda f:f['nextInterval'])
        cases.append({'case':i,'mode':c['mode'],'timedFrames':len(frames),'maxInvocations':150,
                      'possiblePeriodicDisposals':0,
                      'longest':{k:longest[k] for k in ['age','nextInterval','rv','outsideRV','objects','projectiles','viewChanged']}})
    result={'scope':'D43 native-06 only; not a new game test or proof of overall cause',
            'method':'fresh instance starts worldPass=0; at most one increment per update; all 150 updates precede first possible stale-raster disposal at pass 180',
            'firstPossiblePeriodicDisposalPass':first_possible,'cases':cases,
            'limits':['Periodic dictionary scanning still occurs at passes 60/120.','Other BitmapData disposal/reallocation and GC remain possible.','outsideRV includes final Flash rendering; not proof of unrelated cost.','Longer-lived real play can reach cache eviction; it is not covered by these short windows.'],
            'inputs':{str((SOURCE/n).relative_to(MOD)).replace('\\','/'):sha(SOURCE/n) for n in inputs+['build.json','evidence/result.json']}}
    TARGET.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
