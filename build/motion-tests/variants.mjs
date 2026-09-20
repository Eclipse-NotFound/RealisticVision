// Disposable experiment transforms. src/ and release/ stay untouched.
export function transform(source,variant){
  const allowed=['baseline','profile','gate1','immediate','fast-rays','fast-sync','no-clamp','hires','coverage','corner-history'];
  if(!allowed.includes(variant))throw Error('Unknown variant '+variant);
  source=source.replace(/\r\n/g,'\n').replace(/\bprivate\b/g,'public');
  function replace(a,b){if(!source.includes(a))throw Error('Missing transform anchor '+a);source=source.replace(a,b);}
  if(['gate1','fast-sync'].includes(variant))replace('this.frameCount - this.lastFovFrame >= 3','this.frameCount - this.lastFovFrame >= 1');
  if(['immediate','fast-sync'].includes(variant))replace('this.fogBlurPending && !fieldFresh','this.fogBlurPending');
  if(variant==='no-clamp')replace('if(vBlur[vi] < vRaw[vi])','if(false)');
  if(variant==='corner-history')replace(
    'this.seenSub[(ty * FOG_SUB + sy) * this.subW + (tx * FOG_SUB + sx)] = 1;',
    'this.seenSub[(ty * FOG_SUB + (sy == 0 ? 0 : FOG_SUB-1)) * this.subW + (tx * FOG_SUB + (sx == 0 ? 0 : FOG_SUB-1))] = 1;');
  if(variant==='hires'){
    replace('const FOG_SUB:int = 8','const FOG_SUB:int = 16');
    replace('const FOG_PAD:int = 4','const FOG_PAD:int = 8');
    replace('new BlurFilter(4.0,4.0,3);   // current','new BlurFilter(8.0,8.0,3);   // current');
  }
  if(variant==='coverage'){
    const start=source.indexOf('public function recalcTile('),end=source.indexOf('/** current：全亮瓦片',start);
    source=source.slice(0,start)+`public function recalcTile(loc:Location, tx:int, ty:int, bx:Number, by:Number,
         floorF:Number, dimA:int, cs:Number, doorView:Boolean):void
      {
         this.motionTiles++;
         for(var sy:int=0;sy<FOG_SUB;sy++)for(var sx:int=0;sx<FOG_SUB;sx++){
            var index:int=(ty*FOG_SUB+sy)*this.subW+tx*FOG_SUB+sx;
            var seen:Boolean=this.seenSub[index]==1,anyLit:Boolean=false,sum:Number=0;
            for(var qy:int=0;qy<2;qy++)for(var qx:int=0;qx<2;qx++){
               var px:Number=bx+(sx+0.25+0.5*qx)*cs,py:Number=by+(sy+0.25+0.5*qy)*cs;
               var lit:Number=Math.max(0,Math.min(1,this.castRay(loc,this.eyeX,this.eyeY,px,py,tx,ty)));
               var alpha:Number;
               if(lit>0.0001 || doorView){
                  var dx:Number=px-this.eyeX,dy:Number=py-this.eyeY;
                  alpha=(1-Math.max(floorF,lit*this.distFalloff(dx*dx+dy*dy)))*255;
                  if(lit>0.0001)anyLit=true;
               }else alpha=seen?dimA:255;
               sum+=alpha;
            }
            if(anyLit)this.seenSub[index]=1;
            this.fogCache.setPixel32(FOG_PAD+tx*FOG_SUB+sx,FOG_PAD+ty*FOG_SUB+sy,Math.round(sum/4)<<24);
         }
      }

      `+source.slice(end);
  }
  if(['fast-rays','fast-sync'].includes(variant)){
    replace('public function computeFov(loc:Location):void\n      {',`public var motionOpac:Vector.<Number>;
      public function computeFov(loc:Location):void
      {
         var count:int=this.spaceX*this.spaceY;
         if(this.motionOpac==null || this.motionOpac.length!=count)this.motionOpac=new Vector.<Number>(count,true);
         for(var oy:int=0;oy<this.spaceY;oy++)for(var ox:int=0;ox<this.spaceX;ox++)
            this.motionOpac[ox+oy*this.spaceX]=this.tileOpac(loc,loc.getTile(ox,oy));`);
    // Only castRay: preserve step ordering, endpoint double-count, water and partial-opacity semantics.
    const start=source.indexOf('public function castRay('),end=source.indexOf('public function tileOpac(',start);
    let ray=source.slice(start,end);
    ray=ray.replace('t = loc.getTile(c1x,c1y);\n            op = this.tileOpac(loc,t);','op = this.motionOpac[c1x+c1y*this.spaceX];')
      .replace('t = loc.getTile(tx,ty);\n         op = this.tileOpac(loc,t);','op = this.motionOpac[tx+ty*this.spaceX];');
    source=source.slice(0,start)+ray+source.slice(end);
  }
  // Coarse timers only: no getTimer within individual rays / pixels.
  source=source.replace('public class RealisticVisionMod extends Sprite\n   {','public class RealisticVisionMod extends Sprite\n   {\n      public var motionPerf:Object={}; public var motionRays:int=0; public var motionTiles:int=0;');
  if(variant!=='baseline'){
    replace('public function castRay(loc:Location, ex:Number, ey:Number, cx:Number, cy:Number, tx:int, ty:int):Number\n      {','public function castRay(loc:Location, ex:Number, ey:Number, cx:Number, cy:Number, tx:int, ty:int):Number\n      {\n         this.motionRays++;');
    if(variant!=='coverage')replace('floorF:Number, dimA:int, cs:Number, doorView:Boolean):void\n      {','floorF:Number, dimA:int, cs:Number, doorView:Boolean):void\n      {\n         this.motionTiles++;');
    for(const name of ['computeFov','fillFogCache','refreshWallField','applyVision','hideEnemies','structHash']){
      const pos=source.indexOf('public function '+name+'('),start=source.indexOf('{',pos);
      let end=start+1,depth=1;
      // These methods contain balanced braces in code/comments; verified by compilation.
      for(;depth;end++){if(source[end]==='{')depth++;else if(source[end]==='}')depth--;}
      const fallback=name==='structHash'?'return 0;':name==='refreshWallField'?'return false;':'';
      source=source.slice(0,start+1)+`\nvar motionStart:int=getTimer();try {`+source.slice(start+1,end-1)+`\n} finally { this.motionPerf["${name}"]=(this.motionPerf["${name}"]||0)+getTimer()-motionStart; }\n${fallback}\n`+source.slice(end-1);
    }
  }
  return source;
}
