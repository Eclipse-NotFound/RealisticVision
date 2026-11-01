  // Called only before warmup ends and after the last measured frame.
  private function displaySnapshot(w:*):Object {
   var ids:Dictionary=new Dictionary(true),nodes:Array=[],roots:Object={},next:int=1;
   function id(v:DisplayObject):int {if(!v)return 0;if(!ids[v])ids[v]=next++;return int(ids[v]);}
   function rect(r:Rectangle):Array {return r?[r.x,r.y,r.width,r.height]:null;}
   function matrix(m:Matrix):Array {return m?[m.a,m.b,m.c,m.d,m.tx,m.ty]:null;}
   var seen:Dictionary=new Dictionary(true);
   function add(v:DisplayObject):void {
    while(v&&!seen[v]){
     seen[v]=true;var fs:Array=[];for each(var f:Object in v.filters)fs.push(getQualifiedClassName(f));
     var c:ColorTransform=v.transform.colorTransform;
     nodes.push({id:id(v),parent:id(v.parent),type:getQualifiedClassName(v),name:v.name,visible:v.visible,alpha:v.alpha,
      cache:v.cacheAsBitmap,mask:id(v.mask),maskParent:v.mask?id(v.mask.parent):0,filters:fs,blend:v.blendMode,
      scroll:rect(v.scrollRect),localMatrix:matrix(v.transform.matrix),screenMatrix:matrix(v.transform.concatenatedMatrix),
      localBounds:rect(v.getBounds(v)),screenBounds:rect(v.getBounds(host.stage)),
      color:[c.redMultiplier,c.greenMultiplier,c.blueMultiplier,c.alphaMultiplier,c.redOffset,c.greenOffset,c.blueOffset,c.alphaOffset]});
     v=v.parent;
    }
   }
   function root(label:String,v:DisplayObject):void {roots[label]=id(v);add(v);}
   root('visual',w.grafon.visual);root('fogVis',rv.fogVis);root('fogShadow',rv.fogShadow);root('fogBase',rv.fogBase);
   root('floor',rv.fogBitmap);root('wall',rv.wallLayer);root('air',rv.wallSurface.airPixels);
   var units:Array=[];
   for(var i:int=0;i<crowd.length;i++){
    var u:*=crowd[i];root('unit'+i,u.vis);root('bar'+i,u.hpbar);
    units.push({id:u.id,visible:u.vis.visible,alpha:u.vis.alpha,x:u.X,y:u.Y,masked:u.vis.mask!=null});
    var j:int=0;for each(var child:* in u.childObjs)if(child.vis)root('weapon'+i+'-'+j++,child.vis);
   }
   for each(var layer:DisplayObjectContainer in w.grafon.visObjs){
    for(var k:int=0;k<layer.numChildren;k++){var v:DisplayObject=layer.getChildAt(k);if(getQualifiedClassName(v).indexOf('visualGrifArm')==0){root('arm',v);break;}}
   }
   return {nodes:nodes,roots:roots,units:units,quality:host.stage.quality,scaleMode:host.stage.scaleMode,screen:[host.stage.stageWidth,host.stage.stageHeight]};
  }
