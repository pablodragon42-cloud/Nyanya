// Characters: the hamster, the guy, the demon. Same model sheet in every shot.

// ================================================================ HAMSTER
const HAM = {
  fur: '#f5a63f', furSh: '#d8802a', furHi: '#ffc978', cream: '#fff4de', creamSh: '#eed6b2',
  pink: '#ffa3b4', pinkD: '#ff6b8c', paw: '#ffc3cb', brow: '#5a3216',
};
function blinkAt(t, seed = 0, every = 3.1) {
  const ph = (t + hash(seed) * every) % every;
  return ph < 0.13 ? Math.sin(ph / 0.13 * Math.PI) : 0;
}
function hamBodyPath(c) {
  c.beginPath();
  c.moveTo(-72, 0);
  c.bezierCurveTo(-126, 0, -124, -70, -113, -112);
  c.bezierCurveTo(-101, -174, -97, -240, 0, -242);
  c.bezierCurveTo(97, -240, 101, -174, 113, -112);
  c.bezierCurveTo(124, -70, 126, 0, 72, 0);
  c.closePath();
}
function hamArm(c, sx, sy, px, py, lw, behind) {
  const mx = (sx + px) / 2 + (sx < 0 ? -10 : 10), my = (sy + py) / 2 + 6;
  c.beginPath(); c.moveTo(sx, sy); c.quadraticCurveTo(mx, my, px, py);
  c.lineCap = 'round'; c.lineWidth = 30 + lw * 2; c.strokeStyle = INK; c.stroke();
  c.lineWidth = 30; c.strokeStyle = behind ? HAM.furSh : HAM.fur; c.stroke();
  circle(c, px, py, 15, HAM.paw, lw);
  line(c, [px - 6, py + 4, px - 4, py + 12], 3); line(c, [px + 4, py + 4, px + 5, py + 12], 3);
}
function hamEye(c, x, y, o, side) {
  const st = o.eyes || 'normal';
  const r = st === 'cute' ? 21 : st === 'shock' ? 24 : 16;
  const lx = (o.look ? o.look[0] : 0) * 5, ly = (o.look ? o.look[1] : 0) * 5;
  if (st === 'closed') {
    c.beginPath(); c.arc(x, y + 6, 14, Math.PI * 1.1, Math.PI * 1.9); c.lineWidth = 7; c.strokeStyle = INK; c.lineCap = 'round'; c.stroke();
    return;
  }
  if (st === 'shock') {
    ellipse(c, x, y, r, r * 1.1, '#fff', 5);
    circle(c, x + lx, y + ly, 6, INK, 0);
    return;
  }
  const glowA = o.glow || 0;
  ellipse(c, x, y, r, r * 1.08, glowA > 0.5 ? '#b30000' : INK, 0);
  if (glowA > 0) {
    glow(c, x, y, 70 * glowA, 'rgba(255,40,20,0.9)', glowA);
    ellipse(c, x + lx * .5, y + ly * .5, r * .55, r * .62, `rgba(255,${80 + 120 * glowA},60,${glowA})`, 0);
    circle(c, x + lx * .5, y + ly * .5, r * .25, `rgba(255,255,200,${glowA})`, 0);
  }
  if (glowA < 0.8) {
    c.save(); c.globalAlpha = 1 - glowA;
    circle(c, x - r * .3 + lx * .3, y - r * .35 + ly * .3, r * .36, '#fff', 0);
    circle(c, x + r * .35 + lx * .3, y + r * .35 + ly * .3, r * .16, '#fff', 0);
    if (st === 'cute') star4(c, x + r * .4, y - r * .5, r * .45, '#fff', 0.3);
    c.restore();
  }
  // eyelids: narrow (unimpressed) / blink / squint
  let lid = o.blink || 0;
  if (st === 'narrow') lid = Math.max(lid, 0.52);
  if (st === 'squint') lid = Math.max(lid, 0.35);
  if (lid > 0.02) {
    c.save(); c.beginPath(); c.ellipse(x, y, r + 3, r * 1.08 + 3, 0, 0, TAU); c.clip();
    const yy = y - r * 1.1 + lid * r * 2.2;
    const tilt = (st === 'narrow' ? 0.12 : 0) * side;
    c.translate(x, yy); c.rotate(tilt);
    c.fillStyle = HAM.fur; c.fillRect(-r - 8, -r * 3, r * 2 + 16, r * 3);
    c.restore();
    c.save(); c.translate(x, yy); c.rotate(tilt);
    const hw = Math.sqrt(Math.max(0, 1 - Math.pow((yy - y) / (r * 1.08), 2))) * r + 3;
    line(c, [-hw, 0, hw, 0], 6); c.restore();
  }
}
function hamMouth(c, o) {
  const open = o.mouth || 0, rnd = o.round || 0, y0 = -110;
  if (open < 0.07) {
    const sm = o.smirk || 0, fr = o.frown || 0;
    // tiny buck teeth peeking under the "w"
    c.save(); c.fillStyle = '#fff';
    rrect(c, -8, y0 + 3, 7, 9, 2); fillStroke(c, '#fff', 3); rrect(c, 1, y0 + 3, 7, 9, 2); fillStroke(c, '#fff', 3);
    c.restore();
    c.beginPath();
    c.moveTo(-20, y0 + 1 - sm * 3 + fr * 6);
    c.quadraticCurveTo(-10, y0 + 12 + sm * 2 - fr * 8, 0, y0 + 1);
    c.quadraticCurveTo(10 + sm * 4, y0 + 12 + sm * 5 - fr * 8, 22 + sm * 6, y0 - sm * 9 + fr * 6);
    c.lineWidth = 5; c.strokeStyle = INK; c.lineCap = 'round'; c.stroke();
    return;
  }
  const h = 8 + 40 * open, w = 34 + 16 * (1 - rnd) - 6 * rnd + (o.yell ? 12 : 0) + 6 * open;
  c.beginPath();
  c.moveTo(-w / 2, y0 + 2);
  c.quadraticCurveTo(0, y0 - 4, w / 2, y0 + 2);
  c.bezierCurveTo(w / 2 + 2, y0 + h * .7, w * .3, y0 + h + 2, 0, y0 + h + 2);
  c.bezierCurveTo(-w * .3, y0 + h + 2, -w / 2 - 2, y0 + h * .7, -w / 2, y0 + 2);
  c.closePath();
  fillStroke(c, '#5b1531', 0);
  c.save(); c.clip();
  ellipse(c, 0, y0 + h + 4, w * .42, h * .42, HAM.pinkD, 0);
  c.restore();
  fillStroke(c, null, 5);
  rrect(c, -9, y0 - 1, 8, 13, 2); fillStroke(c, '#fff', 3);
  rrect(c, 1, y0 - 1, 8, 13, 2); fillStroke(c, '#fff', 3);
}
function drawHamster(c, o = {}) {
  const lw = 6, sq = o.sq || 1, wide = (o.wide || 1) * (1 + (o.belly || 0) * 0.16);
  c.save();
  c.scale(wide / Math.sqrt(sq), sq);
  // ears
  for (const s of [-1, 1]) {
    withT(c, s * 64, -216, 1, s * (0.2 + (o.earWig || 0) * Math.sin((o.t || 0) * 30)), () => {
      ellipse(c, 0, 0, 30, 28, HAM.fur, lw); ellipse(c, 0, 3, 17, 15, HAM.pink, 0);
    });
  }
  // arms that go behind the body
  const shL = [-80, -104], shR = [80, -104];
  const pL = o.pawL || [-40, -76], pR = o.pawR || [40, -76];
  // feet
  const fy = o.stand ? -4 : -6;
  for (const s of [-1, 1]) {
    ellipse(c, s * 50, fy, 30, 15, HAM.paw, lw);
    line(c, [s * 50 - 8, fy + 2, s * 50 - 8, fy + 10], 3); line(c, [s * 50 + 6, fy + 2, s * 50 + 6, fy + 10], 3);
  }
  // body with cel shading
  hamBodyPath(c); c.fillStyle = HAM.furSh; c.fill();
  c.save(); hamBodyPath(c); c.clip();
  c.translate(-15, -9); hamBodyPath(c); c.fillStyle = HAM.fur; c.fill(); c.translate(15, 9);
  ellipse(c, -50, -200, 26, 16, HAM.furHi, 0, -0.5);
  // cream front (belly + cheeks)
  c.fillStyle = HAM.creamSh;
  c.beginPath(); c.ellipse(0, -60, 84, 70, 0, 0, TAU); c.ellipse(0, -112, 80, 48, 0, 0, TAU); c.fill();
  c.fillStyle = HAM.cream;
  c.beginPath(); c.ellipse(-6, -64, 78, 64, 0, 0, TAU); c.ellipse(-4, -115, 74, 43, 0, 0, TAU); c.fill();
  c.restore();
  hamBodyPath(c); fillStroke(c, null, lw);
  // top tuft
  line(c, [-6, -240, -14, -258], 5); line(c, [2, -241, 4, -262], 5); line(c, [9, -240, 18, -254], 5);
  // cheek pouches (eating)
  const ch = o.cheeks || 0;
  if (ch > 0.02) {
    for (const s of [-1, 1]) {
      const r = 20 + 30 * ch;
      ellipse(c, s * (76 + 18 * ch), -100 + 4 * ch, r * 1.05, r * .95, HAM.cream, lw);
      ellipse(c, s * (76 + 18 * ch) + s * r * .25, -100 - r * .4, r * .3, r * .15, '#fff', 0, 0.4 * s);
    }
  }
  // blush
  c.save(); c.globalAlpha = 0.55 + (o.blush || 0) * 0.4;
  for (const s of [-1, 1]) ellipse(c, s * (62 + 20 * ch), -118, 16, 9, HAM.pink, 0);
  c.restore();
  // eyes + brows
  for (const s of [-1, 1]) hamEye(c, s * 40, -158, o, s);
  const br = o.brow || 0;
  if (br) {
    for (const s of [-1, 1]) {
      withT(c, s * 42, -190 + (br < 0 ? -6 : 4), 1, -s * 0.42 * br, () => {
        rrect(c, -22, -6, 44, 12, 6); fillStroke(c, HAM.brow, 4);
      });
    }
  }
  if (o.twitch) { line(c, [56, -190, 70, -196], 4); line(c, [58, -180, 74, -180], 4); }
  // nose + whiskers + mouth
  ellipse(c, 0, -124, 10, 7, HAM.pinkD, 4);
  ellipse(c, -3, -126, 3, 2, '#fff', 0);
  for (const s of [-1, 1]) {
    const wv = Math.sin((o.t || 0) * 9 + s) * 2;
    line(c, [s * 34, -118, s * 88, -130 + wv], 3);
    line(c, [s * 36, -112, s * 92, -114 + wv], 3);
    line(c, [s * 34, -106, s * 86, -96 + wv], 3);
  }
  hamMouth(c, o);
  // gold chain
  if (o.chain) {
    c.beginPath(); c.moveTo(-66, -96); c.quadraticCurveTo(0, -40, 66, -96);
    c.lineWidth = 12; c.strokeStyle = INK; c.stroke(); c.lineWidth = 7; c.strokeStyle = '#ffd34d'; c.setLineDash([9, 5]); c.stroke(); c.setLineDash([]);
    circle(c, 0, -60, 17, '#ffd34d', 5); text(c, '₸', 0, -59, 20, INK, { stroke: 0 });
  }
  // arms (front)
  hamArm(c, shL[0], shL[1], pL[0], pL[1], lw);
  hamArm(c, shR[0], shR[1], pR[0], pR[1], lw);
  // held items
  if (o.hold) o.hold(c, pL, pR);
  // head accessories
  if (o.horns) {
    const hs = o.horns;
    for (const s of [-1, 1]) {
      c.save(); c.translate(s * 46, -228); c.scale(hs, hs);
      c.beginPath(); c.moveTo(-14 * s, 6); c.quadraticCurveTo(-4 * s, -30, 18 * s, -46); c.quadraticCurveTo(10 * s, -14, 14 * s, 8); c.closePath();
      fillStroke(c, '#e0233a', 5); c.restore();
    }
  }
  if (o.glasses) {
    for (const s of [-1, 1]) { c.beginPath(); c.arc(s * 40, -158, 25, 0, TAU); c.lineWidth = 5; c.strokeStyle = '#c99a2e'; c.stroke(); }
    line(c, [-15, -160, 15, -160], 4, '#c99a2e');
    c.save(); c.globalAlpha = .35; for (const s of [-1, 1]) line(c, [s * 40 - 10, -168, s * 40 + 2, -178], 4, '#fff'); c.restore();
  }
  if (o.shades) {
    const a = o.shades;
    c.save(); c.globalAlpha = clamp(a); c.translate(0, -(1 - Math.min(1, a)) * 300);
    rrect(c, -78, -176, 70, 36, 10); fillStroke(c, '#111', 5); rrect(c, 8, -176, 70, 36, 10); fillStroke(c, '#111', 5);
    line(c, [-10, -166, 10, -166], 7, '#111');
    line(c, [-64, -168, -44, -168], 5, 'rgba(255,255,255,.6)'); line(c, [22, -168, 42, -168], 5, 'rgba(255,255,255,.6)');
    c.restore();
  }
  if (o.crown) {
    c.save(); c.translate(6, -236); c.rotate(0.12);
    poly(c, [-44, 0, -50, -46, -24, -22, 0, -58, 24, -22, 50, -46, 44, 0], '#ffd23f', 5);
    circle(c, 0, -14, 8, '#e0233a', 3); circle(c, -28, -10, 5, '#3ec1ff', 3); circle(c, 28, -10, 5, '#3ec1ff', 3);
    c.restore();
  }
  if (o.fedora) {
    c.save(); c.translate(0, -232); c.rotate(-0.1);
    ellipse(c, 0, 4, 118, 22, '#2b2b33', 5);
    c.beginPath(); c.moveTo(-70, 4); c.bezierCurveTo(-72, -70, -40, -84, 0, -70); c.bezierCurveTo(40, -84, 72, -70, 70, 4); c.closePath();
    fillStroke(c, '#34343e', 5);
    c.beginPath(); c.moveTo(-70, -8); c.lineTo(70, -8); c.lineTo(70, 6); c.lineTo(-70, 6); c.closePath(); fillStroke(c, '#c4202f', 0);
    line(c, [-30, -66, 0, -54, 30, -66], 4);
    c.restore();
  }
  c.restore();
}
// props the hamster can hold
function propSeed(c, x, y, s = 1, rot = 0) {
  withT(c, x, y, s, rot, () => {
    c.beginPath(); c.moveTo(0, -26); c.bezierCurveTo(16, -18, 14, 18, 0, 26); c.bezierCurveTo(-14, 18, -16, -18, 0, -26); c.closePath();
    fillStroke(c, '#2a2a2e', 4);
    line(c, [0, -20, 0, 20], 3, '#e8e8e8'); line(c, [-6, -14, -7, 12], 2, '#bbb'); line(c, [6, -14, 7, 12], 2, '#bbb');
  });
}
function propMic(c, x, y, s = 1, rot = 0) {
  withT(c, x, y, s, rot, () => {
    rrect(c, -9, -10, 18, 70, 6); fillStroke(c, '#26262e', 5);
    circle(c, 0, -26, 22, '#b9bec9', 5);
    c.save(); c.beginPath(); c.arc(0, -26, 20, 0, TAU); c.clip();
    for (let i = -20; i < 22; i += 7) { line(c, [i, -50, i, 0], 2, '#7d8391'); line(c, [-22, -26 + i, 22, -26 + i], 2, '#7d8391'); }
    c.restore();
    rrect(c, -12, -6, 24, 9, 3); fillStroke(c, '#ffd23f', 3);
  });
}

