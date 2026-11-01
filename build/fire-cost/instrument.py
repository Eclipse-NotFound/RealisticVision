"""Diagnostic only: count actual mask allocation/retirement at its writers."""
def once(s,old,new):
 assert s.count(old)==1,(old[:100],s.count(old))
 return s.replace(old,new)

def instrument(s):
 p=s.index('{',s.index('public class'))+1
 s=s[:p]+'''
 public var fireNewN:int=0,fireNewPixels:Number=0,fireFreeN:int=0,fireFreePixels:Number=0;
 public var fireRasters:int=0,fireRecords:int=0,fireEvictions:int=0,fireDiffs:int=0,fireBinds:int=0;
 public function fireReset():void {fireNewN=fireFreeN=fireRasters=fireRecords=fireEvictions=fireDiffs=fireBinds=0;fireNewPixels=fireFreePixels=0;}
 public function fireBitmap(w:int,h:int):BitmapData {fireNewN++;fireNewPixels+=w*h;return new BitmapData(w,h,true,0);}
 public function fireDispose(b:BitmapData):void {fireFreeN++;fireFreePixels+=b.width*b.height;b.dispose();}
 public function fireFrame():Array {return [fireNewN,fireNewPixels,fireFreeN,fireFreePixels,fireRasters,fireRecords,fireEvictions,fireDiffs,fireBinds];}
''' +s[p:]
 start=s.index('public function refreshMask(');end=s.index('\n      public function ',start+1)
 t=s[start:end]
 assert t.count('new BitmapData(totx,toty,true,0)')==2
 t=t.replace('new BitmapData(totx,toty,true,0)','this.fireBitmap(totx,toty)')
 t=once(t,'new BitmapData(bd.width,bd.height,true,0)','this.fireBitmap(bd.width,bd.height)')
 for var in ['bd','bdb','previousInput']:t=t.replace(var+'.dispose();','this.fireDispose('+var+');')
 t=once(t,'if(maskDelta is BitmapData) BitmapData(maskDelta).dispose();','if(maskDelta is BitmapData){this.fireDiffs++;this.fireNewN++;this.fireNewPixels+=BitmapData(maskDelta).width*BitmapData(maskDelta).height;this.fireDispose(BitmapData(maskDelta));}')
 s=s[:start]+t+s[end:]
 for old,new in [
  ('if(raster==null){raster={worldRaster:true,','if(raster==null){this.fireRasters++;raster={worldRaster:true,'),
  ('record={shape:new Shape(),baseMask:','this.fireRecords++;record={shape:new Shape(),baseMask:'),
  ('this.disposeWorldMask(raster);delete this.worldMasks[key];','this.fireEvictions++;this.disposeWorldMask(raster);delete this.worldMasks[key];'),
  ('if(record[key] != null)BitmapData(record[key]).dispose();','if(record[key] != null)this.fireDispose(BitmapData(record[key]));'),
 ]:s=once(s,old,new)
 start=s.index('public function applyWorldVisual(');end=s.index('\n      public function ',start+1)
 s=s[:start]+once(s[start:end],'if(visual.mask!==shape)visual.mask=shape;','if(visual.mask!==shape){this.fireBinds++;visual.mask=shape;}')+s[end:]
 return s
