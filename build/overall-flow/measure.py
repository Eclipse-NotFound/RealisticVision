"""D40 pairs frozen D39 against a candidate using D39's corrected capture."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/followup-performance/measure.py').read_text(encoding='utf-8')
s=s.replace("source=source.replace('native-performance-output','followup-performance-output')", "source=source.replace('native-performance-output','overall-flow-output')")
s=s.replace("MOD/'build/native-performance-output/production/src'", "MOD/'build/overall-flow-output/candidate-00/src'")
s=s.replace("exec(compile(source,", "source=source.replace(\"if build_info.get('verify') or name.startswith(('timing-final','native-final')):\", \"if True:\")\nexec(compile(source,")
s=s[:s.rindex("\nif __name__=='__main__':")]
exec(compile(s,str(HERE/'measure.py'),'exec'),globals())
original_build=build
def build(name,candidate,verify=False,profile=False,live=False,native=False,wide=False):
 original_compile=inv.r.runner.compile
 def compile_entry(entry,*args,**kwargs):
  if verify and name.startswith('safe-') and entry.name=='RecoveryFrameProbeMod.as':
   text=entry.read_text(encoding='utf-8')
   first='var a:*=mods[0],b:*=mods[1],ok:Boolean=true;'
   block='''var ca:BitmapData=canvas.clone(),cb:BitmapData=canvas.clone();
         a.fogVis.visible=true;b.fogVis.visible=true;ca.fillRect(ca.rect,0xffffff);cb.fillRect(cb.rect,0xffffff);parentCapture(ca,a,w);parentCapture(cb,b,w);'''
   assert text.count(first)==1
   text=text.replace('var ca:BitmapData=canvas.clone(),cb:BitmapData=canvas.clone();','')
   text=text.replace('a.fogVis.visible=true;b.fogVis.visible=true;ca.fillRect(ca.rect,0xffffff);cb.fillRect(cb.rect,0xffffff);parentCapture(ca,a,w);parentCapture(cb,b,w);','')
   # Canonical full-room diagnostic sampling has display side effects. Capture
   # the actual completed frame BEFORE those diagnostic calls, for both sides.
   text=text.replace(first,first+'\n         '+block)
   if 'shared' in name:
    before='var start:int=getTimer();m.frameCount++;m.onFrameInner();'
    inject='''if(m.sharedLight==null){m.sharedLight=new Array(m.spaceX*m.spaceY);m.sharedExplored=new Array(m.spaceX*m.spaceY);for(var si:int=0;si<m.sharedLight.length;si++){m.sharedLight[si]=0;m.sharedExplored[si]=0;}}
            for(var change:int=0;change<24;change++){var cellIndex:int=(change*113+(frame+30)*7)%(m.spaceX*m.spaceY);m.sharedExplored[cellIndex]=1;m.sharedLight[cellIndex]=(change%4)*.25;}
            '''
    assert text.count(before)==1;text=text.replace(before,inject+before)
   entry.write_text(text,encoding='utf-8',newline='\n')
  return original_compile(entry,*args,**kwargs)
 inv.r.runner.compile=compile_entry
 try:return original_build(name,candidate,verify,profile,live,native,wide)
 finally:inv.r.runner.compile=original_compile
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['build','run','analyze']);a.add_argument('name');a.add_argument('--candidate',default='candidate-00');a.add_argument('--verify',action='store_true');a.add_argument('--wide',action='store_true');a.add_argument('--profile',action='store_true');a.add_argument('--live',action='store_true');a.add_argument('--native',action='store_true');x=a.parse_args()
 if x.action=='build':build(x.name,x.candidate,x.verify,x.profile,x.live,x.native,x.wide)
 elif x.action=='run':run(x.name)
 else:inv.analyze(x.name)