// ================================================================ GUY
const GUY = {
  skin: '#f6c9a0', skinSh: '#e2a47b', hair: '#3a2417', hairHi: '#5a3926',
  hood: '#2db3a0', hoodSh: '#1f8a7c', hoodHi: '#56d1bf', pants: '#3b4258', shoe: '#ffffff', shoeAcc: '#e8364f',
  phone: '#e8364f',
};
function guyHead(c, o) {
  const lw = 6, t = o.t || 0, blow = o.hairBlow || 0;
  // ears
  ellipse(c, -100, -420, 18, 26, GUY.skin, lw); ellipse(c, 100, -420, 18, 26, GUY.skin, lw);
  // head
  c.beginPath(); c.ellipse(0, -424, 100, 112, 0, 0, TAU); c.fillStyle = GUY.skinSh; c.fill();
  c.save(); c.clip(); c.beginPath(); c.ellipse(-10, -430, 98, 110, 0, 0, TAU); c.fillStyle = GUY.skin; c.fill(); c.restore();
  c.beginPath(); c.ellipse(0, -424, 100, 112, 0, 0, TAU); fillStroke(c, null, lw);
  // hair (spiky, can be blown back)
  const bx = blow * -40, wob = blow ? Math.sin(t * 40) * 6 * blow : 0;
  const hp = [-104, -400, -116, -470, -100, -515, -126 + bx, -548 + wob, -72, -556, -66 + bx, -598 + wob, -22, -572, 8 + bx, -612 - wob,
    30, -570, 78 + bx, -592 + wob, 86, -548, 124 + bx, -534 - wob, 108, -484, 108, -404, 96, -440, 80, -472, 52, -452, 28, -484, 2, -456,
    -26, -486, -50, -458, -78, -480, -94, -446];
  c.beginPath(); c.moveTo(hp[0], hp[1]);
  for (let i = 2; i < hp.length; i += 2) {
    const px = hp[i - 2], py = hp[i - 1], x = hp[i], y = hp[i + 1];
    c.quadraticCurveTo(px + (x - px) * .5 + (y - py) * .08, py + (y - py) * .5 - (x - px) * .08, x, y);
  }
  c.closePath(); fillStroke(c, GUY.hair, lw);
  line(c, [-60, -530, -30, -548], 6, GUY.hairHi); line(c, [10, -540, 40, -548], 6, GUY.hairHi);
  // face
  const ex = o.expr || 'neutral', lk = o.look || [0, 0];
  const eyeR = ex === 'shock' || ex === 'scared' ? [28, 34] : [23, 29];
  for (const s of [-1, 1]) {
    const x = s * 42, y = -418;
    ellipse(c, x, y, eyeR[0], eyeR[1], '#fff', 5);
    const pr = ex === 'shock' || ex === 'scared' ? 7 : ex === 'dreamy' ? 13 : 11;
    if (ex === 'happy') { c.save(); c.beginPath(); c.ellipse(x, y, eyeR[0], eyeR[1], 0, 0, TAU); c.clip(); }
    circle(c, x + lk[0] * 8, y + lk[1] * 8 + 2, pr, INK, 0);
    circle(c, x + lk[0] * 8 - pr * .35, y + lk[1] * 8 - pr * .3, pr * .32, '#fff', 0);
    if (ex === 'happy') c.restore();
    let lid = o.blink || 0;
    if (ex === 'angry' || ex === 'determined') lid = Math.max(lid, 0.3);
    if (ex === 'dead') lid = Math.max(lid, 0.55);
    if (lid > 0.02) {
      c.save(); c.beginPath(); c.ellipse(x, y, eyeR[0] + 2, eyeR[1] + 2, 0, 0, TAU); c.clip();
      const yy = y - eyeR[1] + lid * eyeR[1] * 2;
      c.fillStyle = GUY.skin; c.fillRect(x - 40, yy - 80, 80, 80); c.restore();
      line(c, [x - eyeR[0] * Math.sqrt(1 - Math.pow((yy - y) / eyeR[1], 2)), yy, x + eyeR[0] * Math.sqrt(1 - Math.pow((yy - y) / eyeR[1], 2)), yy], 5);
    }
  }
  // brows
  const bAng = { neutral: 0, angry: 0.38, determined: 0.25, shock: -0.25, scared: -0.4, happy: -0.1, dreamy: -0.15, dead: 0 }[ex] || 0;
  const bY = { shock: -472, scared: -466 }[ex] || -458;
  for (const s of [-1, 1]) {
    withT(c, s * 44, bY, 1, -s * bAng, () => { rrect(c, -26, -7, 52, 14, 7); fillStroke(c, GUY.hair, 4); });
  }
  // nose
  c.beginPath(); c.moveTo(-2, -398); c.quadraticCurveTo(14, -382, -4, -378); c.lineWidth = 5; c.strokeStyle = INK; c.lineCap = 'round'; c.stroke();
  // blush / angry flush
  if (ex === 'angry') { c.save(); c.globalAlpha = .35; ellipse(c, 0, -440, 90, 60, '#ff2a2a', 0); c.restore(); }
  c.save(); c.globalAlpha = .35; ellipse(c, -66, -378, 16, 9, '#ff7b7b', 0); ellipse(c, 66, -378, 16, 9, '#ff7b7b', 0); c.restore();
  // mouth
  const m = o.mouth || 0, rnd = o.round || 0, my = -350;
  if (m < 0.07 && !o.mouthOpenFixed) {
    const curve = { happy: 14, dreamy: 10, shock: 0, scared: -10, angry: -12, determined: -4, neutral: 2, dead: -6 }[ex] || 0;
    if (ex === 'shock' || ex === 'scared') { ellipse(c, 0, my, 12, 14, '#5b1531', 5); }
    else { c.beginPath(); c.moveTo(-30, my); c.quadraticCurveTo(0, my + curve * 1.6, 30, my); c.lineWidth = 6; c.strokeStyle = INK; c.stroke(); }
    if (ex === 'scared') { c.beginPath(); c.moveTo(-34, my + 4); for (let i = 0; i <= 8; i++) c.lineTo(-34 + i * 8.5, my + 4 + (i % 2 ? -6 : 6)); c.lineWidth = 5; c.stroke(); }
  } else {
    const mm = o.mouthOpenFixed || m;
    const h = 12 + 58 * mm, w = 46 + 18 * (1 - rnd) - 10 * rnd + (ex === 'shock' ? 10 : 0);
    c.beginPath(); c.moveTo(-w / 2, my - 4);
    c.quadraticCurveTo(0, my - 10, w / 2, my - 4);
    c.bezierCurveTo(w / 2 + 2, my + h * .6, w * .3, my + h, 0, my + h);
    c.bezierCurveTo(-w * .3, my + h, -w / 2 - 2, my + h * .6, -w / 2, my - 4);
    c.closePath(); fillStroke(c, '#5b1531', 0);
    c.save(); c.clip();
    c.fillStyle = '#fff'; c.fillRect(-w / 2, my - 12, w, 12 + Math.min(10, h * .2));
    ellipse(c, 0, my + h + 2, w * .36, h * .36, '#ff7d93', 0);
    c.restore();
    fillStroke(c, null, 5);
  }
  if (o.sweat) {
    const sw = o.sweat;
    sweat(c, 104, -480 + ((t * 120) % 60), 1.1 * sw, 0.2);
    sweat(c, -112, -460 + ((t * 90 + 30) % 50), 0.9 * sw, -0.2);
  }
  if (o.vein) {
    c.save(); c.translate(-58, -500); c.scale(o.vein, o.vein);
    for (const r of [0, 1, 2, 3]) withT(c, 0, 0, 1, r * Math.PI / 2, () => { c.beginPath(); c.moveTo(4, -18); c.quadraticCurveTo(4, -4, 18, -4); c.lineWidth = 7; c.strokeStyle = '#e8203a'; c.stroke(); });
    c.restore();
  }
}
function guyArm(c, sx, sy, hx, hy, lw, col) {
  const dx = hx - sx, dy = hy - sy, L = Math.hypot(dx, dy);
  const bend = Math.max(0, 1 - L / 230) * 60 * (sx < 0 ? -1 : 1);
  const mx = (sx + hx) / 2 - dy / L * bend, my = (sy + hy) / 2 + dx / L * bend;
  c.beginPath(); c.moveTo(sx, sy); c.quadraticCurveTo(mx, my, hx, hy);
  c.lineCap = 'round'; c.lineWidth = 40 + lw * 2; c.strokeStyle = INK; c.stroke();
  c.lineWidth = 40; c.strokeStyle = col || GUY.hood; c.stroke();
  circle(c, hx, hy, 23, GUY.skin, lw);
}
function drawGuy(c, o = {}) {
  const lw = 6, t = o.t || 0;
  c.save();
  if (o.lean) c.rotate(o.lean);
  const pose = o.pose || 'stand';
  // legs
  if (pose === 'stand') {
    for (const s of [-1, 1]) {
      poly(c, [s * 10, -160, s * 72, -160, s * 64, -34, s * 18, -34], GUY.pants, lw);
      c.beginPath(); c.ellipse(s * 44, -22, 42, 22, 0, 0, TAU); fillStroke(c, GUY.shoe, lw);
      line(c, [s * 10, -18, s * 78, -18], 7, GUY.shoeAcc);
    }
  } else if (pose === 'run') {
    const ph = t * 26;
    c.save(); c.globalAlpha = 0.35;
    for (let k = 0; k < 3; k++) { c.beginPath(); c.arc(0, -80, 95 - k * 22, ph * .5 + k, ph * .5 + k + 2.6); c.lineWidth = 6; c.strokeStyle = INK; c.stroke(); }
    c.restore();
    for (let k = 0; k < 2; k++) {
      const a = Math.sin(ph + k * Math.PI);
      const hx = k ? 26 : -26, hy = -160;
      const th = 0.15 + a * 0.95, kx = hx + Math.sin(th) * 80, ky = hy + Math.cos(th) * 80;
      const sh2 = th - 0.5 - Math.max(0, -a) * 1.2, fx = kx + Math.sin(sh2) * 78, fy = ky + Math.cos(sh2) * 78;
      limb(c, [hx, hy, kx, ky, fx, fy], 40, k ? GUY.pants : '#323850', lw);
      ellipse(c, fx + 14, fy + 6, 38, 19, GUY.shoe, lw, sh2 * 0.3);
      line(c, [fx - 14, fy + 12, fx + 44, fy + 12], 6, GUY.shoeAcc);
    }
  }
  // headphones band behind the neck
  // torso (hoodie)
  const sh = -322;
  c.beginPath();
  c.moveTo(-60, sh - 6); c.bezierCurveTo(-118, sh - 4, -122, sh + 40, -118, sh + 70);
  c.lineTo(-100, -150); c.quadraticCurveTo(0, -136, 100, -150);
  c.lineTo(118, sh + 70); c.bezierCurveTo(122, sh + 40, 118, sh - 4, 60, sh - 6); c.closePath();
  c.fillStyle = GUY.hoodSh; c.fill();
  c.save(); c.clip(); c.translate(-12, -4);
  c.beginPath(); c.moveTo(-60, sh - 6); c.bezierCurveTo(-118, sh - 4, -122, sh + 40, -118, sh + 70);
  c.lineTo(-100, -150); c.quadraticCurveTo(0, -136, 100, -150);
  c.lineTo(118, sh + 70); c.bezierCurveTo(122, sh + 40, 118, sh - 4, 60, sh - 6); c.closePath();
  c.fillStyle = GUY.hood; c.fill(); c.restore();
  c.beginPath(); c.moveTo(-60, sh - 6); c.bezierCurveTo(-118, sh - 4, -122, sh + 40, -118, sh + 70);
  c.lineTo(-100, -150); c.quadraticCurveTo(0, -136, 100, -150);
  c.lineTo(118, sh + 70); c.bezierCurveTo(122, sh + 40, 118, sh - 4, 60, sh - 6); c.closePath();
  fillStroke(c, null, lw);
  // waistband + pocket + strings
  rrect(c, -102, -172, 204, 26, 12); fillStroke(c, GUY.hoodSh, lw);
  c.beginPath(); c.moveTo(-58, -176); c.lineTo(-44, -236); c.lineTo(44, -236); c.lineTo(58, -176); fillStroke(c, null, 5);
  line(c, [-18, -300, -22, -246], 5, '#fff'); line(c, [18, -300, 22, -246], 5, '#fff');
  circle(c, -22, -244, 5, '#fff', 3); circle(c, 22, -244, 5, '#fff', 3);
  // hood collar
  c.beginPath(); c.moveTo(-70, sh - 4); c.quadraticCurveTo(0, sh + 52, 70, sh - 4); c.quadraticCurveTo(0, sh + 22, -70, sh - 4);
  fillStroke(c, GUY.hoodSh, 5);
  // neck
  rrect(c, -26, sh - 30, 52, 36, 10); fillStroke(c, GUY.skinSh, 5);
  // headphones around the neck
  if (o.headphones) {
    c.beginPath(); c.arc(0, sh - 6, 62, Math.PI * 0.05, Math.PI * 0.95); c.lineWidth = 14; c.strokeStyle = INK; c.stroke(); c.lineWidth = 8; c.strokeStyle = '#2c2c34'; c.stroke();
    for (const s of [-1, 1]) { ellipse(c, s * 58, sh + 6, 24, 32, GUY.phone, lw, s * 0.3); ellipse(c, s * 58, sh + 6, 11, 16, '#a51d33', 0, s * 0.3); }
  }
  // arms
  const aL = o.handL || [-150, -170], aR = o.handR || [150, -170];
  guyArm(c, -104, sh + 26, aL[0], aL[1], lw);
  if (o.holdBack) o.holdBack(c);
  // head
  withT(c, 0, sh - 20, 1, o.headTilt || 0, () => { c.translate(0, -(sh - 20)); guyHead(c, o); });
  guyArm(c, 104, sh + 26, aR[0], aR[1], lw);
  if (o.hold) o.hold(c);
  c.restore();
}

