// The guy's studio apartment and props. World units: guy ~560 tall, floor line y=1400.
const R = {
  floorY: 1400, deskX0: 700, deskX1: 1700, deskTop: 1300, deskFront: 1560,
  cageX: 1400, cageW: 290, cageH: 210, doorX: 120, doorW: 330, fridgeX: 1950,
};
function drawWall(c, o) {
  const t = o.t || 0;
  c.fillStyle = vgrad(c, 0, R.floorY, [[0, '#4b3d78'], [1, '#6a58a0']]);
  c.fillRect(-2000, -1500, 6400, R.floorY + 1500);
  // wallpaper stripes + tiny diamonds
  c.save(); c.globalAlpha = 0.18; c.fillStyle = '#8f7cd0';
  for (let x = -2000; x < 4400; x += 90) c.fillRect(x, -1500, 26, R.floorY + 1500);
  c.restore();
  // ceiling
  c.fillStyle = '#3a2f60'; c.fillRect(-2000, -1500, 6400, 1640);
  line(c, [-2000, 140, 4400, 140], 8);
  rrect(c, -2000, 140, 6400, 24, 0); fillStroke(c, '#5a4a8a', 0);
  // floor
  c.fillStyle = vgrad(c, R.floorY, R.floorY + 900, [[0, '#9a5f3a'], [1, '#c98b55']]);
  c.fillRect(-2000, R.floorY, 6400, 2000);
  c.save(); c.strokeStyle = 'rgba(60,30,20,0.35)'; c.lineWidth = 4;
  for (let i = 0; i < 12; i++) { const y = R.floorY + Math.pow(i / 12, 1.6) * 900; c.beginPath(); c.moveTo(-2000, y); c.lineTo(4400, y); c.stroke(); }
  for (let x = -2000; x < 4400; x += 160) { c.beginPath(); c.moveTo(x + 1200 * 0, R.floorY); c.lineTo(1200 + (x - 1200) * 2.4, R.floorY + 1000); c.stroke(); }
  c.restore();
  rrect(c, -2000, R.floorY - 26, 6400, 30, 0); fillStroke(c, '#3a2f60', 0); line(c, [-2000, R.floorY + 4, 4400, R.floorY + 4], 7);
  // rug
  c.save(); c.globalAlpha = o.noRug ? 0 : 1;
  ellipse(c, 1200, 1690, 520, 120, '#c43c5a', 7); ellipse(c, 1200, 1690, 440, 92, '#e2617c', 0);
  ellipse(c, 1200, 1690, 300, 60, '#c43c5a', 0);
  c.restore();
}
function drawWindow(c, o) {
  const t = o.t || 0, x = 1300, y = 520, w = 430, h = 470;
  rrect(c, x - 20, y - 20, w + 40, h + 40, 14); fillStroke(c, '#efe6ff', 7);
  c.save(); rrect(c, x, y, w, h, 6); c.clip();
  c.fillStyle = vgrad(c, y, y + h, [[0, '#1b1e4a'], [1, '#4d3a7d']]); c.fillRect(x, y, w, h);
  circle(c, x + w * .72, y + 110, 46, '#fff3c4', 0); circle(c, x + w * .72 + 18, y + 98, 40, '#26285a', 0);
  for (let i = 0; i < 25; i++) circle(c, x + hash(i) * w, y + hash(i + 9) * h * .5, 2 + hash(i + 3) * 2, `rgba(255,255,255,${.5 + .5 * Math.sin(t * 3 + i)})`, 0);
  for (let i = 0; i < 9; i++) {
    const bx = x - 20 + i * 56, bh = 120 + hash(i * 3.3) * 200;
    c.fillStyle = '#17163a'; c.fillRect(bx, y + h - bh, 50, bh);
    for (let k = 0; k < 10; k++) if (hash(i * 31 + k) > .45) { c.fillStyle = '#ffd36e'; c.fillRect(bx + 8 + (k % 3) * 13, y + h - bh + 16 + Math.floor(k / 3) * 26, 7, 11); }
  }
  c.restore();
  line(c, [x + w / 2, y, x + w / 2, y + h], 12, '#efe6ff'); line(c, [x, y + h * .45, x + w, y + h * .45], 12, '#efe6ff');
  rrect(c, x, y, w, h, 6); fillStroke(c, null, 7);
  // curtains
  for (const s of [0, 1]) {
    const cx = s ? x + w + 10 : x - 70;
    c.beginPath(); c.moveTo(cx, y - 60); c.lineTo(cx + 80, y - 60);
    c.quadraticCurveTo(cx + 60 + (s ? -20 : 20), y + h * .6, cx + 90, y + h + 60); c.lineTo(cx - 10, y + h + 60);
    c.quadraticCurveTo(cx + 10, y + h * .5, cx, y - 60); c.closePath(); fillStroke(c, '#e45b7a', 7);
    line(c, [cx + 30, y - 40, cx + 26, y + h + 40], 5, '#c03d5d');
  }
  rrect(c, x - 110, y - 80, w + 220, 24, 12); fillStroke(c, '#8b5a3c', 6);
}
function drawDoor(c, o) {
  const t = o.t || 0, x = R.doorX, y = R.floorY - 640, w = R.doorW, h = 640;
  rrect(c, x - 26, y - 26, w + 52, h + 26, 6); fillStroke(c, '#d9c7a8', 7);
  rrect(c, x, y, w, h, 4); fillStroke(c, '#9a6a45', 7);
  rrect(c, x + 40, y + 50, w - 80, 230, 8); fillStroke(c, '#87593a', 5);
  rrect(c, x + 40, y + 330, w - 80, 260, 8); fillStroke(c, '#87593a', 5);
  circle(c, x + w - 44, y + 340, 18, '#ffd23f', 5);
  // EXIT sign
  const sf = o.signFall || 0;
  c.save(); c.translate(x + w / 2, y - 90 + sf * 520); c.rotate(sf * 2.2);
  const on = sf > 0 ? (Math.sin(t * 60) > 0 ? 1 : .3) : 1;
  if (on > .5) glow(c, 0, 0, 180, 'rgba(60,255,120,0.5)');
  rrect(c, -110, -40, 220, 80, 12); fillStroke(c, on > .5 ? '#22c55e' : '#14532d', 7);
  text(c, 'ВЫХОД', 0, 3, 46, '#eafff0', { stroke: 6, scol: '#0b3d1e' });
  c.restore();
}
function drawPoster(c, o) {
  const x = 560, y = 640, sf = o.posterFall || 0;
  c.save(); c.translate(x + 140, y + sf * 700); c.rotate(-0.04 + sf * 1.4);
  rrect(c, -140, 0, 280, 360, 6); fillStroke(c, '#ffe9a8', 7);
  c.save(); rrect(c, -120, 20, 240, 250, 4); c.clip();
  c.fillStyle = '#7dd3fc'; c.fillRect(-120, 20, 240, 250);
  withT(c, 0, 250, 0.7, 0, () => drawHamster(c, { eyes: 'cute' }));
  c.restore(); rrect(c, -120, 20, 240, 250, 4); fillStroke(c, null, 5);
  text(c, 'МИЛОТА', 0, 312, 40, '#ff5c8a', { stroke: 6 });
  circle(c, 0, 10, 8, '#e0233a', 4);
  c.restore();
}
function drawFridge(c, o) {
  const x = R.fridgeX, w = 320, h = 600, y = R.floorY + 40 - h;
  rrect(c, x, y, w, h, 26); fillStroke(c, '#eef3f8', 7);
  c.save(); rrect(c, x, y, w, h, 26); c.clip(); c.fillStyle = '#cfdbe8'; c.fillRect(x + w - 50, y, 50, h); c.restore();
  rrect(c, x, y, w, h, 26); fillStroke(c, null, 7);
  line(c, [x, y + 210, x + w, y + 210], 7);
  rrect(c, x + 30, y + 120, 18, 70, 8); fillStroke(c, '#9aa7b6', 5);
  rrect(c, x + 30, y + 240, 18, 110, 8); fillStroke(c, '#9aa7b6', 5);
  // magnets
  circle(c, x + 150, y + 290, 18, '#ff5c8a', 4); rrect(c, x + 200, y + 330, 60, 40, 6); fillStroke(c, '#7dd3fc', 4);
  star4(c, x + 120, y + 380, 22, '#ffd23f');
  rrect(c, x + 160, y + 410, 80, 100, 4); fillStroke(c, '#fff', 4);
  text(c, 'КУПИТЬ:', x + 200, y + 430, 13, INK, { stroke: 0, fam: 'Rubik' }); text(c, 'КОРМ', x + 200, y + 455, 14, '#e0233a', { stroke: 0 });
  text(c, 'хомяку', x + 200, y + 480, 13, INK, { stroke: 0 });
}
function drawMonitor(c, x, y, t, o = {}) {
  // x,y = bottom centre of stand
  c.save(); c.translate(x, y);
  poly(c, [-60, 0, 60, 0, 40, -14, -40, -14], '#2b2b36', 6);
  rrect(c, -14, -70, 28, 60, 4); fillStroke(c, '#2b2b36', 6);
  rrect(c, -150, -240, 300, 180, 14); fillStroke(c, '#22222c', 7);
  c.save(); rrect(c, -136, -226, 272, 152, 6); c.clip();
  c.fillStyle = vgrad(c, -226, -74, [[0, '#2563eb'], [1, '#22d3ee']]); c.fillRect(-140, -230, 280, 160);
  if (o.screen === 'error') {
    c.fillStyle = '#1e3a8a'; c.fillRect(-140, -230, 280, 160);
    text(c, ':(', -90, -180, 46, '#fff', { stroke: 0 }); text(c, 'ХОМЯК ВСЁ СЛОМАЛ', 0, -110, 20, '#fff', { stroke: 0 });
  } else {
    // a little platformer game
    c.fillStyle = '#16a34a'; c.fillRect(-140, -110, 280, 40);
    for (let i = 0; i < 4; i++) { const bx = ((i * 90 - t * 80) % 360 + 360) % 360 - 140; c.fillStyle = '#f59e0b'; c.fillRect(bx, -150, 30, 30); }
    circle(c, -40, -122 - Math.abs(Math.sin(t * 5)) * 30, 14, '#ef4444', 3);
    text(c, 'LVL 99', 80, -205, 18, '#fff', { stroke: 4, fam: 'Press' });
  }
  c.restore();
  glow(c, 0, -150, 300, 'rgba(80,180,255,0.35)');
  c.restore();
}
function drawFoodBag(c, x, y, s, o = {}) {
  // bottom centre at x,y; o.empty 0..1 deflates it; o.shake
  const e = o.empty || 0, sh = o.shake ? Math.sin((o.t || 0) * 50) * 6 * o.shake : 0;
  c.save(); c.translate(x + sh, y); c.scale(s * (1 + e * .15), s * (1 - e * .55));
  c.beginPath(); c.moveTo(-70, 0); c.lineTo(-62, -200); c.lineTo(-74, -230); c.lineTo(74, -230); c.lineTo(62, -200); c.lineTo(70, 0); c.closePath();
  fillStroke(c, '#22c55e', 7);
  c.beginPath(); c.moveTo(-74, -230); c.lineTo(74, -230); c.lineTo(70, -206); c.lineTo(-70, -206); c.closePath(); fillStroke(c, '#15803d', 6);
  text(c, 'КОРМ', 0, -150, 40, '#fff', { stroke: 7 });
  withT(c, 0, -40, 0.32, 0, () => drawHamster(c, { eyes: 'cute' }));
  c.restore();
}
function drawHeadphones(c, x, y, s, rot = 0) {
  withT(c, x, y, s, rot, () => {
    c.beginPath(); c.arc(0, 0, 70, Math.PI * 1.05, Math.PI * 1.95); c.lineWidth = 24; c.strokeStyle = INK; c.stroke(); c.lineWidth = 14; c.strokeStyle = '#2c2c34'; c.stroke();
    for (const k of [-1, 1]) { ellipse(c, k * 68, 6, 26, 36, GUY.phone, 6); ellipse(c, k * 68, 6, 12, 18, '#a51d33', 0); }
  });
}
function drawCage(c, x, y, o = {}) {
  // x,y = bottom-left on the desk
  const w = R.cageW, h = R.cageH, t = o.t || 0;
  // back bars
  c.save(); c.globalAlpha = .55;
  for (let i = 0; i <= 14; i++) line(c, [x + 10 + i * (w - 20) / 14, y - h + 30, x + 10 + i * (w - 20) / 14, y - 20], 3, '#c9d2dc');
  c.restore();
  // wheel
  c.save(); c.translate(x + w - 80, y - 90);
  circle(c, 0, 0, 62, null, 7); circle(c, 0, 0, 54, null, 4);
  c.rotate(t * (o.wheelSpin || 0.3));
  for (let i = 0; i < 8; i++) { const a = i / 8 * TAU; line(c, [0, 0, Math.cos(a) * 56, Math.sin(a) * 56], 4, '#8b95a3'); }
  c.restore(); line(c, [x + w - 80, y - 90, x + w - 80, y - 18], 7);
  // bedding + bowl + bottle
  rrect(c, x, y - 30, w, 30, 8); fillStroke(c, '#f2d38a', 6);
  for (let i = 0; i < 12; i++) ellipse(c, x + 14 + hash(i) * (w - 28), y - 26 + hash(i + 5) * 10, 9, 4, '#e3b863', 0, hash(i) * 3);
  if (!o.noBowl) { ellipse(c, x + 62, y - 30, 34, 12, '#3b82f6', 5); }
  rrect(c, x + 24, y - h + 46, 26, 70, 10); fillStroke(c, 'rgba(160,220,255,0.7)', 5); line(c, [x + 37, y - h + 116, x + 37, y - h + 136], 6);
}
function drawCageFront(c, x, y, o = {}) {
  const w = R.cageW, h = R.cageH;
  // roof
  c.beginPath(); c.moveTo(x - 6, y - h + 30); c.quadraticCurveTo(x + w / 2, y - h - 30, x + w + 6, y - h + 30); c.lineTo(x + w + 6, y - h + 42); c.lineTo(x - 6, y - h + 42); c.closePath();
  fillStroke(c, '#ff7aa2', 6);
  rrect(c, x + w / 2 - 22, y - h - 18, 44, 22, 8); fillStroke(c, '#ff7aa2', 5);
  // front bars (with a door gap in the middle unless door attached)
  const doorOff = o.doorGone || 0;
  for (let i = 0; i <= 14; i++) {
    const bx = x + 10 + i * (w - 20) / 14;
    const inDoor = i >= 5 && i <= 9;
    if (inDoor && doorOff) continue;
    line(c, [bx, y - h + 40, bx, y - 4], 3.5, '#e5ebf2');
  }
  rrect(c, x - 6, y - 14, w + 12, 18, 6); fillStroke(c, '#ff7aa2', 6);
  if (!doorOff) {
    const dx0 = x + 10 + 5 * (w - 20) / 14, dx1 = x + 10 + 9 * (w - 20) / 14;
    rrect(c, dx0 - 6, y - h + 70, dx1 - dx0 + 12, h - 90, 6); fillStroke(c, null, 6);
  }
}
function cageDoor(c, x, y, s, rot) {
  const w = R.cageW, h = R.cageH, dw = 4 * (w - 20) / 14;
  withT(c, x, y, s, rot, () => {
    rrect(c, -dw / 2 - 6, -(h - 90) / 2, dw + 12, h - 90, 6); fillStroke(c, null, 7);
    for (let i = 0; i <= 4; i++) line(c, [-dw / 2 + i * dw / 4, -(h - 90) / 2, -dw / 2 + i * dw / 4, (h - 90) / 2], 5, '#e5ebf2');
    rrect(c, -dw / 2 - 6, -(h - 90) / 2, dw + 12, h - 90, 6); fillStroke(c, null, 6);
  });
}
function drawDesk(c, o = {}) {
  const t = o.t || 0, x0 = R.deskX0, x1 = R.deskX1, top = R.deskTop;
  // legs
  rrect(c, x0 + 30, top, 34, R.deskFront - top, 6); fillStroke(c, '#5b3a29', 6);
  rrect(c, x1 - 64, top, 34, R.deskFront - top, 6); fillStroke(c, '#5b3a29', 6);
  // drawer block
  rrect(c, x0 + 70, top + 40, 200, 180, 8); fillStroke(c, '#8a5a3c', 6);
  line(c, [x0 + 70, top + 130, x0 + 270, top + 130], 6); rrect(c, x0 + 150, top + 80, 40, 12, 6); fillStroke(c, '#ffd23f', 4); rrect(c, x0 + 150, top + 170, 40, 12, 6); fillStroke(c, '#ffd23f', 4);
  // top
  rrect(c, x0 - 10, top - 30, x1 - x0 + 20, 30, 8); fillStroke(c, '#c98b55', 7);
  rrect(c, x0 - 16, top - 4, x1 - x0 + 32, 44, 10); fillStroke(c, '#a86b42', 7);
}
function drawDeskItems(c, o = {}) {
  const t = o.t || 0, top = R.deskTop - 26;
  if (!o.noMonitor) drawMonitor(c, 840, top, t, o);
  if (!o.noKeyboard) { rrect(c, 740, top - 26, 200, 26, 8); fillStroke(c, '#30303c', 6); for (let i = 0; i < 9; i++) { rrect(c, 752 + i * 20, top - 20, 14, 8, 2); fillStroke(c, '#5d5d70', 0); } }
  // energy drink cans
  if (!o.noCans) for (let i = 0; i < 2; i++) { const cx = 1000 + i * 46; rrect(c, cx, top - 80, 36, 80, 8); fillStroke(c, i ? '#38bdf8' : '#a3e635', 6); text(c, 'Z', cx + 18, top - 42, 26, '#111', { stroke: 0 }); }
}
function drawChair(c, x, y, s = 1, rot = 0) {
  withT(c, x, y, s, rot, () => {
    rrect(c, -110, -330, 220, 330, 50); fillStroke(c, '#26262e', 7);
    rrect(c, -60, -300, 120, 260, 30); fillStroke(c, '#e0233a', 0);
    rrect(c, -60, -300, 120, 260, 30); fillStroke(c, null, 5);
    rrect(c, -40, -380, 80, 60, 20); fillStroke(c, '#26262e', 7);
  });
}
function drawLamp(c, x, y, s = 1, rot = 0, on = 1) {
  withT(c, x, y, s, rot, () => {
    ellipse(c, 0, 0, 50, 14, '#3b3b48', 6);
    line(c, [0, 0, 30, -120, -20, -200], 12, INK); line(c, [0, 0, 30, -120, -20, -200], 6, '#5b5b6a');
    c.save(); c.translate(-20, -200); c.rotate(-0.5);
    poly(c, [-50, 40, 50, 40, 26, -30, -26, -30], '#ffd23f', 6); c.restore();
    if (on) glow(c, -40, -150, 160, 'rgba(255,220,120,0.35)');
  });
}
function drawPlant(c, x, y, s = 1, rot = 0) {
  withT(c, x, y, s, rot, () => {
    for (let i = 0; i < 6; i++) { const a = -Math.PI / 2 + (i - 2.5) * 0.35; withT(c, 0, -90, 1, a + Math.PI / 2, () => { ellipse(c, 0, -60, 26, 64, '#22c55e', 6); line(c, [0, -10, 0, -110], 4, '#15803d'); }); }
    poly(c, [-60, -100, 60, -100, 46, 0, -46, 0], '#f97316', 7);
  });
}
function drawBook(c, x, y, s, rot, col) {
  withT(c, x, y, s, rot, () => { rrect(c, -50, -70, 100, 140, 6); fillStroke(c, col, 6); line(c, [-36, -70, -36, 70], 5); });
}
// swirling hell portal (on the floor, perspective ellipse). Draw back/front separately for emerging characters.
function drawPortal(c, x, y, r, t, part = 'all', open = 1) {
  if (open <= 0) return;
  const rx = r * open, ry = r * 0.32 * open;
  if (part !== 'front') {
    glow(c, x, y - 80, rx * 2.2, 'rgba(255,60,20,0.55)', open);
    c.save(); c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, TAU); c.clip();
    const g = c.createRadialGradient(x, y, 0, x, y, rx);
    g.addColorStop(0, '#fff2a8'); g.addColorStop(.25, '#ff8a00'); g.addColorStop(.6, '#d6142c'); g.addColorStop(1, '#3b0418');
    c.fillStyle = g; c.fillRect(x - rx, y - ry, rx * 2, ry * 2);
    c.translate(x, y); c.scale(1, 0.32);
    for (let k = 0; k < 6; k++) {
      c.beginPath();
      for (let i = 0; i <= 40; i++) {
        const u = i / 40, a = k / 6 * TAU + u * 5 - t * 5, rr = u * rx;
        const px = Math.cos(a) * rr, py = Math.sin(a) * rr;
        i ? c.lineTo(px, py) : c.moveTo(px, py);
      }
      c.lineWidth = 26 * open; c.strokeStyle = k % 2 ? 'rgba(80,0,30,0.65)' : 'rgba(255,200,80,0.55)'; c.stroke();
    }
    c.restore();
  }
  if (part !== 'back') {
    c.save(); c.beginPath(); c.ellipse(x, y, rx, ry, 0, 0, Math.PI); c.lineWidth = 18; c.strokeStyle = '#ffb347'; c.stroke();
    c.lineWidth = 7; c.strokeStyle = INK; c.beginPath(); c.ellipse(x, y, rx + 9, ry + 9, 0, 0, TAU); c.stroke(); c.restore();
    // lightning arcs
    for (let k = 0; k < 4; k++) {
      const seed = Math.floor(t * 12) + k * 17; if (hash(seed) < .45) continue;
      const a0 = hash(seed + 1) * TAU; let px = x + Math.cos(a0) * rx, py = y + Math.sin(a0) * ry;
      c.beginPath(); c.moveTo(px, py);
      for (let i = 0; i < 6; i++) { px += (hash(seed + i * 3) - .5) * 120; py -= 40 + hash(seed + i * 5) * 60; c.lineTo(px, py); }
      c.lineWidth = 10; c.strokeStyle = 'rgba(255,240,180,0.9)'; c.stroke(); c.lineWidth = 4; c.strokeStyle = '#fff'; c.stroke();
    }
    // embers
    particles(c, t, 40, i => ({ t0: Math.floor(t) - 2 + hash(i) * 3, x: x + (hash(i + 1) - .5) * rx * 1.6, life: 1.6 + hash(i + 2) }), (c2, p, age, u) => {
      circle(c2, p.x + Math.sin(age * 3 + p.x) * 30, y - age * 420, 7 * (1 - u) + 2, `rgba(255,${150 + 100 * (1 - u)},40,${1 - u})`, 0);
    });
  }
}
function fireBurst(c, x, y, w, h, t, a = 1) {
  // stylised cartoon flames rising from a line
  c.save(); c.globalAlpha *= a;
  for (let i = 0; i < 18; i++) {
    const fx = x - w / 2 + (i + .5) * w / 18, fh = h * (0.55 + 0.45 * Math.abs(noise1(t * 4 + i * 1.7)));
    for (const [col, k] of [['#d6142c', 1], ['#ff7a00', .72], ['#ffd23f', .42]]) {
      c.beginPath(); c.moveTo(fx - w / 18 * k, y);
      c.quadraticCurveTo(fx - w / 30 * k, y - fh * k * .6, fx + noise1(t * 6 + i) * 20, y - fh * k);
      c.quadraticCurveTo(fx + w / 30 * k, y - fh * k * .6, fx + w / 18 * k, y);
      c.closePath(); c.fillStyle = col; c.fill();
    }
  }
  c.restore();
}
function drawRoom(c, o = {}) {
  drawWall(c, o);
  drawWindow(c, o);
  drawDoor(c, o);
  if (!o.noPoster) drawPoster(c, o);
  drawFridge(c, o);
  if (!o.noPlant) drawPlant(c, 1830, 1440, 1);
}
