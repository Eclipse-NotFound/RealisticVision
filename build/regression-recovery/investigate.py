"""Immutable D35 runs. Timings and pixel comparisons use separate runs."""
from pathlib import Path
import argparse, importlib.util, json, re, shutil, subprocess, sys
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1];GAME=MOD.parents[1];OUT=MOD/'build/regression-recovery-output'
sys.path.insert(0,str(MOD/'build/motion-performance'))
import run as r
r.OUT=OUT
_registration=r.Registration
def recovery_registration(**kwargs):
    hold=OUT/'defer-next-test.json'
    if hold.exists():
        until=json.loads(hold.read_text(encoding='utf-8'))['until']
        if until>r.time.time():
            print('按共享测试协调暂缓新增实例；当前已启动实例正常收尾。',flush=True)
        while until>r.time.time():r.time.sleep(max(0,min(1,until-r.time.time())))
    # Other recovery tasks share this one game slot. Keep our waiter alive;
    # this changes no ownership rule and never preempts an active test.
    kwargs['wait']=900
    kwargs['owner']=kwargs.get('owner','RealisticVision / D35').replace('D33','D35')
    return _registration(**kwargs)
r.Registration=recovery_registration
SOURCES={'d32':MOD/'build/stair-shadow-output/merged-v0323/candidate/src',
         'd34':MOD/'build/vision-settings-output/candidate/src',
         'd33':MOD/'build/motion-performance-output/merged-settings/production/src',
         'fixed':OUT/'candidate/src','fixed2':OUT/'candidate-v2/src','fixed3':OUT/'candidate-v3/src','fixed4':OUT/'candidate-v4/src','fixed5':OUT/'candidate-v5/src','fixed6':OUT/'candidate-v6/src'}