// ================================================================ DEMON
const DEM = {
  skin: '#d6273b', sh: '#9e1628', hi: '#f0525f', wing: '#5c0d1b', wingM: '#7d1628', horn: '#2a1b20', hornTip: '#efe0c8',
  eye: '#ffe14d', claw: '#1d1326', cap: '#ffc21a', bag: '#ffc21a', bagSh: '#d99a00',
};
function demonWing(c, s, spread, t) {
  c.save(); c.scale(s, 1); c.translate(190, -880); c.rotate(-0.25 - spread * 0.35 + Math.sin(t * 3) * 0.04);
  const pts = [0, 0, 160, -260, 420, -420, 640, -380];
  c.beginPath(); c.moveTo(0, 0); c.lineTo(160, -260); c.lineTo(420, -420); c.lineTo(640, -380);
  c.quadraticCurveTo(560, -260, 600, -150); c.quadraticCurveTo(500, -170, 450, -40);
  c.quadraticCurveTo(360, -90, 300, 40); c.quadraticCurveTo(200, -10, 120, 120); c.closePath();
  fillStroke(c, DEM.wingM, 7);
  line(c, [160, -260, 600, -150], 6); line(c, [160, -260, 450, -40], 6); line(c, [160, -260, 300, 40], 6);
  line(c, pts, 16, INK); line(c, pts, 9, DEM.wing);
  c.restore();
}
function demonHand(c, x, y, s, ang, open, side) {
  withT(c, x, y, s, ang, () => {
    c.scale(side, 1);
    ellipse(c, 0, 0, 52, 46, DEM.skin, 7);
    for (let i = 0; i < 4; i++) {
      const a = -0.9 + i * 0.5 + (open ? -0.2 : 0.3), L = open ? 74 : 54;
      const x0 = Math.cos(a) * 34, y0 = Math.sin(a) * 30 - 10;
      const x1 = x0 + Math.cos(a - 0.4) * L, y1 = y0 + Math.sin(a - 0.4) * L;
      limb(c, [x0, y0, x1, y1], 24, DEM.skin, 7);
      c.save(); c.translate(x1, y1); c.rotate(a - 0.4);
      poly(c, [8, -10, 34, 0, 8, 10], DEM.claw, 0); c.restore();
    }
    limb(c, [-20, 10, -56, 40], 24, DEM.skin, 7);
  });
}
function drawDemon(c, o = {}) {
  const lw = 7, t = o.t || 0, sc = o.scared || 0, br = Math.sin(t * 2.2) * 6 * (1 - sc);
  c.save();
  // tail
  c.beginPath(); c.moveTo(80, -480); c.bezierCurveTo(400, -420, 420, -760, 560 + Math.sin(t * 2) * 30, -720);
  c.lineWidth = 34; c.strokeStyle = INK; c.lineCap = 'round'; c.stroke(); c.lineWidth = 20; c.strokeStyle = DEM.sh; c.stroke();
  withT(c, 560 + Math.sin(t * 2) * 30, -720, 1, -0.6, () => poly(c, [0, -40, 50, 0, 0, 40, 14, 0], DEM.sh, lw));
  // wings
  if (!o.noWings) { demonWing(c, -1, o.spread || 0, t); demonWing(c, 1, o.spread || 0, t); }
  // courier bag (behind)
  if (o.courier) {
    c.save(); c.translate(0, -1000 + br);
    rrect(c, -260, -370, 520, 560, 30); fillStroke(c, DEM.bag, lw);
    rrect(c, -260, -370, 520, 90, 30); fillStroke(c, DEM.bagSh, lw);
    text(c, 'АД•ДОСТАВКА', 0, -325, 44, '#e0233a', { stroke: 8, scol: '#fff' });
    c.restore();
  }
  // legs (goat-ish)
  for (const s of [-1, 1]) {
    c.beginPath(); c.moveTo(s * 40, -520); c.bezierCurveTo(s * 200, -480, s * 230, -330, s * 170, -220);
    c.lineTo(s * 210, -40); c.lineTo(s * 110, -40); c.lineTo(s * 100, -230); c.bezierCurveTo(s * 70, -330, s * 30, -400, s * 20, -470); c.closePath();
    fillStroke(c, DEM.sh, lw);
    rrect(c, s * 160 - 60, -50, 120, 50, 14); fillStroke(c, '#2a1b20', lw);
  }
  // torso
  c.save(); c.translate(0, br * .5);
  const tor = () => {
    c.beginPath(); c.moveTo(-150, -520); c.bezierCurveTo(-200, -650, -300, -760, -280, -860);
    c.bezierCurveTo(-250, -940, -120, -950, 0, -930); c.bezierCurveTo(120, -950, 250, -940, 280, -860);
    c.bezierCurveTo(300, -760, 200, -650, 150, -520); c.quadraticCurveTo(0, -490, -150, -520); c.closePath();
  };
  tor(); c.fillStyle = DEM.sh; c.fill();
  c.save(); tor(); c.clip(); c.translate(-22, -10); tor(); c.fillStyle = DEM.skin; c.fill(); c.restore();
  tor(); fillStroke(c, null, lw);
  // pecs + abs
  c.beginPath(); c.moveTo(-200, -840); c.quadraticCurveTo(-110, -730, -10, -800); c.moveTo(200, -840); c.quadraticCurveTo(110, -730, 10, -800);
  c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
  for (let r = 0; r < 3; r++) for (const s of [-1, 1]) {
    rrect(c, s > 0 ? 8 : -78, -740 + r * 62, 70, 52, 20); fillStroke(c, DEM.hi, 0);
    rrect(c, s > 0 ? 8 : -78, -740 + r * 62, 70, 52, 20); fillStroke(c, null, 4);
  }
  // loincloth / belt
  rrect(c, -160, -560, 320, 50, 16); fillStroke(c, '#2a1b20', lw); circle(c, 0, -535, 22, '#ffd23f', 5);
  // courier straps
  if (o.courier) { for (const s of [-1, 1]) { line(c, [s * 150, -930, s * 110, -600], 34, INK); line(c, [s * 150, -930, s * 110, -600], 22, '#333'); } }
  c.restore();
  // arms (pose)
  const pose = o.pose || 'idle';
  const A = {
    idle: [[-330, -660, -360, -460], [330, -660, 360, -460]],
    roar: [[-430, -980, -520, -1200], [430, -980, 520, -1200]],
    grip: [[-380, -700, -420, -520], [380, -700, 420, -520]],
    scared: [[-300, -720, -170, -900], [300, -720, 170, -900]],
    present: [[-320, -700, -150, -720], [320, -700, 150, -720]],
    catch: [[-300, -660, -90, -640], [300, -660, 90, -640]],
    spot: [[-320, -720, -360, -1000], [330, -660, 360, -460]],
  }[pose];
  for (let k = 0; k < 2; k++) {
    const s = k ? 1 : -1, [ex, ey, hx, hy] = A[k];
    limb(c, [s * 250, -880 + br, ex, ey + br, hx, hy + br], 92, DEM.skin, lw);
    line(c, [s * 250 - s * 10, -870 + br, ex - s * 20, ey + br], 22, 'rgba(255,255,255,0.12)');
    const ang = Math.atan2(hy - ey, hx - ex) + (s < 0 ? Math.PI : 0);
    demonHand(c, hx, hy + br, 1, ang * 0 + (pose === 'roar' ? s * -0.6 : pose === 'scared' ? s * -0.2 : 0), pose === 'roar' || pose === 'scared', s);
  }
  // head
  c.save(); c.translate(0, br + (o.headDy || 0)); c.rotate(o.headTilt || 0);
  // horns
  for (const s of [-1, 1]) {
    const horn = () => { c.beginPath(); c.moveTo(s * 70, -1140); c.bezierCurveTo(s * 120, -1240, s * 220, -1250, s * 240, -1360);
      c.bezierCurveTo(s * 270, -1260, s * 200, -1150, s * 125, -1100); c.closePath(); };
    horn(); c.fillStyle = DEM.horn; c.fill();
    c.save(); horn(); c.clip(); c.fillStyle = DEM.hornTip; c.beginPath(); c.arc(s * 240, -1360, 70, 0, TAU); c.fill(); c.restore();
    horn(); fillStroke(c, null, lw);
    line(c, [s * 110, -1180, s * 150, -1170], 5); line(c, [s * 150, -1222, s * 190, -1206], 5);
  }
  // ears
  for (const s of [-1, 1]) poly(c, [s * 120, -1090, s * 220, -1140, s * 130, -1030], DEM.sh, lw);
  // skull/jaw
  const head = () => {
    c.beginPath(); c.moveTo(0, -1200); c.bezierCurveTo(110, -1200, 140, -1120, 136, -1050);
    c.bezierCurveTo(132, -990, 120, -950, 60, -918); c.quadraticCurveTo(0, -895, -60, -918);
    c.bezierCurveTo(-120, -950, -132, -990, -136, -1050); c.bezierCurveTo(-140, -1120, -110, -1200, 0, -1200); c.closePath();
  };
  head(); c.fillStyle = DEM.sh; c.fill();
  c.save(); head(); c.clip(); c.translate(-14, -8); head(); c.fillStyle = DEM.skin; c.fill(); c.restore();
  head(); fillStroke(c, null, lw);
  // chin beard
  poly(c, [-36, -916, 0, -860, 36, -916], '#2a1b20', 5);
  // brows
  for (const s of [-1, 1]) {
    withT(c, s * 52, -1104 + sc * -16, 1, -s * (0.35 - sc * 0.8), () => { rrect(c, -46, -12, 92, 24, 10); fillStroke(c, '#2a1b20', 5); });
  }
  // eyes
  for (const s of [-1, 1]) {
    const er = sc ? [22, 24] : [32, 18];
    glow(c, s * 50, -1072, 90, 'rgba(255,200,40,0.55)', 1 - sc * .6);
    ellipse(c, s * 50, -1072, er[0], er[1], sc ? '#fff' : DEM.eye, 5, sc ? 0 : s * 0.15);
    if (sc) circle(c, s * 50 + (o.look || 0) * 8, -1070, 7, INK, 0);
    else ellipse(c, s * 50, -1072, 5, 15, INK, 0);
  }
  // nose
  line(c, [-16, -1020, -8, -1008], 6); line(c, [16, -1020, 8, -1008], 6);
  // mouth
  const m = o.mouth || 0, rnd = o.round || 0, my = -975;
  if (m < 0.07) {
    if (sc) {
      c.beginPath(); c.moveTo(-50, my); for (let i = 0; i <= 10; i++) c.lineTo(-50 + i * 10, my + (i % 2 ? -9 : 9)); c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
    } else {
      c.beginPath(); c.moveTo(-70, my - 6); c.quadraticCurveTo(0, my + 14, 70, my - 6); c.lineWidth = 7; c.strokeStyle = INK; c.stroke();
      poly(c, [-48, my, -40, my + 22, -32, my + 3], '#fffbea', 4); poly(c, [48, my, 40, my + 22, 32, my + 3], '#fffbea', 4);
    }
  } else {
    const h = 20 + 120 * m, w = 150 - 40 * rnd;
    c.beginPath(); c.moveTo(-w / 2, my - 14); c.quadraticCurveTo(0, my - 26, w / 2, my - 14);
    c.bezierCurveTo(w / 2 + 6, my + h * .7, w * .3, my + h, 0, my + h); c.bezierCurveTo(-w * .3, my + h, -w / 2 - 6, my + h * .7, -w / 2, my - 14);
    c.closePath(); fillStroke(c, '#3a0610', 0);
    c.save(); c.clip();
    ellipse(c, 0, my + h, w * .35, h * .35, '#c2304a', 0);
    glow(c, 0, my + h * .5, h, 'rgba(255,120,0,0.5)', m);
    c.fillStyle = '#fffbea';
    for (let i = 0; i < 6; i++) { const x = -w / 2 + 8 + i * (w - 16) / 5; c.beginPath(); c.moveTo(x - 11, my - 20); c.lineTo(x + 11, my - 20); c.lineTo(x, my + 4 + (i === 1 || i === 4 ? 18 : 0)); c.fill(); }
    for (let i = 0; i < 5; i++) { const x = -w / 2 + 18 + i * (w - 36) / 4; c.beginPath(); c.moveTo(x - 10, my + h + 4); c.lineTo(x + 10, my + h + 4); c.lineTo(x, my + h - 14 - (i === 0 || i === 4 ? 14 : 0)); c.fill(); }
    c.restore();
    fillStroke(c, null, 6);
  }
  if (sc > 0.3) { sweat(c, 150, -1120 + (t * 160) % 80, 2.2); sweat(c, -160, -1100 + (t * 130 + 40) % 70, 1.8); }
  // courier cap
  if (o.courier) {
    c.save(); c.translate(0, -1170);
    c.beginPath(); c.moveTo(-125, 10); c.bezierCurveTo(-125, -90, 125, -90, 125, 10); c.closePath(); fillStroke(c, DEM.cap, lw);
    c.beginPath(); c.moveTo(-130, 6); c.quadraticCurveTo(0, -10, 200, 18); c.quadraticCurveTo(120, 40, -130, 22); c.closePath(); fillStroke(c, DEM.bagSh, lw);
    text(c, 'АД', 0, -38, 46, '#e0233a', { stroke: 6 });
    c.restore();
  }
  c.restore();
  if (o.hold) o.hold(c, br);
  c.restore();
}
