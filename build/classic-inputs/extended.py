"""Threshold sizes, settings and room/mode transitions; functional evidence only."""
from pathlib import Path
import json, re, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import perf as d
r = d.r
OUT = d.OUT


def main():
    folder = OUT / 'all-transitions-02'
    assert not folder.exists()
    with r.Registration(owner='RealisticVision / D50 边界与切换画面',
                        purpose='房间尺寸临界、设置与换房；仅功能，不计时',
                        run_dir=folder, evidence=folder / 'checks.json', wait=900) as rec:
        src = folder / 'src'
        r.public(OUT / 'candidates/all/src', src)
        (src / 'BaselineVision.as').write_text(
            re.sub(r'\bprivate\b', 'public', (d.BASE / 'RealisticVisionMod.as').read_text(encoding='utf-8'))
            .replace('RealisticVisionMod', 'BaselineVision'), encoding='utf-8')
        fixture = (d.MOD / 'build/motion-tests/MotionLocation.as').read_text(encoding='utf-8')
        fixture = fixture.replace('MotionLocation()', 'MotionLocation(w:int=24,h:int=18)')
        fixture = fixture.replace('spaceX=24;spaceY=18;', 'spaceX=w;spaceY=h;')
        fixture = fixture.replace('      for(var y:int=0;', '      space=[];for(var col:int=0;col<spaceX;col++)space[col]=[];\n      for(var y:int=0;')
        fixture = fixture.replace('tiles[x+y*spaceX]=t;', 'tiles[x+y*spaceX]=t;space[x][y]=t;')
        (src / 'MotionLocation.as').write_text(fixture, encoding='utf-8')
        # Original local fixture only covered small rooms. Supply real public
        # host fields required by the unchanged D44 large-room branches.
        for relative, old, new in [
            ('fe/World.as', 'public var black:Boolean;', 'public var cam:*;public var black:Boolean;'),
            ('fe/loc/Location.as', 'public var id:String;', 'public var space:Array;public var id:String;'),
        ]:
            stub = (d.MOD / 'build/stubs' / relative).read_text(encoding='utf-8')
            assert stub.count(old) == 1
            target = src / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(stub.replace(old, new), encoding='utf-8')
        test = (OUT / 'all-local-01/src/LazyClassicChecks.as').read_text(encoding='utf-8')
        test = test.replace('private var ready:int=0,', 'private var roomW:int,roomH:int; private var ready:int=0,')
        test = test.replace('new MotionLocation()', 'new MotionLocation(roomW,roomH)')
        test = test.replace('w.allStat=1;', 'w.allStat=1;w.cam={vx:0,vy:0,scaleV:1,screenX:640,screenY:400};')
        test = test.replace('   for each(var dim:Number', '''   for each(var size:Array in [[24,18],[48,25],[49,25],[48,26]]){
   roomW=size[0];roomH=size[1];var readyBefore:int=ready;
   for each(var dim:Number''')
        test = test.replace('frame<24', 'frame<32')
        test = test.replace('if(frame==14){a.m.cfgDim=b.m.cfgDim=.35;}',
                            'if(frame==14){a.m.setVisualSetting("dim",.35);b.m.setVisualSetting("dim",.35);}')
        test = test.replace('if(frame==17){a.m.cfgDim=b.m.cfgDim=.6;}', '''if(frame==17){
      for each(var change:Array in [["dim",.6],["soft_classic",20],["viewscale",1.5]]){
       a.m.setVisualSetting(change[0],change[1]);b.m.setVisualSetting(change[0],change[1]);
      }
     }''')
        test = test.replace('     step(a);step(b);', '''     if(frame==23 || frame==26){
      a.m.cfgMode=b.m.cfgMode=frame==23?"current":"classic";
      a.m.curLoc=b.m.curLoc=null; // Same invalidation as the mode menu.
     }
     if(frame==29){
      for each(var o:Object in [a,b]){
       o.loc=new MotionLocation(roomW,roomH);o.loc.gg=new UnitPlayer();
       o.loc.gg.X=200;o.loc.gg.Y=500;o.loc.gg.scY=40;o.loc.lDist1=150;o.loc.lDist2=600;
       o.w.loc=o.loc;o.w.gg=o.loc.gg;
      }
     }
     step(a);step(b);''')
        test = test.replace('var label:String=dim+', 'var label:String=roomW+"x"+roomH+"/"+dim+')
        test = test.replace('     if(b.m.classicLogicInterpolated)ready++;', '''     for each(var request:Array in [[0,0,1,1],[roomW-1,roomH-1,1,1],[10,8,2,2],[roomW-2,0,2,2]]){
      a.m.classicLogicRegion(new Rectangle(request[0],request[1],request[2],request[3]));
      b.m.classicLogicRegion(new Rectangle(request[0],request[1],request[2],request[3]));
      check(same(a.m.fogCache,b.m.fogCache),"edge query entire published field "+label+" @"+request);
      check(same(a.m.fogBmp,b.m.fogBmp),"edge query retains display "+label+" @"+request);
      check(String(a.m.classicLogicTiles)==String(b.m.classicLogicTiles),"edge query flags "+label+" @"+request);
     }
     if(b.m.classicLogicInterpolated)ready++;''')
        test = test.replace('   check(ready>0,', '''   check((roomW<=48 && roomH<=25)?ready>readyBefore:ready==readyBefore,"correct small/large route "+roomW+"x"+roomH);
   trace("SIZE "+roomW+"x"+roomH+" privateReady="+(ready-readyBefore));
   }
   check(ready>0,''')
        (src / 'LazyClassicChecks.as').write_text(test, encoding='utf-8')
        r.runner.compile(src / 'LazyClassicChecks.as', folder / 'LazyClassicChecks.swf',
                         [src, d.MOD / 'build/motion-tests', d.MOD / 'build/stubs'])
        r.save(folder / 'build.json', {'performance_evidence': False, 'files': {
            str(p.relative_to(folder)): r.sha(p) for p in folder.rglob('*') if p.is_file()}})
        r.save(folder / 'environment.json', r.environment())
        code, log = r.air(folder, 'LazyClassicChecks.swf', rec, 300)
        (folder / 'checks.log').write_text(log, encoding='utf-8')
        summary = [x for x in log.splitlines() if x.startswith(('SIZE ', 'READY ', 'LAZY COMPLETE', 'FAIL '))]
        passed = code == 0 and 'failed=0' in log and 'FAIL ' not in log and len([x for x in summary if x.startswith('SIZE ')]) == 4
        r.save(folder / 'checks.json', {'pass': passed, 'exit': code, 'summary': summary, 'performance_evidence': False})
        print('\n'.join(summary), flush=True)
        assert passed
        rec.outcome = 'passed'
        rec.note = '尺寸临界/设置/模式/换房逐查询严格一致；不作性能证据'


if __name__ == '__main__':
    main()
