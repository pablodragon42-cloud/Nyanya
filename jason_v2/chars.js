// Characters in the bright chibi style: scared friend, idiot friend, Jason. Same model sheet in every shot.
function blinkAt(t, seed = 0, every = 3.1) {
  const ph = (t + hash(seed) * every) % every;
  return ph < 0.13 ? Math.sin(ph / 0.13 * Math.PI) : 0;
}

// ================================================================ SCARED FRIEND (narrator)
const SC = {
  skin: '#f6c9a0', skinSh: '#e2a47b', hair: '#3a2417', hairHi: '#5a3926',
  hood: '#ee3b4f', hoodSh: '#b8243a', pants: '#34406a', pantsSh: '#283256', shoe: '#ffffff', shoeAcc: '#2db3a0',
};
function skinOf(pal, o) {
  const p = o.pale || 0;
  return p > 0 ? [mixHex(pal.skin, '#cfe3f2', p), mixHex(pal.skinSh, '#9fbad6', p)] : [pal.skin, pal.skinSh];
}
function eyeLid(c, x, y, rx, ry, lid, skin, tilt = 0) {
  if (lid <= 0.02) return;
  c.save(); c.beginPath(); c.ellipse(x, y, rx + 2, ry + 2, 0, 0, TAU); c.clip();
  const yy = y - ry + lid * ry * 2;
  c.translate(x, yy); c.rotate(tilt);
  c.fillStyle = skin; c.fillRect(-rx - 30, -ry * 3, rx * 2 + 60, ry * 3); c.restore();
  const hw = rx * Math.sqrt(Math.max(0, 1 - Math.pow((yy - y) / ry, 2))) + 2;
  c.save(); c.translate(x, yy); c.rotate(tilt); line(c, [-hw, 0, hw, 0], 6); c.restore();
}
function scaredHead(c, o) {
  const lw = 6, t = o.t || 0, pal = SC, [skin, skinSh] = skinOf(pal, o);
  ellipse(c, -100, -420, 18, 26, skin, lw); ellipse(c, 100, -420, 18, 26, skin, lw);
  c.beginPath(); c.ellipse(0, -424, 100, 112, 0, 0, TAU); c.fillStyle = skinSh; c.fill();
  c.save(); c.clip(); c.beginPath(); c.ellipse(-10, -430, 98, 110, 0, 0, TAU); c.fillStyle = skin; c.fill(); c.restore();
  c.beginPath(); c.ellipse(0, -424, 100, 112, 0, 0, TAU); fillStroke(c, null, lw);
  // spiky hair; hairUp = standing on end from fear
  const up = o.hairUp || 0, wob = up ? Math.sin(t * 50) * 4 * up : 0;
  const U = (y, k) => y - up * 70 * k;
  const hp = [-104, -400, -116, -470, -100, -515, -126, U(-548, .6) + wob, -72, U(-556, .8), -66, U(-598, 1) + wob, -22, U(-572, .8), 8, U(-612, 1.1) - wob,
    30, U(-570, .8), 78, U(-592, 1) + wob, 86, U(-548, .7), 124, U(-534, .6) - wob, 108, -484, 108, -404, 96, -440, 80, -472, 52, -452, 28, -484, 2, -456,
    -26, -486, -50, -458, -78, -480, -94, -446];
  c.beginPath(); c.moveTo(hp[0], hp[1]);
  for (let i = 2; i < hp.length; i += 2) {
    const px = hp[i - 2], py = hp[i - 1], x = hp[i], y = hp[i + 1];
    c.quadraticCurveTo(px + (x - px) * .5 + (y - py) * .08, py + (y - py) * .5 - (x - px) * .08, x, y);
  }
  c.closePath(); fillStroke(c, pal.hair, lw);
  line(c, [-60, U(-530, .7), -30, U(-548, .8)], 6, pal.hairHi); line(c, [10, U(-540, .9), 40, U(-548, .9)], 6, pal.hairHi);
  // eyes
  const ex = o.expr || 'neutral', lk = o.look || [0, 0];
  const big = ex === 'shock' || ex === 'scared' || ex === 'frozen';
  const eyeR = big ? [30, 36] : [23, 29];
  for (const s of [-1, 1]) {
    const x = s * 42 + (o.turn || 0) * 18, y = -418;
    if (ex === 'squeeze') { line(c, [x - s * 22, y - 18, x + s * 14, y, x - s * 22, y + 18], 7); continue; }
    if (ex === 'happy') { c.beginPath(); c.arc(x, y + 8, 18, Math.PI * 1.1, Math.PI * 1.9); c.lineWidth = 7; c.strokeStyle = INK; c.stroke(); continue; }
    ellipse(c, x, y, eyeR[0], eyeR[1], '#fff', 5);
    const pr = ex === 'frozen' ? 5 : big ? 7 : 11;
    const jit = ex === 'frozen' ? shake(t, 2, 40, s * 9) : [0, 0];
    circle(c, x + lk[0] * 9 + jit[0], y + lk[1] * 9 + 2 + jit[1], pr, INK, 0);
    if (!big) circle(c, x + lk[0] * 9 - pr * .35, y + lk[1] * 9 - pr * .3, pr * .32, '#fff', 0);
    let lid = o.blink || 0;
    if (ex === 'angry' || ex === 'hiss') lid = Math.max(lid, 0.3);
    if (ex === 'annoyed') lid = Math.max(lid, 0.42);
    if (ex === 'doomed' || ex === 'despair') lid = Math.max(lid, 0.55);
    if (o.lid) lid = Math.max(lid, o.lid);
    eyeLid(c, x, y, eyeR[0], eyeR[1], lid, skin, ex === 'doomed' ? -s * 0.12 : 0);
    if (ex === 'doomed' || ex === 'despair') {
      line(c, [x - 18, y + 36, x, y + 42, x + 18, y + 36], 4, '#9c6a7a'); line(c, [x - 12, y + 46, x, y + 50, x + 12, y + 46], 3, '#9c6a7a');
    }
  }
  // brows
  const bAng = { neutral: 0, angry: 0.42, hiss: 0.5, determined: 0.25, shock: -0.3, scared: -0.42, frozen: -0.42, happy: -0.1,
    annoyed: 0.1, doomed: -0.18, despair: -0.3, nervous: -0.35, squeeze: 0.3 }[ex] || 0;
  const bY = { shock: -476, scared: -472, frozen: -480 }[ex] || -458;
  for (const s of [-1, 1]) withT(c, s * 44 + (o.turn || 0) * 18, bY, 1, -s * bAng, () => { rrect(c, -26, -7, 52, 14, 7); fillStroke(c, pal.hair, 4); });
  // nose
  const nx = (o.turn || 0) * 24;
  c.beginPath(); c.moveTo(nx - 2, -398); c.quadraticCurveTo(nx + 14, -382, nx - 4, -378); c.lineWidth = 5; c.strokeStyle = INK; c.lineCap = 'round'; c.stroke();
  if (ex === 'angry' || ex === 'hiss') { c.save(); c.globalAlpha = .35; ellipse(c, 0, -440, 90, 60, '#ff2a2a', 0); c.restore(); }
  c.save(); c.globalAlpha = .35; ellipse(c, -66, -378, 16, 9, '#ff7b7b', 0); ellipse(c, 66, -378, 16, 9, '#ff7b7b', 0); c.restore();
  if (o.pale > .3) { c.save(); c.globalAlpha = .5 * o.pale; for (let i = 0; i < 4; i++) line(c, [-60 + i * 40, -500, -60 + i * 40, -470], 5, '#5b6ad6'); c.restore(); }
  // mouth
  const m = o.mouth || 0, rnd = o.round || 0, my = -350, mx = nx * .6;
  if (o.puff) {
    for (const s of [-1, 1]) ellipse(c, s * 62, -366, 34 * o.puff, 30 * o.puff, skin, 5);
    ellipse(c, mx, my, 10, 8, '#5b1531', 5);
  } else if (ex === 'hiss' && m < 0.25) {
    rrect(c, mx - 44, my - 16, 88, 32, 10); fillStroke(c, '#fff', 5);
    line(c, [mx - 44, my, mx + 44, my], 3); for (let i = -2; i <= 2; i++) line(c, [mx + i * 16, my - 14, mx + i * 16, my + 14], 3);
  } else if (m < 0.07 && !o.mouthOpenFixed) {
    const curve = { happy: 14, shock: 0, scared: -10, angry: -12, annoyed: -6, determined: -4, neutral: 2, doomed: -8, despair: -12, nervous: 10 }[ex] || 0;
    if (ex === 'shock' || ex === 'scared') { ellipse(c, mx, my, 14, 18, '#5b1531', 5); }
    else if (ex === 'frozen' || ex === 'nervous') {
      c.beginPath(); c.moveTo(mx - 38, my + 2); for (let i = 0; i <= 8; i++) c.lineTo(mx - 38 + i * 9.5, my + 2 + (i % 2 ? -7 : 7)); c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
    } else { c.beginPath(); c.moveTo(mx - 30, my); c.quadraticCurveTo(mx, my + curve * 1.6, mx + 30, my); c.lineWidth = 6; c.strokeStyle = INK; c.stroke(); }
  } else {
    const mm = o.mouthOpenFixed || m;
    const h = 12 + 62 * mm, w = 46 + 18 * (1 - rnd) - 10 * rnd + (ex === 'shock' || o.yell ? 14 : 0);
    c.beginPath(); c.moveTo(mx - w / 2, my - 4); c.quadraticCurveTo(mx, my - 10, mx + w / 2, my - 4);
    c.bezierCurveTo(mx + w / 2 + 2, my + h * .6, mx + w * .3, my + h, mx, my + h);
    c.bezierCurveTo(mx - w * .3, my + h, mx - w / 2 - 2, my + h * .6, mx - w / 2, my - 4);
    c.closePath(); fillStroke(c, '#5b1531', 0);
    c.save(); c.clip(); c.fillStyle = '#fff'; c.fillRect(mx - w / 2, my - 12, w, 12 + Math.min(10, h * .2));
    ellipse(c, mx, my + h + 2, w * .36, h * .36, '#ff7d93', 0); c.restore();
    fillStroke(c, null, 5);
  }
  if (o.sweat) { sweat(c, 104, -480 + ((t * 120) % 60), 1.1 * o.sweat, 0.2); sweat(c, -112, -460 + ((t * 90 + 30) % 50), 0.9 * o.sweat, -0.2); }
  if (o.vein) {
    c.save(); c.translate(-58, -500); c.scale(o.vein * (1 + .1 * Math.sin(t * 30)), o.vein * (1 + .1 * Math.sin(t * 30)));
    for (const r of [0, 1, 2, 3]) withT(c, 0, 0, 1, r * Math.PI / 2, () => { c.beginPath(); c.moveTo(4, -18); c.quadraticCurveTo(4, -4, 18, -4); c.lineWidth = 7; c.strokeStyle = '#e8203a'; c.stroke(); });
    c.restore();
  }
}
function guyArm(c, sx, sy, hx, hy, lw, col, skin, hand = 'fist') {
  const dx = hx - sx, dy = hy - sy, L = Math.hypot(dx, dy) || 1;
  const bend = Math.max(0, 1 - L / 230) * 60 * (sx < 0 ? -1 : 1);
  const mx = (sx + hx) / 2 - dy / L * bend, my = (sy + hy) / 2 + dx / L * bend;
  c.beginPath(); c.moveTo(sx, sy); c.quadraticCurveTo(mx, my, hx, hy);
  c.lineCap = 'round'; c.lineWidth = 40 + lw * 2; c.strokeStyle = INK; c.stroke();
  c.lineWidth = 40; c.strokeStyle = col; c.stroke();
  drawHand(c, hx, hy, hand, skin, Math.atan2(hy - my, hx - mx), sx < 0 ? -1 : 1);
}
function drawHand(c, x, y, kind, skin, ang, side) {
  const lw = 5;
  if (kind === 'point' || kind === 'shush' || kind === 'peace' || kind === 'open') {
    withT(c, x, y, 1, ang - Math.PI / 2, () => {
      const fingers = kind === 'open' ? [-0.5, -0.17, 0.17, 0.5] : kind === 'peace' ? [-0.25, 0.25] : [0];
      for (const a of fingers) limb(c, [Math.sin(a) * 12, 10, Math.sin(a) * 34, 50], 14, skin, lw);
      if (kind === 'open') limb(c, [side * -14, 4, side * -34, 22], 14, skin, lw);
    });
  }
  circle(c, x, y, 23, skin, lw);
}
// legs for a 2-legged character: pose stand / walk / run / sit / squat
function legs(c, o, pal, P) {
  const lw = 6, t = o.t || 0, pose = o.pose || 'stand';
  const pants = P.pants, pantsSh = P.pantsSh || P.pants;
  if (pose === 'stand' || pose === 'walk') {
    for (const s of [-1, 1]) {
      const lift = pose === 'walk' ? Math.max(0, Math.sin(t * 9 + (s > 0 ? Math.PI : 0))) * 34 : 0;
      P.leg(c, s, -lift);
      c.beginPath(); c.ellipse(s * 44, -22 - lift, 42, 22, 0, 0, TAU); fillStroke(c, P.shoe, lw);
      line(c, [s * 10, -18 - lift, s * 78, -18 - lift], 7, P.shoeAcc);
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
      limb(c, [hx, hy, kx, ky, fx, fy], 40, k ? pants : pantsSh, lw);
      ellipse(c, fx + 14, fy + 6, 38, 19, P.shoe, lw, sh2 * 0.3);
      line(c, [fx - 14, fy + 12, fx + 44, fy + 12], 6, P.shoeAcc);
    }
  } else {      // sit / squat: knees out, body lowered (caller translates the upper body)
    const sq = pose === 'squat';
    for (const s of [-1, 1]) {
      const kx = s * (sq ? 128 : 82), ky = sq ? -118 : -96;
      limb(c, [s * 34, sq ? -32 : -70, kx, ky, s * (sq ? 66 : 70), -26], 42, pants, lw);
      c.beginPath(); c.ellipse(s * (sq ? 62 : 72), -22, 42, 22, 0, 0, TAU); fillStroke(c, P.shoe, lw);
      line(c, [s * (sq ? 30 : 40), -18, s * (sq ? 96 : 106), -18], 7, P.shoeAcc);
    }
  }
}
function bodyDrop(o) { return o.pose === 'sit' ? 70 : o.pose === 'squat' ? 150 : 0; }

