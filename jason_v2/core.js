// Core helpers: math, easing, deterministic noise, camera, drawing primitives, effects.
const W = 1080, H = 1920, FPS = DATA.fps;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const INK = '#1d1326';
const TAU = Math.PI * 2;

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, x) => clamp((x - a) / (b - a));
const E = {
  lin: t => t,
  io: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  sio: t => t * t * (3 - 2 * t),
  out: t => 1 - Math.pow(1 - t, 3),
  out5: t => 1 - Math.pow(1 - t, 5),
  in: t => t * t * t,
  in2: t => t * t,
  back: t => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  elastic: t => t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (TAU / 3)) + 1,
  bounce: t => { const n = 7.5625, d = 2.75; if (t < 1 / d) return n * t * t; if (t < 2 / d) return n * (t -= 1.5 / d) * t + .75; if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + .9375; return n * (t -= 2.625 / d) * t + .984375; },
};
// value between keyframes: kf(t, [[t0,v0],[t1,v1,ease],...])
function kf(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [ta, va] = keys[i - 1], [tb, vb, e] = keys[i];
      const u = tb > ta ? (t - ta) / (tb - ta) : 1;
      return lerp(va, vb, (e || E.io)(u));
    }
  }
  return keys[keys.length - 1][1];
}
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function hash2(a, b) { return hash(a * 57.31 + b * 113.7); }
function noise1(x) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; }
const pulse = (t, a, d) => (t >= a && t < a + d) ? 1 - (t - a) / d : 0;   // 1 -> 0 decay after a
const bump = (t, a, b) => (t > a && t < b) ? Math.sin(Math.PI * (t - a) / (b - a)) : 0;

// --- word timing / lip-sync data
const WD = DATA.words;
const WS = i => WD[i].s, WE = i => WD[i].e;
function mouthAt(sp, t) {
  const f = t * FPS, i = Math.floor(f), u = f - i, m = DATA.mouth[sp];
  if (i < 0 || i >= m.length - 1) return 0;
  return lerp(m[i], m[i + 1], u);
}
function roundAt(t) {          // vowel roundness: pseudo-random per syllable
  return clamp(0.5 + 0.5 * noise1(t * 7.3), 0, 1) * 0.8;
}
// word time by (scene, index-in-phrase), 1-based like the script
const _WI = {}; WD.forEach((w, k) => { _WI[w.sc + ':' + w.i] = k; });
const ws = (sc, i) => WD[_WI[sc + ':' + i]].s, we = (sc, i) => WD[_WI[sc + ':' + i]].e;
function talking(sp, t) { return DATA.quotes.some(q => q.sp === sp && t >= q.s - 0.05 && t <= q.e + 0.06); }
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
function mixHex(a, b, u) {
  const A = hexRgb(a), B = hexRgb(b);
  return '#' + A.map((v, k) => Math.round(lerp(v, B[k], u)).toString(16).padStart(2, '0')).join('');
}

// --- camera: cam = {x, y, z, r} world point at screen centre, zoom, rotation (rad)
function applyCam(c, cam) {
  c.translate(W / 2, H / 2);
  if (cam.r) c.rotate(cam.r);
  c.scale(cam.z, cam.z);
  c.translate(-cam.x, -cam.y);
}
function shake(t, amp, freq = 18, seed = 0) {
  return [amp * (noise1(t * freq + seed) * .8 + noise1(t * freq * 2.3 + seed + 50) * .4),
          amp * (noise1(t * freq + seed + 100) * .8 + noise1(t * freq * 2.1 + seed + 150) * .4)];
}

// --- drawing primitives
function P(c) { c.beginPath(); return c; }
function fillStroke(c, fill, lw = 6, stroke = INK) {
  if (fill) { c.fillStyle = fill; c.fill(); }
  if (lw) { c.lineWidth = lw; c.strokeStyle = stroke; c.lineJoin = 'round'; c.lineCap = 'round'; c.stroke(); }
}
function ellipse(c, x, y, rx, ry, fill, lw = 6, rot = 0) {
  c.beginPath(); c.ellipse(x, y, Math.max(.1, rx), Math.max(.1, ry), rot, 0, TAU); fillStroke(c, fill, lw);
}
function circle(c, x, y, r, fill, lw = 6) { ellipse(c, x, y, r, r, fill, lw); }
function rrectP(c, x, y, w, h, r) {      // rounded-rect sub-path (no beginPath), for compound paths
  r = Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2);
  c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function rrect(c, x, y, w, h, r) {
  r = Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2);
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath(); return c;
}
function line(c, pts, lw = 6, col = INK) {
  c.beginPath(); c.moveTo(pts[0], pts[1]);
  for (let i = 2; i < pts.length; i += 2) c.lineTo(pts[i], pts[i + 1]);
  c.lineWidth = lw; c.strokeStyle = col; c.lineCap = 'round'; c.lineJoin = 'round'; c.stroke();
}
function poly(c, pts, fill, lw = 6) {
  c.beginPath(); c.moveTo(pts[0], pts[1]);
  for (let i = 2; i < pts.length; i += 2) c.lineTo(pts[i], pts[i + 1]);
  c.closePath(); fillStroke(c, fill, lw);
}
// thick limb with outline: polyline drawn twice (ink then colour)
function limb(c, pts, w, col, lw = 6) {
  line(c, pts, w + lw * 2, INK); line(c, pts, w, col);
}
function glow(c, x, y, r, col, a = 1) {
  const g = c.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)');
  c.save(); c.globalAlpha *= a; c.globalCompositeOperation = 'lighter';
  c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); c.restore();
}
function vgrad(c, y0, y1, stops) {
  const g = c.createLinearGradient(0, y0, 0, y1);
  stops.forEach(([o, col]) => g.addColorStop(o, col)); return g;
}
function withT(c, x, y, s, r, fn) {
  c.save(); c.translate(x, y); if (r) c.rotate(r); if (s !== 1) c.scale(s, s); fn(); c.restore();
}

