"""Read-only syntax, image-reference and test-cleanup checks for the evidence page."""
from pathlib import Path
import itertools,json,re,subprocess
from PIL import Image
MOD=Path(__file__).resolve().parents[2]
ROOT=MOD/'knowledge/experiments/wall-options-v0311-20261015'
html=(ROOT/'comparison.html').read_text(encoding='utf-8')
script=re.search(r'<script>(.*?)</script>',html,re.S).group(1)
result=subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True)
assert result.returncode==0,result.stderr
images=[]
for material,variant,position,mode,view in itertools.product(['game','game-rock'],['baseline','off','on'],['upper','lower'],['classic','current'],['detail','stage']):
    path=ROOT/material/(variant+'-'+position+'-'+mode+'-'+view+'.png')
    with Image.open(path) as image:image.verify()
    images.append(str(path.relative_to(ROOT)))
assert (ROOT.parent/'2026-10-15-wall-bright-option.md').exists()
assert not list((MOD/'build/wall-options-output').rglob('test.xml')),'Test descriptor was left behind'
print(json.dumps({'javascript_syntax':'passed','linked_images':len(images),'report_link':'present','test_descriptors':0},indent=2))