function drawScared(c, o = {}) {
  const lw = 6, pal = SC, [skin, skinSh] = skinOf(pal, o);
  c.save();
  if (o.lean) c.rotate(o.lean);
  legs(c, o, pal, {
    pants: pal.pants, pantsSh: pal.pantsSh, shoe: pal.shoe, shoeAcc: pal.shoeAcc,
    leg: (cc, s, dy) => poly(cc, [s * 10, -160, s * 72, -160, s * 64, -34 + dy, s * 18, -34 + dy], pal.pants, lw),
  });
  c.translate(0, bodyDrop(o) + (o.bob || 0));
  const sh = -322;
  const torso = () => {
    c.beginPath(); c.moveTo(-60, sh - 6); c.bezierCurveTo(-118, sh - 4, -122, sh + 40, -118, sh + 70);
    c.lineTo(-100, -150); c.quadraticCurveTo(0, -136, 100, -150);
    c.lineTo(118, sh + 70); c.bezierCurveTo(122, sh + 40, 118, sh - 4, 60, sh - 6); c.closePath();
  };
  torso(); c.fillStyle = pal.hoodSh; c.fill();
  c.save(); torso(); c.clip(); c.translate(-12, -4); torso(); c.fillStyle = pal.hood; c.fill(); c.restore();
  torso(); fillStroke(c, null, lw);
  rrect(c, -102, -172, 204, 26, 12); fillStroke(c, pal.hoodSh, lw);
  c.beginPath(); c.moveTo(-58, -176); c.lineTo(-44, -236); c.lineTo(44, -236); c.lineTo(58, -176); fillStroke(c, null, 5);
  line(c, [-18, -300, -22, -246], 5, '#fff'); line(c, [18, -300, 22, -246], 5, '#fff');
  circle(c, -22, -244, 5, '#fff', 3); circle(c, 22, -244, 5, '#fff', 3);
  c.beginPath(); c.moveTo(-70, sh - 4); c.quadraticCurveTo(0, sh + 52, 70, sh - 4); c.quadraticCurveTo(0, sh + 22, -70, sh - 4);
  fillStroke(c, pal.hoodSh, 5);
  rrect(c, -26, sh - 30, 52, 36, 10); fillStroke(c, skinSh, 5);
  const aL = o.handL || [-150, -170], aR = o.handR || [150, -170];
  if (!o.armLFront) guyArm(c, -104, sh + 26, aL[0], aL[1], lw, pal.hood, skin, o.handLk);
  withT(c, 0, sh - 20, 1, o.headTilt || 0, () => { c.translate(o.headDx || 0, -(sh - 20) + (o.headDy || 0)); scaredHead(c, o); });
  guyArm(c, 104, sh + 26, aR[0], aR[1], lw, pal.hood, skin, o.handRk);
  if (o.armLFront) guyArm(c, -104, sh + 26, aL[0], aL[1], lw, pal.hood, skin, o.handLk);
  if (o.hold) o.hold(c, aL, aR);
  c.restore();
}

