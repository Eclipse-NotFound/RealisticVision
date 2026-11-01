from pathlib import Path
import hashlib, json, shutil

MOD = Path(__file__).resolve().parents[2]
OUT = MOD / 'build/eye-boundary-output'
BASE = MOD / 'build/perf-20261102'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(MOD/'release/RealisticVisionMod.swf') == sha(BASE/'out/RealisticVisionMod.swf') == '2f44ddd1844c7dac7e8ffde4eafb256460f5fb6958675a07fb449477c4ac151f'
manifest=Path(__file__).with_name('baseline-source.json')
if manifest.exists():
    expected=json.loads(manifest.read_text('utf8'))['source']
    assert all(sha(BASE/'src'/name)==digest for name,digest in expected.items()), 'Baseline source changed; do not overwrite the frozen production lineage'
OUT.mkdir(exist_ok=True)
for name in ('baseline','candidate'):
    shutil.copytree(BASE/'src', OUT/name/'src')
shutil.copyfile(MOD/'release/RealisticVisionMod.swf', OUT/'baseline/RealisticVisionMod.swf')
(OUT/'inputs.json').write_text(json.dumps({'installed':sha(MOD/'release/RealisticVisionMod.swf'),'config':sha(MOD/'release/config.txt'),'source':{p.relative_to(BASE/'src').as_posix():sha(p) for p in (BASE/'src').rglob('*.as')}},indent=2),'utf8')
p=OUT/'candidate/src/RealisticVisionMod.as'
s=p.read_text('utf8')
def replace(a,b):
    global s
    assert s.count(a)==1, (a,s.count(a))
    s=s.replace(a,b)
replace('v0.34.2-laser-shadow','v0.34.3-eye-boundary')
replace('var moved:Boolean = Math.abs(gg.X-this.lastGX)>threshold || Math.abs(gg.Y-this.lastGY)>threshold;', '''var eye:Point = this.playerVisionEye(gg);
         var moved:Boolean = Math.abs(eye.x-this.lastGX)>threshold || Math.abs(eye.y-this.lastGY)>threshold;''')
replace('this.lastGX = gg.X;\n            this.lastGY = gg.Y;', 'this.lastGX = eye.x;\n            this.lastGY = eye.y;')
replace('var ex:Number = gg.X;\n            var ey:Number = gg.Y - gg.scY * 0.75;', '''var eye:Point = this.playerVisionEye(gg);
            var ex:Number = eye.x;
            var ey:Number = eye.y;''')
replace('      private function computeFov(loc:Location, prepared:Boolean = false):void', '''      /** Resolve the displayed eye in the same world space as terrain/visuals.
       * Re-read the timeline path: pose changes can replace nested clips. */
      private function playerVisionEye(gg:UnitPlayer):Point
      {
         try
         {
            var v:DisplayObject = gg.vis;
            var eye:DisplayObject = Object(v).osn.body.head.morda.eye as DisplayObject;
            if(v.parent != null && eye != null && v.visible && Object(v).osn.visible)
            {
               var bounds:Rectangle = eye.getBounds(eye);
               if(!bounds.isEmpty())
               {
                  var p:Point = v.parent.globalToLocal(eye.localToGlobal(new Point(
                     (bounds.left+bounds.right)*0.5,(bounds.top+bounds.bottom)*0.5)));
                  if(isFinite(p.x) && isFinite(p.y))return p;
               }
            }
         }
         catch(error:Error) {}
         return new Point(gg.X,gg.Y-gg.scY*0.75);
      }

      private function computeFov(loc:Location, prepared:Boolean = false):void''')
replace('kind=name=="fe.graph::Part" || name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet";', 'kind=name=="fe.graph::Part" ? 1 : (name=="fe.weapon::Bullet" || name=="fe.weapon::PhisBullet" || name=="fe.weapon::SmartBullet" ? 2 : 0);')
start=s.index('               // v0.34.2：激光弹')
end=s.index('\n            }\n            obj=obj.nobj;',start)
s=s[:start]+'''               // A projectile origin cannot represent a tracer, trail or beam.
               // Keep particle acceleration; clip every projectile's full geometry.
               if(this.cfgFxQuality == 0 && kind == 1)
                  this.applyTransientVisual(obj.vis);
               else
                  this.applyWorldVisual(obj.vis,kind == 2);'''+s[end:]
replace('private function applyWorldVisual(visual:DisplayObject):void','private function applyWorldVisual(visual:DisplayObject, dynamicBounds:Boolean = false):void')
replace('if(record!=null && record.lastBounds!=null && record.lastVX==visual.x && record.lastVY==visual.y','if(!dynamicBounds && record!=null && record.lastBounds!=null && record.lastVX==visual.x && record.lastVY==visual.y')
# Cached corner classifications from another eye can reintroduce the very
# silhouette offset being fixed, even when FOV itself was recomputed.
replace('Math.abs(this.eyeX-this.cornerReuseX) <= 16 && Math.abs(this.eyeY-this.cornerReuseY) <= 16','this.eyeX == this.cornerReuseX && this.eyeY == this.cornerReuseY')
p.write_text(s,'utf8',newline='\n')
print('Frozen baseline and candidate:',OUT)
