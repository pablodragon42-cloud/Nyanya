// Shared 3D building blocks: procedural cell materials, microbes, immune cells.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const U = { time: { value: 0 } };

// ---------- deterministic RNG
export function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >> 17; s ^= s << 5; s >>>= 0; return (s % 1e9) / 1e9; };
}
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const ease = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
export const easeIn = t => Math.pow(clamp(t), 3);

// ---------- GLSL simplex noise (Ashima Arts / Stefan Gustavson, MIT)
export const NOISE = /* glsl */`
vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
float snoise(vec3 v){
  const vec2 C=vec2(1.0/6.0,1.0/3.0); const vec4 D=vec4(0.0,0.5,1.0,2.0);
  vec3 i=floor(v+dot(v,C.yyy)); vec3 x0=v-i+dot(i,C.xxx);
  vec3 g=step(x0.yzx,x0.xyz); vec3 l=1.0-g; vec3 i1=min(g.xyz,l.zxy); vec3 i2=max(g.xyz,l.zxy);
  vec3 x1=x0-i1+C.xxx; vec3 x2=x0-i2+C.yyy; vec3 x3=x0-D.yyy;
  i=mod289(i);
  vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
  float n_=0.142857142857; vec3 ns=n_*D.wyz-D.xzx;
  vec4 j=p-49.0*floor(p*ns.z*ns.z); vec4 x_=floor(j*ns.z); vec4 y_=floor(j-7.0*x_);
  vec4 x=x_*ns.x+ns.yyyy; vec4 y=y_*ns.x+ns.yyyy; vec4 h=1.0-abs(x)-abs(y);
  vec4 b0=vec4(x.xy,y.xy); vec4 b1=vec4(x.zw,y.zw);
  vec4 s0=floor(b0)*2.0+1.0; vec4 s1=floor(b1)*2.0+1.0; vec4 sh=-step(h,vec4(0.0));
  vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy; vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
  vec3 p0=vec3(a0.xy,h.x); vec3 p1=vec3(a0.zw,h.y); vec3 p2=vec3(a1.xy,h.z); vec3 p3=vec3(a1.zw,h.w);
  vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
  p0*=norm.x; p1*=norm.y; p2*=norm.z; p3*=norm.w;
  vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0); m=m*m;
  return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}`;

// ---------- living cell material: animated surface displacement + fresnel rim
// opts: color, amp, freq, speed, rim, rimI, rimPow, rough, metal, opacity, emissive, emissiveI, pull
export function cellMat(o = {}) {
  const m = new THREE.MeshStandardMaterial({
    color: o.color ?? 0xffffff, roughness: o.rough ?? 0.55, metalness: o.metal ?? 0.0,
    emissive: o.emissive ?? 0x000000, emissiveIntensity: o.emissiveI ?? 1,
    transparent: (o.opacity ?? 1) < 1, opacity: o.opacity ?? 1, depthWrite: (o.opacity ?? 1) >= 1,
  });
  const u = m.userData.u = {
    uTime: U.time,
    uAmp: { value: o.amp ?? 0.06 }, uFreq: { value: o.freq ?? 2.0 }, uSpeed: { value: o.speed ?? 0.35 },
    uSeed: { value: new THREE.Vector3(...(o.seed ?? [Math.random() * 50, Math.random() * 50, Math.random() * 50])) },
    uRim: { value: new THREE.Color(o.rim ?? 0xffffff).multiplyScalar(o.rimI ?? 0.6) },
    uRimPow: { value: o.rimPow ?? 2.5 },
    uPullDir: { value: new THREE.Vector3(1, 0, 0) }, uPull: { value: 0 },   // cup-shaped pseudopod wrap
    uSpikes: { value: o.spikes ?? 0 },                                       // star-like arms (dendritic/macrophage)
    uGlow: { value: 0 },
  };
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, u);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
uniform float uTime,uAmp,uFreq,uSpeed,uPull,uSpikes; uniform vec3 uSeed,uPullDir;
${NOISE}
float disp(vec3 p){
  vec3 q=normalize(p);
  float d=uAmp*(snoise(p*uFreq+uSeed+vec3(0.0,0.0,uTime*uSpeed))*0.7+snoise(p*uFreq*2.7+uSeed*1.3-vec3(uTime*uSpeed*0.7))*0.3);
  float c=dot(q,normalize(uPullDir));
  d+=uPull*(exp(-pow((c-0.55)/0.22,2.0))*1.0 + smoothstep(0.75,1.0,c)*-0.35);
  if(uSpikes>0.0){ float s=snoise(q*2.2+uSeed); d+=uSpikes*pow(max(s,0.0),2.2)*(1.0+0.25*sin(uTime*1.3+s*6.0)); }
  return d;
}`)
      .replace('#include <beginnormal_vertex>', `
