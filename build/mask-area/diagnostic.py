"""Test-only omissions at attachment sites; avoid per-frame undo/redo invalidations."""
def patch(source):
    replacements={
      '      private var worldMasks:Object = {};': '      private var worldMasks:Object = {};\n      public var diagnosticMaskMode:String="normal";',
      '         this.refreshMask(rec,bb);\n         var s2:Shape=': '         this.refreshMask(rec,bb);\n         if(this.diagnosticMaskMode=="noactors" || this.diagnosticMaskMode=="nomask")return;\n         var s2:Shape=',
      '         if(record.hidden) {visual.visible=record.visible;record.hidden=false;}': '         if(record.hidden) {visual.visible=record.visible;record.hidden=false;}\n         if(this.diagnosticMaskMode=="noactors" || this.diagnosticMaskMode=="nomask")return;',
      'private function applyWorldVisual(visual:DisplayObject):void': 'private function applyWorldVisual(visual:DisplayObject,actor:Boolean=false):void',
      'if(kind)this.applyWorldVisual(child);': 'if(kind)this.applyWorldVisual(child,true);',
      'if(weapon != null && weapon.owner===unit && weapon.vis != null)this.applyWorldVisual(weapon.vis);': 'if(weapon != null && weapon.owner===unit && weapon.vis != null)this.applyWorldVisual(weapon.vis,true);',
      '         if(record==null)\n         {\n            record={shape:new Shape(),baseMask:': '''         if(this.diagnosticMaskMode=="nomask" || (actor && this.diagnosticMaskMode=="noactors") || (!actor && this.diagnosticMaskMode=="noeffects")){
            if(record!=null)this.releaseWorldVisual(visual,record);
            return;
         }
         if(record==null)
         {
            record={shape:new Shape(),baseMask:'''
    }
    # run.py makes members public for the probe before this diagnostic patch.
    for old,new in replacements.items():
        old=old.replace('private ','public ');new=new.replace('private ','public ')
        assert source.count(old)==1,(old,source.count(old))
        source=source.replace(old,new)
    return source
