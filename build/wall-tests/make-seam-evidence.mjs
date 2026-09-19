// Archive only completed, comparable captures; do not overwrite earlier reports.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const mod=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const input=path.join(mod,'build/wall-test-output');
const out=path.join(mod,'knowledge/experiments/classic-seams-20260919');
if(fs.existsSync(path.join(out,'fingerprints.json')))throw Error('This dated evidence is already archived; choose a new output directory for a new experiment.');
const read=p=>fs.readFileSync(path.join(input,p),'utf8');
const clean=s=>s.replace(/\r/g,'').trimEnd()+'\n';
for(const prefix of ['baseline-','']) {
  if(!read('game/'+prefix+'training-seams.log').includes('GAME_PROBE CAPTURED training seams (visual diagnosis only)'))throw Error('Incomplete game capture');
}
const measurements=JSON.parse(read('game/seam-measurements.json'));
if(!measurements.identical_inputs)throw Error('Inputs differ');
fs.mkdirSync(out,{recursive:true});
for(const prefix of ['baseline-','']) {
  for(const name of ['seams-data.json','seam-measurements.json'])fs.writeFileSync(path.join(out,prefix+name),clean(read('game/'+prefix+name)));
  for(const position of ['lower','upper'])for(const mode of ['classic','current'])for(const type of ['', '-fog']) {
    if(mode==='current' && type==='')continue;
    const name=prefix+'seams-'+position+'-'+mode+type+'.png';
    fs.copyFileSync(path.join(input,'game',name),path.join(out,name));
  }
  const gameLog=read('game/'+prefix+'training-seams.log').split(/\r?\n/).filter(s=>s.trim()&&!/^(PNG|DATA) /.test(s)).join('\n')+'\n';
  fs.writeFileSync(path.join(out,prefix+'game-results.txt'),clean(gameLog));
  fs.writeFileSync(path.join(out,prefix+'fixture-results.txt'),clean(read('seams/'+(prefix?'baseline.log':'candidate.log'))));
}
for(const position of ['lower','upper'])for(const type of ['', '-fog']) {
  const name='seams-'+position+'-native'+type+'.png';
  fs.copyFileSync(path.join(input,'game',name),path.join(out,name));
}
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const files=['src/RealisticVisionMod.as','build/RealisticVisionMod_test.swf','release/RealisticVisionMod.swf','release/config.txt','../../pfe.swf'];
const fingerprints={date:'2026-09-19',baselineCommit:'6c0170e',candidateCommit:'ee7988c',status:'diagnosed-candidate-has-seam-regression-not-release-ready',hashes:{}};
for(const file of files)fingerprints.hashes[file]=hash(path.join(mod,file));
fs.writeFileSync(path.join(out,'fingerprints.json'),JSON.stringify(fingerprints,null,2)+'\n');
const html=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>classic 墙边检查对照</title>
<style>body{margin:0;background:#151917;color:#eef3ef;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1480px;margin:auto;padding:28px 24px}h1{font-size:28px;line-height:1.4}p,small{color:#c0cbc2}.status{padding:12px 18px;background:#423525;border-left:4px solid #edc582}.controls{display:flex;gap:20px;flex-wrap:wrap;align-items:center;margin:22px 0}select{font:inherit;background:#28352c;color:inherit;padding:6px;border:1px solid #637967}.pair{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0;border:1px solid #435b49;background:#202a23}figcaption{padding:10px 12px}svg{display:block;width:100%;background:#000}footer{border-top:1px solid #435b49;margin-top:24px;padding-top:14px;color:#c0cbc2}.marks{display:none;fill:none;stroke:#ffbc70;stroke-width:1;stroke-dasharray:3 2}@media(max-width:950px){.pair{grid-template-columns:1fr}main{padding:18px 12px}}</style>
<main><small>RealisticVision · 2026-09-19 · 同一训练房、同一探索路线</small><h1>墙边亮面与新增接缝，分开看</h1>
<p class="status">检查结论：v0.28.1 候选新增了墙与地板的亮度断层，尚不能作为已验候选部署。本页是问题对照，没有实施新修复。</p>
<p>原版也有沿墙的亮面和向黑芯过渡的渐变。候选版在部分转角把墙与地板接成了两种亮度；上次只看墙内和小墙投影端点，未覆盖这一边界。</p>
<div class="controls"><label>位置 <select id="area"><option value="lower">梯子下层，观察左上墙沿</option><option value="upper">回到上层，观察梯子口拐角</option></select></label><label><input id="fog" type="checkbox"> 只看阴影</label><label><input id="marks" type="checkbox"> 标出测量区域</label><label><input id="full" type="checkbox"> 完整房间</label></div>
<div class="pair"><figure><figcaption>原版照明参照</figcaption><svg><image id="native" width="1920" height="1000"></image><rect class="marks" x="150" y="625" width="170" height="80"></rect></svg></figure><figure><figcaption>正式版对应源码 · v0.28.0</figcaption><svg><image id="baseline" width="1920" height="1000"></image><rect class="marks" x="150" y="625" width="170" height="80"></rect></svg></figure><figure><figcaption>未部署候选 · v0.28.1</figcaption><svg><image id="candidate" width="1920" height="1000"></image><rect class="marks" x="150" y="625" width="170" height="80"></rect></svg></figure></div>
<p id="finding"></p><footer>来自独立 AIR 游戏副本的实际画面；原图未做修图。输入含墙体、原版照明、视野和探索记忆，已逐项核对相同。原版参照没有视野记忆压暗，不能拿整图平均亮度比较优劣。玩家位置依截图估计，沿途按原版更新照明；没有重放用户的准确存档、移动过程或相机。场景动画可能不同，纯阴影对照可排除动画影响。正式 SWF、配置、游戏本体与用户存档均未修改。</footer></main>
<script>function render(){const area=document.getElementById('area').value;const type=document.getElementById('fog').checked?'-fog':'';const full=document.getElementById('full').checked;document.getElementById('native').setAttribute('href','seams-'+area+'-native'+type+'.png');document.getElementById('baseline').setAttribute('href','baseline-seams-'+area+'-classic'+type+'.png');document.getElementById('candidate').setAttribute('href','seams-'+area+'-classic'+type+'.png');document.querySelectorAll('svg').forEach(x=>x.setAttribute('viewBox',full?'0 0 1920 1000':area==='lower'?'130 560 500 410':'130 580 590 245'));document.querySelectorAll('.marks').forEach(x=>x.style.display=document.getElementById('marks').checked?'block':'none');document.getElementById('finding').textContent=area==='lower'?'左上墙沿的最大额外亮度跳变：正式版 3，候选 166（0–255）。候选墙面仍亮，紧贴墙面的地板先变暗，接缝因此显得突出。':'梯子右侧拐角的最大额外亮度跳变：正式版 4，候选 84（0–255）。墙内像素本身未变，变化发生在交界外侧。';}document.querySelectorAll('input,select').forEach(x=>x.onchange=render);render();</script></html>`;
fs.writeFileSync(path.join(out,'comparison.html'),html);
console.log(out);