vec3 _n=normalize(normal); vec3 _t=normalize(cross(_n,abs(_n.y)<0.99?vec3(0.0,1.0,0.0):vec3(1.0,0.0,0.0))); vec3 _b=cross(_n,_t);
float _e=0.012;
vec3 _p0=position+_n*disp(position);
vec3 _q1=position+_t*_e; vec3 _q2=position+_b*_e;
vec3 _p1=_q1+_n*disp(_q1); vec3 _p2=_q2+_n*disp(_q2);
vec3 objectNormal=normalize(cross(_p1-_p0,_p2-_p0));`)
      .replace('#include <begin_vertex>', 'vec3 transformed=_p0;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform vec3 uRim; uniform float uRimPow; uniform float uGlow;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
float _fr=pow(1.0-abs(dot(normal,normalize(vViewPosition))),uRimPow);
totalEmissiveRadiance+=uRim*_fr*(1.0+uGlow*2.0)+diffuseColor.rgb*uGlow*0.6;`);
  };
  m.customProgramCacheKey = () => 'cell';
  return m;
}

// ---------- additive fresnel hologram material
export function holoMat(color = 0x4fd8ff, power = 2.0, base = 0.06, scan = 1) {
  return new THREE.ShaderMaterial({
    uniforms: { uTime: U.time, uColor: { value: new THREE.Color(color) }, uPow: { value: power }, uBase: { value: base }, uA: { value: 1 }, uScan: { value: scan } },
    vertexShader: `varying vec3 vN; varying vec3 vV; varying float vY;
      void main(){ vec4 mv=modelViewMatrix*vec4(position,1.0); vN=normalize(normalMatrix*normal); vV=-mv.xyz; vY=(modelMatrix*vec4(position,1.0)).y; gl_Position=projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uColor; uniform float uPow,uBase,uA,uTime,uScan; varying vec3 vN; varying vec3 vV; varying float vY;
      void main(){ float f=pow(1.0-abs(dot(normalize(vN),normalize(vV))),uPow);
        float s=0.82+0.18*sin(vY*28.0-uTime*3.0);
        float band=smoothstep(0.0,0.04,0.04-abs(fract(vY*0.12-uTime*0.18)-0.5))*0.8*uScan;
        vec3 c=uColor*(f*1.3+uBase)*s + uColor*band*0.5;
        gl_FragColor=vec4(c*uA,1.0); }`,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
  });
}

// ---------- soft round sprite texture for particles
let _spr;
export function spriteTex() {
  if (_spr) return _spr;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'); const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.35, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  _spr = new THREE.CanvasTexture(c); return _spr;
}
export function particles(n, spread, color, size, seed = 1, opacity = 0.6) {
  const R = rng(seed); const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { pos[i * 3] = (R() - .5) * spread[0]; pos[i * 3 + 1] = (R() - .5) * spread[1]; pos[i * 3 + 2] = (R() - .5) * spread[2]; }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const m = new THREE.PointsMaterial({ color, size, map: spriteTex(), transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending, sizeAttenuation: true });
  return new THREE.Points(g, m);
}

