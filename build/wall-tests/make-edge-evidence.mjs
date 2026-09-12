import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const mod=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const input=path.join(mod,'build/wall-test-output');
const out=path.join(mod,'knowledge/experiments/classic-edge-v0281');
fs.mkdirSync(out,{recursive:true});
const logs={
  'edge-baseline-results':'edges/baseline.log',
  'edge-candidate-results':'edges/candidate.log',
  'wall-candidate-results':'candidate.log',
  'training-baseline-results':'game/baseline-training.log',
  'training-candidate-results':'game/training.log'
};
for(const [name,source] of Object.entries(logs)) {
  const lines=fs.readFileSync(path.join(input,source),'utf8').split(/\r?\n/);
  fs.writeFileSync(path.join(out,name+'.txt'),lines.filter(x=>x.trim()&&!/^(PNG|DATA) /.test(x)).join('\n')+'\n');
}
for(const [source,target] of Object.entries({
  'edges/baseline-edge-contact.png':'edge-contact-v0280.png',
  'edges/candidate-edge-contact.png':'edge-contact-v0281.png',
  'game/baseline-training-classic.png':'comparison-classic-v0280.png',
  'game/training-classic.png':'comparison-classic-v0281.png',
  'game/baseline-training-classic-fog.png':'classic-fog-v0280.png',
  'game/training-classic-fog.png':'classic-fog-v0281.png',
  'game/baseline-training-current-fog.png':'current-fog-v0280.png',
  'game/training-current-fog.png':'current-fog-v0281.png',
  'game/training-data.json':'training-data-v0281.json',
  'game/training-comparison.json':'training-comparison.json'
}))fs.copyFileSync(path.join(input,source),path.join(out,target));
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(mod,p))).digest('hex');
fs.writeFileSync(path.join(out,'fingerprints.json'),JSON.stringify({date:'2026-09-12',baselineCommit:'6c0170e',status:'candidate-not-deployed',source:hash('src/RealisticVisionMod.as'),testSwf:hash('build/RealisticVisionMod_test.swf'),releaseSwf:hash('release/RealisticVisionMod.swf'),config:hash('release/config.txt'),game:hash('../../pfe.swf'),testBytes:fs.statSync(path.join(mod,'build/RealisticVisionMod_test.swf')).size},null,2)+'\n');
const images={};
for(const version of ['v0280','v0281'])for(const kind of ['comparison-classic','classic-fog']) {
  images[kind+'-'+version]='data:image/png;base64,'+fs.readFileSync(path.join(out,kind+'-'+version+'.png')).toString('base64');
}
const html=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>classic 小墙块阴影修复对照</title>
<style>body{margin:0;background:#151917;color:#edf3ee;font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1180px;margin:auto;padding:34px 22px}h1{font-size:28px;line-height:1.3;margin:8px 0 15px}p,small{color:#b9c7bd}.facts{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0}.facts div{background:#23342a;padding:14px 22px;border-radius:8px}.facts b{display:block;font-size:25px;color:#c4eed3}.controls{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin:22px 0 14px}button{font:inherit;border:1px solid #708b78;border-radius:6px;padding:6px 14px;background:#24382a;color:#edf3ee;cursor:pointer}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#1e2822;border:1px solid #435b49;border-radius:8px;overflow:hidden}figcaption{padding:12px 15px}svg{display:block;width:100%;height:auto;background:black}.outline{fill:none;stroke:#90ffad;stroke-width:1;stroke-dasharray:3 2;display:none}footer{margin-top:25px;border-top:1px solid #435b49;padding-top:14px;color:#b9c7bd}input{accent-color:#96d4a7}@media(max-width:760px){.pair{grid-template-columns:1fr}main{padding:20px 12px}h1{font-size:24px}}</style>
<main><small>RealisticVision · v0.28.1 修复候选 · 尚未部署</small><h1>上方小墙块：阴影接回墙角</h1><p>同一个训练房间、同一玩家位置。修复 classic 的视野与记忆阴影位置，保留墙内原版明暗层次。</p>
<div class="facts"><div><b>约 20 → 不足 1 像素</b>小墙顶端轮廓偏差</div><div><b>39 / 39</b>原有墙内阴影检查通过</div><div><b>0 像素变化</b>同场景 current 阴影图</div></div>
<div class="controls"><button id="zoom">查看完整房间</button><label><input id="fog" type="checkbox"> 只看阴影</label><label><input id="outline" type="checkbox"> 标出小墙块</label></div>
<div class="pair"><figure><figcaption>修复前 · v0.28.0</figcaption><svg viewBox="720 300 430 240"><image id="before" width="1920" height="1000"></image><rect class="outline" x="920" y="400" width="40" height="80"></rect></svg></figure><figure><figcaption>修复后 · v0.28.1</figcaption><svg viewBox="720 300 430 240"><image id="after" width="1920" height="1000"></image><rect class="outline" x="920" y="400" width="40" height="80"></rect></svg></figure></div>
<p>观察小墙块右上角：旧版的暗区提前向左收回，修复后接到墙角。classic 仍使用整格柔和过渡；正在投影的薄墙旁仍会有约半格的渐变，未改成 current 的细线投影。</p>
<footer>画面由独立游戏副本实际绘制。房间与照明输入已核对一致，场景灯光和动画的瞬间画面可能不同；“只看阴影”可排除这些差异。两模式墙内像素与 v0.28.0 一致，原版照明记录改写为零。完整说明及复验入口见上级测试报告。</footer></main>
<script>const images=${JSON.stringify(images)};let full=false;function render(){const kind=document.getElementById('fog').checked?'classic-fog':'comparison-classic';document.getElementById('before').setAttribute('href',images[kind+'-v0280']);document.getElementById('after').setAttribute('href',images[kind+'-v0281']);document.querySelectorAll('svg').forEach(s=>s.setAttribute('viewBox',full?'0 0 1920 1000':'720 300 430 240'));document.querySelectorAll('.outline').forEach(s=>s.style.display=document.getElementById('outline').checked?'block':'none');}document.getElementById('zoom').onclick=function(){full=!full;this.textContent=full?'回到小墙块':'查看完整房间';render()};document.getElementById('fog').onchange=render;document.getElementById('outline').onchange=render;render();</script></html>`;
fs.writeFileSync(path.join(out,'comparison.html'),html);
console.log('Saved classic-edge-v0281 evidence and comparison.html');
