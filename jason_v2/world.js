// Locations: dusk camp, night forest, cabin (outside + inside), forest path, the big tree.

// ---------------------------------------------------------------- skies (screen space)
function skyNight(c, t, o = {}) {
  c.fillStyle = vgrad(c, 0, H, [[0, '#120c38'], [0.45, '#2f2378'], [0.8, '#5a3aa6'], [1, '#7a4cc0']]); c.fillRect(-W, -H, W * 3, H * 3);
  for (let i = 0; i < 90; i++) {
    const x = hash(i * 3.3) * W, y = hash(i * 7.1) * H * 0.62, tw = 0.5 + 0.5 * Math.sin(t * (2 + hash(i) * 4) + i);
    if (i % 9 === 0) star4(c, x, y, 9 + 6 * tw, `rgba(255,250,220,${0.5 + 0.5 * tw})`, t * .5 + i);
    else circle(c, x, y, 2 + 2 * hash(i * 1.7), `rgba(255,255,240,${0.4 + 0.6 * tw})`, 0);
  }
  if (o.moon !== false) {
    const [mx, my] = o.moon || [800, 330], r = o.r || 110;
    glow(c, mx, my, r * 3.4, 'rgba(255,240,190,0.55)');
    circle(c, mx, my, r, '#fff6c8', 7);
    circle(c, mx - r * .35, my - r * .15, r * .2, '#f2e3a2', 0); circle(c, mx + r * .3, my + r * .3, r * .14, '#f2e3a2', 0);
    circle(c, mx + r * .1, my - r * .45, r * .1, '#f2e3a2', 0);
  }
}
function skyDusk(c, t, dark = 0) {
  c.fillStyle = vgrad(c, 0, H, [[0, '#4b2c9a'], [0.4, '#ff5f8f'], [0.75, '#ff9a5a'], [1, '#ffd36b']]); c.fillRect(-W, -H, W * 3, H * 3);
  glow(c, 760, 900, 520, 'rgba(255,230,140,0.7)');
  circle(c, 760, 900, 120, '#ffe680', 0);
  for (let i = 0; i < 4; i++) {
    const x = (i * 330 + t * 30) % (W + 400) - 200, y = 300 + i * 110;
    c.save(); c.globalAlpha = .9;
    for (const [dx, dy, r] of [[0, 0, 60], [60, -20, 70], [130, 0, 55], [60, 20, 60]]) circle(c, x + dx, y + dy, r, '#ffb3c7', 0);
    c.restore();
  }
  if (dark > 0) { c.fillStyle = `rgba(18,12,56,${dark})`; c.fillRect(-W, -H, W * 3, H * 3); }
}

// ---------------------------------------------------------------- vegetation
const TREE = { a: '#2fae6e', b: '#1f7f52', trunk: '#8a5232' };
const TREE_N = { a: '#1d8a6a', b: '#146750', trunk: '#5e3a2a' };
const TREE_FAR = { a: '#36307a', b: '#2a2566', trunk: '#2a2566' };
function pine(c, x, y, h, col = TREE, lw = 6) {
  const w = h * 0.52;
  rrect(c, x - w * .09, y - h * .2, w * .18, h * .22, 6); fillStroke(c, col.trunk, lw);
  for (let k = 0; k < 3; k++) {
    const by = y - h * (0.16 + k * 0.26), ty = by - h * 0.42, hw = w * (0.5 - k * 0.11);
    const path = () => { c.beginPath(); c.moveTo(x, ty); c.quadraticCurveTo(x + hw * .5, ty + (by - ty) * .5, x + hw, by - 8);
      c.quadraticCurveTo(x + hw * .5, by + 12, x, by + 4); c.quadraticCurveTo(x - hw * .5, by + 12, x - hw, by - 8);
      c.quadraticCurveTo(x - hw * .5, ty + (by - ty) * .5, x, ty); c.closePath(); };
    path(); c.fillStyle = col.b; c.fill();
    c.save(); path(); c.clip(); c.translate(-hw * .18, -4); path(); c.fillStyle = col.a; c.fill(); c.restore();
    path(); fillStroke(c, null, lw);
  }
}
function forestRow(c, y, x0, x1, seed, hmin, hmax, col, lw = 6, gap = 0.62) {
  let x = -3000;
  let i = 0;
  while (x < x1 && x < 6000) {
    const h = lerp(hmin, hmax, hash(seed * 31 + i * 1.7)), w = h * 0.52;
    if (x + w > x0) pine(c, x, y + hash(seed + i * 5.3) * 30, h, col, lw);
    x += w * (gap + hash(seed * 7 + i * 2.9) * 0.4); i++;
  }
}
function ground(c, y, col = '#2f8a5c', colSh = '#246c48') {
  c.fillStyle = col; c.fillRect(-3000, y, 9000, 4000);
  c.fillStyle = colSh;
  for (let i = 0; i < 40; i++) { const x = -2000 + i * 180 + hash(i) * 80; ellipse(c, x, y + 60 + hash(i * 3) * 400, 60, 14, colSh, 0); }
  line(c, [-3000, y, 6000, y], 7);
}
function fog(c, y, h, a = 0.4, t = 0) {
  for (let k = 0; k < 3; k++) {
    c.save(); c.globalAlpha = a * (0.5 + 0.25 * k);
    c.fillStyle = '#c9b8ff';
    for (let i = -6; i < 12; i++) { const x = i * 260 + Math.sin(t * .4 + k + i) * 40 + k * 90; ellipse(c, x, y + k * h * .25, 200, h * .35, '#c9b8ff', 0); }
    c.restore();
  }
}

