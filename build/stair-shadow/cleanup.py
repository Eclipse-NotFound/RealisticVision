"""Remove only this experiment's byte-identical copied runtime assets.

Candidate binaries, sources, logs, evidence and recovery inputs are retained.
Run only after all D30 AIR descriptors have been removed by the runner.
"""
from pathlib import Path
import hashlib,json,re
MOD=Path(__file__).resolve().parents[2]
OUT=(MOD/'build/stair-shadow-output').resolve()
FROZEN=MOD/'build/wall-restore-output/game-rock'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    receipt=OUT/'runtime-cleanup.json'
    if receipt.exists():raise RuntimeError('Cleanup already recorded; preserve the existing receipt')
    plan_file=OUT/'runtime-cleanup-plan.json'
    if plan_file.exists():raise RuntimeError('Existing cleanup plan needs review; do not overwrite a possibly interrupted run')
    plan=[]
    for name in ['diagnostic','reproduction','reproduction-isolation']:
        folder=OUT/name
        assert folder.is_dir() and not (folder/'test.xml').exists(),'AIR may still be running'
        pairs=[]
        for p in folder.iterdir():
            if re.fullmatch(r'(pfe|sound|sound_unit|sound_weapon|sprite|sprite1|texture|texture1)\.swf|(text_.*|lang|launcher_text)\.xml',p.name):
                source=MOD/'build/wall-performance-output/runtime-inputs/pfe.swf' if p.name=='pfe.swf' else FROZEN/p.name
                pairs.append((p,source))
        pairs += [(p,FROZEN/'Rooms'/p.relative_to(folder/'Rooms')) for p in (folder/'Rooms').rglob('*') if p.is_file()]
        for p,source in pairs:
            assert not p.is_symlink() and p.resolve().is_relative_to(OUT)
            digest=sha(p);assert digest==sha(source),'Unexpected asset change: '+str(p)
            plan.append({'path':str(p),'retained_source':str(source),'bytes':p.stat().st_size,'sha256':digest})
    plan_file.write_text(json.dumps({'status':'PLANNED','files':len(plan),
        'bytes':sum(i['bytes'] for i in plan),'items':plan},ensure_ascii=False,indent=2),encoding='utf-8')
    for item in plan:
        p=Path(item['path']);assert p.resolve().is_relative_to(OUT) and sha(p)==item['sha256']
        p.unlink()
    # Remove empty Rooms directories only; never recursively remove an output tree.
    for name in ['diagnostic','reproduction','reproduction-isolation']:
        root=OUT/name/'Rooms'
        if root.exists():
            for p in sorted((p for p in root.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
                if not any(p.iterdir()):p.rmdir()
            if not any(root.iterdir()):root.rmdir()
    data={'status':'PASS','files':len(plan),'bytes':sum(i['bytes'] for i in plan),'items':plan}
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k!='items'},ensure_ascii=False))
if __name__=='__main__':main()
