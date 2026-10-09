"""Freeze/build a production RV cache candidate, or run isolated AIR assertions.

Uses the existing external-stub build route. Production and public test copies
are separate; no installed SWF, ordinary game process, or player save is changed.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, uuid
MOD=Path(__file__).resolve().parents[2];GAME=MOD.parents[1]
SDK=Path('D:/RemainsMod/mods/Sandevistan/build/tools/flexsdk')
JAVA=Path('C:/Users/hello/Documents/_sandevistan_dev/jdk-11.0.32.1+1-jre/bin/java.exe')
FFDEC=SDK.parent/'ffdec/ffdec-cli.jar'
ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['build','checks']);ap.add_argument('folder');a=ap.parse_args()
out=(MOD/a.folder).resolve();assert out.parent==MOD/'build' and out.name.startswith('exploration-cache-')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def run(cmd,log,timeout=120):
    r=subprocess.run(cmd,cwd=out,env=dict(os.environ,AIR_HOME=str(SDK)),capture_output=True,timeout=timeout)
    log.write_bytes(r.stdout+b'\n'+r.stderr)
    if r.returncode:print(log.read_bytes().decode('gb18030',errors='replace')[-5000:]);raise SystemExit(r.returncode)
    return log.read_text(encoding='utf-8',errors='replace')
base=[str(JAVA),'-Xmx512m','-jar']
common=['+configname=air','+flexlib='+str(SDK/'frameworks')]
if a.mode=='build':
    out.mkdir(exist_ok=False)
    inputs={}
    for directory in ('src','build/stubs','build/motion-tests'):
        for p in (MOD/directory).rglob('*'):
            if not p.is_file():continue
            n=p.relative_to(MOD).as_posix();dest=out/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);inputs[n]=sha(p)
    originals={n:sha(GAME/n) for n in ('pfe.swf','application.xml','mods/RealisticVision/release/RealisticVisionMod.swf','mods/RealisticVision/release/config.txt')}
    shutil.copy2(MOD/'release/RealisticVisionMod.swf',out/'installed-before.swf')
    # The unmodified oracle is the checked-in current source, hash pinned before editing.
    old=subprocess.check_output(['git','-C',str(MOD),'show','HEAD:src/RealisticVisionMod.as'])
    old_text=old.decode('utf-8-sig').replace('\r\n','\n')
    # Freeze original checked-in source explicitly; the benchmark never runs it as a deployed mod.
    (out/'original.as').write_text(old_text,encoding='utf-8')
    classes=['fe.World','fe.Pt','fe.Obj','fe.loc.Location','fe.loc.Tile','fe.graph.Grafon','fe.unit.Unit','fe.unit.UnitPlayer','fe.unit.Pers','fe.weapon.Weapon']
    run(base+[str(SDK/'lib/compc.jar')]+common+['-source-path='+str(out/'build/stubs'),'-include-classes']+classes+['-output='+str(out/'GameStubs.swc')],out/'stubs.log')
    run(base+[str(SDK/'lib/mxmlc.jar')]+common+['-swf-version=32','-debug=false','-optimize=true','-warnings=true',
        '-static-link-runtime-shared-libraries=true','-external-library-path='+str(out/'GameStubs.swc'),'-source-path='+str(out/'src'),
        '-output='+str(out/'RealisticVisionMod.swf'),str(out/'src/RealisticVisionMod.as')],out/'build.log')
    with (out/'classes.txt').open('wb') as stdout, (out/'classes-stderr.log').open('wb') as stderr:
        subprocess.run([str(JAVA),'-jar',str(FFDEC),'-dumpAS3',str(out/'RealisticVisionMod.swf')],stdout=stdout,stderr=stderr,check=True)
    actual={line.split()[0] for line in (out/'classes.txt').read_text(encoding='utf-8-sig').splitlines() if line.strip()}
    intended={p.relative_to(out/'src').with_suffix('').as_posix().replace('/','.') for p in (out/'src').rglob('*.as')}
    assert actual==intended,(actual,intended)
    save(out/'inputs.json',dict(source=inputs,protected=originals,original_sha256=sha(out/'original.as'),candidate_sha256=sha(out/'RealisticVisionMod.swf'),classes=sorted(actual),size=(out/'RealisticVisionMod.swf').stat().st_size))
    print(json.dumps(dict(candidate=sha(out/'RealisticVisionMod.swf'),classes=sorted(actual))))
else:
    m=json.loads((out/'inputs.json').read_text(encoding='utf-8'))
    for n,h in m['source'].items():assert sha(out/n)==h,n
    for n,h in m['protected'].items():assert sha(GAME/n)==h,n
    assert sha(out/'RealisticVisionMod.swf')==m['candidate_sha256']
    checks=out/'checks';checks.mkdir(exist_ok=False)
    source=(out/'src/RealisticVisionMod.as').read_text(encoding='utf-8')
    old=(out/'original.as').read_text(encoding='utf-8')
    start=old.index('      private function captureExploration(');end=old.index('      private function mergeExploration(',start)
    oracle=old[start:end].replace('captureExploration','referenceCapture')
    source=source.replace('      private function mergeExploration(',oracle+'      private function mergeExploration(')
    (checks/'RealisticVisionMod.as').write_text(re.sub(r'\bprivate\b','public',source),encoding='utf-8')
    records={}
    for entry in ('SoftHarness','SharedExplorationHarness','ExplorationCacheHarness'):
        run(base+[str(SDK/'lib/mxmlc.jar')]+common+['-swf-version=32','-debug=true','-optimize=false','-omit-trace-statements=false',
            '-static-link-runtime-shared-libraries=true','-source-path='+','.join(str(p) for p in (checks,out/'build/motion-tests',out/'build/stubs',out/'src')),
            '-output='+str(checks/(entry+'.swf')),str(out/'build/motion-tests'/(entry+'.as'))],checks/(entry+'-build.log'))
        desc=checks/(entry+'.xml');appid='rv-cache-check-'+uuid.uuid4().hex
        desc.write_text('<application xmlns="http://ns.adobe.com/air/application/30.0"><id>'+appid+'</id><versionNumber>1.0</versionNumber><filename>RVCacheCheck</filename><initialWindow><content>'+entry+'.swf</content><visible>false</visible><renderMode>cpu</renderMode></initialWindow></application>',encoding='utf-8')
        log=run([str(GAME/'adl64.exe'),'-runtime',str(GAME/'runtimes/air/win64'),str(desc)],checks/(entry+'.log'),60)
        assert 'COMPLETE' in log and 'FAIL ' not in log and 'failures=0' in log,(entry,log)
        records[entry]=dict(passed=log.count('PASS '),log_sha256=sha(checks/(entry+'.log')),appid=appid)
        print(entry+' '+log[-450:],flush=True)
    save(out/'checks.json',records)
    for n,h in m['protected'].items():assert sha(GAME/n)==h,n
