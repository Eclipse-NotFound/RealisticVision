"""D28: frozen installed lineage; never regenerate historical candidates."""
from pathlib import Path
import hashlib,shutil,subprocess,json
MOD=Path(__file__).resolve().parents[2]
OUT=MOD/'build/wall-restore-output'
BASE=MOD/'build/wall-options-output/candidate/src'
PIN='2a01d94da3a42462701e651579b395aaab76146e995d5c4034506cb48b22b65a'

def upgrade(s):
    assert s.count('private var cfgWallBright:Boolean = true;')==1
    s=s.replace('private var cfgWallBright:Boolean = true;','private var cfgWallBright:Boolean = false;')
    s=s.replace('"hint":"关闭后墙面随视野变暗；两种模式始终修正墙边阴影","def":true',
                '"hint":"关闭后墙面随视野变暗；两种模式始终修正墙边阴影","def":false')
    s=s.replace('v0.31.1-wall-options-candidate','v0.32.0-wall-restore-candidate')
    return s

def prepare():
    assert hashlib.sha256((BASE/'RealisticVisionMod.as').read_bytes()).hexdigest()==PIN
    pins=json.loads((Path(__file__).parent/'inputs.json').read_text(encoding='utf-8'))
    for root,key in [(BASE,'installed_source'),(MOD/'build/wall-options-output/baseline/src','legacy_source')]:
        for name,digest in pins[key].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Frozen input changed: '+name
    assert hashlib.sha256((MOD/'src/RVWallSurface.as').read_bytes()).hexdigest()==pins['helper_sha256'],'Helper changed: use a new experiment, do not overwrite this candidate'
    OUT.mkdir(parents=True,exist_ok=True)
    for variant in ['baseline','candidate']:
        dest=OUT/variant/'src'
        if not dest.exists():shutil.copytree(BASE,dest)
    dest=OUT/'candidate/src'
    (dest/'RealisticVisionMod.as').write_text(upgrade((BASE/'RealisticVisionMod.as').read_text(encoding='utf-8-sig')),encoding='utf-8')
    shutil.copyfile(MOD/'src/RVWallSurface.as',dest/'RVWallSurface.as')
    # Independent pre-D27 reference keeps newer keys/locales/scene compatibility.
    old=MOD/'build/wall-options-output/baseline/src'
    if not (OUT/'legacy/src').exists():shutil.copytree(old,OUT/'legacy/src')
    if not (OUT/'wip-before.patch').exists():
        (OUT/'wip-before.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=MOD))
    print('D28 source prepared; release untouched')

if __name__=='__main__':prepare()
