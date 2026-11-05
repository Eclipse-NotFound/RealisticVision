package {
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.utils.Dictionary;
   /** Records only RV's writes, preserving the pre-view native state. Ordinary
    * single-player/A never attach and retain their existing assignments. */
   public final class RVAuthorityView {
      private var records:Dictionary=new Dictionary(true),masks:Dictionary=new Dictionary(true);
      private var owner:String=null,generation:uint=0;
      public function get active():Boolean{return owner!=null;}
      public function publish(main:DisplayObjectContainer):void {
         var carrier:RVAuthorityCarrier=new RVAuthorityCarrier();carrier.name="RVAuthorityViewAPI";
         carrier.visible=carrier.mouseEnabled=carrier.mouseChildren=false;
         carrier.authorityAPI={version:1,attach:attach};main.addChild(carrier);
      }
      private function attach(request:Object):Object {
         if(request==null || request.version!==1 || !(request.session is String) || request.session.length<1 ||
            request.session.length>128 || ["host","join"].indexOf(request.role)<0 || owner!=null)return null;
         owner=request.session;var token:uint=++generation,self:RVAuthorityView=this;
         return {version:1,
            prepare:function():void{if(token!=self.generation || !self.active)throw new Error("Expired RV B lease");self.restore();},
            readNative:function(operation:Function):*{if(token!=self.generation || !self.active)throw new Error("Expired RV B lease");return self.readNative(operation);},
            inspect:function():Object{return {active:self.active && token==self.generation};},
            detach:function():void{if(token!=self.generation)return;self.restore();self.owner=null;++self.generation;}};
      }
      public function remember(target:Object,key:String):void {
         if(!active || target==null)return;
         var fields:Object=records[target];if(fields==null)fields=records[target]={};
         if(!fields.hasOwnProperty(key))fields[key]={before:target[key],after:target[key]};
      }
      public function changed(target:Object,key:String):void {
         if(!active || target==null)return;
         var fields:Object=records[target];if(fields!=null && fields[key]!=null)fields[key].after=target[key];
      }
      public function write(target:Object,key:String,value:*,nativeOnClear:Boolean=false):void {
         if(target==null)return;
         if(!active){target[key]=value;return;}
         remember(target,key);var state:Object=records[target][key];
         if(nativeOnClear)value=state.before;
         if(key=="mask" && value!=null && value!==state.before)masks[value]=true;
         target[key]=value;state.after=target[key];
      }
      public function restore():void {
         for(var target:Object in records)for(var key:String in records[target]) {
            var state:Object=records[target][key];
            // Do not overwrite an intervening native change or another owner.
            if(target[key]===state.after)target[key]=state.before;
         }
         for(var mask:Object in masks) {
            var display:DisplayObject=mask as DisplayObject;
            if(display!=null && display.parent!=null)display.parent.removeChild(display);
         }
         records=new Dictionary(true);masks=new Dictionary(true);
      }
      /** Sample after native frame construction without exporting RV's local
       * visibility or losing that local view before this frame is rendered. */
      private function readNative(operation:Function):* {
         var fields:Array=[],detached:Array=[];
         for(var target:Object in records)for(var key:String in records[target]) {
            var state:Object=records[target][key];
            if(target[key]===state.after) {
               fields.push({target:target,key:key,before:state.before,after:state.after});target[key]=state.before;
            }
         }
         // Record all indices before removing any sibling mask.
         for(var mask:Object in masks) {
            var display:DisplayObject=mask as DisplayObject;
            if(display!=null && display.parent!=null)detached.push({display:display,parent:display.parent,index:display.parent.getChildIndex(display)});
         }
         detached.sortOn("index",Array.NUMERIC);
         for each(var item:Object in detached)item.parent.removeChild(item.display);
         try {return operation();}
         finally {
            for each(item in detached)if(item.display.parent==null)item.parent.addChildAt(item.display,Math.min(item.index,item.parent.numChildren));
            for each(item in fields)if(item.target[item.key]===item.before)item.target[item.key]=item.after;
         }
      }
   }
}
