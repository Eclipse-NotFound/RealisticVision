"""D57: new evidence only; D56 is the installed baseline."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;M=H.parents[1];O=M/'build/enemy-combat-output'
assert not O.exists()
B=M/'build/effect-mask-origin-output/production/src'
shutil.copytree(B,O/'baseline/src')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'baseline/manifest.json').write_text(json.dumps({'installed':sha(M/'release/RealisticVisionMod.swf'),'files':{p.relative_to(B).as_posix():sha(p) for p in B.rglob('*.as')}},indent=2))
s=(M/'build/effect-mask-origin/native_run.py').read_text()
s=s.replace('effect-mask-origin-output','enemy-combat-output').replace('RealisticVision / D56','RealisticVision / D57')
s=s.replace("BASE=MOD/'build/combat-render-output/production-final2/src'","BASE=OUT/'baseline/src'")
s=s.replace("if '--both' in sys.argv:","if '--diagnostic' in sys.argv:\n  s=s.replace(\"['off-idle','normal-idle','off','normal','noeffects','noeffects','normal','off','normal-idle','off-idle']\",\"['off','normal','enemy-nodraw','effect-nodraw','effect-nodraw','enemy-nodraw','normal','off']\")\n if '--both' in sys.argv:")
s=s.replace("s=(HERE/'SavedFireProbe.as').read_text()","s=(HERE/'SavedFireProbe.as').read_text()\n if '--short' in sys.argv:s=s.replace('SAMPLE_COUNT=180','SAMPLE_COUNT=120').replace('WARMUP_COUNT=90','WARMUP_COUNT=45')")
s=s.replace("'hideEnemies','refreshMask'","'hideEnemies','applyMask','applyWeaponVisual','enemyState','refreshMask'")
s=s.replace("print(c['variant'],'shots',c['attacks']","assert c['enemyShots']>10,(c['variant'],c['enemyShots'])\n  print(c['variant'],'enemyShots',c['enemyShots'],'shots',c['attacks']")
(H/'run.py').write_text(s,encoding='utf-8')
s=(M/'build/effect-mask-origin/SavedFireProbe.as').read_text().replace('effect-mask-origin-output','enemy-combat-output').replace('D56','D57')
s=s.replace('plan.push({n:0,','plan.push({n:6,')
s=s.replace('SWEEP?low-700:low+1000','SWEEP?low+550:low+1000').replace('floor-250+220*Math.sin(age/25)','floor-65+80*Math.sin(age/25)')
s=s.replace('u.step();crowd.push(u);','u.step();crowd.push(u);shots[u.currentWeapon]=int(u.currentWeapon.kol_shoot);')
s=s.replace('maxParticles:0,attacks:0','maxParticles:0,attacks:0,enemyShots:0,maxPartialEnemies:0,enemyMaskRemovals:0,effectMaskRemovals:0')
s=s.replace("if(kind=='nodraw'){","if(kind=='enemy-nodraw'||kind=='effect-nodraw'){")
s=s.replace('if(false)for each(var unit:* in w.loc.units)',"if(kind=='enemy-nodraw')for each(var unit:* in w.loc.units)")
s=s.replace("if(kind=='nodraw')masks+=alter(obj.vis,seen,owned);","if(kind=='effect-nodraw')masks+=alter(obj.vis,seen,owned);")
s=s.replace("if(false){if(getQualifiedClassName(visual).indexOf('visualGrifArm')==0)","if(kind=='enemy-nodraw'){if(getQualifiedClassName(visual).indexOf('visualGrifArm')==0)")
s=s.replace('var memStart:Number=System.totalMemory;','''for(var fighterIndex:int=0;fighterIndex<crowd.length;fighterIndex++){
      var fixedFighter:*=crowd[fighterIndex];fixedFighter.setPos(low+210+fighterIndex*55,floor-1);fixedFighter.dx=fixedFighter.dy=0;fixedFighter.setVisPos();
    }
    var memStart:Number=System.totalMemory;''')
# Remove duplicate function-scoped declarations from the dormant CONTROLLED block.
s=s.replace('for(var fighterIndex:int=0;fighterIndex<crowd.length;fighterIndex++){','for(fighterIndex=0;fighterIndex<crowd.length;fighterIndex++){',1)
s=s.replace('var fixedFighter:*=crowd[fighterIndex];','fixedFighter=crowd[fighterIndex];',1)
s=s.replace('previousFrame={age:age,','''var partial:int=0;for each(var unitState:Object in rv.unitVis)if(unitState.state==2)partial++;
    row.maxPartialEnemies=Math.max(row.maxPartialEnemies,partial);
    if(kind=='enemy-nodraw')row.enemyMaskRemovals+=masks;
    if(kind=='effect-nodraw')row.effectMaskRemovals+=masks;
    previousFrame={partialEnemies:partial,age:age,''')
s=s.replace('if(age==90 &&', '''for each(var fighter:* in crowd){
     fighter.setCel(w.gg);var enemyGun:*=fighter.currentWeapon;enemyGun.hold=enemyGun.holder;
     if(age%6==0)enemyGun.attack();
     var enemyDelta:int=Math.max(0,int(enemyGun.kol_shoot)-int(shots[enemyGun]));row.enemyShots+=enemyDelta;shots[enemyGun]=int(enemyGun.kol_shoot);
    }
    if(age==90 &&''')
s=s.replace("if(VISUAL){var bitmap:","if(VISUAL||index==0){var bitmap:")
s=s.replace("undo();host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D57 COMPLETE');","undo();host.stage.removeEventListener(Event.ENTER_FRAME,inputFrame);host.stage.removeEventListener(Event.ENTER_FRAME,step);trace('D57 COMPLETE');")
(H/'SavedFireProbe.as').write_text(s,encoding='utf-8')
print('D57 frozen baseline and six-enemy native diagnostic prepared')
