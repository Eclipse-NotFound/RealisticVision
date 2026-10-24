"""One registered test group; sequential children share its real reservation."""
from pathlib import Path
import sys, runpy, json, contextlib, hashlib, time, traceback, zlib

HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];GAME=MOD.parents[1]
OUT=MOD/'build/effect-load-v3-output'
sys.path.insert(0,str(GAME/'mods/ModLoader/tools'))
sys.path.insert(0,str(HERE))
import test_registry
RealRegistration=test_registry.Registration

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def step(args,done):
    marker=OUT/done
    if marker.exists():
        data=json.loads(marker.read_text(encoding='utf-8-sig'))
        if done.endswith('last-run.json'):assert data['exit']==0,(done,data)
        print('EXISTING '+done,flush=True)
        return
    label=' '.join(args)
    target=OUT/'group-steps';target.mkdir(exist_ok=True)
    log=target/(str(time.time_ns())+'-'+args[0]+'.log')
    print('GROUP START '+label,flush=True)
    old=sys.argv[:]
    try:
        sys.argv=[str(HERE/args[0]),*args[1:]]
        with log.open('w',encoding='utf-8') as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
            runpy.run_path(str(HERE/args[0]),run_name='__main__')
        assert marker.exists(),done
    except BaseException:
        with log.open('a',encoding='utf-8') as stream:traceback.print_exc(file=stream)
        print(log.read_text(encoding='utf-8')[-2500:],flush=True)
        raise
    finally:sys.argv=old
    print('GROUP PASS '+label,flush=True)

if __name__=='__main__':
    with RealRegistration(owner='RealisticVision / D43 最终验证组',purpose='准确包、视觉、反序战斗；各子实例顺序退出',run_dir=OUT/'group-steps',evidence=OUT/'verified.json',wait=900) as record:
        # Same-process helpers borrow the existing reservation; there is never
        # a nested acquisition or an unregistered AIR child. Existing launch
        # helpers still call before_launch, child and child_stopped on record.
        def borrowed(**kwargs):return contextlib.nullcontext(record)
        test_registry.Registration=borrowed
        try:
            assert sha(GAME/'mods/RConnect/release/RConnectMod.swf')=='78c052aea963f1689b705ae1e14d274916ae1a1f7e81933390caf8d1a88f4699'
            step(['native.py','build','native-05','--lean','--samples','120'],'native-05/build.json')
            files=['pfe.swf','mods/ModLoader/release/ModLoaderMod.swf','mods/ModLoader/release/telemetry.json']
            pins={rel:sha(OUT/'native-05'/rel) for rel in files}
            assert all(sha(GAME/rel)==digest for rel,digest in pins.items())
            data=(OUT/'native-05/mods/ModLoader/release/ModLoaderMod.swf').read_bytes()
            body=zlib.decompress(data[8:]) if data[:3]==b'CWS' else data[8:]
            (OUT/'native-05/supplemental-inputs.json').write_text(json.dumps({'files':pins,'runtime_contains_frame_recorder':b'FrameRecorder' in body,'runtime_contains_telemetry_path':b'telemetry.json' in body},indent=2),encoding='utf-8')
            step(['functional.py','build','functional-03'],'functional-03/build.json')
            step(['functional.py','run','functional-03'],'functional-03/last-run.json')
            step(['native.py','run','native-05','--lean','--samples','120'],'native-05/last-run.json')
            step(['review.py','native-03','native-05'],'verified.json')
            record.outcome='passed';record.note='功能/来源门禁通过，性能是否采用仍需独立判断'
        finally:test_registry.Registration=RealRegistration
