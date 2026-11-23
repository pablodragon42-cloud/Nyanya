import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import * as L from './lib.js';
import { buildScenes } from './scenes.js';
import { SUBS, CHIPS } from './text.js';

const W = 1920, H = 1080;
export const OFF = 1.0;           // narration starts 1 s into the film
const XF = 0.8;                   // crossfade length
const { ss, clamp, lerp } = L;

const glc = document.createElement('canvas'); glc.width = W; glc.height = H;
const renderer = new THREE.WebGLRenderer({ canvas: glc, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
const mkRT = () => new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const rtA = mkRT(), rtB = mkRT();

const composer = new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(W, H);
const mixPass = new ShaderPass({
  uniforms: { tA: { value: null }, tB: { value: null }, uMix: { value: 0 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tA,tB; uniform float uMix; varying vec2 vUv;
    void main(){ vec2 c=vUv-0.5;
      vec4 a=texture2D(tA, 0.5+c*(1.0-0.06*uMix));
      vec4 b=texture2D(tB, 0.5+c*(1.0+0.05*(1.0-uMix)));
      float m=smoothstep(0.0,1.0,uMix);
      vec3 col=mix(a.rgb,b.rgb,m) + vec3(1.0,0.85,0.8)*0.25*sin(m*3.14159)*0.0;
      gl_FragColor=vec4(col,1.0); }`,
});
mixPass.uniforms.tA.value = rtA.texture; mixPass.uniforms.tB.value = rtB.texture;
composer.addPass(mixPass);
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.55, 0.55, 0.8); composer.addPass(bloom);
composer.addPass(new OutputPass());
const finish = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uFade: { value: 1 }, uTime: { value: 0 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uFade,uTime; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p,vec2(12.9898,78.233))+uTime*13.1)*43758.5453); }
    void main(){ vec2 c=vUv-0.5; float r=length(c);
      vec3 col; col.r=texture2D(tDiffuse,vUv-c*0.0025).r; col.g=texture2D(tDiffuse,vUv).g; col.b=texture2D(tDiffuse,vUv+c*0.0025).b;
      col*=1.0-smoothstep(0.35,0.95,r)*0.55;
      col+=(h(vUv*1000.0)-0.5)*0.028;
      gl_FragColor=vec4(col*uFade,1.0); }`,
});
composer.addPass(finish);

const scenes = buildScenes();

// ---------------------------------------------------------------- 2D overlay
const oc = document.createElement('canvas'); oc.width = W; oc.height = H; document.body.appendChild(oc);
const g = oc.getContext('2d');
const FONT = 'Montserrat';
function rr(x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function wrap(text, maxW) {
  const words = text.split(' '); const lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (g.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t; }
  if (cur) lines.push(cur);
  // balance two lines
  if (lines.length === 2) {
    const all = text.split(' '); let best = null;
    for (let i = 1; i < all.length; i++) { const a = all.slice(0, i).join(' '), b = all.slice(i).join(' '); const d = Math.abs(g.measureText(a).width - g.measureText(b).width); if (g.measureText(a).width <= maxW && g.measureText(b).width <= maxW && (!best || d < best.d)) best = { d, l: [a, b] }; }
    if (best) return best.l;
  }
  return lines;
}
function subtitle(v) {
  for (const s of SUBS) {
    if (v < s.s - 0.06 || v > s.e + 0.12) continue;
    const a = ss(s.s - 0.06, s.s + 0.08, v) * (1 - ss(s.e, s.e + 0.12, v));
    g.font = `600 44px ${FONT}`;
    const lines = wrap(s.t, 1500); const lh = 58;
    const tw = Math.max(...lines.map(l => g.measureText(l).width));
    const bh = lines.length * lh + 28, by = H - 64 - bh;
    g.globalAlpha = a * 0.62; g.fillStyle = '#060a16'; rr(W / 2 - tw / 2 - 34, by, tw + 68, bh, 18); g.fill();
    g.globalAlpha = a; g.fillStyle = '#ffffff'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 8;
    lines.forEach((l, i) => g.fillText(l, W / 2, by + 14 + lh * (i + 0.5) + 2));
    g.shadowBlur = 0; g.globalAlpha = 1;
  }
}
function chip(v) {
  for (const c of CHIPS) {
    if (v < c.s || v > c.e) continue;
    const a = ss(c.s, c.s + 0.5, v) * (1 - ss(c.e - 0.4, c.e, v));
    const slide = (1 - ss(c.s, c.s + 0.6, v)) * -40;
    g.globalAlpha = a; g.font = `800 26px ${FONT}`;
    const num = String(c.n); const nw = 52; g.font = `600 28px ${FONT}`; const tw = g.measureText(c.t).width;
    const x = 64 + slide, y = 56;
    g.fillStyle = 'rgba(6,12,28,0.62)'; rr(x, y, nw + tw + 46, 56, 28); g.fill();
    g.strokeStyle = 'rgba(127,224,255,0.55)'; g.lineWidth = 2; g.stroke();
    g.fillStyle = '#7fe0ff'; g.beginPath(); g.arc(x + 28, y + 28, 20, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#04101e'; g.font = `800 24px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(num, x + 28, y + 29);
    g.fillStyle = '#ffffff'; g.font = `600 28px ${FONT}`; g.textAlign = 'left'; g.fillText(c.t, x + nw + 14, y + 29);
    g.globalAlpha = 1;
  }
}
const _v = new THREE.Vector3();
function labels(list, camera, alphaMul) {
  for (const l of list) {
    const a = (l.a ?? 0) * alphaMul; if (a <= 0.01 || !l.text) continue;
    if (l.obj) l.obj.getWorldPosition(_v); else _v.copy(l.p);
    _v.project(camera); if (_v.z > 1) continue;
    const x = (_v.x * 0.5 + 0.5) * W, y = (-_v.y * 0.5 + 0.5) * H;
    const lx = x + l.ox, ly = y + l.oy;
    g.globalAlpha = a; const col = l.color || '#7fe0ff';
    g.font = `700 30px ${FONT}`; const tw = g.measureText(l.text).width;
    const left = l.ox < 0; let bx = left ? lx - tw - 36 : lx; const bw = tw + 36;
    bx = Math.min(Math.max(bx, 30), W - 30 - bw); let lyc = Math.min(Math.max(ly, 150), H - 230);
    const lx2 = left ? bx + bw : bx;
    // redirect leader to the clamped box
    l._lx = lx2; l._ly = lyc;
    // leader line grows in
    const grow = clamp(a * 1.4);
    g.strokeStyle = col; g.lineWidth = 2.5; g.shadowColor = col; g.shadowBlur = 10;
    g.beginPath(); g.moveTo(x, y); g.lineTo(lerp(x, l._lx, grow), lerp(y, l._ly, grow)); g.stroke();
    g.beginPath(); g.arc(x, y, 7, 0, Math.PI * 2); g.fillStyle = col; g.fill();
    g.beginPath(); g.arc(x, y, 13, 0, Math.PI * 2); g.lineWidth = 2; g.stroke();
    g.shadowBlur = 0;
    g.fillStyle = 'rgba(6,12,28,0.72)'; rr(bx, lyc - 26, bw, 52, 26); g.fill();
    g.strokeStyle = col; g.lineWidth = 2; g.stroke();
    g.fillStyle = '#ffffff'; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(l.text, bx + 18, lyc + 1);
    g.globalAlpha = 1;
  }
}
function glowText(t, x, y, size, weight, a, col = '#ffffff', glow = '#4fd8ff', align = 'center', spacing = 0) {
  g.globalAlpha = a; g.font = `${weight} ${size}px ${FONT}`; g.textAlign = align; g.textBaseline = 'middle';
  if (spacing) g.letterSpacing = spacing + 'px'; else g.letterSpacing = '0px';
  g.shadowColor = glow; g.shadowBlur = 24; g.fillStyle = col; g.fillText(t, x, y); g.shadowBlur = 0; g.fillText(t, x, y);
  g.letterSpacing = '0px'; g.globalAlpha = 1;
}
function panel(x, y, w, h, a, col) {
  g.globalAlpha = a * 0.7; g.fillStyle = '#060c1c'; rr(x, y, w, h, 22); g.fill();
  g.globalAlpha = a; g.strokeStyle = col; g.lineWidth = 2.5; rr(x, y, w, h, 22); g.stroke(); g.globalAlpha = 1;
}
function specials(v) {
  // opening question
  {
    const a = ss(0.0, 0.6, v) * (1 - ss(5.3, 6.1, v));
    if (a > 0) {
      glowText('АДАМ ИММУНИТЕТІ', W / 2, 150, 34, 700, a * 0.9, '#7fe0ff', '#1a8fff', 'center', 10);
      glowText('қалай жұмыс істейді?', W / 2, 218, 64, 800, a);
    }
  }
  // phagocytosis title + steps
  {
    const a = ss(34.8, 35.3, v) * (1 - ss(37.4, 37.9, v));
    if (a > 0) {
      const sc = 1 + (1 - ss(34.8, 35.6, v)) * 0.15;
      g.save(); g.translate(W / 2, 170); g.scale(sc, sc); glowText('ФАГОЦИТОЗ', 0, 0, 92, 800, a, '#ffffff', '#ffb050', 'center', 6); g.restore();
    }
    const steps = ['Анықтау', 'Қоршау', 'Жұту', 'Қорыту'], times = [26.6, 30.8, 32.0, 33.2];
    const b = ss(26.6, 27.2, v) * (1 - ss(37.4, 37.9, v));
    if (b > 0) {
      g.font = `700 26px ${FONT}`;
      const ws = steps.map(s => g.measureText(s).width + 40); const gap = 46; const total = ws.reduce((p, q) => p + q, 0) + gap * 3;
      let x = W - 64 - total; const y = 84;
      steps.forEach((s, i) => {
        const on = ss(times[i], times[i] + 0.3, v);
        g.globalAlpha = b; g.fillStyle = on > 0.5 ? 'rgba(255,176,80,0.9)' : 'rgba(6,12,28,0.6)'; rr(x, y - 24, ws[i], 48, 24); g.fill();
        g.strokeStyle = 'rgba(255,190,110,0.9)'; g.lineWidth = 2; g.stroke();
        g.fillStyle = on > 0.5 ? '#1a0c00' : '#ffe2c0'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, x + ws[i] / 2, y + 1);
        if (i < 3) { g.fillStyle = '#ffd09a'; g.font = `800 26px ${FONT}`; g.fillText('→', x + ws[i] + gap / 2, y); g.font = `700 26px ${FONT}`; }
        x += ws[i] + gap;
      });
      g.globalAlpha = 1;
    }
  }
  // innate vs adaptive panels
  {
    const a = ss(63.9, 64.6, v) * (1 - ss(77.4, 78.0, v));
    const a2 = ss(65.4, 66.1, v) * (1 - ss(77.4, 78.0, v));
    const hl = ss(67.4, 68.2, v) * (1 - ss(72.1, 72.8, v)), hr = ss(72.3, 73.0, v);
    const pw = 800, ph = 300, py = 40;
    const LB = ['Туғаннан бері болады', 'Бірден, жылдам әрекет етеді', 'Барлық бөгде заттарға ортақ қорғаныс'];
    const RB = ['Қоздырғышпен кездескен соң қалыптасады', 'Белгілі бір қоздырғышқа ғана арналған', 'Жады жасушаларын қалдырады', 'Мысалы: ауырып жазылған соң, вакцинадан кейін'];
    const draw = (x, alpha, title, bullets, col, hlv, bulletT) => {
      if (alpha <= 0) return;
      const dim = 1 - (hl + hr > 0 ? (1 - hlv) * 0.45 : 0);
      panel(x, py, pw, ph, alpha * dim, col);
      glowText(title, x + pw / 2, py + 50, 40, 800, alpha * dim, '#ffffff', col);
      g.font = `600 28px ${FONT}`;
      bullets.forEach((b, i) => {
        const ba = alpha * dim * ss(bulletT + i * 0.6, bulletT + i * 0.6 + 0.4, v);
        g.globalAlpha = ba; g.fillStyle = col; g.beginPath(); g.arc(x + 46, py + 112 + i * 46, 7, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#eef6ff'; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(b, x + 68, py + 113 + i * 46);
      });
      g.globalAlpha = 1;
    };
    draw(W / 2 - pw - 40, a, 'Туа пайда болған', LB, '#ffb070', hl, 67.8);
    draw(W / 2 + 40, a2, 'Жүре пайда болған', RB, '#7fc8ff', hr, 72.8);
  }
  // memory: primary vs secondary response chart
  {
    const a = ss(79.6, 80.3, v) * (1 - ss(87.9, 88.4, v));
    if (a > 0) {
      const x = W - 64 - 620, y = 130, w = 620, h = 340;
      panel(x, y, w, h, a, '#b8a8ff');
      g.globalAlpha = a; g.fillStyle = '#ffffff'; g.font = `700 28px ${FONT}`; g.textAlign = 'left'; g.textBaseline = 'middle';
      g.fillText('Иммундық жауап', x + 28, y + 38);
      const ox = x + 70, oy = y + h - 60, aw = w - 110, ah = h - 130;
      g.strokeStyle = 'rgba(220,220,255,0.8)'; g.lineWidth = 2.5; g.beginPath(); g.moveTo(ox, oy - ah); g.lineTo(ox, oy); g.lineTo(ox + aw, oy); g.stroke();
      g.font = `500 21px ${FONT}`; g.fillStyle = '#d8d8ff'; g.fillText('уақыт →', ox + aw - 100, oy + 26);
      g.save(); g.translate(ox - 22, oy - ah / 2 + 70); g.rotate(-Math.PI / 2); g.fillText('антиденелер', 0, 0); g.restore();
      const curve = (x0, peak, rise, width, prog, col, label) => {
        const pts = []; const n = 60;
        for (let i = 0; i <= n * prog; i++) { const t = i / n; const xx = x0 + t * width; const tt = t * 3.0; const yy = peak * (tt < rise ? Math.pow(tt / rise, 2) : Math.exp(-(tt - rise) * 1.1)); pts.push([ox + xx * aw, oy - yy * ah]); }
        if (pts.length < 2) return;
        g.strokeStyle = col; g.lineWidth = 4; g.shadowColor = col; g.shadowBlur = 12; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(...p) : g.moveTo(...p)); g.stroke(); g.shadowBlur = 0;
        if (prog > 0.4) { g.fillStyle = col; g.font = `700 22px ${FONT}`; g.fillText(label, ox + (x0 + 0.02) * aw, oy - ah * peak - 22); }
      };
      curve(0.02, 0.32, 1.6, 0.42, ss(80.4, 83.4, v), '#ffb070', '1-рет кездескенде');
      curve(0.5, 0.95, 0.6, 0.48, ss(84.2, 86.4, v), '#7ff0c8', 'Қайта кездескенде');
      g.globalAlpha = 1;
    }
  }
  // final title
  {
    const a = ss(95.6, 96.5, v);
    if (a > 0) {
      const rise = (1 - easeO(ss(95.6, 96.8, v))) * 30;
      glowText('ИММУНИТЕТ', W / 2, 150 + rise, 104, 800, a, '#ffffff', '#3fd0ff', 'center', 14);
      glowText('ағзамыздың табиғи қорғаныс қалқаны', W / 2, 238 + rise, 44, 600, ss(96.2, 97.0, v), '#bff0ff', '#1a8fff');
    }
  }
}
const easeO = t => 1 - Math.pow(1 - t, 3);

// ---------------------------------------------------------------- frame
function activeAt(v) {
  const out = [];
  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    const a = i === 0 ? -99 : s.v0 - XF / 2, b = i === scenes.length - 1 ? 999 : s.v1 + XF / 2;
    if (v >= a && v < b) out.push(s);
  }
  return out;
}
function renderScene(s, v, rt) {
  const labs = s.update(v - s.v0, v) || [];
  renderer.setRenderTarget(rt); renderer.render(s.scene, s.camera); renderer.setRenderTarget(null);
  return labs;
}
window.renderFrame = (t, opts = {}) => {
  const v = t - OFF;
  L.U.time.value = t;
  const act = activeAt(v);
  let mix = 0, labsA = [], labsB = [];
  labsA = renderScene(act[0], v, rtA);
  if (act.length > 1) { labsB = renderScene(act[1], v, rtB); mix = ss(act[1].v0 - XF / 2, act[1].v0 + XF / 2, v); }
  mixPass.uniforms.uMix.value = mix;
  finish.uniforms.uTime.value = t;
  finish.uniforms.uFade.value = ss(0.0, 0.9, t) * (1 - ss(103.6, 105.0, v));
  composer.render();
  g.clearRect(0, 0, W, H);
  g.drawImage(glc, 0, 0);
  const fade = finish.uniforms.uFade.value;
  labels(labsA, act[0].camera, (1 - mix) * fade);
  if (act[1]) labels(labsB, act[1].camera, mix * fade);
  g.globalAlpha = 1;
  chip(v);
  specials(v);
  if (!opts.nosubs) subtitle(v);
  return oc.toDataURL('image/jpeg', opts.q ?? 0.93);
};
await document.fonts.load(`600 40px ${FONT}`); await document.fonts.load(`800 40px ${FONT}`); await document.fonts.load(`700 40px ${FONT}`); await document.fonts.load(`500 40px ${FONT}`);
// warm up shaders for all scenes
for (const s of scenes) { s.update(0.01, s.v0 + 0.01); renderer.compile(s.scene, s.camera); }
window.READY = true; window.DBG = { renderer, rtA, scenes, composer, THREE };
