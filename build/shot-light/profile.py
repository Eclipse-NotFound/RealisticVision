"""Diagnostic phase counters. Do not deploy or infer final gains from this source."""
def once(s,a,b):
 assert s.count(a)==1,(a[:90],s.count(a))
 return s.replace(a,b)
def instrument_field(s):
 s=once(s,'public const cell:int = 12;', '''public const cell:int = 12;
        public var perf:Array=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
        public function perfReset():void {for(var p:int=0;p<perf.length;p++)perf[p]=0;}''')
 s=once(s,'var started:int = getTimer();','var started:int = getTimer(),phaseStart:int=started,oldRebuilds:int=rebuilds;')
 markers=[
 ('            var scan:Rectangle=view.clone();',0),
 ('            ambientBackground(ambient,zones,darkness,environment,reuse);',1),
 ('            var alive:Object={};',2),
 ('            data.lock(); data.copyPixels',3),
 ('            for(var key:String in cache) if(!alive[key])',4),
 ('            trailRaster.render(data,bounds,cell,loc,lights);',5)]
 for marker,index in markers:
  s=once(s,marker,'            perf['+str(index)+']+=getTimer()-phaseStart;phaseStart=getTimer();\n'+marker)
 s=once(s,'data.unlock();elapsedMs=getTimer()-started;','''data.unlock();elapsedMs=getTimer()-started;
            perf[6]+=getTimer()-phaseStart;perf[7]+=elapsedMs;perf[8]++;
            perf[9]+=trailRaster.visits;perf[10]+=trailRaster.rays;perf[11]+=rebuilds-oldRebuilds;
            for(var pk:int=0;pk<4;pk++)perf[12+pk]+=trailRaster.perfKinds[pk];perf[16]+=trailRaster.painted;''')
 return s
def instrument_trail(s):
 s=once(s,'public var visits:int=0;','public var visits:int=0;public var perfKinds:Array=[0,0,0,0];')
 s=once(s,'visits=rays=painted=0;limited=false;touched.length=0;','visits=rays=painted=0;limited=false;touched.length=0;for(var pk:int=0;pk<4;pk++)perfKinds[pk]=0;')
 s=once(s,'if(cx<0 || cy<0 || ex<0 || ey<0 || cx>=loc.spaceX || cy>=loc.spaceY || ex>=loc.spaceX || ey>=loc.spaceY)return false;',
 '''if(cx<0 || cy<0 || ex<0 || ey<0 || cx>=loc.spaceX || cy>=loc.spaceY || ex>=loc.spaceX || ey>=loc.spaceY){perfKinds[0]++;return false;}
            if(cx==ex && cy==ey)perfKinds[1]++;
            else if((cx==ex && (cy==ey-1 || cy==ey+1)) || (cy==ey && (cx==ex-1 || cx==ex+1)))perfKinds[2]++;
            else perfKinds[3]++;''')
 return s

def detail_field(s):
 s=once(s,'public var perf:Array=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];',
 'public var perf:Array=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];public var perfSources:Object={};')
 s=once(s,'public function perfReset():void {','public function perfReset():void {perfSources={};')
 s=once(s,'if(light.power<=0)return;','''if(light.power<=0)return;
            var sourceKind:String=identity.indexOf("projectile:")==0?identity.split(":").slice(0,2).join(":"):identity.indexOf("headlamp")==0?identity:"scene";
            var sourceStats:Array=perfSources[sourceKind];if(!sourceStats){sourceStats=[0,0,0,0];perfSources[sourceKind]=sourceStats;}
            var makeStart:int=getTimer();''')
 s=once(s,'entry={key:signature,data:makeLight(light)};cache[identity]=entry;rebuilds++;',
 '''entry={key:signature,data:makeLight(light)};cache[identity]=entry;rebuilds++;
                var makeMs:int=getTimer()-makeStart;perf[17]+=makeMs;sourceStats[0]+=makeMs;sourceStats[2]++;
            } else {perf[24]++;''')
 s=once(s,'target.draw(entry.data,matrix,transform,BlendMode.SCREEN,null,true);',
 '''var blendStart:int=getTimer();target.draw(entry.data,matrix,transform,BlendMode.SCREEN,null,true);
            var blendMs:int=getTimer()-blendStart;perf[18]+=blendMs;perf[19]++;sourceStats[1]+=blendMs;sourceStats[3]++;''')
 s=once(s,'var radius:Number=Number(light.radius);','var fanStart:int=getTimer();var radius:Number=Number(light.radius);')
 s=once(s,'result.draw(root);return result;',
 'perf[22]+=getTimer()-fanStart;var rasterStart:int=getTimer();result.draw(root);perf[23]+=getTimer()-rasterStart;return result;')
 s=once(s,'public function traceRay(sx:Number,sy:Number,dx:Number,dy:Number,radius:Number):Number {',
 'public function traceRay(sx:Number,sy:Number,dx:Number,dy:Number,radius:Number):Number {perf[20]++;')
 s=once(s,'while(distance<radius) {','while(distance<radius) {perf[21]++;')
 return s
