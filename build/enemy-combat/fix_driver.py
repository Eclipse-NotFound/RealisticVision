"""One-time D57 fixture correction after source review; old runs stay frozen."""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'SavedFireProbe.as';s=p.read_text()
block='''    for(var fighterIndex:int=0;fighterIndex<crowd.length;fighterIndex++){
      var fixedFighter:*=crowd[fighterIndex];fixedFighter.setPos(low+210+fighterIndex*55,floor-1);fixedFighter.dx=fixedFighter.dy=0;fixedFighter.setVisPos();
    }
'''
assert s.count(block)==1;s=s.replace(block,'')
at='''   triggerNow=row.variant.indexOf('idle')<0;'''
assert s.count(at)==1;s=s.replace(at,block+at)
# CONTROLLED is a dormant old path. Remove it to avoid obsolete declarations.
a=s.index('    if(CONTROLLED){');z=s.index('    var memStart:Number',a);s=s[:a]+s[z:]
block='''for each(var fighter:* in crowd){
     fighter.setCel(w.gg);var enemyGun:*=fighter.currentWeapon;enemyGun.hold=enemyGun.holder;
     if(age%6==0)enemyGun.attack();
     var enemyDelta:int=Math.max(0,int(enemyGun.kol_shoot)-int(shots[enemyGun]));row.enemyShots+=enemyDelta;shots[enemyGun]=int(enemyGun.kol_shoot);
    }
    '''
assert s.count(block)==1;s=s.replace(block,'')
at='    var memStart:Number=System.totalMemory;'
block='''    // Stimulus is before RV so newly created effects receive this frame's mask.
    // kol_shoot may reset between frames; positive deltas are a lower bound,
    // never advertised as an exact lifetime shot count.
    var driveStart:int=getTimer(),nativeEnemyShotLowerBound:int=0,forcedEnemyShots:int=0;
    for each(var fighter:* in crowd){
     fighter.setCel(w.gg);var enemyGun:*=fighter.currentWeapon;enemyGun.hold=enemyGun.holder;
     var beforeForced:int=int(enemyGun.kol_shoot);
     nativeEnemyShotLowerBound+=Math.max(0,beforeForced-int(shots[enemyGun]));
     if(age%6==0)enemyGun.attack();
     forcedEnemyShots+=Math.max(0,int(enemyGun.kol_shoot)-beforeForced);shots[enemyGun]=int(enemyGun.kol_shoot);
    }
    var driveMs:int=getTimer()-driveStart;
    row.enemyShots+=nativeEnemyShotLowerBound+forcedEnemyShots;
    if(age>=WARMUP_COUNT){row.sampleNativeEnemyShotsLowerBound+=nativeEnemyShotLowerBound;row.sampleForcedEnemyShots+=forcedEnemyShots;}
'''
assert s.count(at)==1;s=s.replace(at,block+at)
s=s.replace('enemyShots:0,maxPartialEnemies:', 'enemyShots:0,sampleNativeEnemyShotsLowerBound:0,sampleForcedEnemyShots:0,samplePlayerShotsLowerBound:0,maxPartialEnemies:')
s=s.replace('previousFrame={partialEnemies:', 'previousFrame={nativeEnemyShotLowerBound:nativeEnemyShotLowerBound,forcedEnemyShots:forcedEnemyShots,enemyDriveMs:driveMs,partialEnemies:')
s=s.replace('row.attacks+=delta;', 'row.attacks+=delta;if(age>=WARMUP_COUNT)row.samplePlayerShotsLowerBound+=delta;')
p.write_text(s,encoding='utf-8')
# Native-timing injection locates the object regardless of the extra fields.
p=H/'run.py';s=p.read_text().replace("s=s.replace('previousFrame={partialEnemies:', 'previousFrame={start:now,nativeTick:NativeTimingAccess.tick(w),partialEnemies:')", "s=s.replace('previousFrame={nativeEnemyShotLowerBound:', 'previousFrame={start:now,nativeTick:NativeTimingAccess.tick(w),nativeEnemyShotLowerBound:')")
s=s.replace("assert c['enemyShots']>10,(c['variant'],c['enemyShots'])", "assert c['enemyShots']>10,(c['variant'],c['enemyShots'])\n  assert c['sampleNativeEnemyShotsLowerBound']+c['sampleForcedEnemyShots']>50,c['variant']\n  assert c['samplePlayerShotsLowerBound']>20,c['variant']")
p.write_text(s,encoding='utf-8')
print('Fixture corrected: native menu, pre-world pose, pre-RV firing, sampled lower-bound shot evidence')