// ---------------------------------------------------------------- props
function campfire(c, x, y, s, t, a = 1) {
  withT(c, x, y, s, 0, () => {
    glow(c, 0, -60, 420 * a, 'rgba(255,170,60,0.55)', a);
    for (const r of [-0.35, 0.35]) withT(c, 0, -10, 1, r, () => { rrect(c, -90, -16, 180, 32, 14); fillStroke(c, '#8a5232', 6); });
    const fl = (sc, col, ph) => {
      c.beginPath(); c.moveTo(-60 * sc, 0);
      for (let i = 0; i <= 6; i++) { const u = i / 6, xx = lerp(-60, 60, u) * sc, hh = (i % 2 ? 160 : 90) * sc * (1 + .2 * Math.sin(t * 12 + i + ph)) * a; c.quadraticCurveTo(xx - 10 * sc, -hh * .6, xx, -hh); }
      c.lineTo(60 * sc, 0); c.closePath(); fillStroke(c, col, sc > .9 ? 6 : 0);
    };
    if (a > 0.05) { fl(1, '#ff6a2a', 0); fl(.7, '#ffb02e', 1); fl(.4, '#fff1a0', 2); }
  });
}
function campChair(c, x, y, s, front) {
  withT(c, x, y, s, 0, () => {
    if (!front) {
      for (const sx of [-1, 1]) { line(c, [sx * 130, -420, sx * 112, 0], 10); line(c, [sx * 112, -160, -sx * 100, 0], 10); }
      rrect(c, -130, -440, 260, 300, 26); fillStroke(c, '#3ec1ff', 6);
      rrect(c, -130, -440, 260, 60, 26); fillStroke(c, '#2b8fd6', 6);
    } else {
      rrect(c, -140, -170, 280, 50, 20); fillStroke(c, '#2b8fd6', 6);
      for (const sx of [-1, 1]) { rrect(c, sx * 150 - 26, -260, 52, 24, 10); fillStroke(c, '#e8364f', 5); }
    }
  });
}
function logSeat(c, x, y, s) {
  withT(c, x, y, s, 0, () => {
    rrect(c, -220, -90, 440, 90, 40); fillStroke(c, '#a8643a', 6);
    line(c, [-180, -54, -60, -50], 5, '#7a4428'); line(c, [20, -40, 160, -46], 5, '#7a4428');
    ellipse(c, 220, -45, 30, 45, '#f0c48a', 6); ellipse(c, 220, -45, 14, 22, null, 4);
  });
}

