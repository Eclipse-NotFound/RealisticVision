"""Test-only counters; no mask/cache/visible or release scheduling changes."""
def patch(source):
 def replace(old,new):
  nonlocal source
  assert source.count(old)==1,old
  source=source.replace(old,new)
 replace('public var worldPass:int = 0;', '''public var worldPass:int = 0;
      public var diagReleasedRasters:int=0,diagReleasedBuffers:int=0,diagCreatedRasters:int=0,diagSweepMs:int=0;
      public var diagReleasedPixels:Number=0;
      public var diagSweep:Boolean=false;''')
 replace('         this.worldPass++;','''         this.worldPass++;
         this.diagReleasedRasters=0;this.diagReleasedBuffers=0;this.diagCreatedRasters=0;this.diagReleasedPixels=0;this.diagSweepMs=0;
         this.diagSweep=this.worldPass%60==0;''')
 replace('         if(this.worldPass%60==0)for(var key:String in this.worldMasks)', '''         var diagSweepStart:int=getTimer();
         if(this.worldPass%60==0)for(var key:String in this.worldMasks)''')
 replace('this.disposeWorldMask(raster);delete this.worldMasks[key];\n            }\n         }', '''this.disposeWorldMask(raster);delete this.worldMasks[key];
            }
         }
         if(this.diagSweep)this.diagSweepMs=getTimer()-diagSweepStart;''')
 replace('if(raster==null){raster={worldRaster:true,','if(raster==null){this.diagCreatedRasters++;raster={worldRaster:true,')
 replace('''         for each(var key:String in ["m2d","m2e","maskInput"])
            if(record[key] != null)BitmapData(record[key]).dispose();''','''         this.diagReleasedRasters++;
         for each(var key:String in ["m2d","m2e","maskInput"])
            if(record[key] != null){
               this.diagReleasedBuffers++;this.diagReleasedPixels+=BitmapData(record[key]).width*BitmapData(record[key]).height;
               BitmapData(record[key]).dispose();
            }''')
 return source