// ================================================================ IDIOT FRIEND
const ID = {
  skin: '#f6c9a0', skinSh: '#e2a47b', shirt: '#ffd23f', shirtSh: '#f0a51c', shorts: '#c7a066', shortsSh: '#a27c45',
  shoe: '#e8364f', shoeAcc: '#ffffff', cap: '#2f6fe0', capSh: '#1f4caf', hair: '#e07b39', hairSh: '#b55a22',
};
function idiotHead(c, o) {
  const lw = 6, t = o.t || 0, pal = ID, [skin, skinSh] = skinOf(pal, o);
  const tn = (o.turn || 0) * 18;
  // backwards cap visor sticking out behind
  withT(c, 70, -520, 1, -0.35, () => { ellipse(c, 0, 0, 80, 24, pal.capSh, lw); });
  ellipse(c, -110, -408, 18, 26, skin, lw); ellipse(c, 110, -408, 18, 26, skin, lw);
  c.beginPath(); c.ellipse(0, -412, 112, 106, 0, 0, TAU); c.fillStyle = skinSh; c.fill();
  c.save(); c.clip(); c.beginPath(); c.ellipse(-10, -418, 110, 104, 0, 0, TAU); c.fillStyle = skin; c.fill(); c.restore();
  c.beginPath(); c.ellipse(0, -412, 112, 106, 0, 0, TAU); fillStroke(c, null, lw);
  // freckles
  c.save(); c.globalAlpha = .7;
  for (const s of [-1, 1]) for (const [dx, dy] of [[0, 0], [12, -6], [14, 8], [-4, 10]]) circle(c, s * 66 + dx + tn, -372 + dy, 3, '#c97c54', 0);
  c.restore();
  // ginger tufts
  for (const s of [-1, 1]) poly(c, [s * 96, -440, s * 126, -470, s * 112, -478, s * 134, -500, s * 98, -492, s * 88, -470], pal.hair, 5);
  // eyes
  const ex = o.expr || 'dumb', lk = o.look || [0, 0];
  for (const s of [-1, 1]) {
    const x = s * 40 + tn, y = -410;
    if (ex === 'happy') { c.beginPath(); c.arc(x, y + 8, 18, Math.PI * 1.1, Math.PI * 1.9); c.lineWidth = 7; c.strokeStyle = INK; c.stroke(); continue; }
    if (ex === 'sneeze') { line(c, [x - s * 22, y - 16, x + s * 14, y, x - s * 22, y + 16], 7); continue; }
    const r = ex === 'sympathy' ? [26, 30] : ex === 'shout' ? [24, 28] : [21, 24];
    ellipse(c, x, y, r[0], r[1], '#fff', 5);
    const pr = ex === 'sympathy' ? 14 : 8;
    circle(c, x + lk[0] * 8, y + lk[1] * 8 + 3, pr, INK, 0);
    circle(c, x + lk[0] * 8 - pr * .35, y + lk[1] * 8 - pr * .2, pr * .35, '#fff', 0);
    if (ex === 'sympathy') circle(c, x + lk[0] * 8 + pr * .4, y + lk[1] * 8 + pr * .45, pr * .18, '#fff', 0);
    let lid = { dumb: .42, serious: .52, blank: .5, shout: .08, sympathy: 0, smug: .45 }[ex] ?? .42;
    lid = Math.max(lid, o.blink || 0);
    if (o.lid !== undefined) lid = o.lid;
    eyeLid(c, x, y, r[0], r[1], lid, skin, ex === 'serious' ? s * 0.12 : 0);
  }
  // brows: thin and high (clueless) / down (serious plan) / up-in (sympathy)
  const bA = { dumb: -0.1, serious: 0.35, sympathy: -0.45, shout: -0.2, happy: -0.15, blank: 0, smug: 0.1, sneeze: 0.4 }[ex] || 0;
  const bY = { serious: -446, sneeze: -448 }[ex] || -470;
  for (const s of [-1, 1]) withT(c, s * 42 + tn, bY, 1, -s * bA, () => { rrect(c, -22, -5, 44, 10, 5); fillStroke(c, pal.hairSh, 4); });
  // round nose
  ellipse(c, tn * 1.2, -376, 16, 12, skinSh, 5); ellipse(c, tn * 1.2 - 5, -380, 4, 3, '#fff', 0);
  if (ex === 'sneeze') { line(c, [tn - 26, -392, tn - 14, -386], 4); line(c, [tn + 26, -392, tn + 14, -386], 4); }
  // mouth (buck teeth)
  const m = o.mouth || 0, my = -338, mx = tn * .8;
  const base = { dumb: .22, happy: .5, smug: 0, serious: 0, blank: 0, sympathy: 0, shout: .3, sneeze: 0 }[ex] ?? .2;
  const open = Math.max(base, m) + (ex === 'shout' ? m * .4 : 0);
  if (open < 0.07) {
    const curve = { smug: 8, serious: -2, sympathy: -8, blank: 0 }[ex] || 0;
    c.beginPath(); c.moveTo(mx - 28, my - (ex === 'smug' ? 6 : 0)); c.quadraticCurveTo(mx, my + curve * 1.6, mx + 30, my - (ex === 'smug' ? 14 : 0));
    c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
    rrect(c, mx - 12, my + 1, 11, 14, 3); fillStroke(c, '#fff', 4); rrect(c, mx + 1, my + 1, 11, 14, 3); fillStroke(c, '#fff', 4);
  } else {
    const h = 14 + 64 * open, w = (ex === 'happy' ? 74 : 54) + (ex === 'shout' ? 18 : 0);
    const sm = ex === 'happy' || ex === 'dumb' ? 10 : 0;
    c.beginPath(); c.moveTo(mx - w / 2, my - 6 - sm); c.quadraticCurveTo(mx, my - 2, mx + w / 2, my - 6 - sm);
    c.bezierCurveTo(mx + w / 2 + 2, my + h * .6, mx + w * .3, my + h, mx, my + h);
    c.bezierCurveTo(mx - w * .3, my + h, mx - w / 2 - 2, my + h * .6, mx - w / 2, my - 6 - sm);
    c.closePath(); fillStroke(c, '#5b1531', 0);
    c.save(); c.clip(); ellipse(c, mx, my + h + 2, w * .38, h * .38, '#ff7d93', 0); c.restore();
    fillStroke(c, null, 5);
    rrect(c, mx - 14, my - 6, 13, 18, 3); fillStroke(c, '#fff', 4); rrect(c, mx + 1, my - 6, 13, 18, 3); fillStroke(c, '#fff', 4);
  }
  // backwards cap crown + strap gap
  c.beginPath(); c.moveTo(-114, -446); c.bezierCurveTo(-118, -560, 118, -560, 114, -446);
  c.quadraticCurveTo(0, -476, -114, -446); c.closePath(); fillStroke(c, pal.cap, lw);
  c.save(); c.beginPath(); c.moveTo(-114, -446); c.bezierCurveTo(-118, -560, 118, -560, 114, -446); c.quadraticCurveTo(0, -476, -114, -446); c.clip();
  ellipse(c, 60, -500, 70, 60, pal.capSh, 0); c.restore();
  c.beginPath(); c.moveTo(-114, -446); c.bezierCurveTo(-118, -560, 118, -560, 114, -446); c.quadraticCurveTo(0, -476, -114, -446); c.closePath(); fillStroke(c, null, lw);
  c.beginPath(); c.arc(0, -458, 22, Math.PI, 0); c.closePath(); fillStroke(c, pal.hair, 5);
  line(c, [-30, -462, 30, -462], 6, '#fff'); circle(c, 0, -548, 8, pal.capSh, 4);
  if (o.sweat) sweat(c, 116, -470 + ((t * 100) % 50), o.sweat, 0.2);
  if (o.blush) { c.save(); c.globalAlpha = .45 * o.blush; for (const s of [-1, 1]) ellipse(c, s * 70 + tn, -370, 20, 11, '#ff6b8c', 0); c.restore(); }
}
function drawIdiot(c, o = {}) {
  const lw = 6, pal = ID, [skin, skinSh] = skinOf(pal, o);
  c.save();
  if (o.lean) c.rotate(o.lean);
  legs(c, o, pal, {
    pants: pal.shorts, pantsSh: pal.shortsSh, shoe: pal.shoe, shoeAcc: pal.shoeAcc,
    leg: (cc, s, dy) => {
      poly(cc, [s * 22, -110, s * 62, -110, s * 56, -34 + dy, s * 28, -34 + dy], skin, lw);
      poly(cc, [s * 24, -80 + dy, s * 60, -80 + dy, s * 58, -34 + dy, s * 26, -34 + dy], '#ffffff', lw);
      line(cc, [s * 26, -66 + dy, s * 58, -66 + dy], 4, '#e8364f');
      poly(cc, [s * 6, -176, s * 84, -176, s * 78, -104, s * 14, -104], pal.shorts, lw);
    },
  });
  c.translate(0, bodyDrop(o) + (o.bob || 0));
  const sh = -322;
  const torso = () => {
    c.beginPath(); c.moveTo(-64, sh - 6); c.bezierCurveTo(-128, sh - 2, -140, sh + 50, -146, sh + 110);
    c.bezierCurveTo(-158, -200, -130, -150, -110, -146); c.quadraticCurveTo(0, -128, 110, -146);
    c.bezierCurveTo(130, -150, 158, -200, 146, sh + 110); c.bezierCurveTo(140, sh + 50, 128, sh - 2, 64, sh - 6); c.closePath();
  };
  torso(); c.fillStyle = pal.shirtSh; c.fill();
  c.save(); torso(); c.clip(); c.translate(-14, -4); torso(); c.fillStyle = pal.shirt; c.fill(); c.restore();
  torso(); fillStroke(c, null, lw);
  // pizza print
  withT(c, -4, -240, 1, 0.05, () => {
    poly(c, [-44, -40, 44, -40, 0, 46], '#ffb347', 5); poly(c, [-48, -48, 48, -48, 44, -34, -44, -34], '#c97b3a', 5);
    circle(c, -12, -22, 8, '#e8364f', 3); circle(c, 14, -18, 7, '#e8364f', 3); circle(c, 0, 6, 7, '#e8364f', 3);
  });
  line(c, [-60, -170, 0, -160, 60, -170], 4);
  c.beginPath(); c.moveTo(-50, sh - 6); c.quadraticCurveTo(0, sh + 40, 50, sh - 6); fillStroke(c, skinSh, 5);
  const aL = o.handL || [-170, -170], aR = o.handR || [170, -170];
  const sleeve = (s) => withT(c, s * 112, sh + 34, 1, s * 0.3, () => { rrect(c, -34, -26, 68, 64, 22); fillStroke(c, pal.shirt, lw); });
  if (!o.armLFront) { guyArm(c, -112, sh + 30, aL[0], aL[1], lw, skin, skin, o.handLk); sleeve(-1); }
  withT(c, 0, sh - 20, 1, o.headTilt || 0, () => { c.translate(o.headDx || 0, -(sh - 20) + (o.headDy || 0)); idiotHead(c, o); });
  guyArm(c, 112, sh + 30, aR[0], aR[1], lw, skin, skin, o.handRk); sleeve(1);
  if (o.armLFront) { guyArm(c, -112, sh + 30, aL[0], aL[1], lw, skin, skin, o.handLk); sleeve(-1); }
  if (o.hold) o.hold(c, aL, aR);
  c.restore();
}

