"""D37 reuses isolated, registered same-input replay without changing old runs."""
from pathlib import Path
import importlib.util,argparse
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1];OUT=MOD/'build/native-performance-output'
spec=importlib.util.spec_from_file_location('d35',MOD/'build/regression-recovery/investigate.py')
inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
inv.OUT=OUT;inv.r.OUT=OUT
inv.SOURCES['d36']=MOD/'build/combat-visibility-output/production/src'
def build(name,candidate,verify=False,profile=False,live=False,native=False,wide=False):
    inv.SOURCES['d37']=OUT/candidate/'src'
    src=(MOD/'build/regression-recovery/investigate.py').read_text(encoding='utf-8')
    start=src.index('def build(');end=src.index('\ndef analyze(',start)
    f=src[start:end].replace('/RealisticVision/build/regression-recovery-output/','/RealisticVision/build/native-performance-output/')
    if verify:
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        s=s.replace('ok=equal(ca,cb);ca.dispose();cb.dispose();', 'ok=equal(ca,cb);if(!ok){dumpImage(ca,"baseline");dumpImage(cb,"candidate");var dd:BitmapData=ca.compare(cb) as BitmapData;trace("DIFFERENCE "+dd.getColorBoundsRect(0xFFFFFFFF,0,false)+" camera="+w.cam.vx+","+w.cam.vy+" view="+b.scenePaintBounds()+" frame="+b.frameCount);dumpImage(dd,"difference");dd.dispose();}ca.dispose();cb.dispose();')
        s=s.replace('      private function verify(w:*):void{','      private function dumpImage(image:BitmapData,name:String):void {var path:String=File.applicationDirectory.nativePath.replace(/\\\\\\\\/g,"/");if(path.indexOf("/RealisticVision/build/native-performance-output/")<0)throw new Error("wrong image output");var f:FileStream=new FileStream();f.open(new File(path+"/evidence/"+name+".png"),FileMode.WRITE);f.writeBytes(image.encode(image.rect,new PNGEncoderOptions()));f.close();}\\n      private function verify(w:*):void{')
'''+marker)
    if candidate not in ['candidate-01','candidate-02','candidate-03','candidate-04'] and verify:
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        s=s.replace('var a:*=mods[0],b:*=mods[1],ok:Boolean=true;', 'var a:*=mods[0],b:*=mods[1],ok:Boolean=true;if(b.cfgMode=="classic"){a.classicLogicRegion(new Rectangle(0,0,a.spaceX,a.spaceY));b.classicLogicRegion(new Rectangle(0,0,b.spaceX,b.spaceY));}')
        s=s.replace('if(a[field]&&b[field]&&!equal(a[field],b[field]))', 'if(!(b.cfgMode=="classic"&&field=="fogBmp")&&a[field]&&b[field]&&!sameField(a,b,field))')
        s=s.replace('      private function verify(w:*):void{','      private function sameField(a:*,b:*,key:String):Boolean {if(key!="fogCache"||b.cfgMode!="classic")return equal(a[key],b[key]);var r:Rectangle=new Rectangle(4,4,b.spaceX*8,b.spaceY*8),x:BitmapData=new BitmapData(r.width,r.height,true,0),y:BitmapData=x.clone();x.copyPixels(a[key],r,new Point());y.copyPixels(b[key],r,new Point());var ok:Boolean=equal(x,y);x.dispose();y.dispose();return ok;}\\n      private function verify(w:*):void{')
'''+marker)
    if name.startswith('camera-'):
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        start=s.index('private var cases:Array=');end=s.index(';',start)
        s=s[:start]+'private var cases:Array=[{mode:"classic",dense:true,bright:false,dim:.35}]'+s[end:]
        s=s.replace('trace("FRAME CASE "+','trace("CAMERA scale="+w.cam.scaleV+" type="+getQualifiedClassName(w.cam.scaleV));trace("FRAME CASE "+')
        s=s.replace('if(frame==-1){for each(m in mods){', 'if(frame==-1){trace("CAMERA warm scale="+w.cam.scaleV+" full="+mods[1].classicFullRaster+" tiles="+mods[1].classicRenderedTiles);for each(m in mods){')
