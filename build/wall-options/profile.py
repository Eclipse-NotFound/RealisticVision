"""Instrument only a disposable candidate copy to locate render costs."""
from pathlib import Path
import shutil,verify
runner=verify.runner
root=verify.OUT/'profile'
root.mkdir(exist_ok=True)
for variant in ['baseline','candidate']:
    shutil.copytree(verify.OUT/variant/'src',root/variant/'src',dirs_exist_ok=True)
path=root/'candidate/src/RVWallSurface.as'
source=path.read_text(encoding='utf-8')
def replace(old,new):
    global source
    assert source.count(old)==1,old
    source=source.replace(old,new)
replace('   import flash.display.Bitmap;', '   import flash.utils.getTimer;\n   import flash.display.Bitmap;')
replace('      private var owner:*;', '      public var profile:Array=[0,0,0,0,0,0,0,0,0,0];\n      private var owner:*;')
replace('         if(baseOwner!==base)', '         var stamp:int=getTimer();\n         if(baseOwner!==base)')
replace('         var seen:Array=[],lights:Array=[];', '         profile[0]+=getTimer()-stamp;stamp=getTimer();\n         var seen:Array=[],lights:Array=[];')
replace('         var nextSeen:String=seen.join("");', '         profile[1]+=getTimer()-stamp;stamp=getTimer();\n         var nextSeen:String=seen.join("");')
replace('         wallPixels.visible=count>0;', '         profile[2]+=getTimer()-stamp;stamp=getTimer();\n         wallPixels.visible=count>0;')
replace('         for each(var piece:Object in pieces){', '         profile[3]+=getTimer()-stamp;stamp=getTimer();\n         for each(var piece:Object in pieces){')
replace('            var shadeChanged:Boolean=false;', '            profile[4]+=getTimer()-stamp;stamp=getTimer();\n            var shadeChanged:Boolean=false;')
replace('            piece.nextBase.copyPixels', '            profile[5]+=getTimer()-stamp;stamp=getTimer();\n            piece.nextBase.copyPixels')
replace('         }} finally {base.mask=baseClip;}', '            profile[6]+=getTimer()-stamp;stamp=getTimer();\n         }} finally {base.mask=baseClip;}\n         profile[7]+=getTimer()-stamp;profile[8]++;profile[9]=pieces.length;')
path.write_text(source,encoding='utf-8')
runner.OUT=root;runner.HERE=verify.HERE
runner.game(bench=True)