// ---------------------------------------------------------------- cabin (front view, local units: 760 wide, base y=0)
const CAB = { w: 760, h: 420, win: [420, -300, 230, 180], door: [80, -300, 160, 300] };
function cabin(c, x, y, s, t, o = {}) {
  withT(c, x, y, s, 0, () => {
    const [wx, wy, ww, wh] = CAB.win, [dx, dy, dw, dh] = CAB.door, top = -CAB.h;
    // chimney + smoke
    rrect(c, 540, top - 260, 90, 220, 10); fillStroke(c, '#9a8a9e', 6);
    for (let k = 0; k < 4; k++) { const ph = (t * .3 + k * .25) % 1; c.save(); c.globalAlpha = .55 * (1 - ph); circle(c, 585 + Math.sin(ph * 6 + k) * 30, top - 280 - ph * 300, 30 + 50 * ph, '#e8e0ff', 0); c.restore(); }
    // window + door openings (what's inside)
    rrect(c, wx, wy, ww, wh, 10); fillStroke(c, o.dark ? '#3a2a50' : '#ffd36b', 0);
    if (o.inside) { c.save(); rrect(c, wx, wy, ww, wh, 10); c.clip(); o.inside(c, wx, wy, ww, wh); c.restore(); }
    rrect(c, dx, dy, dw, dh, 12); fillStroke(c, '#ffcf6b', 0);
    // log wall with holes for window/door
    c.save();
    c.beginPath(); c.rect(0, top, CAB.w, CAB.h); rrectP(c, wx, wy, ww, wh, 10); rrectP(c, dx, dy, dw, dh + 2, 12);
    c.fillStyle = '#c8743c'; c.fill('evenodd'); c.clip('evenodd');
    for (let yy = top; yy < 0; yy += 46) { rrect(c, -20, yy + 4, CAB.w + 40, 40, 20); fillStroke(c, (yy / 46) % 2 ? '#c8743c' : '#d6844a', 5); }
    c.fillStyle = 'rgba(80,30,10,0.18)'; c.fillRect(CAB.w - 120, top, 120, CAB.h);
    c.restore();
    rrect(c, 0, top, CAB.w, CAB.h, 4); fillStroke(c, null, 7);
    for (let yy = top + 23; yy < 0; yy += 46) for (const ex of [-8, CAB.w + 8]) { circle(c, ex, yy, 22, '#f0c48a', 5); circle(c, ex, yy, 9, null, 3); }
    // door
    const dO = o.doorOpen || 0;
    if (dO < 0.05) {
      rrect(c, dx, dy, dw, dh, 12); fillStroke(c, '#8a4a2a', 7);
      for (let i = 1; i < 3; i++) line(c, [dx + i * dw / 3, dy + 14, dx + i * dw / 3, -14], 4, '#6a361e');
      circle(c, dx + dw - 26, dy + 160, 10, '#ffd23f', 4);
    } else {
      const ww2 = dw * (1 - dO * .85);
      poly(c, [dx, dy, dx - ww2 * .3, dy + 16, dx - ww2 * .3, -6, dx, 0], '#8a4a2a', 7);
      if (o.doorBang) glow(c, dx + dw / 2, dy + dh / 2, 300, 'rgba(255,220,120,0.6)', o.doorBang);
    }
    // window frame / shutters
    const sO = o.shutters || 0;
    if (sO < 0.05) {
      line(c, [wx + ww / 2, wy, wx + ww / 2, wy + wh], 10, '#8a4a2a'); line(c, [wx, wy + wh / 2, wx + ww, wy + wh / 2], 10, '#8a4a2a');
      c.save(); c.globalAlpha = .5; line(c, [wx + 20, wy + 50, wx + 50, wy + 20], 8, '#fff'); c.restore();
    } else {
      for (const sd of [-1, 1]) {
        const ax = sd < 0 ? wx : wx + ww, wd = ww / 2 * Math.cos(sO * Math.PI * 0.5), push = Math.sin(sO * Math.PI * .5) * 18;
        const ox = sd < 0 ? ax - (ww / 2) * Math.sin(sO * Math.PI * .5) : ax + (ww / 2) * Math.sin(sO * Math.PI * .5);
        poly(c, [ax, wy, ox, wy - push, ox, wy + wh + push, ax, wy + wh], '#8a4a2a', 7);
        line(c, [(ax + ox) / 2, wy + 10, (ax + ox) / 2, wy + wh - 10], 4, '#6a361e');
      }
    }
    rrect(c, wx, wy, ww, wh, 10); fillStroke(c, null, 8);
    if (o.front) o.front(c, wx, wy, ww, wh);
    rrect(c, wx - 20, wy + wh, ww + 40, 26, 8); fillStroke(c, '#8a4a2a', 6);
    // roof
    const rp = [-80, top + 20, CAB.w / 2, top - 260, CAB.w + 80, top + 20, CAB.w + 80, top + 60, -80, top + 60];
    poly(c, rp, '#e8364f', 7);
    c.save(); c.beginPath(); c.moveTo(rp[0], rp[1]); for (let i = 2; i < rp.length; i += 2) c.lineTo(rp[i], rp[i + 1]); c.closePath(); c.clip();
    for (let i = 1; i < 7; i++) { const yy = top - 260 + i * 46; line(c, [-200, yy, CAB.w + 200, yy], 5, '#b8243a'); }
    c.fillStyle = 'rgba(0,0,0,0.15)'; c.fillRect(CAB.w / 2, top - 300, 600, 400); c.restore();
    poly(c, rp, null, 7);
    // porch lantern
    glow(c, dx + dw + 60, dy + 50, 200, 'rgba(255,210,120,0.6)', o.dark ? 0.3 : 1);
    line(c, [dx + dw + 60, dy + 10, dx + dw + 60, dy + 30], 5);
    rrect(c, dx + dw + 42, dy + 30, 36, 44, 8); fillStroke(c, '#ffe08a', 5);
    rrect(c, dx - 40, -6, dw + 80, 30, 8); fillStroke(c, '#8a4a2a', 6);
  });
}
// wall strip under the window, redrawn over someone leaning out
function cabinSill(c, x, y, s) {
  withT(c, x, y, s, 0, () => {
    const [wx, wy, ww, wh] = CAB.win;
    c.save(); c.beginPath(); c.rect(wx - 30, wy + wh, ww + 60, -(wy + wh) + 40); c.clip();
    c.fillStyle = '#c8743c'; c.fillRect(wx - 30, wy + wh, ww + 60, 400);
    for (let yy = -CAB.h; yy < 0; yy += 46) if (yy + 44 > wy + wh) { rrect(c, wx - 60, yy + 4, ww + 120, 40, 20); fillStroke(c, (yy / 46) % 2 ? '#c8743c' : '#d6844a', 5); }
    c.restore();
    rrect(c, wx - 20, wy + wh, ww + 40, 26, 8); fillStroke(c, '#8a4a2a', 6);
  });
}