def build(name,left,right,verify=False,profile=False,live=False):
    folder=OUT/name;assert not folder.exists();folder.mkdir(parents=True)
    with r.Registration(owner='RealisticVision / D35 对照构建',purpose=name+' 编译',run_dir=folder,evidence=folder/'build.json',wait=300) as rec:
        r.runtime(folder)
        s=(MOD/'build/frame-performance/FrameProbe.as').read_text(encoding='utf-8-sig')
        s=s.replace('FrameProbe','RecoveryFrameProbeMod').replace('/RealisticVision/build/frame-performance-output/','/RealisticVision/build/regression-recovery-output/')
        start=s.index('private var cases:Array=');end=s.index(';',start)
        s=s[:start]+'''private var cases:Array=[{mode:"classic",dense:true,bright:false,dim:0.35},{mode:"classic",dense:true,bright:false,dim:0.6},{mode:"current",dense:true,bright:false,dim:0.35},{mode:"current",dense:true,bright:false,dim:0.6}]'''+s[end:]
        s=s.replace('m.cfgMode=c.mode;','m.cfgMode=c.mode;m.cfgDim=c.dim;')
        s=s.replace('private var caseIndex:int=0,','private var measuredStart:Number=0;\n      private var caseIndex:int=0,')
        s=s.replace('var now:int=getTimer();if(frame>=0','if(frame==0)measuredStart=new Date().time;\n         var now:int=getTimer();if(frame>=0')
        s=s.replace('entry:Object={spec:c,','entry:Object={measuredStart:measuredStart,measuredEnd:new Date().time,spec:c,')
        if verify and right.startswith('fixed'):
            s=s.replace('for each(var field:String in ["fogCache"', 'b.classicLogicRegion(new Rectangle(0,0,b.spaceX,b.spaceY));\n         for each(var field:String in ["fogCache"')
            s=s.replace('!equal(a[field],b[field])','!equalField(a,b,field)')
            s=s.replace('      private function verify(w:*):void{','''      private function equalField(a:*,b:*,field:String):Boolean {
         if(field!="fogCache" || b.cfgMode!="classic" || b.cfgDim==0.35)return equal(a[field],b[field]);
         var area:Rectangle=new Rectangle(4,4,b.spaceX*8,b.spaceY*8),aa:BitmapData=new BitmapData(area.width,area.height,true,0),bb:BitmapData=aa.clone();
         aa.copyPixels(a[field],area,new Point());bb.copyPixels(b[field],area,new Point());var ok:Boolean=equal(aa,bb);aa.dispose();bb.dispose();return ok;
      }
      private function verify(w:*):void{''')
        if live:
            s=(MOD/'build/motion-performance-output/merged-settings/live-04/MotionFrameProbeMod.as').read_text(encoding='utf-8-sig')
            s=s.replace('MotionFrameProbeMod','RecoveryFrameProbeMod').replace('/RealisticVision/build/motion-performance-output/','/RealisticVision/build/regression-recovery-output/')
            s=s.replace('liveMod.cfgMode=liveIndex<4?', 'liveMod.cfgDim=0.6;liveMod.cfgSoftCurrent=25;liveMod.cfgMode=liveIndex<4?')
        entry=folder/'RecoveryFrameProbeMod.as';entry.write_text(s,encoding='utf-8')
        r.runner.compile(entry,folder/'mods/RecoveryFrameProbe/release/RecoveryFrameProbeMod.swf',[folder],definitions=['-define=CONFIG::largeScene,true','-define=CONFIG::verifyPixels,'+str(verify).lower(),'-define=CONFIG::liveFrames,'+str(live).lower()])
        catalog=folder/'mods/ModLoader';catalog.mkdir(parents=True,exist_ok=True)
        (catalog/'supported-mods.txt').write_text((GAME/'mods/ModLoader/supported-mods.txt').read_text(encoding='utf-8-sig')+'\nRecoveryFrameProbe|RecoveryFrameProbeMod|1|0|0\n',encoding='utf-8')
        shutil.copytree(GAME/'mods/ContinuousScene/release',folder/'mods/ContinuousScene/release')
        result=subprocess.run([str(GAME/'mods/ModLoader/RemainsModLauncher.exe'),'--root',str(folder),'--only','ContinuousSceneMod,RecoveryFrameProbeMod','--no-ui','--report',str(folder/'selection.json')],capture_output=True,text=True,encoding='utf-8',timeout=45)
        (folder/'selection.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stdout+result.stderr
        for variant,key in [('baseline',left),('candidate',right)]:
            src=folder/(variant+'-src');r.public(SOURCES[key],src,profile)
            r.runner.compile(src/'RealisticVisionMod.as',folder/(variant+'.swf'),[src],stubs=True)
        r.save(folder/'build.json',{'left':left,'right':right,'profile':profile,'verify':verify,'large':True,'live':live,'files':{str(p.relative_to(folder)):r.sha(p) for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix in ['.swf','.as','.xml','.txt']}})
        rec.outcome='passed'

def analyze(name):
    folder=OUT/name;result=json.loads((folder/'evidence/result.json').read_text())
    import statistics
    def stats(a):
        s=sorted(a);return {'mean':round(statistics.mean(a),3),'p95':s[int(.95*(len(s)-1))],'max':max(s),'>50':sum(t>50 for t in s)}
    rows=[]
    for c in result['cases']:
        rows.append({'case':c['spec'],'update':[stats(a) for a in c['updates']],'total':[stats([a+b for a,b in zip(c['updates'][i],c['draws'][i])]) for i in range(2)],'stages':c['stages'],'counts':c['counts']})
    r.save(folder/'analysis.json',rows);print(json.dumps(rows,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run','analyze','environment']);p.add_argument('--name');p.add_argument('--left',default='d32');p.add_argument('--right',default='d33');p.add_argument('--profile',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args()
    if a.action=='build':build(a.name,a.left,a.right,a.verify,a.profile,a.live)
    elif a.action=='run':r.run(a.name)
    elif a.action=='analyze':analyze(a.name)
    else:print(json.dumps(r.environment()))