// ---------- gradient backdrop sphere
export function backdrop(top, bottom, r = 300) {
  const m = new THREE.ShaderMaterial({
    uniforms: { cT: { value: new THREE.Color(top) }, cB: { value: new THREE.Color(bottom) }, uTime: U.time },
    vertexShader: 'varying vec3 vP; void main(){ vP=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: `uniform vec3 cT,cB; uniform float uTime; varying vec3 vP; ${NOISE}
      void main(){ float h=vP.y*0.5+0.5; float n=snoise(vP*3.0+vec3(0.0,0.0,uTime*0.03))*0.5+0.5;
      vec3 c=mix(cB,cT,smoothstep(0.0,1.0,h)); c*=0.75+0.5*n; gl_FragColor=vec4(c,1.0);} `,
    side: THREE.BackSide, depthWrite: false, fog: false,
  });
  const s = new THREE.Mesh(new THREE.SphereGeometry(r, 48, 24), m); s.renderOrder = -10; return s;
}

export function stdLights(scene, { hemiTop = 0xffe6ee, hemiBot = 0x401020, hemiI = 1.0, key = 0xffffff, keyI = 2.2, rimC = 0x88aaff, rimI = 1.5 } = {}) {
  scene.add(new THREE.HemisphereLight(hemiTop, hemiBot, hemiI));
  const k = new THREE.DirectionalLight(key, keyI); k.position.set(5, 8, 6); scene.add(k);
  const r = new THREE.DirectionalLight(rimC, rimI); r.position.set(-6, -2, -8); scene.add(r);
}

// ---------- red blood cell (biconcave disc)
let _rbcG;
export function rbcGeo() {
  if (_rbcG) return _rbcG;
  const pts = [];
  const N = 28;
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * Math.PI; // around the rim profile
    const r = 1.0;
    // biconcave profile (Evans–Fung): z(ρ)=0.5*sqrt(1-ρ²)*(c0+c1ρ²+c2ρ⁴)
    const rho = Math.sin(a * 0.5 + 0) ; // not used
  }
  const prof = [];
  const M = 40;
  for (let i = 0; i <= M; i++) {
    const rho = i / M;
    const z = 0.5 * Math.sqrt(Math.max(0, 1 - rho * rho)) * (0.21 + 2.0 * rho * rho - 1.12 * rho ** 4);
    prof.push(new THREE.Vector2(rho, z));
  }
  for (let i = M; i >= 0; i--) { const p = prof[i]; pts.push(new THREE.Vector2(p.x, p.y)); }
  for (let i = 1; i <= M; i++) { const p = prof[i]; pts.push(new THREE.Vector2(p.x, -p.y)); }
  // lathe around y: profile x=ρ, y=z
  _rbcG = new THREE.LatheGeometry(pts.reverse().map(p => new THREE.Vector2(Math.max(p.x, 0.0001), p.y)), 48);
  _rbcG.computeVertexNormals();
  return _rbcG;
}
export function rbcMat() {
  return new THREE.MeshStandardMaterial({ color: 0xb3121c, roughness: 0.42, metalness: 0.0, emissive: 0x3a0306, emissiveIntensity: 1, side: THREE.DoubleSide });
}

// ---------- bacterium: rod with flagella
export function bacterium(seed = 1, scale = 1, color = 0x6fcf3a) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.28, 0.9, 12, 32),
    cellMat({ color, amp: 0.025, freq: 3.5, speed: 0.6, rim: 0xd8ff7a, rimI: 0.9, rough: 0.35, seed: [seed, seed * 2, 3] }));
  body.rotation.z = Math.PI / 2; g.add(body);
  // surface dots (pili)
  const flag = new THREE.Group();
  const fm = new THREE.MeshStandardMaterial({ color: 0xa8e070, roughness: 0.5, emissive: 0x2a4a10 });
  for (let k = 0; k < 3; k++) {
    const pts = [];
    for (let i = 0; i <= 30; i++) { const t = i / 30; pts.push(new THREE.Vector3(-0.6 - t * 1.4, Math.sin(t * 9 + k * 2) * 0.12 * t + (k - 1) * 0.12, Math.cos(t * 9 + k * 2) * 0.12 * t)); }
    flag.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, 0.018, 5), fm));
  }
  g.add(flag); g.userData.flag = flag; g.userData.body = body;
  g.scale.setScalar(scale);
  return g;
}

// ---------- virus: capsid with spike proteins
let _spikeG;
function spikeGeo() {
  if (_spikeG) return _spikeG;
  const parts = []; const N = 46;
  for (let i = 0; i < N; i++) {
    const y = 1 - (i + 0.5) / N * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963;
    const d = new THREE.Vector3(Math.cos(th) * r, y, Math.sin(th) * r);
    const st = new THREE.CylinderGeometry(0.025, 0.035, 0.22, 6); st.translate(0, 0.11 + 0.95, 0);
    const tip = new THREE.SphereGeometry(0.075, 8, 6); tip.scale(1, 0.75, 1); tip.translate(0, 1.2, 0);
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
    const M = new THREE.Matrix4().makeRotationFromQuaternion(q);
    st.applyMatrix4(M); tip.applyMatrix4(M); parts.push(st, tip);
  }
  _spikeG = mergeGeometries(parts); return _spikeG;
}
export function virus(seed = 1, scale = 0.35) {
  const g = new THREE.Group();
  const core = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 4),
    cellMat({ color: 0x8a3bd1, amp: 0.05, freq: 4, speed: 0.3, rim: 0xff7ae0, rimI: 0.9, rough: 0.4, seed: [seed, 1, 2] }));
  const sp = new THREE.Mesh(spikeGeo(), new THREE.MeshStandardMaterial({ color: 0xff3d6e, roughness: 0.35, emissive: 0x6a0a22, emissiveIntensity: 1.2 }));
  g.add(core, sp); g.scale.setScalar(scale); g.userData.core = core;
  return g;
}

// ---------- antibody (Y shape)
let _abG;
export function antibodyGeo() {
  if (_abG) return _abG;
  const mk = (len, ang, y0) => { const c = new THREE.CapsuleGeometry(0.07, len, 4, 8); c.translate(0, len / 2, 0); c.rotateZ(ang); c.translate(0, y0, 0); return c; };
  _abG = mergeGeometries([mk(0.45, 0, -0.45), mk(0.42, 0.62, 0.0), mk(0.42, -0.62, 0.0),
    (() => { const s = new THREE.SphereGeometry(0.1, 8, 6); return s; })()]);
  _abG.computeVertexNormals();
  return _abG;
}
export function antibodyMat() {
  return new THREE.MeshStandardMaterial({ color: 0xdff6ff, emissive: 0x39c6ff, emissiveIntensity: 1.1, roughness: 0.3 });
}

// ---------- microvilli / receptor shells for lymphocytes
let _villiG, _bcrG;
function villiGeo() {
  if (_villiG) return _villiG;
  const parts = []; const N = 160; const R = rng(9);
  for (let i = 0; i < N; i++) {
    const y = 1 - (i + 0.5) / N * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963 + R() * 0.3;
    const d = new THREE.Vector3(Math.cos(th) * r, y, Math.sin(th) * r);
    const L = 0.12 + R() * 0.12;
    const c = new THREE.CylinderGeometry(0.018, 0.03, L, 5); c.translate(0, 0.96 + L / 2, 0);
    const tip = new THREE.SphereGeometry(0.022, 5, 4); tip.translate(0, 0.96 + L, 0);
    const M = new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d));
    c.applyMatrix4(M); tip.applyMatrix4(M); parts.push(c, tip);
  }
  _villiG = mergeGeometries(parts); return _villiG;
}
function bcrGeo() {
  if (_bcrG) return _bcrG;
  const parts = []; const N = 70;
  for (let i = 0; i < N; i++) {
    const y = 1 - (i + 0.5) / N * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963;
    const d = new THREE.Vector3(Math.cos(th) * r, y, Math.sin(th) * r);
    const ab = antibodyGeo().clone(); ab.scale(0.28, 0.28, 0.28); ab.translate(0, 1.08, 0);
    ab.applyMatrix4(new THREE.Matrix4().makeRotationFromQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d)));
    parts.push(ab);
  }
  _bcrG = mergeGeometries(parts); return _bcrG;
}

export function tCell(seed = 1, r = 0.8, detail = 4) {
  const g = new THREE.Group();
  const mat = cellMat({ color: 0x2f6fe0, amp: 0.035, freq: 3, speed: 0.4, rim: 0x7fe0ff, rimI: 0.9, rough: 0.45, seed: [seed, 4, 1] });
  const b = new THREE.Mesh(new THREE.IcosahedronGeometry(1, detail), mat);
  const v = new THREE.Mesh(villiGeo(), new THREE.MeshStandardMaterial({ color: 0x5d98ff, roughness: 0.5, emissive: 0x0d2a66 }));
  g.add(b, v); g.scale.setScalar(r); g.userData.mat = mat; g.userData.villi = v;
  return g;
}
export function bCell(seed = 1, r = 0.8, detail = 4) {
  const g = new THREE.Group();
  const mat = cellMat({ color: 0xe0a92a, amp: 0.035, freq: 3, speed: 0.4, rim: 0xfff0a0, rimI: 0.9, rough: 0.45, seed: [seed, 7, 2] });
  const b = new THREE.Mesh(new THREE.IcosahedronGeometry(1, detail), mat);
  const v = new THREE.Mesh(bcrGeo(), antibodyMat());
  g.add(b, v); g.scale.setScalar(r); g.userData.mat = mat; g.userData.rec = v;
  return g;
}

// ---------- neutrophil: translucent cell, multi-lobed nucleus, granules
export function neutrophil(seed = 1, r = 1.0) {
  const g = new THREE.Group();
  const nucM = cellMat({ color: 0x6a2c9e, amp: 0.05, freq: 2.5, speed: 0.3, rim: 0xc48cff, rimI: 0.5, rough: 0.5, seed: [seed, 2, 2] });
  const lobes = [[-0.32, 0.1, 0], [0.0, -0.18, 0.1], [0.33, 0.08, -0.05], [0.12, 0.32, 0.05]];
  const nuc = new THREE.Group();
  lobes.forEach(p => { const m = new THREE.Mesh(new THREE.IcosahedronGeometry(0.26, 3), nucM); m.position.set(...p); nuc.add(m); });
  g.add(nuc);
  const gr = particles(140, [1.3, 1.3, 1.3], 0xff9ad8, 0.06, seed + 3, 0.8); gr.material.blending = THREE.NormalBlending;
  // keep granules within sphere
  const pa = gr.geometry.attributes.position;
  for (let i = 0; i < pa.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(pa, i); if (v.length() > 0.8) v.setLength(0.3 + (v.length() % 0.5)); pa.setXYZ(i, v.x, v.y, v.z); }
  g.add(gr);
  const outM = cellMat({ color: 0xf2e6f4, amp: 0.07, freq: 3.2, speed: 0.45, rim: 0xffc8f0, rimI: 1.0, rimPow: 2.0, rough: 0.3, opacity: 0.42, seed: [seed, 5, 9] });
  const out = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 5), outM); out.renderOrder = 2;
  g.add(out); g.scale.setScalar(r); g.userData.mat = outM; g.userData.outer = out;
  return g;
}

// ---------- macrophage: large irregular cell with pseudopods
export function macrophage(seed = 1, r = 1.6, opacity = 0.62) {
  const g = new THREE.Group();
  const nucM = cellMat({ color: 0x8a4a2a, amp: 0.06, freq: 2, speed: 0.2, rim: 0xffb070, rimI: 0.3, seed: [seed, 1, 1] });
  const nuc = new THREE.Mesh(new THREE.IcosahedronGeometry(0.35, 3), nucM); nuc.position.set(-0.35, 0.15, -0.2); nuc.scale.set(1.3, 0.9, 1);
  g.add(nuc);
  const ves = particles(60, [1.4, 1.2, 1.2], 0xffd27a, 0.09, seed + 11, 0.7); ves.material.blending = THREE.NormalBlending;
  const pa = ves.geometry.attributes.position;
  for (let i = 0; i < pa.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(pa, i); v.multiplyScalar(0.8); pa.setXYZ(i, v.x, v.y, v.z); }
  g.add(ves);
  const mat = cellMat({ color: 0xe8a868, amp: 0.12, freq: 1.4, speed: 0.35, rim: 0xffd9a8, rimI: 1.0, rimPow: 2.2, rough: 0.35, opacity, spikes: 0.35, seed: [seed, 3, 3] });
  const out = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 6), mat); out.renderOrder = 2;
  g.add(out); g.scale.setScalar(r); g.userData.mat = mat; g.userData.outer = out;
  return g;
}

// generic leukocyte (white, ruffled)
export function leukocyte(seed = 1, r = 1, detail = 4) {
  const g = new THREE.Group();
  const mat = cellMat({ color: 0xeee8f6, amp: 0.08, freq: 3.6, speed: 0.4, rim: 0xc8d8ff, rimI: 0.7, rough: 0.5, seed: [seed, 9, 4] });
  g.add(new THREE.Mesh(new THREE.IcosahedronGeometry(1, detail), mat));
  g.scale.setScalar(r); g.userData.mat = mat; return g;
}

// big body/tissue cell
export function bodyCell(seed = 1, r = 2, color = 0xe58a9a, detail = 5) {
  const mat = cellMat({ color, amp: 0.05, freq: 1.6, speed: 0.15, rim: 0xffc0d0, rimI: 0.5, rough: 0.6, seed: [seed, 3, 7] });
  const m = new THREE.Mesh(new THREE.IcosahedronGeometry(1, detail), mat);
  m.scale.set(r, r * 0.8, r); m.userData.mat = mat; return m;
}

export function setOpacity(obj, a) {
  obj.traverse(o => {
    if (!o.material) return;
    const m = o.material;
    if (m.userData.baseOp === undefined) m.userData.baseOp = m.opacity;
    m.transparent = true; m.opacity = m.userData.baseOp * a;
    m.depthWrite = a > 0.99 && m.userData.baseOp >= 1;
    if (m.uniforms && m.uniforms.uA) m.uniforms.uA.value = a;
  });
}
