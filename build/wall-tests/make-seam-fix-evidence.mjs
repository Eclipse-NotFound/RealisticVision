// v0.28.2 repair evidence, kept separate from the earlier failed-candidate diagnosis.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const mod=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const input=path.join(mod,'build/wall-test-output'),game=path.join(input,'game');
const out=path.join(mod,'knowledge/experiments/classic-seams-v0282');
if(fs.existsSync(path.join(out,'fingerprints.json')))throw Error('Evidence already archived; choose a new directory.');
const clean=s=>s.replace(/\r/g,'').trimEnd()+'\n';
const read=p=>fs.readFileSync(p,'utf8');
const report=JSON.parse(read(path.join(game,'seam-measurements.json')));
if(!report.identical_inputs || report.validation!=='repair')throw Error('Run inspect-seams.py --repair first.');
for(const prefix of ['baseline-','']) {
  const log=read(path.join(game,prefix+'training-seams.log'));
  if(!log.includes('GAME_PROBE CAPTURED training seams') || log.includes('GAME_PROBE FAIL'))throw Error('Incomplete game capture');
}
for(const [name,marker] of [['candidate.log','WALL_TESTS PASS'],['edges/candidate.log','WALL_EDGE_TESTS PASS'],['seams/candidate.log','WALL_SEAM_TESTS PASS']])
  if(!read(path.join(input,name)).includes(marker))throw Error('Missing fixture PASS: '+name);
fs.mkdirSync(out,{recursive:true});
for(const prefix of ['baseline-','']) {
  for(const name of ['seams-data.json','seam-measurements.json'])
    fs.writeFileSync(path.join(out,prefix+name),clean(read(path.join(game,prefix+name))));
  for(const pos of ['lower','upper'])for(const mode of ['classic','current'])for(const suffix of ['', '-fog']) {
    if(mode==='current' && suffix==='')continue;
    const name=prefix+`seams-${pos}-${mode}${suffix}.png`;
    fs.copyFileSync(path.join(game,name),path.join(out,name));
  }
  const log=read(path.join(game,prefix+'training-seams.log')).split(/\r?\n/).filter(s=>s.trim()&&!/^(PNG|DATA) /.test(s)).join('\n');
  fs.writeFileSync(path.join(out,prefix+'game-results.txt'),clean(log));
}
for(const pos of ['lower','upper'])for(const suffix of ['', '-fog']) {
  const name=`seams-${pos}-native${suffix}.png`;fs.copyFileSync(path.join(game,name),path.join(out,name));
}
for(const [from,to] of [['candidate.log','wall-results.txt'],['edges/candidate.log','edge-results.txt'],['seams/candidate.log','seam-results.txt'],['test-swf-as3.txt','test-swf-classes.txt']]) {
  const log=read(path.join(input,from)).split(/\r?\n/).filter(s=>s.trim()&&!s.startsWith('PNG ')).join('\n');
  fs.writeFileSync(path.join(out,to),clean(log));
}
const hashes={};
for(const name of ['src/RealisticVisionMod.as','build/RealisticVisionMod_test.swf','release/RealisticVisionMod.swf','release/config.txt','../../pfe.swf'])
  hashes[name]=crypto.createHash('sha256').update(fs.readFileSync(path.join(mod,name))).digest('hex');
fs.writeFileSync(path.join(out,'fingerprints.json'),JSON.stringify({date:'2026-09-19',baselineCommit:'ee7988c',candidateVersion:'v0.28.2',status:'repair-validated-test-build-not-deployed',hashes},null,2)+'\n');
fs.writeFileSync(path.join(out,'comparison.html'),`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>classic 墙边修复对照</title>
<style>body{margin:0;background:#171b19;color:#edf2ee;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1480px;margin:auto;padding:28px 24px}h1{font-size:28px}p,small{color:#c5d0c8}.status{padding:12px 18px;background:#243e30;border-left:4px solid #91cca7}.controls{display:flex;gap:22px;flex-wrap:wrap;align-items:center;margin:22px 0}select{font:inherit;background:#29362d;color:inherit;padding:6px;border:1px solid #69816f}.pair{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0;border:1px solid #425b49;background:#202a23}figcaption{padding:10px 12px}svg{display:block;width:100%;background:#000}footer{border-top:1px solid #425b49;margin-top:24px;padding-top:14px;color:#bdc9c1}@media(max-width:950px){.pair{grid-template-columns:1fr}main{padding:18px 12px}}</style>
<main><small>RealisticVision · v0.28.2 测试候选 · 2026-09-19</small><h1>墙边与拐角接回同一条阴影</h1>
<p class="status">修复和回归已完成，尚未部署。墙面沿用原版黑芯与基础渐变；墙和地板在交界处共享遮挡过渡。</p>
<div class="controls"><label>位置 <select id="area"><option value="lower">梯子下层</option><option value="upper">回到上层</option></select></label><label><input id="fog" type="checkbox"> 只看阴影</label><label><input id="full" type="checkbox"> 完整房间</label></div>
<div class="pair"><figure><figcaption>原版光照参照</figcaption><svg><image id="native" width="1920" height="1000"></image></svg></figure><figure><figcaption>修复前候选 · v0.28.1</figcaption><svg><image id="baseline" width="1920" height="1000"></image></svg></figure><figure><figcaption>修复后候选 · v0.28.2</figcaption><svg><image id="candidate" width="1920" height="1000"></image></svg></figure></div>
<p id="finding"></p><p>接缝夹具 8/8、小墙 10 方向检查通过；小墙端点误差 0.25 像素。完整场景 current 纯阴影逐像素相同，classic 没有抬亮原版墙面或黑芯。</p>
<footer>独立 AIR 副本的实际截图，未经修图；同一照明、几何、视野与探索输入。原版参照没有记忆压暗。动画可能不同，可切换纯阴影排除影响。训练房位置依据用户截图估计，未重放用户精确存档；原版自身宽亮面及 classic 粗格渐变保留。正式 release 仍为独立念力热修复 v0.28.0-grabfix.1。</footer></main>
<script>const area=document.querySelector('#area'),fog=document.querySelector('#fog'),full=document.querySelector('#full');function update(){const pos=area.value,suffix=fog.checked?'-fog':'';document.querySelector('#native').setAttribute('href','seams-'+pos+'-native'+suffix+'.png');document.querySelector('#baseline').setAttribute('href','baseline-seams-'+pos+'-classic'+suffix+'.png');document.querySelector('#candidate').setAttribute('href','seams-'+pos+'-classic'+suffix+'.png');document.querySelectorAll('svg').forEach(s=>s.setAttribute('viewBox',full.checked?'0 0 1920 1000':'120 560 680 400'));document.querySelector('#finding').textContent=pos==='lower'?'下层：墙边最大额外亮度跳变 166 → 11；地板内部格线最大相邻差 5。':'上层：墙边最大额外亮度跳变 84 → 4；地板内部格线最大相邻差 6。';}for(const el of [area,fog,full])el.addEventListener('change',update);update();</script></html>\n`);
console.log(out);