// ---------------------------------------------------------------- interior (screen-ish world: window rect given)
function interiorRoom(c, t, o = {}) {
  const [wx, wy, ww, wh] = o.win || [60, 520, 470, 560], floorY = o.floorY || 1560;
  // night view through the window
  c.save(); rrect(c, wx, wy, ww, wh, 16); c.clip();
  c.fillStyle = vgrad(c, wy, wy + wh, [[0, '#1a1446'], [1, '#4a3290']]); c.fillRect(wx, wy, ww, wh);
  circle(c, wx + ww * .75, wy + 90, 46, '#fff6c8', 5);
  forestRow(c, wy + wh * .7, wx - 100, wx + ww + 100, 3, wh * .35, wh * .55, TREE_FAR, 4);
  c.fillStyle = '#22604a'; c.fillRect(wx, wy + wh * .72, ww, wh);
  if (o.outside) o.outside(c, wx, wy, ww, wh);
  fog(c, wy + wh * .78, 90, 0.35, t);
  c.restore();
  // wall (planks) with window hole
  c.save(); c.beginPath(); c.rect(-2000, -2000, 5000, floorY + 2000); rrectP(c, wx, wy, ww, wh, 16); c.clip('evenodd');
  c.fillStyle = '#d98a4e'; c.fillRect(-2000, -2000, 5000, floorY + 2000);
  for (let yy = -2000 + ((floorY + 2000) % 70); yy < floorY; yy += 70) { line(c, [-2000, yy, 3000, yy], 5, '#b8693a'); }
  for (let i = 0; i < 40; i++) circle(c, -1000 + hash(i) * 3000, -600 + hash(i * 3) * 2100, 6, '#b8693a', 0);
  c.restore();
  // floor
  c.fillStyle = '#8c4a2a'; c.fillRect(-2000, floorY, 5000, 3000); line(c, [-2000, floorY, 3000, floorY], 8);
  for (let i = -20; i < 30; i++) line(c, [540 + i * 90, floorY, 540 + i * 260, floorY + 1600], 4, '#6e3820');
  ellipse(c, 700, floorY + 240, 520, 110, '#e8364f', 7); ellipse(c, 700, floorY + 240, 420, 80, null, 5);
  // window frame + curtains
  rrect(c, wx - 26, wy - 26, ww + 52, wh + 52, 22); fillStroke(c, null, 0);
  c.save(); c.lineWidth = 26; c.strokeStyle = '#8a4a2a'; rrect(c, wx - 13, wy - 13, ww + 26, wh + 26, 18); c.stroke(); c.restore();
  rrect(c, wx - 26, wy - 26, ww + 52, wh + 52, 22); fillStroke(c, null, 7); rrect(c, wx, wy, ww, wh, 16); fillStroke(c, null, 6);
  const sO = o.shutters || 0;
  if (sO < 0.05) { line(c, [wx + ww / 2, wy, wx + ww / 2, wy + wh], 14, '#8a4a2a'); line(c, [wx, wy + wh / 2, wx + ww, wy + wh / 2], 14, '#8a4a2a'); }
  rrect(c, wx - 40, wy + wh + 10, ww + 80, 34, 10); fillStroke(c, '#8a4a2a', 6);
  for (const sd of [-1, 1]) {
    const ax = sd < 0 ? wx - 30 : wx + ww + 30, cw = 150, wind = (o.wind || 0) * Math.sin(t * 9 + sd) * 40;
    const inner = ax - sd * cw;
    c.beginPath(); c.moveTo(ax + sd * 20, wy - 70); c.lineTo(inner, wy - 70);
    c.quadraticCurveTo(inner - sd * 30 + wind, wy + wh * .5, inner - sd * 10 + wind * 1.6, wy + wh + 70); c.lineTo(ax + sd * 20, wy + wh + 70); c.closePath();
    fillStroke(c, '#ff4d6d', 7);
    c.save(); c.clip(); for (let k = 0; k < 6; k++) { const xx = lerp(ax, inner, k / 5); line(c, [xx, wy - 80, xx + wind * k / 5, wy + wh + 80], 14, 'rgba(255,255,255,0.35)'); } c.restore();
  }
  rrect(c, wx - 200, wy - 92, ww + 400, 24, 12); fillStroke(c, '#5a3a24', 5);
  // calendar "13"
  if (o.calendar !== false) {
    const cx = wx + ww + 330, cy = wy + 120;
    withT(c, cx, cy, 1, 0.05, () => {
      rrect(c, -90, -70, 180, 200, 14); fillStroke(c, '#fff', 7); rrect(c, -90, -70, 180, 52, 14); fillStroke(c, '#e8364f', 7);
      text(c, 'ПЯТНИЦА', 0, -44, 26, '#fff', { stroke: 0 }); text(c, '13', 0, 50, 96, '#e8364f', { stroke: 0 });
    });
    // antlers
    withT(c, cx, wy - 220, 1, 0, () => {
      rrect(c, -50, -40, 100, 90, 30); fillStroke(c, '#8a4a2a', 6);
      for (const s of [-1, 1]) limb(c, [s * 30, -30, s * 90, -110, s * 140, -130], 22, '#fff1d6', 6), limb(c, [s * 86, -100, s * 100, -170], 18, '#fff1d6', 6);
    });
  }
  // table + lamp
  const lx = o.lampX || 1150, ly = floorY - 360;
  glow(c, lx, ly - 90, 600, 'rgba(255,200,110,0.45)');
  for (const sx of [-1, 1]) rrect(c, lx + sx * 200 - 14, ly + 20, 28, 340, 8), fillStroke(c, '#8a4a2a', 6);
  rrect(c, lx - 250, ly, 500, 40, 14); fillStroke(c, '#a8643a', 6);
  rrect(c, lx - 40, ly - 120, 80, 120, 20); fillStroke(c, '#ffe08a', 6);
  poly(c, [lx - 70, ly - 120, lx + 70, ly - 120, lx + 40, ly - 160, lx - 40, ly - 160], '#3a3a48', 6);
}

