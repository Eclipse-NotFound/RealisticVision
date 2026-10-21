"""D34: derive only from the installed D32 production sources, never HEAD."""
from pathlib import Path
import hashlib, json, re, shutil
MOD = Path(__file__).resolve().parents[2]
OUT = MOD / 'build/vision-settings-output'
BASE = MOD / 'build/stair-shadow-output/merged-v0323/candidate'
OLD = '76314b819151fba6f67f6d740b21030a9eec8359af4c9c9ddeb83d4caf5c46b7'
VERSION = 'v0.33.0-vision-settings'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
    assert s.count(a)==1, (a[:100],s.count(a))
    return s.replace(a,b)
def main_source(s):
    s=re.sub(r'private static const VERSION:String = "[^"]+";', 'private static const VERSION:String = "'+VERSION+'";', s)
    s=replace(s,'      private var cfgDim:Number = 0.35;', '''      private var cfgDim:Number = 0.35;
      private var cfgViewScale:Number = 1;
      private var cfgSoftCurrent:Number = 20;
      private var cfgSoftClassic:Number = 0;
      private var settingsDirty:Boolean = false;
      private var rangeLight:Array;
      private var rangeRoom:Location;
      private var rangeMem:Object = {};
      private var classicLogicCache:BitmapData;
      private var classicSoftInput:BitmapData;''')
    s=replace(s,'                   this.cfgDim = Number(val);','                   this.cfgDim = settingNumber(val,0,1,0.35);')
    s=replace(s,'                else if(key == "doordim")','''               else if(key == "viewscale") this.cfgViewScale = settingNumber(val,0.5,3,1);
               else if(key == "soft_current") this.cfgSoftCurrent = settingNumber(val,0,60,20);
               else if(key == "soft_classic") this.cfgSoftClassic = settingNumber(val,0,40,0);
                else if(key == "doordim")''')
    s=replace(s,'      private function saveConfig():void','''      private static function settingNumber(v:*,lo:Number,hi:Number,fallback:Number):Number
      {
         if(v == null || String(v).replace(/\\s/g,"") == "") return fallback;
         var n:Number = Number(v);
         return isFinite(n) ? Math.max(lo,Math.min(hi,n)) : fallback;
      }

      private function setVisualSetting(key:String,v:*):void
      {
         if(key == "dim") this.cfgDim = settingNumber(v,0,1,0.35);
         else if(key == "viewscale") this.cfgViewScale = settingNumber(v,0.5,3,1);
         else if(key == "soft_current") this.cfgSoftCurrent = settingNumber(v,0,60,20);
         else if(key == "soft_classic") this.cfgSoftClassic = settingNumber(v,0,40,0);
         else return;
         // Repaint in place: resetting the room would discard subcell memory.
         this.settingsDirty = true;
         this.saveConfig();
      }

      private function updateViewDistances(loc:Location):void
      {
         var d1:Number = (loc.lDist1 > 0 ? loc.lDist1 : 300)*this.cfgViewScale;
         var d2:Number = (loc.lDist2 > 0 ? loc.lDist2 : 1000)*this.cfgViewScale;
         if(d1 != this.locDist1 || d2 != this.locDist2) this.settingsDirty = true;
         this.locDist1 = d1; this.locDist2 = d2;
         this.curBlur.blurX = this.curBlur.blurY = this.cfgSoftCurrent/5;
      }

      /** Native corner light sampling, in a mod-owned field. No native writes.
       * Retain the native subtractive opacity and phase, including solid cores. */
      private function updateRangeLight(loc:Location):void
      {
         if(this.cfgViewScale == 1) return;
         if(this.rangeRoom !== loc || this.rangeLight == null || this.rangeLight.length != this.spaceX*this.spaceY)
         {
            this.rangeRoom = loc;
            var saved:Object=this.rangeMem[loc.id];
            if(saved == null || saved.width != this.spaceX || saved.height != this.spaceY)
            {saved={width:this.spaceX,height:this.spaceY,values:new Array(this.spaceX*this.spaceY)};this.rangeMem[loc.id]=saved;}
            this.rangeLight = saved.values;
         }
         var ex:Number = this.eyeX, ey:Number = this.eyeY;
         for(var y:int=1;y<this.spaceY;y++) for(var x:int=1;x<this.spaceX;x++)
         {
            var dx:Number=x*Tile.tileX-ex,dy:Number=y*Tile.tileY-ey;
            var value:Number=this.distFalloff(dx*dx+dy*dy);
            if(value>0)
            {
               if(Math.abs(dx)==Math.abs(dy)) dy++;
               var sx:Number,sy:Number,steps:int;
               if(Math.abs(dx)>=Math.abs(dy)) {sx=dx>0?Tile.tileX:-Tile.tileX;sy=dy/dx*sx;steps=int(dx/sx);}
               else {sy=dy>0?Tile.tileY:-Tile.tileY;sx=dx/dy*sy;steps=int(dy/sy);}
               for(var k:int=1;k<=steps;k++)
               {
                  var t:Tile=loc.getTile(Math.floor((ex+k*sx)/Tile.tileX),Math.floor((ey+k*sy)/Tile.tileY));
                  var opacity:Number=t.opac;
                  if(t.water>0 && loc.opacWater>opacity) opacity=loc.opacWater;
                  if(opacity>0) value-=opacity;
                  if(value<=0) {value=0;break;}
               }
            }
            var i:int=x+y*this.spaceX, previous:Number=Number(this.rangeLight[i]);
            this.rangeLight[i]=loc.retDark?value:Math.max(value,isNaN(previous)?0:previous);
         }
      }

      private function saveConfig():void''')
    s=replace(s,'               + "dim=" + this.cfgDim + "\\n"','''               + "dim=" + this.cfgDim + "\\n"
               + "viewscale=" + this.cfgViewScale + "\\n"
               + "soft_current=" + this.cfgSoftCurrent + "\\n"
               + "soft_classic=" + this.cfgSoftClassic + "\\n"''')
    s=replace(s,'         // current 随每帧位移刷新；classic 保留既有节奏。','''         this.updateViewDistances(loc);
         if(this.settingsDirty) {this.lastGX=-99999;this.fogDirty=true;this.settingsDirty=false;}
         // current 随每帧位移刷新；classic 保留既有节奏。''')
    s=replace(s,'         this.roomMem = {};','         this.rangeMem = {}; this.rangeRoom = null; this.rangeLight = null;\n         this.roomMem = {};')
    s=replace(s,'         this.locDist1 = loc.lDist1 > 0 ? loc.lDist1 : 300;\n         this.locDist2 = loc.lDist2 > 0 ? loc.lDist2 : 1000;','         this.updateViewDistances(loc);')
    s=replace(s,'            var r:Number = loc.lDist2;','            this.updateViewDistances(loc);\n            this.updateRangeLight(loc);\n            var r:Number = this.cfgViewScale == 1 ? loc.lDist2 : this.locDist2;')
    s=replace(s,'         return light;\n      }\n\n      private function memorySeen','''         if(this.cfgViewScale != 1 && this.rangeRoom === loc && this.rangeLight != null)
            light = Math.max(light,Number(this.rangeLight[x+y*this.spaceX]) || 0);
         return light;
      }

      private function memorySeen''')
    # D31 exact fast path in the production branch has an inlined native read.
    needle='               light = Math.max(0,Math.min(1,tile.visi));'
    if needle in s:
        s=replace(s,needle,needle+'\n               if(this.cfgViewScale != 1 && this.rangeRoom === loc && this.rangeLight != null)\n                  light = Math.max(light,Number(this.rangeLight[index]) || 0);')
    s=replace(s,'               if(lit > 0.0001 && a < MASK_LIT_A && sdx*sdx+sdy*sdy <= this.locDist2*this.locDist2)', '''               var logicalA:int=Math.round((1-Math.max(lit*this.distFalloff(sdx*sdx+sdy*sdy),doorView?floorF:0.35))*255);
               if(lit > 0.0001 && logicalA < MASK_LIT_A && sdx*sdx+sdy*sdy <= this.locDist2*this.locDist2)''')
    s=replace(s,'               if(f < dimF)','               var logicalF:Number = f;\n               if(f < dimF)')
    s=replace(s,'if(Math.round((1-f)*255)<MASK_LIT_A)','if(Math.round((1-Math.max(logicalF,0.35))*255)<MASK_LIT_A)')
    s=replace(s,'return Math.round(255-gv*255*(1-cur+cur*this.cfgDim));','return Math.round(255-gv*255*(1-cur+cur*0.35));')
    s=replace(s,'         var cur:Number = this.memCur[tx+ty*this.spaceX];','''         if(this.cfgViewScale != 1 && this.rangeRoom === this.curLoc && this.rangeLight != null)
            gv=Math.max(gv,Number(this.rangeLight[tx+ty*this.spaceX]) || 0);
         var cur:Number = this.memCur[tx+ty*this.spaceX];''')
    s=s.replace('this.sharedLight == null ? a','this.sharedLight == null && this.cfgDim == 0.35 ? a')
    s=replace(s,'private function applyVisionClassic(w:World, loc:Location, needFov:Boolean):void','private function applyVisionClassic(w:World, loc:Location, needFov:Boolean, logicOnly:Boolean = false):void')
    s=replace(s,'         var changed:Boolean = needFov;\n         // 先推进全图', '''         var separateLogic:Boolean = !logicOnly && this.cfgDim != 0.35;
         if(separateLogic)
         {
            var displayDim:Number=this.cfgDim;
            try {this.cfgDim=0.35;this.applyVisionClassic(w,loc,needFov,true);}
            finally {this.cfgDim=displayDim;}
            this.classicLogicCache=this.sizedScratch(this.classicLogicCache);
            this.classicLogicCache.copyPixels(this.fogCache,this.fogRect,this.fogPoint);
         }
         var changed:Boolean = needFov || separateLogic;
         // 先推进全图''')
    s=replace(s,'for(var mi:int = 0; mi < this.spaceX*this.spaceY; mi++) this.advanceMemory(loc,mi);','if(!separateLogic) for(var mi:int = 0; mi < this.spaceX*this.spaceY; mi++) this.advanceMemory(loc,mi);')
    s=replace(s,'''            this.fogCache.copyPixels(this.fogBmp,this.fogRect,this.fogPoint);
            this.fovVersion++;''','''            this.fogCache.copyPixels(this.fogBmp,this.fogRect,this.fogPoint);
            if(!logicOnly && this.cfgSoftClassic > 0)
            {
               this.classicSoftInput=this.sizedScratch(this.classicSoftInput);
               this.classicSoftInput.copyPixels(this.fogBmp,this.fogRect,this.fogPoint);
               this.fogBlur.blurX=this.fogBlur.blurY=this.cfgSoftClassic/5;
               this.fogBmp.applyFilter(this.classicSoftInput,this.fogRect,this.fogPoint,this.fogBlur);
               // Reconnect the softened floor to the untouched native wall field.
               this.fogRaw.copyChannel(this.fogBmp,this.fogRect,this.fogPoint,BitmapDataChannel.ALPHA,BitmapDataChannel.BLUE);
               this.joinClassicWalls(loc);
               this.fogCache.copyPixels(this.classicSoftInput,this.fogRect,this.fogPoint);
            }
            if(separateLogic) this.fogCache.copyPixels(this.classicLogicCache,this.fogRect,this.fogPoint);
            this.fovVersion++;''')
    s=replace(s,'      private function classicCornerDeltaAt(','''      private function sizedScratch(b:BitmapData):BitmapData
      {
         if(b == null || b.width != this.fogBmp.width || b.height != this.fogBmp.height)
         {if(b != null)b.dispose();b=new BitmapData(this.fogBmp.width,this.fogBmp.height,true,0);}
         return b;
      }

      private function classicCornerDeltaAt(''')
    s=replace(s,'"label":"记忆区暗度"','"label":"已探索区域亮度"')
    s=replace(s,'"min":0,"max":0.8,"step":0.05,"hint":"0=全亮 越大越暗"','"min":0,"max":1,"step":0.05,"hint":"视野外已探索区域：0=全黑，1=最亮；不会显示隐藏敌人"')
    s=replace(s,'"set":function(v:*):void { self.cfgDim = Number(v); }};', '"set":function(v:*):void { self.setVisualSetting("dim",v); }};')
    marker='         items[items.length] = {"key":"doordim"'
    additions=''
    for key,label,lo,hi,step,default,field,hint in [
        ('viewscale','最大视距倍率',.5,3,.25,1,'cfgViewScale','1=房间默认；仍受墙门遮挡；扩大视距会保留探索记忆'),
        ('soft_current','平滑阴影渐变宽度',0,60,5,20,'cfgSoftCurrent','仅平滑阴影：0=硬边，20=原效果；数值为柔化尺度（像素）'),
        ('soft_classic','仿原版额外柔化',0,40,5,0,'cfgSoftClassic','仅仿原版：0=原效果；保留墙内渐变，不扩大可见范围')]:
        additions+='''         items[items.length] = {"key":"%s","label":"%s","kind":"slider",
            "min":%s,"max":%s,"step":%s,"hint":"%s","def":%s,
            "get":function():* { return self.%s; },
            "set":function(v:*):void { self.setVisualSetting("%s",v); }};
'''%(key,label,lo,hi,step,hint,default,field,key)
    s=replace(s,marker,additions+marker)
    return s

