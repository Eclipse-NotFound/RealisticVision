"""Remove only byte-identical native runtime copies after D34 deployment."""
from pathlib import Path
import json
import run
MOD,GAME,OUT=run.MOD,run.GAME,run.OUT
def main():
    assert json.loads((OUT/'deployment/receipt.json').read_text())['result']=='PASS'
    targets=[]
    for name in ['native','native-final']:
        folder=(OUT/name).resolve(strict=True)
        assert folder.is_relative_to(OUT.resolve()) and not list(folder.glob('test-*.xml'))
        candidates=list(folder.glob('*.swf'))+list(folder.glob('*.xml'))+list((folder/'Rooms').rglob('*'))
        for f in candidates:
            if not f.is_file():continue
            resolved=f.resolve(strict=True)
            assert resolved.is_relative_to(folder)
            original=GAME/f.relative_to(folder)
            if original.is_file() and run.p.sha(original)==run.p.sha(f):
                targets.append({'path':str(resolved.relative_to(MOD)),'source':str(original.relative_to(GAME)),'sha':run.p.sha(f),'bytes':f.stat().st_size})
    dest=MOD/'knowledge/experiments/vision-settings-v0330-20261021/cleanup.json'
    assert not dest.exists()
    run.save(dest,{'status':'PLANNED','files':targets})
    for row in targets:
        f=(MOD/row['path']).resolve(strict=True)
        assert f.is_relative_to(OUT.resolve()) and run.p.sha(f)==row['sha'] and run.p.sha(GAME/row['source'])==row['sha']
        f.unlink()
    run.save(dest,{'status':'COMPLETE','count':len(targets),'bytes':sum(r['bytes'] for r in targets),'files':targets})
    print('Removed identical owned runtime copies:',len(targets),sum(r['bytes'] for r in targets),'bytes')
if __name__=='__main__':main()