// ---------------------------------------------------------------- the big tree
function bigTree(c, x, y, s = 1) {
  withT(c, x, y, s, 0, () => {
    for (const sd of [-1, 1]) poly(c, [sd * 140, -240, sd * 360, 10, sd * 230, 20, sd * 70, 0], '#8a5232', 7);
    const tr = () => { c.beginPath(); c.moveTo(-250, 0); c.bezierCurveTo(-220, -600, -200, -1400, -230, -2600); c.lineTo(230, -2600); c.bezierCurveTo(200, -1400, 220, -600, 250, 0); c.closePath(); };
    tr(); c.fillStyle = '#6e3f26'; c.fill();
    c.save(); tr(); c.clip(); c.translate(-50, 0); tr(); c.fillStyle = '#8a5232'; c.fill();
    for (let i = 0; i < 14; i++) { const bx = -180 + hash(i * 3) * 360, by = -100 - hash(i * 7) * 2300; line(c, [bx, by, bx + 10, by - 160 - hash(i) * 140], 7, '#5e3420'); }
    c.restore(); tr(); fillStroke(c, null, 8);
    ellipse(c, -60, -760, 50, 70, '#5e3420', 7); ellipse(c, -60, -760, 24, 36, '#2a1a12', 0);
  });
}

// ---------------------------------------------------------------- forest path (perspective, screen space)
const PZ = { hz: 760, f: 900, ch: 420, cx: 540 };
function pp(X, Z) { const z = Math.max(Z, 1); return [PZ.cx + X / z * PZ.f, PZ.hz + PZ.ch / z * PZ.f]; }
function ps(Z) { return PZ.f / Math.max(Z, 1); }
function pathScene(c, t, camz, actors = []) {
  skyNight(c, t, { moon: [800, 230], r: 90 });
  forestRow(c, PZ.hz + 10, -400, 1500, 9, 260, 420, TREE_FAR, 4, 0.5);
  c.fillStyle = '#2f8a5c'; c.fillRect(-500, PZ.hz, 2200, 2000);
  const pw = 520;
  const a = pp(-pw / 2, 30), b = pp(pw / 2, 30), cc = pp(pw / 2, 9000), d = pp(-pw / 2, 9000);
  poly(c, [a[0], a[1], b[0], b[1], cc[0], cc[1], d[0], d[1]], '#e0a86a', 0);
  poly(c, [pp(0, 30)[0], a[1], b[0], b[1], cc[0], cc[1], pp(0, 9000)[0], cc[1]], '#cf9458', 0);
  const items = [];
  for (let i = 0; i < 60; i++) {
    const side = i % 2 ? -1 : 1, X = side * lerp(pw * .75, pw * 3, hash(i * 3.7));
    const Z = ((hash(i * 9.1) * 9000 - camz) % 9000 + 9000) % 9000 + 60;
    items.push([Z, 'tree', X, lerp(900, 1500, hash(i * 2.3))]);
  }
  for (let i = 0; i < 14; i++) { const Z = ((hash(i * 4.4) * 9000 - camz) % 9000 + 9000) % 9000 + 60; items.push([Z, 'rock', lerp(-pw * .4, pw * .4, hash(i * 6.2)), 0]); }
  actors.forEach(a2 => items.push([a2[0], 'actor', a2[1]]));
  items.sort((p, q) => q[0] - p[0]);
  for (const it of items) {
    if (it[1] === 'actor') { it[2](c); continue; }
    const [x, y] = pp(it[2], it[0]), s = ps(it[0]);
    if (it[1] === 'tree') {
      const haze = clamp((it[0] - 1500) / 6000);
      pine(c, x, y, it[3] * s, haze > .5 ? TREE_FAR : TREE, Math.max(2, 6 * Math.min(1, s * 1.4)));
    } else ellipse(c, x, y, 30 * s, 16 * s, '#9a8aa8', Math.max(1.5, 5 * Math.min(1, s * 2)));
  }
  c.save(); c.globalAlpha = .5; c.fillStyle = vgrad(c, PZ.hz - 80, PZ.hz + 160, [[0, 'rgba(201,184,255,0)'], [0.5, 'rgba(201,184,255,0.8)'], [1, 'rgba(201,184,255,0)']]);
  c.fillRect(0, PZ.hz - 80, W, 240); c.restore();
}