def locale_source(s):
    rows={
      '已探索区域亮度':['Explored area brightness','Яркость изученных областей'],
      '视野外已探索区域：0=全黑，1=最亮；不会显示隐藏敌人':['Remembered areas outside sight: 0 = black, 1 = brightest; hidden enemies stay hidden.','Изученные области вне обзора: 0 — чёрные, 1 — светлые; скрытые враги не появляются.'],
      '最大视距倍率':['Maximum view distance multiplier','Множитель дальности обзора'],
      '1=房间默认；仍受墙门遮挡；扩大视距会保留探索记忆':['1 = room default. Walls and doors still block sight; explored areas remain remembered.','1 — стандарт комнаты. Стены и двери блокируют обзор; изученные области сохраняются в памяти.'],
      '平滑阴影渐变宽度':['Soft shadow transition width','Ширина перехода мягких теней'],
      '仅平滑阴影：0=硬边，20=原效果；数值为柔化尺度（像素）':['Soft shadows only: 0 = hard edge, 20 = original. Softening scale in pixels.','Только мягкие тени: 0 — резкий край, 20 — исходный эффект. Масштаб размытия в пикселях.'],
      '仿原版额外柔化':['Classic additional softening','Дополнительное размытие Classic'],
      '仅仿原版：0=原效果；保留墙内渐变，不扩大可见范围':['Classic only: 0 = original. Preserves shading inside walls and does not extend sight.','Только Classic: 0 — исходный эффект. Сохраняет тени внутри стен и не расширяет обзор.']}
    text=''.join('  '+json.dumps(k,ensure_ascii=False)+': '+json.dumps(dict(zip(['en','ru'],v)),ensure_ascii=False)+',\n' for k,v in rows.items())
    return replace(s,'      public static const DATA:Object = {','      public static const DATA:Object = {\n'+text)

def prepare():
    assert sha(BASE/'RealisticVisionMod.swf')==OLD and sha(MOD/'release/RealisticVisionMod.swf')==OLD
    assert not OUT.exists(), 'Do not overwrite frozen experiments'
    shutil.copytree(BASE/'src',OUT/'baseline/src')
    shutil.copytree(BASE/'src',OUT/'candidate/src')
    for rel,fn in [('RealisticVisionMod.as',main_source),('modlocales/vision/RVLocaleMessages.as',locale_source)]:
        p=OUT/'candidate/src'/rel;p.write_text(fn(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
    (OUT/'baseline.json').write_text(json.dumps({'installed':OLD,'source':{p.relative_to(BASE/'src').as_posix():sha(p) for p in (BASE/'src').rglob('*.as')}},indent=2),encoding='utf-8')
    print('Prepared D34 from exact deployed D32')
if __name__=='__main__':prepare()
