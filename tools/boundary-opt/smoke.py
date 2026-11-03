"""Native ModLoader startup of the exact release bytes, isolated and registered."""
import json, shutil, subprocess, sys
from run import GAME, HERE, MOD, OUT, r, runtime

folder=OUT/sys.argv[1];assert not folder.exists();runtime(folder)
probe=folder/'mods/SmokeProbe/release'
entry=MOD/'build/eye-boundary/SmokeProbeMod.as'
r.runner.compile(entry,probe/'SmokeProbeMod.swf',[entry.parent])
release=folder/'mods/RealisticVision/release'
shutil.copyfile(OUT/'production/RealisticVisionMod.swf',release/'RealisticVisionMod.swf')
# Test-only enable. The user's Local Store and installed template are untouched.
cfg=(release/'config.txt').read_text('utf8')
assert cfg.count('enabled=0')==1
(release/'config.txt').write_text(cfg.replace('enabled=0','enabled=1'),'utf8')
catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True)
(catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text('utf-8-sig')+'\nSmokeProbe|SmokeProbeMod|1|0|0\n','utf8')
p=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),
    '--only','RealisticVisionMod,SmokeProbeMod','--no-ui','--report',str(folder/'selection.json')],capture_output=True)
assert p.returncode==0,p.stdout+p.stderr
with r.Registration(owner='RealisticVision / ray-loop production',purpose=sys.argv[1],
    resource='game-coexist',run_dir=folder,evidence=folder/'validation.json',wait=300) as rec:
    code,log=r.air(folder,'pfe.swf',rec,180)
    rvlog=(folder/'storage/RVision.log').read_text('utf8')
    print(log[-1000:]);print(rvlog[-1000:])
    assert code==0 and 'PRODUCTION SMOKE COMPLETE' in log and 'FAIL ' not in log
    assert 'init ok v0.34.5-ray-loop' in rvlog and 'onFrame error' not in rvlog
    assert 'tick ' in rvlog
    assert all('ModLoader[ok_'+n+']' in log for n in ['RealisticVisionMod','SmokeProbeMod'])
    r.save(folder/'validation.json',{'passed':True,'production':r.sha(release/'RealisticVisionMod.swf'),
        'config':r.sha(release/'config.txt'),'host':r.sha(folder/'pfe.swf')})
    rec.outcome='passed';rec.note='Exact production bytes: native init, settings registration and active frames'
