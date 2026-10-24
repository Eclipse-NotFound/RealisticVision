from pathlib import Path
import types,sys
from environment_guard import classify
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
code=(MOD/'build/effect-visibility/native_walk.py').read_text(encoding='utf-8').replace('effect-visibility-output','effect-load-v3-output').replace(".replace('D39','D42')",".replace('D39','D43')")
code=code[:code.index("exec(compile(code,str(HERE/'native_walk.py')")]
exec(compile(code,str(HERE/'native.py'),'exec'),globals())
# Reuse the validated walk fixture, six real native mercenaries with smg10.
code=code[:code.index("if __name__=='__main__':")]
exec(compile(code,str(HERE/'native.py'),'exec'),globals())
original=t.source_probe
SAMPLE_FRAMES=240
def dense(short=False):
 s=original(short).replace('private var walkLow:Number=0,','private var crowd:Array=[];\n      private var walkLow:Number=0,')
 old='w.loc.addObj(armedEnemy);w.loc.units.push(armedEnemy);armedEnemy.step();'
 assert old in s
 s=s.replace(old,old+'''crowd.push(armedEnemy);
               for(var ci:int=0;ci<5;ci++){var enemy:*=new raiderClass("1",10,null,{weap:"smg10"});enemy.putLoc(w.loc,walkLow+70+ci*65,walkFloor-1);enemy.invulner=true;w.loc.addObj(enemy);w.loc.units.push(enemy);enemy.step();crowd.push(enemy);}''')
 old='armedEnemy.setCel(w.gg);if(scenario=="battle" && liveAge%6==0)armedEnemy.currentWeapon.attack();'
 assert old in s;s=s.replace(old,'for each(var fighter:* in crowd){fighter.setCel(w.gg);if(liveAge%6==0)fighter.currentWeapon.attack();}')
 # Six combatants can physically push the player beyond the single-enemy
 # walking route. Observe native knockback without forced walking/teleporting.
 s=s.replace('w.ctr.keyLeft=walkDirection<0;w.ctr.keyRight=walkDirection>0;w.ctr.keyRun=true;','w.ctr.keyLeft=false;w.ctr.keyRight=false;w.ctr.keyRun=false;')
 start=s.index('if(w.gg.X<walkLow-50');end=s.index('\n',start);s=s[:start]+s[end:]
 start=s.index('            if(liveRow.grounded<200');end=s.index('\n',start);s=s[:start]+s[end:]
 s=s.replace('nativeKeys:true','nativeKeys:false,denseMercenaries:6')
 if '--reverse' in sys.argv:s=s.replace('["off","candidate","baseline","baseline","candidate","off","off","candidate","baseline","baseline","candidate","off"]','["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]')
 if SAMPLE_FRAMES!=240:
  assert 'if(++liveAge<270)return;' in s
  s=s.replace('if(++liveAge<270)return;','if(++liveAge<'+str(30+SAMPLE_FRAMES)+')return;')
 s=s.replace('nativeKeys:false,denseMercenaries:6','nativeKeys:false,denseMercenaries:6,sampleFrames:'+str(SAMPLE_FRAMES))
 if '--calibrate' in sys.argv:
  marker='      private function makeUnits(w:*):void{';assert marker in s
  s=s.replace(marker,'''      private function calibrate():Object {
         var begin:int=getTimer(),sum:Number=0;
         for(var i:int=0;i<1000000;i++)sum+=(i&7)*0.125;
         return {ms:getTimer()-begin,checksum:sum};
      }
'''+marker)
  marker='var previousView:Rectangle=liveMod.wallViewBounds;';assert marker in s
  s=s.replace(marker,'if(liveAge==29)liveRow.calibrationStart=calibrate();'+marker)
  marker='if(++liveAge<'+str(30+SAMPLE_FRAMES)+')return;';assert marker in s
  s=s.replace(marker,marker+'liveRow.calibrationEnd=calibrate();')
 return s
t.source_probe=dense
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('action');a.add_argument('name');a.add_argument('--lean',action='store_true');a.add_argument('--reverse',action='store_true');a.add_argument('--calibrate',action='store_true');a.add_argument('--high-qos',action='store_true');a.add_argument('--samples',type=int,choices=[120,240],default=240);x=a.parse_args();SAMPLE_FRAMES=x.samples
 if x.action=='run':
  from policy_capture import wrap
  t.r.HiddenProcess=wrap(t.r.HiddenProcess,x.high_qos)
 if x.lean:
  sampled=[False]
  def quiet_environment():
   env=classify(lean_environment())
   if not sampled[0]:
    sampled[0]=True;begin=time.monotonic()
    env['host_cpu_percent_before_air']=psutil.cpu_percent(interval=3)
    env['host_cpu_sample_seconds']=time.monotonic()-begin
   return env
  t.r.environment=quiet_environment
 t.build(x.name,True,'candidate',False,True) if x.action=='build' else t.run(x.name)
