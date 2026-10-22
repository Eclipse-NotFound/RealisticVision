"""Use native directional controls on a validated platform, no per-frame teleport."""
from pathlib import Path
import argparse
import sys,time,psutil
import trace as t
OUT=t.OUT
base=t.original_source
def probe(short=False):
 s=base(False).replace('long-frame-output','overall-flow-output')
 s=s.replace('private var scenario:String="";','private var scenario:String="";\n      private var walkLow:Number=0,walkHigh:Number=0,walkFloor:Number=0,walkDirection:int=1,lastWalkX:Number=NaN;')
 s=s.replace('scenario="sweep"','scenario="battle"')
 s=s.replace('eventSequence:events,frames:[],','eventSequence:events,frames:[],nativeKeys:true,grounded:0,walkDistance:0,reversals:0,')
 s=s.replace('if(anchorX==0){', '''if(anchorX==0){
               var bestStart:int=-1,bestEnd:int=-1,bestY:int=0;
               // One-time fixture placement. Find a straight native solid floor
               // with three clear tiles above it and room to brake at both ends.
               for(var fy:int=6;fy<w.loc.spaceY-2 && bestStart<0;fy++){
                  var begin:int=-1;
                  for(var fx:int=2;fx<w.loc.spaceX-2;fx++){
                     var floorTile:*=w.loc.getTile(fx,fy);
                     var clear:Boolean=floorTile.opac>=1 && int(floorTile.zForm)==0;
                     for(var ay:int=1;ay<=3 && clear;ay++)if(w.loc.getTile(fx,fy-ay).opac>=1)clear=false;
                     if(clear){if(begin<0)begin=fx;}
                     else begin=-1;
                     if(begin>=0 && fx-begin>=15){bestStart=begin;bestEnd=fx;bestY=fy;break;}
                  }
               }
               if(bestStart<0)throw new Error("native walk platform unavailable");
               walkLow=(bestStart+2)*40;walkHigh=(bestEnd-1)*40;walkFloor=bestY*40;
               w.gg.setPos(walkLow+80,walkFloor-1);w.gg.setVisPos();w.ctr.clearAll();w.gg.ggControl=true;
               trace("NATIVE WALK floor="+walkFloor+" range="+walkLow+","+walkHigh);
''')
 # On subsequent cases controls keep running. No reposition or camera writes.
 old='''w.ctr.clearAll();w.gg.ggControl=false;
            var px:Number=scenario=="still"?anchorX-120:scenario=="sweep"?240+Math.abs((liveAge%200)-100)*18:anchorX+Math.abs((liveAge%40)-20)*12-120;
            w.gg.setPos(Math.max(80,Math.min(w.loc.limX-80,px)),anchorY);w.gg.setVisPos();w.cam.calc(w.gg);'''
 new='''w.ctr.clearAll();w.gg.ggControl=true;
            if(w.gg.X>=walkHigh && walkDirection>0){walkDirection=-1;liveRow.reversals++;}
            else if(w.gg.X<=walkLow && walkDirection<0){walkDirection=1;liveRow.reversals++;}
            w.ctr.keyLeft=walkDirection<0;w.ctr.keyRight=walkDirection>0;w.ctr.keyRun=true;
            if(liveAge>=30){
               if(w.gg.X<walkLow-50 || w.gg.X>walkHigh+50 || Math.abs(w.gg.Y-walkFloor)>8)throw new Error("native walk left validated floor "+w.gg.X+","+w.gg.Y);
               if(w.gg.stay)liveRow.grounded++;
               if(lastWalkX==lastWalkX)liveRow.walkDistance+=Math.abs(w.gg.X-lastWalkX);
            }
            lastWalkX=w.gg.X;'''
 assert old in s;s=s.replace(old,new)
 s=s.replace('lastTrace={viewChanged:', 'lastTrace={grounded:w.gg.stay,dx:w.gg.dx,dy:w.gg.dy,epoch:new Date().time,viewChanged:')
 s=s.replace('if(++liveAge<330)return;', '''if(++liveAge<270)return;
            if(liveRow.grounded<220 || liveRow.walkDistance<300 || liveRow.reversals<1)throw new Error("native walk fixture inactive "+JSON.stringify({grounded:liveRow.grounded,distance:liveRow.walkDistance,reversals:liveRow.reversals}));''')
 return s
def lean_probe(short=False):
 s=probe(short)
 return s.replace('["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]','["off","candidate","baseline","baseline","candidate","off","off","candidate","baseline","baseline","candidate","off"]')

def lean_environment():
 # Registry remains the exclusivity guard. Enumerate processes only before
 # launch and after exit; avoid repeated global process discovery during play.
 begin=time.time();env={'time':begin,'available_bytes':psutil.virtual_memory().available,'processes':[]}
 running=OUT/sys.argv[2]/'running.json'
 if running.exists():
  try:
   import json
   identity=json.loads(running.read_text());process=psutil.Process(identity['pid'])
   if process.is_running():env['processes']=[{'pid':process.pid,'name':process.name()}];env['scope']='owned process only during play'
  except (psutil.Error,OSError,ValueError):pass
 if not env['processes']:
  env['processes']=[p.info for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower() in ['adl.exe','adl64.exe','java.exe','javaw.exe']];env['scope']='global pre/post launch'
 env['sampleDurationMs']=(time.time()-begin)*1000
 return env

t.source_probe=lean_probe if '--lean' in sys.argv else probe
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run']);a.add_argument('name');a.add_argument('--lean',action='store_true');x=a.parse_args()
 if x.lean:t.r.environment=lean_environment
 t.build(x.name,True,'candidate-05',False,True) if x.action=='build' else t.run(x.name)
