"""Keep display and canonical low-resolution samples independent across frames."""
import shutil
import prepare as p
import prepare_late

def change(s):
 s=prepare_late.change(s)
 old='''            var displayDim:Number=this.cfgDim;
            try {this.cfgDim=0.35;this.applyVisionClassic(w,loc,needFov,true);}
            finally {this.cfgDim=displayDim;}'''
 new='''            var displayDim:Number=this.cfgDim;
            if(this.classicLogicMemorySamples == null)
            {
               this.classicLogicMemorySamples=new BitmapData(this.classicMemoryRaw.width,this.classicMemoryRaw.height,true,0xFF000000);
               this.classicLogicVisibilitySamples=new BitmapData(this.classicVisibilityRaw.width,this.classicVisibilityRaw.height,false,0xFFFFFF);
            }
            var displayMemory:BitmapData=this.classicMemoryRaw;
            var displayVisibility:BitmapData=this.classicVisibilityRaw;
            try
            {
               // Do not toggle the same bitmap between display and canonical
               // brightness: that dirties the whole explored map every pass.
               this.classicMemoryRaw=this.classicLogicMemorySamples;
               this.classicVisibilityRaw=this.classicLogicVisibilitySamples;
               this.cfgDim=0.35;this.applyVisionClassic(w,loc,needFov,true);
            }
            finally
            {
               this.cfgDim=displayDim;
               this.classicMemoryRaw=displayMemory;this.classicVisibilityRaw=displayVisibility;
            }'''
 assert s.count(old)==1;s=s.replace(old,new)
 begin=s.index('               if(this.classicLogicMemorySamples == null)',s.index('         if(logicOnly)'))
 end=s.index('               this.classicLogicCache=this.sizedScratch',begin)
 s=s[:begin]+s[end:]
 s=s.replace('''               // Always snapshot: a live brightness change can enter this
               // path before any canonical cache exists, even if samples match.
''','''            if(changed || this.classicLogicCache == null)
            {
''')
 s=s.replace('''               if(changed) this.fovVersion++;
            return;
         }''','''               if(changed) this.fovVersion++;
            }
            return;
         }''',1)
 return s

if __name__=='__main__':
 dest=p.OUT/'candidate-v5/src';assert not dest.exists();shutil.copytree(p.BASE,dest)
 file=dest/'RealisticVisionMod.as';file.write_text(change(file.read_text(encoding='utf-8-sig')),encoding='utf-8')
 print('prepared persistent sample candidate')