// --- text
function font(px, fam = 'Rubik') {
  if (fam === 'Rubik') return `900 ${px}px Rubik`;
  if (fam === 'Mont') return `900 ${px}px Mont`;
  return `${px}px ${fam}`;
}
function text(c, s, x, y, px, fill = '#fff', o = {}) {
  c.save();
  c.font = font(px, o.fam || 'Rubik');
  c.textAlign = o.align || 'center'; c.textBaseline = o.base || 'middle';
  if (o.ls) c.letterSpacing = o.ls + 'px';
  if (o.stroke !== 0) {
    c.lineJoin = 'round'; c.miterLimit = 2;
    c.lineWidth = o.stroke || px * .2; c.strokeStyle = o.scol || INK; c.strokeText(s, x, y);
  }
  if (o.shadow) { c.fillStyle = o.shadow; c.fillText(s, x + px * .06, y + px * .08); }
  c.fillStyle = fill; c.fillText(s, x, y);
  c.restore();
}

// --- effects (screen space)
function speedLines(c, cx, cy, t, o = {}) {
  const n = o.n || 70, r0 = o.r0 || 360, col = o.col || 'rgba(255,255,255,0.85)';
  c.save(); c.fillStyle = col;
  for (let i = 0; i < n; i++) {
    const a = hash(i * 3.1 + Math.floor(t * 20) * 0.37) * TAU;
    const len = 300 + hash(i * 7.7 + Math.floor(t * 20)) * 900;
    const w = (o.w || 10) * (0.4 + hash(i * 1.3));
    const r1 = r0 + hash(i * 5.1 + Math.floor(t * 20) * 1.1) * 200;
    const ca = Math.cos(a), sa = Math.sin(a), px = -sa * w, py = ca * w;
    c.beginPath();
    c.moveTo(cx + ca * r1, cy + sa * r1);
    c.lineTo(cx + ca * (r1 + len) + px, cy + sa * (r1 + len) + py);
    c.lineTo(cx + ca * (r1 + len) - px, cy + sa * (r1 + len) - py);
    c.closePath(); c.fill();
  }
  c.restore();
}
function sunburst(c, cx, cy, t, col1, col2, n = 18, spin = 0.3) {
  c.save(); c.fillStyle = col1; c.fillRect(-W, -H, W * 3, H * 3); c.fillStyle = col2;
  const R = 3000;
  for (let i = 0; i < n; i++) {
    const a0 = i / n * TAU + t * spin, a1 = a0 + TAU / n / 2;
    c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx + Math.cos(a0) * R, cy + Math.sin(a0) * R);
    c.lineTo(cx + Math.cos(a1) * R, cy + Math.sin(a1) * R); c.closePath(); c.fill();
  }
  c.restore();
}
function vignette(c, a = 0.55, col = '0,0,0') {
  const g = c.createRadialGradient(W / 2, H / 2, H * .25, W / 2, H / 2, H * .75);
  g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(1, `rgba(${col},${a})`);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
}
function flash(c, a, col = '255,255,255') {
  if (a <= 0) return; c.fillStyle = `rgba(${col},${clamp(a)})`; c.fillRect(0, 0, W, H);
}
function halftoneTint(c, col, a) {
  if (a <= 0) return; c.save(); c.globalAlpha = a; c.globalCompositeOperation = 'multiply';
  c.fillStyle = col; c.fillRect(0, 0, W, H); c.restore();
}
// particles: pure function of time. spawn(i) -> {t0, x, y, vx, vy, life, ...}
function particles(c, t, n, spawn, draw) {
  for (let i = 0; i < n; i++) {
    const p = spawn(i); const age = t - p.t0;
    if (age < 0 || age > p.life) continue;
    draw(c, p, age, age / p.life, i);
  }
}
// sparkle star
function star4(c, x, y, r, col, rot = 0) {
  c.save(); c.translate(x, y); c.rotate(rot); c.fillStyle = col; c.beginPath();
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * TAU, rr = i % 2 ? r * .28 : r;
    c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
  }
  c.closePath(); c.fill(); c.restore();
}
function heart(c, x, y, s, col, lw = 0) {
  c.save(); c.translate(x, y); c.scale(s / 50, s / 50); c.beginPath();
  c.moveTo(0, 18); c.bezierCurveTo(-60, -20, -28, -62, 0, -30); c.bezierCurveTo(28, -62, 60, -20, 0, 18);
  c.closePath(); fillStroke(c, col, lw); c.restore();
}
function sweat(c, x, y, s, rot = 0) {
  c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s); c.beginPath();
  c.moveTo(0, -22); c.bezierCurveTo(10, -6, 14, 4, 14, 10); c.arc(0, 10, 14, 0, Math.PI); c.bezierCurveTo(-14, 4, -10, -6, 0, -22);
  c.closePath(); fillStroke(c, '#8fd8ff', 4); ellipse(c, -4, 8, 4, 6, '#fff', 0); c.restore();
}
// offscreen canvases for transitions
const OFF = [0, 1].map(() => { const o = document.createElement('canvas'); o.width = W; o.height = H; return o; });
