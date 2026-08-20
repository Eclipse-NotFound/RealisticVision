// v0.24.5 fogCache 采样索引映射验证：掩膜子格 (scx,scy) → fogCache 像素
const TILE=40, SUB=8, CS=TILE/SUB, PAD=4, SPX=48, SPY=26;
// 模拟 fogCache：alpha 场（模拟一张 48×26 瓦片房间）
function fogIndex(tx,ty,sx,sy){ return PAD + ty*SUB + sy, 0; } // placeholder
// 逐掩膜子格计算：wx=(x0*SUB+scx+0.5)*CS, 映射回瓦片+子格，再映射到 fogCache 坐标
function maskSubcellToFog(x0,y0,scx,scy){
  const wx=(x0*SUB+scx+0.5)*CS, wy=(y0*SUB+scy+0.5)*CS;
  const ftx=Math.floor(wx/TILE), fty=Math.floor(wy/TILE);
  const sx=Math.floor((wx-ftx*TILE)/CS), sy=Math.floor((wy-fty*TILE)/CS);
  return {ftx,fty,sx,sy, fx:PAD+ftx*SUB+sx, fy:PAD+fty*SUB+sy};
}
// 反向：fogCache 像素 (fx,fy) 应覆盖世界坐标（不含 PAD）(fx-PAD)*CS ~ (fx-PAD+1)*CS
let bad=0, n=0;
for(let x0=0;x0<SPX-4;x0++) for(let y0=0;y0<SPY-4;y0++)
  for(let scx=0;scx<SUB;scx++) for(let scy=0;scy<SUB;scy++){
    const r=maskSubcellToFog(x0,y0,scx,scy);
    n++;
    // 校验：掩膜子格中心世界坐标应落在 fogCache 像素覆盖的瓦片子格内
    const wx=(x0*SUB+scx+0.5)*CS, wy=(y0*SUB+scy+0.5)*CS;
    const cellX=(r.fx-PAD)*CS, cellY=(r.fy-PAD)*CS;
    if(wx < cellX || wx >= cellX+CS || wy < cellY || wy >= cellY+CS) bad++;
    if(r.ftx<0||r.ftx>=SPX||r.fty<0||r.fty>=SPY||r.fx<0||r.fx>=SPX*SUB+2*PAD||r.fy<0||r.fy>=SPY*SUB+2*PAD) bad++;
  }
console.log("映射验证: " + n + " 子格, 越界/错位 = " + bad + (bad===0?" PASS":" FAIL"));
// 阈值行为验证：门景 128 < 140 可见；记忆 166 / 未探索 255 / 暗部 ≥140 不可见
const cases=[["门景",128,true],["亮部",0,true],["亮部边缘",139,true],["记忆区",166,false],["未探索",255,false],["衰减环暗部",140,false]];
let ok2=true;
for(const [name,a,expect] of cases){ const got=a<140; if(got!==expect){ok2=false;console.log("阈值 FAIL: "+name+" alpha="+a);} }
console.log("阈值验证: " + (ok2?"PASS":"FAIL") + " (140 界: 门景 128 亮 / 记忆 166 暗)");
process.exit(bad===0&&ok2?0:1);