// ================================================================ JASON
const JP = {
  jacket: '#5d6e52', jacketSh: '#46553e', jacketDk: '#323d2c', shirt: '#2b2b30', pants: '#2c3044', pantsSh: '#21253a',
  boot: '#2a1f1c', skin: '#a8a4b8', skinSh: '#878399', mask: '#f6f1e1', maskSh: '#d6cfb8', red: '#e0233a', hole: '#1d1326',
};
const JSIL = {
  jacket: '#1a1530', jacketSh: '#130f24', jacketDk: '#0e0b1b', shirt: '#0e0b1b', pants: '#130f24', pantsSh: '#0e0b1b',
  boot: '#0e0b1b', skin: '#2a2440', skinSh: '#201b33', mask: '#8b86a6', maskSh: '#6e6a88', red: '#7a2a44', hole: '#05030a',
};
function drawJason(c, o = {}) {
  const lw = 7, t = o.t || 0, pal = (o.sil || 0) > 0.5 ? JSIL : JP;
  const br = Math.sin(t * 2.0) * 7 * (o.breathe ?? 1);
  c.save();
  // legs
  const walk = o.pose === 'walk';
  for (const s of [-1, 1]) {
    const lift = walk ? Math.max(0, Math.sin(t * 6 + (s > 0 ? Math.PI : 0))) * 40 : 0;
    poly(c, [s * 20, -460, s * 150, -460, s * 138, -70 - lift, s * 44, -70 - lift], s < 0 ? pal.pants : pal.pantsSh, lw);
    line(c, [s * 90, -330, s * 100, -250], 5);
    rrect(c, s * 92 - 66, -92 - lift, 132, 92, 22); fillStroke(c, pal.boot, lw);
    line(c, [s * 92 - 60, -20 - lift, s * 92 + 60, -20 - lift], 6, '#000');
  }
  c.translate(0, br * 0.4);
  // torso: big jacket with torn hem
  const tor = () => {
    c.beginPath(); c.moveTo(-120, -860); c.bezierCurveTo(-220, -860, -250, -800, -240, -700);
    c.lineTo(-200, -420); c.lineTo(-160, -380); c.lineTo(-130, -420); c.lineTo(-90, -370); c.lineTo(-50, -410); c.lineTo(0, -372);
    c.lineTo(50, -410); c.lineTo(96, -368); c.lineTo(140, -414); c.lineTo(170, -382); c.lineTo(200, -420);
    c.lineTo(240, -700); c.bezierCurveTo(250, -800, 220, -860, 120, -860); c.closePath();
  };
  tor(); c.fillStyle = pal.jacketSh; c.fill();
  c.save(); tor(); c.clip(); c.translate(-26, -6); tor(); c.fillStyle = pal.jacket; c.fill(); c.restore();
  tor(); fillStroke(c, null, lw);
  poly(c, [-56, -850, 56, -850, 70, -400, -70, -400], pal.shirt, 6);
  for (const s of [-1, 1]) poly(c, [s * 120, -860, s * 40, -850, s * 90, -700], pal.jacketDk, 6);
  line(c, [-180, -620, -150, -580], 5, pal.jacketDk); line(c, [150, -520, 180, -560], 5, pal.jacketDk);
  // arms
  const aL = o.handL || [-250, -440], aR = o.handR || [250, -430];
  const arm = (sx, sy, hx, hy) => {
    const dx = hx - sx, dy = hy - sy, L = Math.hypot(dx, dy) || 1, s = sx < 0 ? -1 : 1;
    const bend = Math.max(0, 1 - L / 420) * 90 * s;
    const mx = (sx + hx) / 2 - dy / L * bend, my = (sy + hy) / 2 + dx / L * bend;
    c.beginPath(); c.moveTo(sx, sy); c.quadraticCurveTo(mx, my, hx, hy);
    c.lineCap = 'round'; c.lineWidth = 78 + lw * 2; c.strokeStyle = INK; c.stroke(); c.lineWidth = 78; c.strokeStyle = s < 0 ? pal.jacket : pal.jacketSh; c.stroke();
    return Math.atan2(hy - my, hx - mx);
  };
  const angL = arm(-200, -800 + br, aL[0], aL[1] + br);
  if (o.holdL) o.holdL(c, aL[0], aL[1] + br);
  circle(c, aL[0], aL[1] + br, 40, pal.skin, lw);
  line(c, [aL[0] - 20, aL[1] + br + 10, aL[0] + 20, aL[1] + br + 10], 4);
  // head
  c.save(); c.translate(0, br + (o.headDy || 0)); c.rotate(o.headTilt || 0);
  rrect(c, -62, -900, 124, 70, 24); fillStroke(c, pal.skinSh, lw);
  const tn = (o.turn || 0) * 26;
  c.beginPath(); c.ellipse(0, -995, 118, 132, 0, 0, TAU); fillStroke(c, pal.skin, lw);
  line(c, [-118, -1010, 118, -1010], 8, '#1d1326'); line(c, [-112, -950, 112, -950], 8, '#1d1326');
  const mask = () => { c.beginPath(); c.moveTo(tn, -1130); c.bezierCurveTo(tn + 104, -1128, tn + 116, -1040, tn + 110, -980);
    c.bezierCurveTo(tn + 104, -905, tn + 60, -860, tn, -852); c.bezierCurveTo(tn - 60, -860, tn - 104, -905, tn - 110, -980);
    c.bezierCurveTo(tn - 116, -1040, tn - 104, -1128, tn, -1130); c.closePath(); };
  mask(); c.fillStyle = pal.maskSh; c.fill();
  c.save(); mask(); c.clip(); c.translate(-16, -6); mask(); c.fillStyle = pal.mask; c.fill(); c.restore();
  mask(); fillStroke(c, null, lw);
  // chevrons + vent holes
  poly(c, [tn - 30, -1104, tn, -1080, tn + 30, -1104, tn + 30, -1088, tn, -1062, tn - 30, -1088], pal.red, 4);
  for (const s of [-1, 1]) { poly(c, [tn + s * 92, -968, tn + s * 50, -958, tn + s * 88, -938], pal.red, 4); poly(c, [tn + s * 96, -1006, tn + s * 62, -996, tn + s * 92, -984], pal.red, 4); }
  for (const [x, y] of [[-40, -1060], [40, -1060], [-66, -1046], [66, -1046], [-20, -1050], [20, -1050], [-58, -912], [-36, -900], [-62, -892],
    [58, -912], [36, -900], [62, -892], [-12, -878], [12, -878], [0, -866], [-12, -930], [12, -930]]) circle(c, tn + x, y, 5.5, pal.hole, 0);
  // eye holes (+ glowing pupils when scary)
  const lk = o.look || [0, 0], g = o.glow || 0;
  for (const s of [-1, 1]) {
    const ex = tn + s * 46;
    poly(c, [ex - s * 34, -1022, ex + s * 26, -1012, ex + s * 30, -990, ex + s * 4, -978, ex - s * 32, -990], pal.hole, 5);
    if (g > 0.02) {
      glow(c, ex + lk[0] * 6, -998, 90 * g, 'rgba(255,30,30,0.95)', g);
      circle(c, ex + lk[0] * 6, -998 + lk[1] * 4, 9 * Math.min(1, g * 1.5), '#ff3b3b', 0);
      circle(c, ex + lk[0] * 6, -998 + lk[1] * 4, 4 * Math.min(1, g * 1.5), '#fff2c0', 0);
    } else if (o.dots !== false) circle(c, ex + lk[0] * 6, -996 + lk[1] * 4, 4, '#e8e8f0', 0);
  }
  line(c, [tn, -985, tn - 6, -930, tn + 6, -925], 4, pal.maskSh);
  c.restore();
  // right arm + machete
  arm(200, -800 + br, aR[0], aR[1] + br);
  if (o.machete !== false) machete(c, aR[0], aR[1] + br, 1, o.macheteRot ?? 0.12, pal === JSIL);
  if (o.holdR) o.holdR(c, aR[0], aR[1] + br);
  circle(c, aR[0], aR[1] + br, 40, pal.skin, lw);
  line(c, [aR[0] - 20, aR[1] + br + 10, aR[0] + 20, aR[1] + br + 10], 4);
  c.restore();
}
function machete(c, x, y, s, rot, dark) {
  withT(c, x, y, s, rot, () => {
    rrect(c, -14, -50, 28, 70, 8); fillStroke(c, '#5a3a24', 6);
    c.beginPath(); c.moveTo(-18, 30); c.lineTo(20, 30); c.lineTo(34, 300); c.quadraticCurveTo(30, 360, 0, 380); c.lineTo(-20, 330); c.closePath();
    fillStroke(c, dark ? '#4a4a60' : '#d7dde6', 6);
    if (!dark) { c.save(); c.globalAlpha = .8; line(c, [-8, 50, -6, 320], 6, '#ffffff'); c.restore(); }
    rrect(c, -30, 22, 60, 16, 6); fillStroke(c, '#3a3a44', 5);
  });
}

// ================================================================ props
function phone(c, x, y, s = 1, rot = 0, o = {}) {
  withT(c, x, y, s, rot, () => {
    rrect(c, -30, -56, 60, 112, 12); fillStroke(c, '#22222c', 6);
    if (o.back) {
      circle(c, -12, -36, 9, '#5a6070', 4); circle(c, 10, -38, 6, o.flash ? '#fffbe0' : '#b8b8a8', 3);
      if (o.flash) glow(c, 10, -38, 260 * o.flash, 'rgba(255,255,230,1)', o.flash);
    } else {
      rrect(c, -22, -46, 44, 92, 6); fillStroke(c, o.screen || '#5ab4ff', 0);
      if (o.ui === 'rotate') { /* drawn by caller */ }
    }
  });
}
function sodaCan(c, x, y, s = 1, rot = 0) {
  withT(c, x, y, s, rot, () => {
    rrect(c, -22, -40, 44, 80, 8); fillStroke(c, '#e8364f', 5);
    rrect(c, -22, -6, 44, 16, 0); fillStroke(c, '#fff', 0); line(c, [-22, -40, 22, -40], 5);
    ellipse(c, 0, -42, 20, 6, '#c8ccd6', 4);
  });
}
