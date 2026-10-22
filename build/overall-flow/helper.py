"""D40 helper equivalence adds alpha-only <-> general foreground transitions."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;MOD=HERE.parents[1]
s=(MOD/'build/long-frame/helper.py').read_text(encoding='utf-8').replace('long-frame-output','overall-flow-output').replace('D39','D40')
s=s.replace("spec=importlib.util.spec_from_file_location('d39trace',HERE/'trace.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);r=t.r", "spec=importlib.util.spec_from_file_location('d40measure',HERE/'measure.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);r=t.inv.r")
anchor="  at=s.index('         for each(var zoom:Number')"
s=s.replace(anchor,'''  s=s.replace('         known=true;bright=true;intensity=.35;', '''+repr('''         known=true;bright=false;intensity=.35;
         for(var change:int=0;change<12;change++){
            pixels.fillRect(new Rectangle(80,80,40,20),uint((change*23%256)<<24)|uint(change*913));
            compare("direct alpha dynamic color "+change);
            var extraShape:Shape=new Shape();extraShape.graphics.beginFill(0x234567,.5);extraShape.graphics.drawRect(88,88,45,35);extraShape.graphics.endFill();front.addChild(extraShape);
            compare("fallback after direct alpha "+change);front.removeChild(extraShape);
            compare("direct after fallback "+change);
            var saved:ColorTransform=front.transform.colorTransform;front.transform.colorTransform=new ColorTransform(1,1,1,.73);
            compare("transformed fallback "+change);front.transform.colorTransform=saved;
            compare("untransformed again "+change);
         }
         known=true;bright=true;intensity=.35;''')+''')
'''+anchor)
exec(compile(s,str(HERE/'helper.py'),'exec'),globals())