'''+marker)
    if name.startswith('diagnose-wide'):
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        s=s.replace('var ca:BitmapData=canvas.clone(),cb:BitmapData=canvas.clone();', 'for each(var pk:String in ["classicWallShade","fogRaw","classicVisibilityField"]){var pa:BitmapData=a[pk],pb:BitmapData=b[pk];if(pa&&pb&&!equal(pa,pb)){var pd:BitmapData=pa.compare(pb) as BitmapData;trace("FIELD DIFF "+pk+" "+pd.getColorBoundsRect(0xFFFFFFFF,0,false));dumpImage(pd,pk+"-diff");pd.dispose();}}for each(pk in ["floorField","field","contourFog"]){pa=a.wallSurface[pk];pb=b.wallSurface[pk];if(pa&&pb&&!equal(pa,pb))trace("SURFACE DIFF "+pk);}if(b.cfgMode=="classic"){var z:Number=w.cam.scaleV,region:Rectangle=new Rectangle(4+Math.floor(-w.cam.vx/z/5),4+Math.floor(-w.cam.vy/z/5),Math.ceil(w.cam.screenX/z/5)+1,Math.ceil(w.cam.screenY/z/5)+1);region=region.intersection(a.fogBmp.rect);var xa:BitmapData=new BitmapData(region.width,region.height,true,0),xb:BitmapData=xa.clone();xa.copyPixels(a.fogBmp,region,new Point());xb.copyPixels(b.fogBmp,region,new Point());if(!equal(xa,xb)){trace("FOG DISPLAY DIFF region="+region);dumpImage(xa,"fog-baseline");dumpImage(xb,"fog-candidate");}xa.dispose();xb.dispose();}var ca:BitmapData=canvas.clone(),cb:BitmapData=canvas.clone();')
'''+marker)
    if native:
        assert live
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        s=s.replace('["baseline","candidate","candidate","baseline","baseline","candidate","candidate","baseline"]','["off","baseline","candidate","candidate","baseline","off","off","baseline","candidate","candidate","baseline","off"]')
        s=s.replace('liveIndex<4','liveIndex<6')
        s=s.replace('liveRow={variant:name,','liveRow={cameraScale:Number(w.cam.scaleV),variant:name,')
'''+marker)
    if wide:
        assert verify and not live
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        start=s.index('private var cases:Array=');end=s.index(';',start)
        s=s[:start]+'private var cases:Array='+WIDE_CASES+s[end:]
        s=s.replace('canvas=new BitmapData(1280,720,false,0xffffff);','canvas=new BitmapData(w.cam.screenX,w.cam.screenY,false,0xffffff);')
        s=s.replace('m.cfgDim=c.dim;','m.cfgDim=c.dim;m.cfgSoftClassic=c.soft;m.cfgSoftCurrent=c.soft;m.cfgViewScale=c.distance;')
        s=s.replace('w.cam.calc(w.gg);w.loc.lighting();','w.cam.calc(w.gg);var zoom:Number=[1,0.75,1.25,0.5][int((frame+30)/30)%4];w.cam.scaleV=zoom;w.cam.vx=-Math.max(0,Math.min(w.loc.limX*zoom-w.cam.screenX,w.gg.X*zoom-w.cam.screenX/2));w.cam.vy=-Math.max(0,Math.min(w.loc.limY*zoom-w.cam.screenY,w.gg.Y*zoom-w.cam.screenY/2));w.loc.lighting();')
        s=s.replace('new Matrix(1,0,0,1,LARGE?', 'new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,LARGE?')
'''+marker)
        import json
        inv.WIDE_CASES=json.dumps([dict(mode=mode,dense=True,bright=bright,dim=dim,soft=soft,distance=distance) for mode in ['classic','current'] for bright,dim,soft,distance in [(False,.35,0,1),(False,.6,40,3),(True,0,0,.5),(True,1,40,1)]])
        if name.startswith('focus-'):inv.WIDE_CASES=json.dumps(json.loads(inv.WIDE_CASES)[:1])
    if name.endswith(('-visible','-parent')):
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        s=s.replace('canvas.draw(m.fogVis,new Matrix(1,0,0,1,LARGE?w.cam.vx:-120,LARGE?w.cam.vy:-240)', 'canvas.draw(m.fogVis,displayMatrix(m,w)')
        s=s.replace('canvas.draw(m.fogVis,new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,LARGE?w.cam.vx:-120,LARGE?w.cam.vy:-240)', 'canvas.draw(m.fogVis,displayMatrix(m,w)')
        s=s.replace('ca.draw(a.fogVis,mat,','ca.draw(a.fogVis,displayMatrix(a,w),').replace('cb.draw(b.fogVis,mat,','cb.draw(b.fogVis,displayMatrix(b,w),')
        s=s.replace('      private function verify(w:*):void{','      private function displayMatrix(m:*,w:*):Matrix {var mat:Matrix=m.fogVis.transform.matrix;var camera:Matrix=new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,w.cam.vx,w.cam.vy);mat.concat(camera);return mat;}\\n      private function verify(w:*):void{')
        s=s.replace('canvas=new BitmapData(1280,720,false,0xffffff);','canvas=new BitmapData(w.cam.screenX,w.cam.screenY,false,0xffffff);')
