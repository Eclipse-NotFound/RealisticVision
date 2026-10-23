from pathlib import Path
import sys,types
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
code=(MOD/'build/long-frame/trace.py').read_text(encoding='utf-8')
code=code[:code.index("if __name__=='__main__':")].replace('long-frame-output','effect-visibility-output').replace('candidate-00','baseline').replace('D39','D42')
t=types.ModuleType('trace');t.__file__=str(HERE/'trace.py');exec(compile(code,t.__file__,'exec'),t.__dict__);t.original_source=t.source_probe
body=(MOD/'build/motion-performance/run.py').read_text(encoding='utf-8');body=body[body.index('def run(name):'):body.index('\ndef repeat(')]
body=body.replace('>=6*1024**3','>=5*1024**3').replace('Less than 6 GiB','Less than 5 GiB');exec(body,t.r.__dict__)
sys.modules['trace']=t
code=(MOD/'build/overall-flow/native_walk.py').read_text(encoding='utf-8').replace('overall-flow-output','effect-visibility-output').replace("'candidate-05'","'candidate'")
# Real mercenary attack, body, separate arm and gun run in the same native loop.
code=code.replace('s=base(False).replace(', 's=base(False).replace("fe.unit.UnitRaider","fe.unit.UnitMerc").replace(')
# Mercenary hits cause brief grounded-flag transitions. Keep the stronger
# position/floor checks each frame; require >=200/240 grounded samples.
code=code.replace('liveRow.grounded<220','liveRow.grounded<200')
# A real hit can lift the player by more than the walking-only 8 px tolerance.
# Still require the same platform (within one tile), position bounds, sustained
# ground contact and native movement; do not teleport or disable knockback.
code=code.replace('Math.abs(w.gg.Y-walkFloor)>8','Math.abs(w.gg.Y-walkFloor)>40')
code=code.replace('if(w.gg.X<walkLow-50', 'liveRow.maxFloorDeviation=Math.max(Number(liveRow.maxFloorDeviation)||0,Math.abs(w.gg.Y-walkFloor));if(w.gg.X<walkLow-50')
exec(compile(code,str(HERE/'native_walk.py'),'exec'),globals())
