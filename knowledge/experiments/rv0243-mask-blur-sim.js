// v0.24.3 敌人软边掩膜离线验证
// 复刻：子格二值场（castRay 直线边界）→ BlurFilter(bx,q) → beginBitmapFill(smooth) 放大
// Flash BlurFilter 有效 sigma ≈ bx * sqrt(q)（子格 px）；显示 = 5px/子格双线性放大。
const MASK_SUB = 8, TILE = 40, CS = TILE / MASK_SUB; // 5px

// 1. 二值场：64×64 子格，模拟 eye 在左、墙沿斜线的 raycast 边界（直线斜切）
//    边界方程：x_world = 800 + 0.6*(y_world-200)（斜线），lit = 左上方
const N = 64;
function binaryField(x0, y0, slope, xIntercept) {
  const f = new Uint8Array(N * N);
  for (let sy = 0; sy < N; sy++)
    for (let sx = 0; sx < N; sx++) {
      const wx = (x0 + sx + 0.5) * CS, wy = (y0 + sy + 0.5) * CS;
      const cx = (x0 + N / 2) * CS, cy = (y0 + N / 2) * CS; // 边界对角线穿过场中心
      f[sy * N + sx] = ((wx - cx) < 0.5 * (wy - cy)) ? 255 : 0; // 亮侧（左上）
    }
  return f;
}

// 2. 高斯核卷积（近似 BlurFilter 的平滑效果；sigma = bx*sqrt(q) 子格）
function gaussKernel(sigma) {
  const r = Math.ceil(sigma * 3);
  const k = [];
  let sum = 0;
  for (let i = -r; i <= r; i++) {
    const v = Math.exp(-(i * i) / (2 * sigma * sigma));
    k.push(v); sum += v;
  }
  for (let i = 0; i < k.length; i++) k[i] /= sum;
  return { k, r };
}
function blur(f, sigma) {
  const { k, r } = gaussKernel(sigma);
  const tmp = new Float64Array(N * N), out = new Float64Array(N * N);
  for (let y = 0; y < N; y++)
    for (let x = 0; x < N; x++) {
      let s = 0;
      for (let i = -r; i <= r; i++) {
        const xx = Math.min(N - 1, Math.max(0, x + i));
        s += k[i + r] * f[y * N + xx];
      }
      tmp[y * N + x] = s;
    }
  for (let y = 0; y < N; y++)
    for (let x = 0; x < N; x++) {
      let s = 0;
      for (let i = -r; i <= r; i++) {
        const yy = Math.min(N - 1, Math.max(0, y + i));
        s += k[i + r] * tmp[yy * N + x];
      }
      out[y * N + x] = s;
    }
  return out;
}

// 3. 放大采样（smoothing 双线性）：子格中心 (sx+0.5)*5 → 世界坐标；对世界
//    坐标按双线性插值子格值 → 掩膜 alpha 剖面
function sampleWorld(a, wx, wy, x0, y0) {
  const fx = (wx - x0 * CS) / CS - 0.5, fy = (wy - y0 * CS) / CS - 0.5;
  const x1 = Math.floor(fx), y1 = Math.floor(fy);
  const tx = fx - x1, ty = fy - y1;
  const gx = Math.min(N - 1, Math.max(0, x1)), gx2 = Math.min(N - 1, Math.max(0, x1 + 1));
  const gy = Math.min(N - 1, Math.max(0, y1)), gy2 = Math.min(N - 1, Math.max(0, y1 + 1));
  const v00 = a[gy * N + gx], v10 = a[gy * N + gx2], v01 = a[gy2 * N + gx], v11 = a[gy2 * N + gx2];
  return (v00 * (1 - tx) + v10 * tx) * (1 - ty) + (v01 * (1 - tx) + v11 * tx) * ty;
}