'''+marker)
    if name.endswith('-parent'):
        assert verify
        marker="        entry=folder/'RecoveryFrameProbeMod.as'"
        f=f.replace(marker,'''        s=s.replace('ca.draw(a.fogVis,displayMatrix(a,w),null,null,null,true);cb.draw(b.fogVis,displayMatrix(b,w),null,null,null,true);','parentCapture(ca,a,w);parentCapture(cb,b,w);')
        s=s.replace('      private function verify(w:*):void{','      private function parentCapture(image:BitmapData,m:*,w:*):void {var node:Sprite=m.fogVis,original:DisplayObjectContainer=node.parent,index:int=original?original.getChildIndex(node):-1,wrapper:Sprite=new Sprite();wrapper.addChild(node);try {image.draw(wrapper,new Matrix(w.cam.scaleV,0,0,w.cam.scaleV,w.cam.vx,w.cam.vy),null,null,null,true);} finally {if(original)original.addChildAt(node,index);else wrapper.removeChild(node);}}\\n      private function verify(w:*):void{')
'''+marker)
    exec(f,inv.__dict__)
    inv.build(name,'d36','d37',verify,profile,live)
def run(name):
    import json
    build_info=json.loads((OUT/name/'build.json').read_text(encoding='utf-8'))
    if build_info.get('verify') or name.startswith(('timing-final','native-final')):
        # D37 measured availability drops: <=2.25 GiB for 8 pixel cases and
        # <=1.2 GiB for paired timing. Require 5 GiB to start; final timing
        # review also requires >=3 GiB throughout. Pixel-run times are unused.
        original=(MOD/'build/motion-performance/run.py').read_text(encoding='utf-8')
        body=original[original.index('def run(name):'):original.index('\ndef repeat(')]
        body=body.replace(">=6*1024**3,'Less than 6 GiB physical memory available; no AIR started'", ">=5*1024**3,'Less than 5 GiB available for the D37 isolated run; no AIR started'")
        exec(body,inv.r.__dict__)
    inv.r.run(name)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','run','analyze']);p.add_argument('name');p.add_argument('--candidate',default='candidate-01');p.add_argument('--verify',action='store_true');p.add_argument('--profile',action='store_true');p.add_argument('--live',action='store_true');p.add_argument('--native',action='store_true');p.add_argument('--wide',action='store_true');a=p.parse_args()
    if a.action=='build':build(a.name,a.candidate,a.verify,a.profile,a.live,a.native,a.wide)
    elif a.action=='run':run(a.name)
    else:inv.analyze(a.name)
