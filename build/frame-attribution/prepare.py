"""Historical D47 initial scaffolding; current run.py includes later repairs.

Retained to explain native-timing-01's internal-field access failure. Do not
regenerate current tooling from this historical version.
"""
from pathlib import Path
import ast,json
MOD=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
assert not (HERE/'run.py').exists(),'Historical scaffold: do not overwrite repaired D47 tools'
OUT=MOD/'build/frame-attribution-output';OUT.mkdir(exist_ok=True)
source=(MOD/'build/mask-area/run.py').read_text(encoding='utf-8').replace('mask-area','frame-attribution').replace('d45','d47').replace('D45','D47')
(HERE/'run.py').write_text(source,encoding='utf-8',newline='\n')
s=(MOD/'build/mask-area/CombatRenderProbeMod.as').read_text(encoding='utf-8').replace('mask-area','frame-attribution').replace('D45','D47')
def change(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
change('  private var phase:int=', '''  private var nativeStep:Function,nativeStart:int=0,nativeEnd:int=0,nativeSerial:int=0,lastNativeSerial:int=0;
  private var phase:int=''')
start=s.index('   for each(var n:int in ');end=s.index('\n',start)
s=s[:start]+"   for each(var n:int in [0,6])for each(var mode:String in ['current','classic'])for each(var variant:String in ['off','normal','normal','off'])plan.push({n:n,mode:mode,variant:variant});"+s[end:]
change('sceneLoc=w.loc;timer.stop();start(w);', '''sceneLoc=w.loc;timer.stop();
     nativeStep=w.mm.mainStep as Function;
     if(nativeStep==null)throw new Error('native mainStep unavailable');
     // Native MainMenu registered first at priority 0, before mod loading.
     // Priority 1 behind existing priority-1 handlers keeps that ordering:
     // all old >0 handlers stay before it; old <=0 handlers stay after it.
     host.stage.removeEventListener(Event.ENTER_FRAME,nativeStep);
     host.stage.addEventListener(Event.ENTER_FRAME,nativeFrame,false,1);
     result.nativeTiming={method:'MainMenu.mainStep',priority:1,originalPriority:0,checkedSource:true};
     start(w);''')
change('  private function undo():void {','''  private function nativeFrame(e:Event):void {
   nativeStart=getTimer();nativeSerial++;
   try {nativeStep(e);} finally {nativeEnd=getTimer();}
  }
  private function undo():void {''')
change('var now:int=getTimer();if(previousFrame)previousFrame.nextInterval=now-last;', '''var now:int=getTimer();
    if(nativeSerial!=lastNativeSerial+1||nativeStart>nativeEnd||nativeEnd>now)throw new Error('unverified native/probe event order');
    lastNativeSerial=nativeSerial;
    if(previousFrame){
     previousFrame.nextInterval=now-last;
     previousFrame.nativeNext=nativeEnd-nativeStart;
     previousFrame.otherHandlersNext=now-nativeEnd;
     previousFrame.afterProbe=nativeStart-previousFrame.probeEnd;
     previousFrame.probeMs=previousFrame.probeEnd-previousFrame.start;
     previousFrame.worldStepsNext=w.t_save-previousFrame.nativeTick;
     if(previousFrame.afterProbe<0||previousFrame.probeMs<0||previousFrame.nativeNext+previousFrame.otherHandlersNext+previousFrame.afterProbe+previousFrame.probeMs!=previousFrame.nextInterval)
      throw new Error('native interval does not partition');
     if(previousFrame.worldStepsNext!=1)throw new Error('native world step count changed: '+previousFrame.worldStepsNext);
    }''')
change('previousFrame={age:age,rv:ms,', 'previousFrame={start:now,nativeTick:w.t_save,nativeSerial:nativeSerial,nativeStart:nativeStart,nativeEnd:nativeEnd,age:age,rv:ms,')
change('    if(++age<WARMUP_COUNT+SAMPLE_COUNT)return;', '    if(++age<WARMUP_COUNT+SAMPLE_COUNT){previousFrame.probeEnd=getTimer();return;}')
change("undo();host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D47 COMPLETE');", "undo();host.stage.removeEventListener(Event.ENTER_FRAME,step);host.stage.removeEventListener(Event.ENTER_FRAME,nativeFrame);trace('D47 COMPLETE');")
(HERE/'CombatRenderProbeMod.as').write_text(s,encoding='utf-8',newline='\n')
group=(MOD/'build/mask-area/group.py').read_text(encoding='utf-8').replace('mask-area','frame-attribution').replace('D45','D47')
(HERE/'group.py').write_text(group,encoding='utf-8',newline='\n')
steps=[['assets.py'],['source.py'],['run.py','build','native-timing-01','--full','--controlled','--frames','180','--warmup','120'],['run.py','run','native-timing-01']]
(HERE/'steps.json').write_text(json.dumps(steps,indent=2)+'\n',encoding='utf-8',newline='\n')
for p in HERE.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
print('D47 prepared; isolated native timing, no production edit')