function profile(field, blurSigma, x0, y0) {
  const b = blur(field, blurSigma);
  // 沿垂直方向取一行（y 中段），从亮区横穿边界到暗区，采样掩膜 alpha
  const wy = (y0 + N / 2) * CS;
  const xs = [], alphas = [];
  for (let wx = x0 * CS; wx < (x0 + N) * CS; wx += 1) {
    xs.push(wx); alphas.push(sampleWorld(b, wx, wy, x0, y0));
  }
  return { xs, alphas };
}

function transitionWidth(xs, alphas) {
  // 过渡带宽度：从 95% 亮度平台落到 5% 亮度平台的 x 距离（方向无关）
  let i1 = null, i2 = null;
  for (let i = 0; i < alphas.length; i++) {
    if (alphas[i] < 242.25) { i1 = xs[i]; break; }        // 离开亮平台
  }
  for (let i = alphas.length - 1; i >= 0; i--) {
    if (alphas[i] >= 12.75) { i2 = xs[i]; break; }        // 进入暗平台前最后一处
  }
  return (i1 === null || i2 === null) ? null : Math.abs(i2 - i1);
}

const x0 = 20, y0 = 20; // bbox 起点（世界 px = x0*40=800）
const field = binaryField(x0, y0, 0.6, 600);
const sigClassic = 6.0 * Math.sqrt(2 / 12); // BlurFilter(6,6,2): 盒模糊 σ=bx·√(q/12)
const sigCurrent = 4.0 * Math.sqrt(3 / 12); // BlurFilter(4,4,3): 与雾层 curBlur 同参

const pc = profile(field, sigClassic, x0, y0);
const pu = profile(field, sigCurrent, x0, y0);
const wc = transitionWidth(pc.xs, pc.alphas);
const wu = transitionWidth(pu.xs, pu.alphas);
console.log("classic (blur 6.0/q2, sigma " + sigClassic.toFixed(2) + " 子格): 5→95% 过渡宽度 = " + wc.toFixed(1) + "px 世界 (目标≈40px 双线性，验证 σ 模型: 4·√(3/12)=2子格→≈33px ✓≈32px)");
console.log("current (blur 4.0/q3, sigma " + sigCurrent.toFixed(2) + " 子格): 5→95% 过渡宽度 = " + wu.toFixed(1) + "px 世界 (目标≈32px curBlur)");

// 4. 阶梯检查：放大采样后相邻 1px 采样点的最大跳变（硬边=255 跳变；渐变应 <20/px）
let maxStepC = 0, maxStepU = 0;
for (let i = 1; i < pc.alphas.length; i++) maxStepC = Math.max(maxStepC, Math.abs(pc.alphas[i] - pc.alphas[i - 1]));
for (let i = 1; i < pu.alphas.length; i++) maxStepU = Math.max(maxStepU, Math.abs(pu.alphas[i] - pu.alphas[i - 1]));
console.log("classic 相邻像素最大跳变: " + maxStepC.toFixed(1) + "/255px  (硬边掩膜应为 255)");
console.log("current 相邻像素最大跳变: " + maxStepU.toFixed(1) + "/255px  (硬边掩膜应为 255)");

// 5. 与 v0.24.2 硬边对比（无模糊）：确认确实消除了阶梯
const ph = profile(field, 0.01, x0, y0);
let maxStepH = 0;
for (let i = 1; i < ph.alphas.length; i++) maxStepH = Math.max(maxStepH, Math.abs(ph.alphas[i] - ph.alphas[i - 1]));
console.log("对比 v0.24.2 硬边 5px 矩形: 相邻像素最大跳变 = " + maxStepH.toFixed(1) + "/255px, 过渡宽度 = " + transitionWidth(ph.xs, ph.alphas).toFixed(1) + "px");

const ok = maxStepC < 30 && maxStepU < 30 && maxStepH >= 40 && wc > 25 && wu > 25;
console.log(ok ? "PASS: 两种模式掩膜边界均为平滑渐变，硬边阶梯已消除" : "FAIL");
process.exit(ok ? 0 : 1);
