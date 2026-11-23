// All 3D scenes of the film. Each scene: { v0, v1, scene, camera, update(lt, v) -> labels[] }.
// v = narration time in seconds, lt = v - v0.
import * as THREE from 'three';
import * as L from './lib.js';
const { rng, clamp, lerp, ss, ease, easeOut, easeIn } = L;
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const ASPECT = 16 / 9;

function cam(fov = 40) { const c = new THREE.PerspectiveCamera(fov, ASPECT, 0.05, 900); return c; }
function shake(c, t, amt = 0.04) {
  c.position.x += Math.sin(t * 0.9) * amt + Math.sin(t * 2.3) * amt * 0.3;
  c.position.y += Math.sin(t * 1.1 + 1) * amt * 0.8;
}
const lbl = (obj, text, a, ox = 110, oy = -80, color = '#7fe0ff') => ({ obj, text, a, ox, oy, color });
const win = (lt, a, b, f = 0.35) => ss(a, a + f, lt) * (1 - ss(b - f, b, lt));

// ============================================================ human hologram
function humanHolo(color = 0x46c8ff) {
  const g = new THREE.Group();
  const skin = L.holoMat(color, 2.4, 0.035);
  const limb = (a, b, r) => {
    const A = V(...a), B = V(...b), len = A.distanceTo(B);
    const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 8, 28), skin);
    m.position.copy(A).add(B).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), B.clone().sub(A).normalize()); g.add(m);
  };
  const ball = (p, r, s = [1, 1, 1]) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 40, 28), skin); m.position.set(...p); m.scale.set(...s); g.add(m); };
  ball([0, 7.3, 0], 0.55, [0.86, 1.05, 0.95]);
  limb([0, 6.45, 0], [0, 6.85, 0], 0.2);
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.95, 1.5, 10, 32), skin); torso.position.set(0, 5.2, 0); torso.scale.set(1.15, 1, 0.6); g.add(torso);
  ball([0, 4.0, 0], 0.85, [1.1, 0.7, 0.65]);
  for (const s of [-1, 1]) {
    limb([s * 1.2, 6.15, 0], [s * 1.5, 4.8, 0], 0.25);
    limb([s * 1.5, 4.8, 0], [s * 1.72, 3.5, 0.15], 0.21);
    ball([s * 1.78, 3.15, 0.18], 0.24, [0.8, 1.2, 0.6]);
    limb([s * 0.5, 3.8, 0], [s * 0.6, 2.0, 0.05], 0.36);
    limb([s * 0.6, 2.0, 0.05], [s * 0.62, 0.35, 0], 0.27);
    limb([s * 0.62, 0.15, 0.0], [s * 0.66, 0.12, 0.45], 0.14);
  }
  // vessels
  const art = [], vein = [];
  const P = (...a) => a.map(p => V(...p));
  art.push(P([0.2, 5.6, 0.1], [0.1, 6.25, 0], [0.12, 6.9, 0.05], [0.15, 7.4, 0.12]));
  for (const s of [-1, 1]) {
    art.push(P([0.15, 5.5, 0], [0.05, 4.3, -0.05], [s * 0.45, 3.65, 0], [s * 0.6, 2.0, 0.08], [s * 0.62, 0.4, 0.05]));
    art.push(P([0.1, 6.2, 0], [s * 1.2, 6.15, 0.05], [s * 1.52, 4.8, 0.05], [s * 1.73, 3.5, 0.18], [s * 1.79, 3.05, 0.2]));
  }
  for (const c of art) vein.push(c.map(p => p.clone().add(V(0.09, 0.0, -0.08))));
  const flows = [];
  const mkV = (pts, col, n) => {
    const curve = new THREE.CatmullRomCurve3(pts);
    const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 80, 0.035, 6),
      new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false }));
    g.add(tube);
    const pos = new Float32Array(n * 3); const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const pts2 = new THREE.Points(geo, new THREE.PointsMaterial({ color: col, size: 0.16, map: L.spriteTex(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    g.add(pts2); flows.push({ curve, geo, n, off: Math.random() });
  };
  art.forEach(c => mkV(c, 0xff3344, 18)); vein.forEach(c => mkV(c, 0x4477ff, 14));
  const heart = new THREE.Mesh(new THREE.SphereGeometry(0.26, 24, 16), new THREE.MeshBasicMaterial({ color: 0xff2840, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  heart.position.set(0.22, 5.6, 0.12); g.add(heart);
  g.userData = { skin, flows, heart };
  g.userData.tick = (t) => {
    for (const f of flows) {
      const a = f.geo.attributes.position;
      for (let i = 0; i < f.n; i++) { const p = f.curve.getPointAt(((i / f.n) + t * 0.18 + f.off) % 1); a.setXYZ(i, p.x, p.y, p.z); }
      a.needsUpdate = true;
    }
    const beat = Math.pow(Math.max(0, Math.sin(t * 7.5)), 8);
    heart.scale.setScalar(1 + beat * 0.35); heart.material.opacity = 0.6 + beat * 0.4;
  };
  return g;
}
function holoStage(scene) {
  const ringM = new THREE.MeshBasicMaterial({ color: 0x2ab8ff, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  for (let i = 0; i < 4; i++) {
    const r = new THREE.Mesh(new THREE.RingGeometry(1.6 + i * 0.9, 1.63 + i * 0.9 + (i === 0 ? 0.06 : 0), 128), ringM);
    r.rotation.x = -Math.PI / 2; r.position.y = 0.01; scene.add(r);
  }
  const grid = new THREE.PolarGridHelper(7, 24, 8, 96, 0x1a5f88, 0x0f3a55); grid.material.transparent = true; grid.material.opacity = 0.5; scene.add(grid);
  const scan = new THREE.Mesh(new THREE.TorusGeometry(1.9, 0.02, 8, 128), new THREE.MeshBasicMaterial({ color: 0x7fe8ff, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  scan.rotation.x = Math.PI / 2; scene.add(scan);
  const dust = L.particles(500, [30, 16, 30], 0x58c8ff, 0.07, 3, 0.5); dust.position.y = 5; scene.add(dust);
  return { scan, dust };
}

export function buildScenes() {
  const S = [];

  // ============================================================ 1. BODY INTRO
  {
    const scene = new THREE.Scene(); scene.background = new THREE.Color(0x02060f);
    scene.add(L.backdrop(0x05162a, 0x010308));
    const body = humanHolo(); scene.add(body);
    const st = holoStage(scene);
    const c = cam(38);
    S.push({
      name: 'body', v0: -1.2, v1: 6.4, scene, camera: c, update(lt, v) {
        body.userData.tick(v + 2);
        body.rotation.y = -0.6 + lt * 0.22;
        st.scan.position.y = 4 + Math.sin(lt * 0.9) * 3.8;
        st.dust.rotation.y = lt * 0.03;
        const k = ease(lt / 6.0), d = easeIn(clamp((lt - 5.2) / 2.4));
        c.position.set(lerp(0, 0.6, k), lerp(4.2, 5.4, k), lerp(17, 8.5, k));
        const tgt = V(0, lerp(4.1, 5.3, k), 0);
        // final dive into the chest
        const heartW = V(0.22, 5.6, 0.12).applyAxisAngle(V(0, 1, 0), body.rotation.y);
        c.position.lerp(heartW.clone().add(V(0, 0, 0.6)), d * 0.95);
        tgt.lerp(heartW, d);
        c.lookAt(tgt); shake(c, lt, 0.03);
        return [];
      }
    });
  }

  // ============================================================ 2. VESSEL FLIGHT (reusable)
  function vesselScene(name, v0, v1, opts = {}) {
    const scene = new THREE.Scene(); const fogC = 0x2a0408;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.035);
    const wallM = L.cellMat({ color: 0x9a1a28, amp: 0.55, freq: 0.22, speed: 0.05, rim: 0xff5a5a, rimI: 0.35, rough: 0.7, seed: [3, 3, 3] });
    const wall = new THREE.Mesh(new THREE.CylinderGeometry(6.5, 6.5, 320, 96, 320, true), wallM);
    wallM.side = THREE.BackSide; wall.rotation.x = Math.PI / 2; wall.position.z = -140; scene.add(wall);
    scene.add(new THREE.HemisphereLight(0xffc0c0, 0x400010, 0.9));
    const pl = new THREE.PointLight(0xffd0c0, 22, 30, 2.0); scene.add(pl);
    const key = new THREE.DirectionalLight(0xffffff, 1.4); key.position.set(2, 5, 3); scene.add(key);
    const N = 340, R = rng(opts.seed ?? 5);
    const rbc = new THREE.InstancedMesh(L.rbcGeo(), L.rbcMat(), N); scene.add(rbc);
    const data = [];
    for (let i = 0; i < N; i++) {
      const a = R() * Math.PI * 2, r = Math.sqrt(R()) * 5.2;
      data.push({ x: Math.cos(a) * r, y: Math.sin(a) * r, z: 20 - R() * 230, rx: R() * 6, ry: R() * 6, sx: (R() - .5) * 1.5, sy: (R() - .5) * 1.5, s: 0.75 + R() * 0.25 });
    }
    const dummy = new THREE.Object3D();
    const plasma = L.particles(1600, [12, 12, 240], 0xffb0a0, 0.05, 8, 0.45); plasma.position.z = -100; scene.add(plasma);
    // leukocytes rolling along the wall
    const wbcs = [];
    const nW = opts.wbcs ?? 3;
    for (let i = 0; i < nW; i++) {
      let w;
      const kind = opts.kinds ? opts.kinds[i % opts.kinds.length] : 'leuk';
      if (kind === 't') w = L.tCell(i + 3, 1.0, 4); else if (kind === 'b') w = L.bCell(i + 3, 1.0, 4);
      else if (kind === 'n') w = L.neutrophil(i + 3, 1.1); else w = L.leukocyte(i + 3, opts.wbcR ?? 1.15, 5);
      const a = -Math.PI / 2 + (i % 2 ? 0.7 : -0.6) + (i * 0.37);
      w.userData.base = { a, z: (opts.z0 ?? -40) - i * (opts.gap ?? 22), r: 4.4 };
      scene.add(w); wbcs.push(w);
    }
    let hero = null;
    if (opts.hero) { hero = new THREE.Mesh(L.rbcGeo(), L.rbcMat()); hero.scale.setScalar(0.95); scene.add(hero); }
    const c = cam(52);
    S.push({
      name, v0, v1, scene, camera: c, update(lt, v) {
        const camZ = -lt * (opts.speed ?? 6.5);
        c.position.set(Math.sin(lt * 0.5) * 0.8, Math.cos(lt * 0.4) * 0.6 - 0.3, camZ);
        c.lookAt(Math.sin(lt * 0.5 + 0.6) * 1.2, Math.cos(lt * 0.4 + 0.5) * 0.5 - 0.6, camZ - 10);
        pl.position.copy(c.position).add(V(0, 0, -1));
        for (let i = 0; i < N; i++) {
          const d = data[i];
          let z = d.z - lt * 3.0; // blood flow
          // recycle cells so the tunnel never empties
          const rel = z - camZ; const wrap = ((rel + 230) % 250 + 250) % 250 - 230; z = camZ + wrap;
          dummy.position.set(d.x + Math.sin(lt * 0.7 + i) * 0.3, d.y + Math.cos(lt * 0.6 + i) * 0.3, z);
          dummy.rotation.set(d.rx + lt * d.sx, d.ry + lt * d.sy, 0);
          const dc = dummy.position.distanceTo(c.position);
          dummy.scale.setScalar(d.s * ss(1.8, 3.2, dc));
          dummy.updateMatrix(); rbc.setMatrixAt(i, dummy.matrix);
        }
        rbc.instanceMatrix.needsUpdate = true;
        wbcs.forEach((w, i) => {
          const b = w.userData.base; const zz = b.z - lt * 1.2;
          w.position.set(Math.cos(b.a) * b.r, Math.sin(b.a) * b.r, zz);
          w.rotation.set(lt * 0.8, lt * 0.3 + i, 0);
        });
        if (hero) { hero.position.set(c.position.x + 2.0 - lt * 0.15, c.position.y + 0.5, camZ - 7.5 + lt * 0.35); hero.rotation.set(0.9 + lt * 0.3, lt * 0.4, 0.3); }
        return opts.labels ? opts.labels(lt, v, { rbc, wbcs, data, camZ, c, hero }) : [];
      }
    });
  }
  vesselScene('vessel', 6.4, 12.95, {
    wbcs: 3, gap: 20, hero: true, wbcR: 1.6, labels(lt, v, o) {
      return [lbl(o.hero, 'Эритроцит — қызыл қан жасушасы', win(v, 6.9, 9.6), 120, -110, '#ff9a9a'),
              lbl(o.wbcs[0], 'Лейкоцит — ақ қан жасушасы', win(v, 9.9, 12.9), 130, -110, '#c8d8ff')];
    }
  });

  // ============================================================ 3. PATHOGEN ENTRY THROUGH A SKIN WOUND
  {
    const scene = new THREE.Scene(); const fogC = 0x1a0d10;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.Fog(fogC, 18, 60);
    scene.add(L.backdrop(0x3a2026, 0x120608));
    L.stdLights(scene, { hemiTop: 0xfff0e6, hemiBot: 0x3a1010, hemiI: 1.1, keyI: 2.6, rimC: 0xff9a7a, rimI: 1.0 });
    const NX = 320;
    const geo = new THREE.PlaneGeometry(60, 60, NX, NX); geo.rotateX(-Math.PI / 2);
    const pos = geo.attributes.position; const col = new Float32Array(pos.count * 3);
    const hash = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
    const vn = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi; const u = xf * xf * (3 - 2 * xf), w = yf * yf * (3 - 2 * yf);
      return lerp(lerp(hash(xi, yi), hash(xi + 1, yi), u), lerp(hash(xi, yi + 1), hash(xi + 1, yi + 1), u), w); };
    const cellular = (x, y) => { // cheap voronoi for skin cells
      const xi = Math.floor(x), yi = Math.floor(y); let d1 = 9, d2 = 9;
      for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) { const cx = xi + i + hash(xi + i, yi + j), cy = yi + j + hash(yi + j + 7, xi + i + 3); const d = Math.hypot(x - cx, y - cy); if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d; }
      return d2 - d1; };
    const skinC = new THREE.Color(0xe7b096), skinD = new THREE.Color(0xc48468), woundC = new THREE.Color(0x8a0f16), woundD = new THREE.Color(0x4a0408);
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i);
      const taper = ss(-16, -7, x) * (1 - ss(7, 16, x));
      const wz = z + Math.sin(x * 0.35) * 0.6;
      const groove = Math.exp(-(wz * wz) / (2 * 0.95 * 0.95)) * taper;
      const lip = Math.exp(-Math.pow((Math.abs(wz) - 1.9) / 0.7, 2)) * taper * 0.35;
      const cel = cellular(x * 1.6, z * 1.6);
      const h = 0.14 * Math.min(cel * 2.2, 1) + 0.35 * vn(x * 0.3, z * 0.3) - groove * 2.6 + lip - 0.12 * vn(x * 4, z * 4) * groove;
      pos.setY(i, h);
      const c = skinC.clone().lerp(skinD, 1 - Math.min(cel * 3, 1)).lerp(woundC, ss(0.15, 0.6, groove)).lerp(woundD, ss(0.6, 1, groove));
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3)); geo.computeVertexNormals();
    const skin = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0 }));
    scene.add(skin);
    // a few blood cells pooling inside the wound
    const rbcs = new THREE.InstancedMesh(L.rbcGeo(), L.rbcMat(), 40); const Rr = rng(77); const dm = new THREE.Object3D();
    for (let i = 0; i < 40; i++) { dm.position.set((Rr() - .5) * 10, -2.35 + Rr() * 0.3, (Rr() - .5) * 0.9); dm.rotation.set(Rr() * 3, Rr() * 3, 0); dm.scale.setScalar(0.35); dm.updateMatrix(); rbcs.setMatrixAt(i, dm.matrix); }
    scene.add(rbcs);
    const R = rng(21); const microbes = [];
    for (let i = 0; i < 12; i++) {
      const isV = i % 2 === 1;
      const m = isV ? L.virus(i, 0.28) : L.bacterium(i, 0.55);
      const start = V((R() - .5) * 7, 4 + R() * 4, (R() - .5) * 5 + 1.5);
      const end = V(start.x * 0.6, -1.9 + R() * 0.5, (R() - .5) * 0.6);
      m.userData.path = { start, end, delay: R() * 1.2, spin: V(R(), R(), R()) };
      scene.add(m); microbes.push(m);
    }
    const dust = L.particles(400, [30, 10, 30], 0xfff0e0, 0.06, 4, 0.35); dust.position.y = 3; scene.add(dust);
    const c = cam(42);
    S.push({
      name: 'entry', v0: 12.95, v1: 17.65, scene, camera: c, update(lt, v) {
        microbes.forEach((m, i) => {
          const p = m.userData.path; const k = ease(clamp((lt - p.delay) / 3.6));
          m.position.lerpVectors(p.start, p.end, k);
          m.position.x += Math.sin(lt * 1.3 + i) * 0.25; m.position.y += Math.sin(lt * 2 + i) * 0.1 * (1 - k);
          m.rotation.set(lt * p.spin.x, lt * p.spin.y * 1.5, lt * p.spin.z);
          if (m.userData.flag) m.userData.flag.rotation.x = lt * 9;
        });
        const k = ease(lt / 4.7);
        c.position.set(lerp(-3, 1.0, k), lerp(8.5, 0.0, k), lerp(13, 2.6, k));
        c.lookAt(lerp(0, 0.3, k), lerp(0, -1.9, k), lerp(0, 0, k)); shake(c, lt, 0.03);
        return [lbl(microbes[0].userData.body, 'Бактерия', win(lt, 0.4, 4.4), -200, 120, '#a6f06a'),
                lbl(microbes[1], 'Вирус', win(lt, 0.6, 4.4), 140, 110, '#ff8ae0')];
      }
    });
  }

  // ============================================================ 4. ALARM: leukocytes gather
  {
    const scene = new THREE.Scene(); const fogC = 0x2a0c1e;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.035);
    scene.add(L.backdrop(0x4a1a36, 0x14040c));
    L.stdLights(scene, { hemiTop: 0xffe0f0, hemiBot: 0x300818, hemiI: 1.0, keyI: 2.2, rimC: 0x9aaaff, rimI: 1.4 });
    // tissue cells around
    const R = rng(31);
    for (let i = 0; i < 9; i++) {
      const a = i / 9 * Math.PI * 2; const r = 16 + R() * 4;
      const bc = L.bodyCell(i, 2.6 + R() * 1.2, 0xd97a92, 4); bc.position.set(Math.cos(a) * r, -3 + R() * 4, Math.sin(a) * r - 2); scene.add(bc);
    }
    // capillary overhead
    const capM = L.cellMat({ color: 0xff7a8a, amp: 0.08, freq: 0.8, speed: 0.1, rim: 0xffb0c0, rimI: 0.8, opacity: 0.35, rough: 0.3, seed: [1, 2, 3] });
    capM.side = THREE.DoubleSide;
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 40, 48, 40, true), capM); cap.rotation.z = Math.PI / 2; cap.position.set(0, 4.2, -1.5); cap.renderOrder = 3; scene.add(cap);
    const capR = new THREE.InstancedMesh(L.rbcGeo(), L.rbcMat(), 60); scene.add(capR); const cd = [];
    for (let i = 0; i < 60; i++) cd.push({ x: (R() - .5) * 40, y: (R() - .5) * 1.8, z: (R() - .5) * 1.8, r: R() * 6 });
    // bacteria colony
    const bacs = [];
    for (let i = 0; i < 9; i++) { const b = L.bacterium(i + 40, 0.6); b.userData.o = V((R() - .5) * 2.4, -0.6 + (R() - .5) * 1.2, (R() - .5) * 1.6); b.rotation.set(R() * 3, R() * 3, R() * 3); scene.add(b); bacs.push(b); }
    // alarm waves (cytokines)
    const waves = [];
    for (let i = 0; i < 4; i++) {
      const w = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), new THREE.MeshBasicMaterial({ color: 0xff5a3a, transparent: true, opacity: 0.0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.BackSide }));
      w.position.set(0, -0.6, 0); scene.add(w); waves.push(w);
    }
    const sig = L.particles(350, [8, 8, 6], 0xffa060, 0.09, 12, 0.8); scene.add(sig);
    const sigBase = Float32Array.from(sig.geometry.attributes.position.array);
    // leukocytes squeezing out of the capillary
    const wbc = [];
    for (let i = 0; i < 6; i++) {
      const isMono = i === 3;
      const w = isMono ? L.leukocyte(99, 1.0, 5) : L.neutrophil(i + 60, 0.85);
      const sx = -7 + i * 2.6;
      const tgt = V(Math.cos(i * 1.1) * 2.4, -0.6 + Math.sin(i * 1.7) * 1.2, Math.sin(i * 1.1) * 1.8 + 0.4);
      w.userData.m = { s: V(sx, 4.2, -1.5), e: tgt, t0: 0.6 + i * 0.75 };
      scene.add(w); wbc.push(w);
    }
    const mono = wbc[3];
    const c = cam(44);
    S.push({
      name: 'alarm', v0: 17.65, v1: 26.45, scene, camera: c, update(lt, v) {
        bacs.forEach((b, i) => { const o = b.userData.o; b.position.set(o.x + Math.sin(lt * 1.4 + i) * 0.15, o.y + Math.cos(lt * 1.1 + i) * 0.12, o.z); b.rotation.y += 0.0; b.userData.flag.rotation.x = lt * 10; b.rotation.z = Math.sin(lt + i) * 0.3 + i; });
        waves.forEach((w, i) => { const ph = ((lt * 0.75 + i / waves.length) % 1); w.scale.setScalar(0.5 + ph * 9); w.material.opacity = (1 - ph) * 0.22 * (1 - ss(6.5, 8.5, lt)); });
        const pa = sig.geometry.attributes.position;
        for (let i = 0; i < pa.count; i++) { const k = ((lt * 0.25 + i * 0.013) % 1); pa.setXYZ(i, sigBase[i * 3] * (0.3 + k), -0.6 + k * 5.0 + sigBase[i * 3 + 1] * 0.2, sigBase[i * 3 + 2] * (0.3 + k)); }
        pa.needsUpdate = true; sig.material.opacity = 0.7 * (1 - ss(6, 8, lt));
        const dm = new THREE.Object3D();
        cd.forEach((d, i) => { dm.position.set(((d.x + lt * 4 + 20) % 40) - 20, 4.2 + d.y, -1.5 + d.z); dm.rotation.set(d.r + lt, d.r * 2, 0); dm.scale.setScalar(0.42); dm.updateMatrix(); capR.setMatrixAt(i, dm.matrix); });
        capR.instanceMatrix.needsUpdate = true;
        wbc.forEach((w, i) => {
          const m = w.userData.m; const k = clamp((lt - m.t0) / 3.2);
          const out = ss(0, 0.3, k); // squeeze through the wall
          const p = m.s.clone().lerp(m.e, ease(k)); p.y = lerp(m.s.y, m.e.y, easeOut(k)) ;
          w.position.copy(p);
          const sq = 1 - Math.sin(out * Math.PI) * 0.45; w.scale.set(w.userData.r0 ?? (w.userData.r0 = w.scale.x), 0, 0);
          const r0 = w.userData.r0; w.scale.set(r0 * (2 - sq) * 0.75 + r0 * 0.25, r0 * sq, r0);
          w.rotation.y = lt * 0.4 + i;
          if (w.userData.mat) w.userData.mat.userData.u.uGlow.value = 0.15 * Math.max(0, Math.sin(lt * 3 + i));
        });
        // monocyte -> macrophage
        const mk = ss(5.4, 8.2, lt);
        const mu = mono.userData.mat.userData.u;
        mono.userData.mat.color.set(0xeee8f6).lerp(new THREE.Color(0xe8a868), mk);
        mu.uRim.value.set(0xc8d8ff).lerp(new THREE.Color(0xffd9a8), mk).multiplyScalar(0.8);
        mu.uSpikes.value = mk * 0.35; mu.uAmp.value = 0.08 + mk * 0.05; mu.uFreq.value = 3.6 - mk * 2.0;
        mono.scale.multiplyScalar(1 + mk * 0.55);
        const k = ease(lt / 8.8); const a = lerp(-0.5, 0.45, k);
        c.position.set(Math.sin(a) * lerp(13, 10, k), lerp(3.2, 1.4, k), Math.cos(a) * lerp(13, 10, k));
        c.lookAt(0, lerp(1.4, -0.3, k), 0); shake(c, lt, 0.03);
        return [lbl(bacs[2].userData.body, 'Бактериялар көбейеді', win(lt, 0.3, 3.6), -340, 90, '#a6f06a'),
                lbl(waves[0], 'Дабыл белгілері', win(lt, 1.2, 4.8), -360, -150, '#ffb070'),
                lbl(wbc[1], 'Лейкоциттер', win(lt, 1.6, 5.2), 120, -100, '#c8d8ff'),
                lbl(mono, mk < 0.5 ? 'Моноцит' : 'Моноцит → Макрофаг', win(lt, 5.0, 8.8), 140, -110, '#ffd09a')];
      }
    });
  }

  // ============================================================ 5. PHAGOCYTOSIS close-up
  {
    const scene = new THREE.Scene(); const fogC = 0x220a1c;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.03);
    scene.add(L.backdrop(0x3e1834, 0x12040e));
    L.stdLights(scene, { hemiTop: 0xfff0f4, hemiBot: 0x2a0a20, hemiI: 1.0, keyI: 2.4, rimC: 0x88b0ff, rimI: 1.6 });
    const mac = L.macrophage(5, 1.8, 0.6); mac.position.set(-2.4, 0, 0); scene.add(mac);
    const neu = L.neutrophil(8, 1.15); neu.position.set(2.6, 0.5, -1.2); scene.add(neu);
    const bA = L.bacterium(101, 0.75); scene.add(bA);
    const bB = L.bacterium(102, 0.6); scene.add(bB);
    const extra = []; const R = rng(55);
    for (let i = 0; i < 5; i++) { const b = L.bacterium(110 + i, 0.5); b.position.set(-1 + R() * 6, -2.5 + R() * 1.2, -3 - R() * 3); b.rotation.set(R() * 3, R() * 3, R() * 3); scene.add(b); extra.push(b); }
    const mkBubble = () => { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), new THREE.MeshStandardMaterial({ color: 0xffe0a0, transparent: true, opacity: 0, roughness: 0.2, emissive: 0x553300, depthWrite: false })); m.renderOrder = 1; scene.add(m); return m; };
    const phA = mkBubble(), phB = mkBubble();
    const lyso = (n, seed) => { const arr = []; const r = rng(seed); for (let i = 0; i < n; i++) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 8), new THREE.MeshBasicMaterial({ color: 0xc8ff4a, transparent: true, opacity: 0 })); m.userData.d = V(r() - .5, r() - .5, r() - .5).normalize(); m.renderOrder = 1; scene.add(m); arr.push(m); } return arr; };
    const lyA = lyso(9, 3), lyB = lyso(7, 4);
    const frag = (seed) => { const p = L.particles(70, [0.8, 0.5, 0.5], 0x8a7a3a, 0.08, seed, 0); p.material.blending = THREE.NormalBlending; p.renderOrder = 1; scene.add(p); return p; };
    const fA = frag(7), fB = frag(8);
    const sporeDust = L.particles(500, [24, 14, 16], 0xffc0e0, 0.05, 9, 0.35); scene.add(sporeDust);
    const c = cam(40);
    // engulf choreography for one phagocyte
    function engulf(cell, bac, ph, ly, fr, lt, t0, approachFrom, r) {
      const u = cell.userData.mat.userData.u;
      const C = cell.position;
      const dir = approachFrom.clone().normalize();
      const surf = C.clone().add(dir.clone().multiplyScalar(r * 1.15));
      const inside = C.clone().add(dir.clone().multiplyScalar(r * 0.25));
      const far = C.clone().add(dir.clone().multiplyScalar(r * 2.6)).add(V(0, 0.6, 0.4));
      const k1 = ease(clamp((lt - t0) / 3.6));            // detect + approach
      const k2 = ss(t0 + 3.4, t0 + 4.8, lt);              // pseudopods wrap
      const k3 = ease(clamp((lt - (t0 + 4.6)) / 1.4));    // swallowed
      const k4 = ss(t0 + 6.2, t0 + 9.0, lt);              // digested
      const p = far.clone().lerp(surf, k1).lerp(inside, k3);
      p.y += Math.sin(lt * 2.0) * 0.12 * (1 - k3);
      bac.position.copy(p);
      bac.rotation.set(0.3, Math.atan2(-dir.z, dir.x) + Math.sin(lt * 1.5) * 0.4 * (1 - k3), Math.sin(lt * 1.2) * 0.3);
      bac.userData.flag.rotation.x = lt * 10 * (1 - k3);
      u.uPullDir.value.copy(dir); u.uPull.value = 0.62 * k2 * (1 - k3 * 0.85);
      const s = (1 - k4 * 0.85) * bac.userData.s0;
      bac.scale.setScalar(Math.max(0.001, s));
      bac.userData.body.material.color.set(0x6fcf3a).lerp(new THREE.Color(0x5a4020), k4);
      L.setOpacity(bac, 1 - ss(0.6, 1, k4));
      ph.position.copy(inside); ph.scale.setScalar(r * 0.42 * (1 - k4 * 0.4)); ph.material.opacity = 0.28 * ss(0, 0.5, k3) * (1 - ss(0.7, 1, k4));
      ly.forEach((m, i) => { const kk = ss(t0 + 5.8 + i * 0.08, t0 + 7.4, lt); m.position.copy(inside).add(m.userData.d.clone().multiplyScalar(r * lerp(0.75, 0.38, kk))); m.material.opacity = ss(t0 + 5.4, t0 + 6.0, lt) * (1 - ss(t0 + 8.2, t0 + 9.4, lt)); });
      fr.position.copy(inside); fr.material.opacity = 0.9 * ss(0.3, 0.6, k4) * (1 - ss(0.85, 1, k4)) ; fr.scale.setScalar(1 + k4 * 0.8);
      return { k1, k2, k3, k4 };
    }
    bA.userData.s0 = 0.75; bB.userData.s0 = 0.6;
    S.push({
      name: 'phago', v0: 26.45, v1: 37.8, scene, camera: c, update(lt, v) {
        mac.rotation.y = Math.sin(lt * 0.2) * 0.2;
        const ea = engulf(mac, bA, phA, lyA, fA, lt, 0.6, V(1, 0.15, 0.55), 1.8);
        engulf(neu, bB, phB, lyB, fB, lt, 1.2, V(-0.4, -0.3, 1), 1.15);
        extra.forEach((b, i) => { b.userData.flag.rotation.x = lt * 9; b.position.x += Math.sin(lt + i) * 0.003; });
        sporeDust.rotation.y = lt * 0.02;
        // camera: wide -> push into macrophage -> pull back for the title
        const k = ease(clamp(lt / 6.5)), kb = ease(clamp((lt - 7.8) / 3.0));
        const p1 = V(0.6, 1.4, 11.5), p2 = V(-0.2, 0.6, 5.6), p3 = V(0.3, 1.0, 9.5);
        c.position.copy(p1).lerp(p2, k).lerp(p3, kb);
        const t1 = V(0, 0, 0), t2 = V(-1.2, 0.1, 0.4), t3 = V(0, 0.2, 0);
        c.lookAt(t1.clone().lerp(t2, k).lerp(t3, kb)); shake(c, lt, 0.025);
        return [lbl(mac.userData.outer, 'Макрофаг', win(lt, 0.4, 8.2), -330, -150, '#ffd09a'),
                lbl(neu.userData.outer, 'Нейтрофил', win(lt, 0.8, 8.2), 120, -150, '#ffc8f0'),
                lbl(bA.userData.body, 'Бактерия', win(lt, 0.6, 4.0), 110, 110, '#a6f06a')];
      }
    });
  }

  // ============================================================ 6. LYMPHOCYTE ACTIVATION
  {
    const scene = new THREE.Scene(); const fogC = 0x06182a;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.045);
    scene.add(L.backdrop(0x0c2c48, 0x020812));
    L.stdLights(scene, { hemiTop: 0xe0f0ff, hemiBot: 0x081830, hemiI: 1.0, keyI: 2.4, rimC: 0x6ad0ff, rimI: 1.8 });
    // crowd of lymphocytes (lymph node)
    const crowdN = 140; const R = rng(61);
    const crowdM = [new THREE.MeshStandardMaterial({ color: 0x2f6fe0, roughness: 0.5, emissive: 0x0a2050 }), new THREE.MeshStandardMaterial({ color: 0xd8a02a, roughness: 0.5, emissive: 0x402a05 })];
    const crowd = [0, 1].map(i => { const m = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.8, 2), crowdM[i], crowdN / 2); scene.add(m); return m; });
    const cdat = []; for (let i = 0; i < crowdN; i++) { let p; do { p = V((R() - .5) * 34, (R() - .5) * 16, -4 - R() * 22); } while (p.length() < 5); cdat.push({ p, s: 0.7 + R() * 0.5, ph: R() * 6 }); }
    const dc = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 6), L.cellMat({ color: 0xc9b6e8, amp: 0.1, freq: 1.2, speed: 0.25, rim: 0xe8d8ff, rimI: 0.8, spikes: 1.1, seed: [2, 8, 1] }));
    dc.scale.setScalar(1.3); scene.add(dc);
    // antigen fragments presented on the dendritic cell
    const ag = []; for (let i = 0; i < 10; i++) { const m = new THREE.Mesh(new THREE.OctahedronGeometry(0.12, 0), new THREE.MeshStandardMaterial({ color: 0xff3d6e, emissive: 0xaa1030, roughness: 0.3 })); const d = V(R() - .5, R() - .5, R() * 0.8).normalize(); m.position.copy(d.multiplyScalar(1.35)); dc.add(m); ag.push(m); }
    const T = L.tCell(11, 0.95, 5), B = L.bCell(12, 0.95, 5); scene.add(T, B);
    const Tc = [L.tCell(13, 0.95, 4), L.tCell(14, 0.95, 4)], Bc = [L.bCell(15, 0.95, 4), L.bCell(16, 0.95, 4)];
    [...Tc, ...Bc].forEach(x => { x.visible = false; scene.add(x); });
    const agB = L.bacterium(200, 0.4); scene.add(agB);
    const c = cam(42);
    const dm = new THREE.Object3D();
    S.push({
      name: 'lymph', v0: 37.8, v1: 45.6, scene, camera: c, update(lt, v) {
        let ci = [0, 0];
        cdat.forEach((d, i) => { const k = i % 2; dm.position.copy(d.p).add(V(Math.sin(lt * 0.4 + d.ph) * 0.4, Math.cos(lt * 0.3 + d.ph) * 0.4, 0)); dm.scale.setScalar(d.s); dm.rotation.set(d.ph, lt * 0.2, 0); dm.updateMatrix(); crowd[k].setMatrixAt(ci[k]++, dm.matrix); });
        crowd.forEach(m => m.instanceMatrix.needsUpdate = true);
        dc.rotation.y = lt * 0.12;
        // T cell docks to the presenting cell, B cell grabs an antigen
        const kT = ease(clamp((lt - 0.3) / 2.8)), kB = ease(clamp((lt - 1.0) / 2.8));
        T.position.set(lerp(6, 2.45, kT), lerp(2.5, 0.5, kT), lerp(1, 0.4, kT));
        B.position.set(lerp(-6.5, -2.9, kB), lerp(-2.5, -0.5, kB), lerp(0.5, 0.6, kB));
        agB.position.set(lerp(-4.0, -1.85, kB), lerp(1.2, -0.2, kB), 0.9); agB.rotation.set(lt, lt * 0.7, 0.3); agB.userData.flag.rotation.x = lt * 9;
        T.rotation.y = lt * 0.3; B.rotation.y = -lt * 0.3;
        const gT = ss(3.1, 3.8, lt), gB = ss(3.6, 4.3, lt);
        T.userData.mat.userData.u.uGlow.value = gT * (0.7 + 0.3 * Math.sin(lt * 6));
        B.userData.mat.userData.u.uGlow.value = gB * (0.7 + 0.3 * Math.sin(lt * 6 + 1));
        // clonal expansion
        const kc = ease(clamp((lt - 4.6) / 2.4));
        Tc.forEach((x, i) => { x.visible = kc > 0; x.scale.setScalar(0.95 * kc); x.position.copy(T.position).add(V(0.9 + i * 0.6, (i ? -1 : 1) * 1.1, -0.6 * i).multiplyScalar(kc * 1.4)); x.userData.mat.userData.u.uGlow.value = gT * 0.7; });
        Bc.forEach((x, i) => { x.visible = kc > 0; x.scale.setScalar(0.95 * kc); x.position.copy(B.position).add(V(-0.9 - i * 0.6, (i ? -1 : 1) * 1.1, -0.6 * i).multiplyScalar(kc * 1.4)); x.userData.mat.userData.u.uGlow.value = gB * 0.7; });
        const k = ease(lt / 7.8);
        c.position.set(lerp(1.5, -0.5, k), lerp(1.8, 0.7, k), lerp(13.5, 10.5, k)); c.lookAt(0, 0, 0); shake(c, lt, 0.03);
        return [lbl(dc, 'Антиген ұсынатын жасуша', win(lt, 0.4, 3.0), -200, -230, '#e0d0ff'),
                lbl(T, 'Т-лимфоцит', win(lt, 3.1, 7.8), 100, -130, '#7fc8ff'),
                lbl(B, 'В-лимфоцит', win(lt, 3.5, 7.8), -300, 120, '#ffd770')];
      }
    });
  }

  // ============================================================ 7. T CELL KILLS AN INFECTED CELL
  {
    const scene = new THREE.Scene(); const fogC = 0x140a24;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.035);
    scene.add(L.backdrop(0x2a1648, 0x08040e));
    L.stdLights(scene, { hemiTop: 0xf0e8ff, hemiBot: 0x1a0a30, hemiI: 1.0, keyI: 2.4, rimC: 0x7ad0ff, rimI: 1.6 });
    const cell = L.bodyCell(4, 2.3, 0xd98aa6, 6); cell.scale.set(2.3, 2.1, 2.3); scene.add(cell);
    const cu = cell.userData.mat.userData.u;
    const R = rng(71);
    const vir = []; for (let i = 0; i < 12; i++) { const v = L.virus(300 + i, 0.24); const d = V(R() - .5, R() - .5, R() - .2).normalize(); v.userData.d = d; v.userData.ph = R() * 6; cell.add(v); vir.push(v); }
    const nuc = new THREE.Mesh(new THREE.IcosahedronGeometry(0.4, 3), new THREE.MeshStandardMaterial({ color: 0x7a3a8a })); // hidden (opaque cell)
    const T = L.tCell(21, 1.0, 5); scene.add(T);
    const gran = L.particles(160, [1, 1, 1], 0xff4ad0, 0.12, 5, 0); scene.add(gran);
    const gBase = Float32Array.from(gran.geometry.attributes.position.array);
    const bodies = []; for (let i = 0; i < 7; i++) { const b = L.bodyCell(40 + i, 0.6 + R() * 0.35, 0xb07090, 3); b.userData.d = V(R() - .5, R() - .5, R() - .5).normalize(); b.visible = false; scene.add(b); bodies.push(b); }
    const freeV = []; for (let i = 0; i < 3; i++) { const v = L.virus(330 + i, 0.24); v.userData.d = V(-0.6 - R() * 0.4, R() - .3, R() - .5).normalize(); scene.add(v); freeV.push(v); }
    const c = cam(42);
    S.push({
      name: 'tkill', v0: 45.6, v1: 51.5, scene, camera: c, update(lt, v) {
        const contact = V(2.25, 0.35, 0.9).normalize().multiplyScalar(2.3 + 1.0);
        const kT = ease(clamp(lt / 2.0));
        T.position.copy(V(6.5, 2.4, 2.5).lerp(contact, kT)); T.rotation.y = lt * 0.4;
        const gl = ss(1.9, 2.4, lt);
        T.userData.mat.userData.u.uGlow.value = gl * (0.6 + 0.4 * Math.sin(lt * 9));
        // granule stream (perforin / granzymes)
        const pa = gran.geometry.attributes.position; const from = T.position.clone(), to = contact.clone().setLength(2.2);
        for (let i = 0; i < pa.count; i++) { const k = ((lt * 0.9 + i / pa.count) % 1); const p = from.clone().lerp(to, k); pa.setXYZ(i, p.x + gBase[i * 3] * 0.6 * (1 - k), p.y + gBase[i * 3 + 1] * 0.6 * (1 - k), p.z + gBase[i * 3 + 2] * 0.6 * (1 - k)); }
        pa.needsUpdate = true; gran.material.opacity = 0.9 * ss(2.2, 2.6, lt) * (1 - ss(3.9, 4.3, lt));
        // infected cell dies (apoptosis): blebbing -> shrink -> fragments
        const kb = ss(3.2, 4.6, lt), kd = ss(4.4, 5.6, lt);
        cu.uAmp.value = 0.05 + kb * 0.28; cu.uFreq.value = 1.6 + kb * 1.6; cu.uSpeed.value = 0.15 + kb * 1.2;
        cell.userData.mat.color.set(0xd98aa6).lerp(new THREE.Color(0x7a4a66), kb);
        const sc = 2.3 * (1 - kb * 0.25);
        cell.scale.set(sc, sc * 0.92, sc); cell.visible = kd < 0.98; L.setOpacity(cell, 1 - kd);
        cell.rotation.y = lt * 0.15;
        vir.forEach((x, i) => { x.position.copy(x.userData.d).multiplyScalar(1.02 + 0.06 * Math.sin(lt * 2 + x.userData.ph)); x.rotation.set(lt, lt * 0.5 + i, 0); });
        bodies.forEach((b, i) => { b.visible = kd > 0.02; b.position.copy(b.userData.d).multiplyScalar(0.8 + kd * 2.6); b.rotation.set(lt, i, 0); L.setOpacity(b, kd * (1 - ss(5.3, 5.9, lt))); });
        freeV.forEach((x, i) => { const k = clamp(lt / 6); x.position.copy(x.userData.d).multiplyScalar(2.6 + k * 2.5 + i * 0.6); x.rotation.set(lt, lt + i, 0); });
        const k = ease(lt / 5.9);
        c.position.set(lerp(-1.5, 1.8, k), lerp(1.6, 1.0, k), lerp(12, 9.2, k)); c.lookAt(lerp(0.6, 1.2, k), 0.2, 0); shake(c, lt, 0.03);
        return [lbl(cell, 'Вирус жұқтырған жасуша', win(lt, 0.3, 3.8), -420, -200, '#ffb0d0'),
                lbl(T, 'Т-лимфоцит', win(lt, 0.8, 5.6), 90, -140, '#7fc8ff'),
                lbl(freeV[0], 'Вирус жасуша ішінде көбейеді', win(lt, 0.6, 3.0), -330, 120, '#ff8ae0')];
      }
    });
  }

  // ============================================================ 8. PLASMA CELL, ANTIBODIES, NEUTRALISATION
  {
    const scene = new THREE.Scene(); const fogC = 0x08142a;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.032);
    scene.add(L.backdrop(0x10284a, 0x020610));
    L.stdLights(scene, { hemiTop: 0xe8f0ff, hemiBot: 0x0a1428, hemiI: 1.0, keyI: 2.3, rimC: 0x5ac8ff, rimI: 1.7 });
    const B = L.bCell(31, 0.95, 5); B.position.set(-4.2, 0.6, 0); scene.add(B);
    const bu = B.userData.mat.userData.u;
    const healthy = L.bodyCell(9, 3.6, 0xe39aa8, 6); healthy.position.set(3.0, -5.4, -1.5); scene.add(healthy);
    // receptors on healthy cell
    const recG = new THREE.CylinderGeometry(0.04, 0.06, 0.35, 6); recG.translate(0, 0.17, 0);
    const recs = new THREE.InstancedMesh(recG, new THREE.MeshStandardMaterial({ color: 0x40e0b0, emissive: 0x0a5a40 }), 70); const R = rng(81); const dm = new THREE.Object3D();
    for (let i = 0; i < 70; i++) { const d = V(R() - .5, 0.4 + R(), R() - .5).normalize(); dm.position.copy(d).multiplyScalar(3.6).multiply(V(1, 0.8, 1)).add(healthy.position); dm.quaternion.setFromUnitVectors(V(0, 1, 0), d); dm.updateMatrix(); recs.setMatrixAt(i, dm.matrix); }
    scene.add(recs);
    const vs = [V(1.6, 1.6, 0.4), V(3.4, 0.4, -0.8), V(2.0, -0.6, 1.0), V(4.4, 2.0, 0.2)].map((p, i) => { const v = L.virus(400 + i, 0.42); v.userData.p0 = p; scene.add(v); return v; });
    const NA = 190; const ab = new THREE.InstancedMesh(L.antibodyGeo(), L.antibodyMat(), NA); scene.add(ab);
    const abd = [];
    for (let i = 0; i < NA; i++) {
      const tgt = i < 120 ? i % 4 : -1;
      const d = V(R() - .5, R() - .5, R() - .5).normalize();
      abd.push({ tgt, d, t0: 1.0 + (i / NA) * 3.0, spin: R() * 6, off: V((R() - .5) * 3, (R() - .5) * 3, (R() - .5) * 3), free: V(R() * 9 - 2, (R() - .5) * 7, (R() - .5) * 5) });
    }
    const c = cam(44);
    S.push({
      name: 'antibody', v0: 51.5, v1: 61.4, scene, camera: c, update(lt, v) {
        // B cell -> plasma cell
        const kp = ss(0.2, 1.8, lt);
        B.scale.setScalar(0.95 + kp * 0.55); B.userData.rec.visible = kp < 0.5; B.userData.mat.color.set(0xe0a92a).lerp(new THREE.Color(0xe87a2a), kp);
        bu.uGlow.value = kp * (0.35 + 0.25 * Math.sin(lt * 5)); bu.uAmp.value = 0.035 + kp * 0.04; bu.uFreq.value = 3 + kp * 3;
        B.rotation.y = lt * 0.2;
        // viruses drift; one neutralised virus later tries to reach the healthy cell and fails
        vs.forEach((x, i) => {
          const p = x.userData.p0.clone().add(V(Math.sin(lt * 0.5 + i) * 0.3, Math.cos(lt * 0.4 + i) * 0.3, 0));
          if (i === 2) { const kk = ss(6.0, 7.8, lt), kr = ss(7.9, 9.4, lt); const near = healthy.position.clone().add(V(-0.6, 3.45, 1)); p.lerp(near, kk * (1 - kr * 0.75)); }
          x.position.copy(p); x.rotation.set(lt * 0.4, lt * 0.3 + i, 0);
        });
        const q = new THREE.Quaternion();
        abd.forEach((a, i) => {
          const src = B.position.clone().add(a.d.clone().multiplyScalar(1.5));
          const k = ease(clamp((lt - a.t0) / 2.4));
          let p, quat;
          if (a.tgt >= 0) {
            const vv = vs[a.tgt]; const dir = a.d.clone();
            const surf = vv.position.clone().add(dir.clone().multiplyScalar(0.42 * 1.45));
            const mid = src.clone().lerp(surf, 0.5).add(a.off);
            p = k < 0.5 ? src.clone().lerp(mid, k * 2) : mid.clone().lerp(surf, (k - 0.5) * 2);
            const qb = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), dir.clone().negate());
            const qs = new THREE.Quaternion().setFromEuler(new THREE.Euler(lt * 2 + a.spin, lt + a.spin, 0));
            quat = qs.slerp(qb, ss(0.6, 1, k));
          } else {
            p = src.clone().lerp(src.clone().add(a.free), easeOut(k)); p.y += Math.sin(lt + i) * 0.2;
            quat = new THREE.Quaternion().setFromEuler(new THREE.Euler(lt * 0.8 + a.spin, lt * 0.5 + a.spin, 0));
          }
          dm.position.copy(p); dm.quaternion.copy(quat); dm.scale.setScalar(k > 0 ? 0.55 : 0.0001); dm.updateMatrix(); ab.setMatrixAt(i, dm.matrix);
        });
        ab.instanceMatrix.needsUpdate = true;
        const k = ease(lt / 9.9), kc = ss(5.6, 8.0, lt);
        c.position.set(lerp(-1.0, 1.6, k), lerp(1.8, -0.4, kc), lerp(13, 11, k));
        c.lookAt(lerp(-0.8, 1.8, k), lerp(0.4, -2.4, kc), 0); shake(c, lt, 0.03);
        return [lbl(B, kp < 0.5 ? 'В-лимфоцит' : 'Плазмалық жасуша', win(lt, 0.2, 4.5), -60, -170, '#ffc070'),
                lbl(vs[3], 'Антиденелер', win(lt, 2.4, 6.0), 60, -160, '#9fe8ff'),
                lbl(vs[0], 'Вирус', win(lt, 0.4, 3.4), -160, -140, '#ff8ae0'),
                lbl(healthy, 'Сау жасуша', win(lt, 6.4, 9.8), -330, -260, '#7ff0c8')];
      }
    });
  }

  // ============================================================ 9. INNATE vs ADAPTIVE
  {
    const scene = new THREE.Scene(); const fogC = 0x070c1a;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.02);
    scene.add(L.backdrop(0x101c36, 0x03050c));
    L.stdLights(scene, { hemiTop: 0xf0f0ff, hemiBot: 0x101830, hemiI: 1.0, keyI: 2.3, rimC: 0x88c0ff, rimI: 1.6 });
    const left = new THREE.Group(), right = new THREE.Group(); left.position.x = -4.4; right.position.x = 4.4; scene.add(left, right);
    const n1 = L.neutrophil(51, 0.95); n1.position.set(-0.9, 0.4, 0); left.add(n1);
    const m1 = L.macrophage(52, 1.25, 0.85); m1.position.set(1.0, -0.5, -0.6); left.add(m1);
    const b1 = L.bacterium(53, 0.5); b1.position.set(0.2, 1.4, 0.8); left.add(b1);
    const t1 = L.tCell(54, 0.85, 5); t1.position.set(-0.9, 0.5, 0); right.add(t1);
    const bb = L.bCell(55, 0.85, 5); bb.position.set(1.1, -0.6, 0); right.add(bb);
    const vv = L.virus(56, 0.32); vv.position.set(0.4, 1.6, 0.6); right.add(vv);
    const abs = new THREE.InstancedMesh(L.antibodyGeo(), L.antibodyMat(), 14); right.add(abs);
    const R = rng(91); const ad = []; for (let i = 0; i < 14; i++) ad.push({ p: V((R() - .5) * 3.6, (R() - .5) * 3, (R() - .5) * 2), s: R() * 6 });
    const div = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 12), new THREE.MeshBasicMaterial({ color: 0x8ad8ff, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false }));
    scene.add(div);
    const dust = L.particles(500, [30, 14, 12], 0x9ac8ff, 0.05, 2, 0.35); scene.add(dust);
    const dm = new THREE.Object3D();
    const c = cam(40);
    S.push({
      name: 'compare', v0: 61.4, v1: 78.0, scene, camera: c, update(lt, v) {
        const hl = ss(67.4, 68.2, v) * (1 - ss(72.1, 72.8, v)), hr = ss(72.3, 73.0, v);
        left.scale.setScalar(1 + hl * 0.12 - hr * 0.08); right.scale.setScalar(1 + hr * 0.12 - hl * 0.08);
        [n1, m1].forEach(x => x.userData.mat.userData.u.uGlow.value = hl * 0.35);
        [t1, bb].forEach(x => x.userData.mat.userData.u.uGlow.value = hr * 0.4);
        n1.rotation.y = lt * 0.3; m1.rotation.y = -lt * 0.2; t1.rotation.y = lt * 0.3; bb.rotation.y = -lt * 0.25;
        b1.rotation.set(lt * 0.5, lt * 0.3, 0.4); b1.userData.flag.rotation.x = lt * 9; vv.rotation.set(lt * 0.3, lt * 0.4, 0);
        ad.forEach((a, i) => { dm.position.copy(a.p).add(V(0, Math.sin(lt + i) * 0.2, 0)); dm.rotation.set(lt * 0.6 + a.s, lt * 0.4 + a.s, 0); dm.scale.setScalar(0.42); dm.updateMatrix(); abs.setMatrixAt(i, dm.matrix); });
        abs.instanceMatrix.needsUpdate = true;
        dust.rotation.y = lt * 0.01;
        const pan = hl * -1.2 + hr * 1.2;
        c.position.set(pan + Math.sin(lt * 0.2) * 0.4, 0.6, 15.5 - ss(0, 3, lt) * 1.5); c.lookAt(pan * 0.9, 1.0, 0); shake(c, lt, 0.02);
        return [];
      }
    });
  }

  // ============================================================ 10. IMMUNE MEMORY
  {
    const scene = new THREE.Scene(); const fogC = 0x0a0820;
    scene.background = new THREE.Color(fogC); scene.fog = new THREE.FogExp2(fogC, 0.03);
    scene.add(L.backdrop(0x1c1648, 0x04030c));
    L.stdLights(scene, { hemiTop: 0xeee8ff, hemiBot: 0x100a28, hemiI: 1.0, keyI: 2.2, rimC: 0xa08aff, rimI: 1.8 });
    const mem = []; const haloM = new THREE.MeshBasicMaterial({ color: 0xb8a8ff, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false });
    for (let i = 0; i < 6; i++) {
      const isB = i % 2 === 0; const x = isB ? L.bCell(60 + i, 0.75, 4) : L.tCell(60 + i, 0.75, 4);
      const a = i / 6 * Math.PI * 2; x.userData.a = a; x.userData.isB = isB; scene.add(x);
      const halo = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.018, 8, 96), haloM); x.add(halo); x.userData.halo = halo; mem.push(x);
    }
    const vir = L.virus(70, 0.45); scene.add(vir);
    const NA = 120; const ab = new THREE.InstancedMesh(L.antibodyGeo(), L.antibodyMat(), NA); scene.add(ab);
    const R = rng(101); const ad = []; for (let i = 0; i < NA; i++) ad.push({ src: i % 3, d: V(R() - .5, R() - .5, R() - .5).normalize(), t0: R() * 0.8, s: R() * 6 });
    const dust = L.particles(600, [30, 16, 20], 0xc0b0ff, 0.05, 6, 0.4); scene.add(dust);
    const dm = new THREE.Object3D(); const c = cam(42);
    S.push({
      name: 'memory', v0: 78.0, v1: 88.4, scene, camera: c, update(lt, v) {
        const alert = ss(5.9, 6.6, lt);
        mem.forEach((x, i) => {
          const a = x.userData.a + lt * 0.12 * (1 - alert);
          const r = lerp(3.4, 2.6, alert);
          x.position.set(Math.cos(a) * r - alert * 1.5, Math.sin(a) * r * 0.55, Math.sin(a) * 1.5);
          x.rotation.y = lt * 0.3 + i;
          x.userData.halo.rotation.set(Math.PI / 2 + Math.sin(lt + i) * 0.3, lt * 0.5, 0);
          x.userData.mat.userData.u.uGlow.value = 0.25 + 0.15 * Math.sin(lt * 1.5 + i) + alert * 0.6;
        });
        const kv = ease(clamp((lt - 5.7) / 1.6));
        vir.position.set(lerp(12, 2.6, kv), lerp(1.5, 0.3, kv), 0); vir.rotation.set(lt * 0.5, lt * 0.4, 0); vir.visible = lt > 5.5;
        const bsrc = mem.filter(x => x.userData.isB);
        ad.forEach((a, i) => {
          const k = ease(clamp((lt - 6.5 - a.t0) / 1.4));
          const src = bsrc[a.src].position.clone().add(a.d.clone().multiplyScalar(0.9));
          const surf = vir.position.clone().add(a.d.clone().multiplyScalar(0.45 * 1.4));
          dm.position.copy(src).lerp(surf, k);
          const qb = new THREE.Quaternion().setFromUnitVectors(V(0, 1, 0), a.d.clone().negate());
          const qs = new THREE.Quaternion().setFromEuler(new THREE.Euler(lt * 2 + a.s, lt + a.s, 0));
          dm.quaternion.copy(qs.slerp(qb, ss(0.6, 1, k))); dm.scale.setScalar(k > 0.001 ? 0.45 : 0.0001); dm.updateMatrix(); ab.setMatrixAt(i, dm.matrix);
        });
        ab.instanceMatrix.needsUpdate = true;
        const k = ease(lt / 10.4);
        c.position.set(lerp(-1.2, 1.2, k) + 1.6, lerp(1.2, 0.5, k), lerp(12.5, 10.5, k)); c.lookAt(lerp(-0.8, 0.4, k) + 2.4, 0.3, 0); shake(c, lt, 0.025);
        return [lbl(mem[0], 'В жады жасушасы', win(lt, 0.5, 5.6), -320, -120, '#ffd770'),
                lbl(mem[3], 'Т жады жасушасы', win(lt, 0.9, 5.6), -320, 110, '#7fc8ff'),
                lbl(vir, 'Сол қоздырғыш қайта келді', win(lt, 6.0, 9.0), -200, -150, '#ff8ae0')];
      }
    });
  }

  // ============================================================ 11. PATROL (vessel with immune cells)
  vesselScene('patrol', 88.4, 92.6, { wbcs: 5, gap: 7, z0: -22, kinds: ['n', 't', 'leuk', 'b', 'n'], seed: 9, speed: 5.5 });

  // ============================================================ 12. FINALE: body with a shield
  {
    const scene = new THREE.Scene(); scene.background = new THREE.Color(0x02060f);
    scene.add(L.backdrop(0x061a30, 0x010308));
    const body = humanHolo(); scene.add(body);
    const st = holoStage(scene);
    const shieldM = L.holoMat(0x5ff0ff, 3.0, 0.0, 0);
    const shield = new THREE.Mesh(new THREE.IcosahedronGeometry(5.6, 2), shieldM); shield.position.y = 4.1; scene.add(shield);
    const wire = new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.IcosahedronGeometry(5.62, 2)), new THREE.LineBasicMaterial({ color: 0x5fe8ff, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false }));
    wire.position.y = 4.1; scene.add(wire);
    // microbes bouncing off the shield
    const R = rng(111); const out = [];
    for (let i = 0; i < 8; i++) { const m = i % 2 ? L.virus(500 + i, 0.3) : L.bacterium(500 + i, 0.5); const d = V(R() - .5, (R() - .5) * 0.8, R() - .5).normalize(); m.userData.d = d; m.userData.ph = R() * 3; scene.add(m); out.push(m); }
    const c = cam(38);
    S.push({
      name: 'finale', v0: 92.6, v1: 106, scene, camera: c, update(lt, v) {
        body.userData.tick(v);
        body.rotation.y = 0.4 + lt * 0.12;
        st.scan.position.y = 4 + Math.sin(lt * 0.9) * 3.8; st.dust.rotation.y = lt * 0.03;
        const ks = ease(clamp((lt - 0.6) / 2.6));
        shield.scale.setScalar(0.2 + ks * 0.8); wire.scale.setScalar(0.2 + ks * 0.8);
        shieldM.uniforms.uA.value = ks * (0.75 + 0.25 * Math.sin(lt * 2)); wire.material.opacity = 0.3 * ks;
        wire.rotation.y = lt * 0.08; shield.rotation.y = lt * 0.08;
        out.forEach((m, i) => {
          const ph = ((lt * 0.35 + m.userData.ph) % 3) / 3; // in, hit, bounce out
          const r = 5.9 + Math.abs(ph - 0.5) * 2 * 6;
          m.position.copy(m.userData.d).multiplyScalar(r).add(V(0, 4.1, 0));
          m.rotation.set(lt, lt * 0.7 + i, 0); if (m.userData.flag) m.userData.flag.rotation.x = lt * 9;
          L.setOpacity(m, ks * (1 - ss(10, 11.5, lt)));
        });
        const k = ease(clamp(lt / 6.5));
        c.position.set(lerp(0.4, 0, k), lerp(5.4, 4.6, k), lerp(4.5, 19, k));
        c.lookAt(0, lerp(5.4, 4.0, k), 0); shake(c, lt, 0.03);
        return [];
      }
    });
  }
  return S;
}
