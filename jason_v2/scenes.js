// Shot list + timeline for "За нами пришёл Джейсон, а мой друг — идиот" (bright cartoon version).
const T = {
  poka: ws(2, 4), jas: ws(2, 10), vur: ws(2, 11), suka: ws(3, 2), my3: ws(3, 3), resh: ws(3, 5), pozn: ws(3, 8),
  tiho: ws(4, 3), eto: ws(4, 4), ne: ws(4, 6), genius: ws(5, 3), rasp: ws(5, 4), oret: ws(5, 7), jas5: ws(5, 8), a5: ws(5, 10),
  mine: ws(5, 13), end5: we(5, 14), dumal: ws(6, 2), shutit: ws(6, 4), no: ws(6, 5), etot: ws(6, 7), dolb: ws(6, 8), foto: ws(6, 10), vsp: ws(6, 13),
  vyb: ws(7, 2), ponesl: ws(7, 6), beg: ws(8, 3), ost: ws(9, 3), shn: ws(9, 4), zav: ws(9, 5), jprox: ws(11, 1),
  gromko: ws(12, 5), chih: ws(12, 6), choo: we(12, 6) + 0.3, zatk: ws(13, 3), brat14: ws(14, 4), doma: ws(14, 10), endDoma: we(14, 10),
  i15: ws(15, 1), prot: ws(16, 4), tel: ws(16, 6), bratan: ws(16, 7), tolko: ws(16, 10), gor: ws(16, 11),
  dob: ws(17, 3), i17: ws(17, 4), dev: ws(17, 8), end17: we(17, 9),
};
const FLASHES = [22.85, 23.2, 23.45, 24.05, 24.35, 24.62];
function flashAmt(t, list = FLASHES) { let f = 0; list.forEach(x => f = Math.max(f, pulse(t, x, 0.16))); return f; }

function cam(c, x, y, z, r = 0, sh = 0, t = 0) {
  const [sx, sy] = sh ? shake(t, sh, 22) : [0, 0];
  c.translate(W / 2 + sx, H / 2 + sy); if (r) c.rotate(r); c.scale(z, z); c.translate(-x, -y);
}
const SCd = (c, x, y, s, o) => withT(c, x, y, s, 0, () => drawScared(c, o));
const IDd = (c, x, y, s, o) => withT(c, x, y, s, 0, () => drawIdiot(c, o));
const JSd = (c, x, y, s, o) => withT(c, x, y, s, 0, () => drawJason(c, o));
const scIdle = (t, x = {}) => Object.assign({ t, blink: blinkAt(t, 3, 2.7), mouth: talking('s', t) ? mouthAt('s', t) : 0, round: roundAt(t) }, x);
const idIdle = (t, x = {}) => Object.assign({ t, blink: blinkAt(t, 9, 3.3), mouth: talking('i', t) ? mouthAt('i', t) : 0, round: roundAt(t) }, x);
const jIdle = (t, x = {}) => Object.assign({ t, glow: 0.55 + 0.25 * Math.sin(t * 3) }, x);
const canHold = (k = 1) => (c, aL, aR) => sodaCan(c, aR[0] * k, aR[1] - 36, 1, 0);

function nightClearing(c, t, o = {}) {
  skyNight(c, t, { moon: o.moon || [820, 300], r: o.r || 100 });
  forestRow(c, o.y1 || 1080, -800, 2000, 3, 340, 520, TREE_FAR, 5);
  forestRow(c, (o.y1 || 1080) + 60, -800, 2000, 7, 420, 640, TREE_N, 6, .8);
  ground(c, (o.y1 || 1080) + 70, '#2f8a5c', '#246c48');
  fog(c, (o.y1 || 1080) + 70, 140, 0.35, t);
}

// ------------------------------------------------------------------ 1. arrival at dusk
function shCamp(c, t) {
  const k = E.io(inv(0, 1.6, t));
  c.save(); cam(c, 540, lerp(640, 1060, k), lerp(1.0, 1.1, inv(0.6, 2.4, t)), 0, 1.5, t);
  skyDusk(c, t);
  for (let i = 0; i < 6; i++) { const bx = -200 + (t * 220 + i * 70) % 1500, by = 420 + i * 30 + Math.sin(t * 3 + i) * 8, fl = Math.sin(t * 16 + i) * 12;
    line(c, [bx - 22, by - fl, bx, by, bx + 22, by - fl], 6, '#5a2a6a'); }
  forestRow(c, 1060, -600, 1800, 4, 380, 560, { a: '#8a4fa8', b: '#6e3a8c', trunk: '#5a2a6a' }, 5);
  ground(c, 1150, '#3f9a5e', '#2f7d4a');
  cabin(c, 150, 1310, 0.95, t);
  // camp sign (Crystal Lake easter egg)
  withT(c, 70, 1400, 1, -0.06, () => { line(c, [0, 0, 0, -220], 14, '#8a5232'); rrect(c, -10, -330, 270, 130, 16); fillStroke(c, '#c8743c', 7);
    text(c, 'ЛАГЕРЬ', 125, -295, 30, '#fff', { stroke: 7 }); text(c, 'ХРУСТАЛЬНОЕ', 125, -255, 30, '#ffe14d', { stroke: 7 }); text(c, 'ОЗЕРО', 125, -218, 26, '#fff', { stroke: 6 }); });
  campfire(c, 540, 1620, 0.7, t);
  campChair(c, 820, 1640, 0.62, false);
  const sip = bump(t, 1.2, 2.2);
  IDd(c, 820, 1640, 0.62, idIdle(t, { pose: 'sit', expr: 'happy', handR: [lerp(170, 40, sip), lerp(-170, -340, sip)], hold: canHold(), handL: [-170, -230] }));
  campChair(c, 820, 1640, 0.62, true);
  const lk = kf(t, [[0.7, -0.9], [1.4, -0.9], [1.8, 0.8], [2.4, 0.8]]);
  SCd(c, 300, 1660, 0.66, scIdle(t, { expr: 'happy', look: [lk, 0], turn: lk * .5, handL: [-120, -200], handR: [120, -200] }));
  c.restore();
  sticker(c, 'ОТДЫХ 😎', 770, 1080, 56, '#2f6fe0', inv(1.15, 1.35, t), 0.1);
}
function shChill(c, t) {
  const bad = inv(T.poka - 0.05, T.poka + 0.15, t);
  c.save(); cam(c, 540, 1120, lerp(1.25, 1.32, inv(2.35, 3.9, t)), 0, 2 + bad * 8, t);
  skyDusk(c, t, bad * 0.85);
  forestRow(c, 950, -600, 1800, 4, 380, 560, bad > .5 ? TREE_FAR : { a: '#8a4fa8', b: '#6e3a8c', trunk: '#5a2a6a' }, 5);
  ground(c, 1040, bad > .5 ? '#2a6e50' : '#3f9a5e', '#2f7d4a');
  logSeat(c, 330, 1500, 0.9);
  const roast = Math.sin(t * 5) * 6;
  SCd(c, 330, 1500, 0.7, scIdle(t, { pose: 'sit', expr: bad > .5 ? 'shock' : 'happy', handR: [200 + roast, -330], handL: [-150, -150],
    hold: (cc, aL, aR) => { line(cc, [aR[0], aR[1], aR[0] + 170, aR[1] + 150], 8, '#8a5232'); ellipse(cc, aR[0] + 178, aR[1] + 158, 22, 18, '#fff6e6', 5); } }));
  campChair(c, 790, 1520, 0.6, false);
  const sip = bump(t, 2.5, 3.4);
  IDd(c, 790, 1520, 0.6, idIdle(t, { pose: 'sit', expr: bad > .5 ? 'blank' : 'happy', handR: [lerp(170, 40, sip), lerp(-170, -340, sip)], hold: canHold(), handL: [-170, -230] }));
  campChair(c, 790, 1520, 0.6, true);
  campfire(c, 560, 1600, lerp(0.75, 0.4, bad), t, 1 - bad * .6);
  c.restore();
  const okA = inv(2.75, 2.95, t);
  if (bad < 0.5) sticker(c, 'ВСЁ НОРМ ✅', W / 2, 640, 72, '#1f9d55', okA, -0.06);
  else sticker(c, 'НЕ НОРМ ❌', W / 2, 640, 80, '#e0233a', 1, 0.06 + Math.sin(t * 40) * 0.03);
}
// ------------------------------------------------------------------ 2. he arrives
function shSil(c, t) {
  const k = inv(T.poka + 0.2, T.jas, t);
  c.save(); cam(c, 540, 1000, lerp(1.0, 1.16, E.io(k)), 0, 1.2, t);
  skyNight(c, t, { moon: [860, 260], r: 90 });
  forestRow(c, 1100, -600, 1800, 11, 420, 620, TREE_FAR, 5);
  ground(c, 1180, '#1f5a46', '#174a3a');
  fog(c, 1200, 160, 0.4, t);
  JSd(c, 540, 1420, lerp(0.6, 0.66, k), { t, sil: 1, glow: inv(T.poka + 0.5, T.poka + 0.8, t) * (0.7 + 0.3 * Math.sin(t * 8)), dots: false });
  for (const [x, h] of [[150, 1500], [930, 1500]]) pine(c, x, 1560, h, TREE_N, 7);
  fog(c, 1450, 200, 0.45, t);
  c.restore();
  boom(c, 'ТУК', 200, 760, 70, '#ff6b7f', bump(t, 4.4, 4.75) * 1.2, -0.15, null);
  boom(c, 'ТУК', 880, 820, 70, '#ff6b7f', bump(t, 4.75, 5.08) * 1.2, 0.15, null);
}
function shBoss(c, t) {
  const lt = t - T.jas, fl = pulse(t, T.jas, 0.25);
  sunburst(c, W / 2, 1000, t, '#2a0812', '#4a0c1c', 18, 1.2);
  c.save(); cam(c, 540, 980, lerp(1.25, 1.4, E.out(clamp(lt / 0.6))), 0, 10 * (1 - clamp(lt / 0.4)), t);
  JSd(c, 540, 1520, 0.78, { t, glow: 1, look: [0, 0] });
  c.restore();
  speedLines(c, W / 2, 900, t, { n: 40, r0: 520, col: 'rgba(255,80,80,0.5)', w: 9 });
  // boss nameplate
  const a = E.out(clamp(lt / 0.2));
  withT(c, lerp(-600, W / 2, a), 1230, 1, -0.04, () => {
    rrect(c, -470, -90, 940, 180, 24); fillStroke(c, 'rgba(15,8,25,0.92)', 8, '#ff2a3d');
    text(c, 'БОСС', -360, -40, 34, '#ff2a3d', { fam: 'Press', stroke: 0 });
    text(c, 'ДЖЕЙСОН ВУРХИЗ', 40, -30, 60, '#fff', { stroke: 10 });
    rrect(c, -420, 22, 840, 40, 8); fillStroke(c, '#300', 5, '#fff');
    rrect(c, -414, 28, 828, 28, 5); fillStroke(c, '#ff2a3d', 0);
    text(c, 'HP ∞', 360, -38, 28, '#ffd23f', { fam: 'Press', stroke: 0 });
  });
  flash(c, fl * 0.8);
}
function shScream(c, t) {
  const sk = inv(T.suka - 0.05, T.suka + 0.25, t);
  sunburst(c, W / 2, 800, t, sk > .5 ? '#3a2a86' : '#2563eb', sk > .5 ? '#2f2378' : '#1d4ed8', 16, sk > .5 ? 0.2 : 1.2);
  c.save(); cam(c, 540, 820, lerp(2.0, 2.15, inv(T.vur, 7.3, t)), 0, sk > .5 ? 1 : 9, t);
  SCd(c, 540, 1480, 1, sk > .5 ? scIdle(t, { expr: 'annoyed', look: [1, 0], turn: 0.3 })
    : scIdle(t, { expr: 'scared', hairUp: E.out(inv(T.vur, T.vur + 0.2, t)), pale: 0.6, sweat: 1, mouthOpenFixed: 0.7, yell: 1 }));
  c.restore();
  if (sk < 0.5) speedLines(c, W / 2, 800, t, { n: 50, r0: 430, col: 'rgba(255,255,255,0.7)', w: 8 });
  pip(c, t, 850, 520, 150, inv(T.suka + 0.1, T.suka + 0.3, t), (cc) => withT(cc, 0, 290, 0.62, 0, () => drawIdiot(cc, idIdle(t, { expr: 'happy', handL: [-200, -560 + Math.sin(t * 14) * 30], handLk: 'open' }))), ['#ffe14d', '#ffd000']);
}
// ------------------------------------------------------------------ 3. "decided to meet him"
function shWave(c, t) {
  const step = E.io(inv(T.resh, T.resh + 0.7, t)), grab = E.out(inv(T.pozn - 0.4, T.pozn - 0.1, t));
  c.save(); cam(c, 540, 1180, lerp(1.0, 1.08, inv(7.36, 9.6, t)), 0, 2 + grab * 5, t);
  nightClearing(c, t, { y1: 1000, moon: [860, 280] });
  cabin(c, 860, 1200, 0.7, t);
  JSd(c, 150, 1250, 0.32, jIdle(t, { glow: 0.9 }));
  const x2 = lerp(600, 470, step) + grab * 50;
  const wave = Math.sin(t * 14) * 40;
  IDd(c, x2, 1640, 0.82, idIdle(t, { expr: 'happy', pose: step > 0 && step < 1 ? 'walk' : 'stand', handL: [-230, -560 + wave], handLk: 'open', handR: [170, -170], hold: canHold() }));
  const x1 = lerp(920, 820, step) - grab * 60;
  const sh = [x2 + 0.82 * 112, 1640 - 0.82 * 300];
  SCd(c, x1, 1660, 0.82, scIdle(t, { expr: 'scared', sweat: 1, pale: .3, mouthOpenFixed: grab > .3 ? .6 : 0, lean: -0.12 * grab,
    handL: grab > 0 ? [lerp(-150, (sh[0] - x1) / 0.82, grab), lerp(-170, (sh[1] - 1660) / 0.82, grab)] : [-150, -170], handLk: grab > .5 ? 'open' : 'fist', armLFront: true }));
  c.restore();
  if (grab > 0) speedLines(c, 600, 1100, t, { n: 30, r0: 380, col: `rgba(255,255,255,${0.6 * grab})`, w: 7 });
  sticker(c, 'ЗНАКОМСТВО 🤝', 360, 820, 56, '#2f6fe0', inv(T.resh, T.resh + 0.2, t), -0.1);
  boom(c, 'НЕТ!', 860, 950, 90, '#e0233a', inv(T.pozn - 0.35, T.pozn - 0.15, t), 0.12);
}
// ------------------------------------------------------------------ 4. inside: "quiet, it's Jason"
function shInside(c, t) {
  const push = 0.07 * E.out(inv(T.tiho, T.tiho + .2, t)) + 0.07 * E.out(inv(T.eto, T.eto + .2, t)) + 0.12 * E.out(inv(T.ne, T.ne + .2, t));
  c.save(); cam(c, 560 + push * 300, 1080 - push * 300, 0.95 + push, 0, 2, t);
  interiorRoom(c, t, { win: [60, 520, 460, 560], outside: (cc, wx, wy, ww, wh) => JSd(cc, wx + ww * .5, wy + wh * .82, 0.24, jIdle(t, { glow: 1 })) });
  const sip = bump(t, 9.85, 10.7) + bump(t, 12.55, 13.2);
  IDd(c, 900, 1700, 0.95, idIdle(t, { expr: 'dumb', look: [-1, 0], handR: [lerp(170, 40, sip), lerp(-170, -340, sip)], hold: canHold() }));
  let P = { expr: 'scared', sweat: 1, look: [-1, 0] };
  if (t < T.tiho) P = Object.assign(P, { turn: -0.6, look: [-1, 0], lean: -0.1, handL: [-180, -380], handR: [120, -260] });
  else if (t < T.eto) P = Object.assign(P, { turn: 0.5, look: [1, 0], handR: [24, -330], handRk: 'shush' });
  else if (t < T.ne) P = Object.assign(P, { turn: 0.3, look: [1, 0], handL: [-330, -440], handLk: 'point', lean: -0.05 });
  else P = Object.assign(P, { expr: 'shock', look: [1, 0], handL: [-150, -380], handR: [150, -380], handLk: 'open', handRk: 'open' });
  SCd(c, 600, 1700, 0.95, scIdle(t, P));
  c.restore();
  boom(c, 'ТССС!', 330, 830, 96, '#2f6fe0', inv(T.tiho, T.tiho + .2, t) * (1 - inv(T.eto - .1, T.eto, t)), -0.12);
  if (t > T.eto && t < T.ne) arrowLabel(c, 'ОН!', 760, 640, 360, 900, inv(T.eto, T.eto + .2, t), '#e0233a');
  boom(c, 'ХЛЮП', 900, 760, 64, '#ff8a1f', bump(t, 12.7, 13.2), 0.1, null);
}
// ------------------------------------------------------------------ 5. the genius opens the window
function shGenius(c, t) {
  const g = inv(T.genius, T.genius + 0.3, t);
  sunburst(c, W / 2, 760, t, '#ffe14d', '#ffd000', 20, 0.4);
  c.save(); cam(c, 540, 820, lerp(1.9, 2.05, inv(13.3, 14.5, t)), 0, 0, t);
  IDd(c, 540, 1480, 1, idIdle(t, { expr: g > 0.3 ? 'smug' : 'dumb', look: [0.3, -0.3], headTilt: -0.06 * g }));
  c.restore();
  particles(c, t, 16, i => ({ t0: T.genius + i * 0.04, life: 0.9, a: hash(i) * TAU }), (cc, p, age, u) =>
    star4(cc, W / 2 + Math.cos(p.a) * (200 + 300 * E.out(u)), 760 + Math.sin(p.a) * (160 + 260 * E.out(u)), 34 * (1 - u), '#fff', u * 5));
  sticker(c, 'ГЕНИЙ 💡', W / 2, 360, 92, '#e0233a', g, -0.06);
}
const WIN_S = 2.35, WIN_X = 540 - WIN_S * 535, WIN_Y = 900 + WIN_S * 210;
function windowShot(c, t, o = {}) {
  skyNight(c, t, { moon: [930, 170], r: 70 });
  forestRow(c, 700, -400, 1600, 5, 380, 520, TREE_FAR, 5);
  ground(c, WIN_Y, '#2f8a5c', '#246c48');
  const sill = WIN_Y + WIN_S * (CAB.win[1] + CAB.win[3]);
  cabin(c, WIN_X, WIN_Y, WIN_S, t, {
    shutters: o.shutters ?? 1,
    inside: (cc, wx, wy, ww, wh) => {
      glow(cc, wx + ww / 2, wy + wh / 2, 300, 'rgba(255,200,110,0.6)');
      for (let yy = wy; yy < wy + wh; yy += 30) line(cc, [wx, yy, wx + ww, yy], 3, '#d98a4e');
      if (o.f1in) withT(cc, wx + ww * .78, wy + wh + 40, 0.17, 0, () => drawScared(cc, o.f1in));
    },
  });
  if (o.lean) o.lean(c, sill);
  cabinSill(c, WIN_X, WIN_Y, WIN_S);
  c.fillStyle = '#2f8a5c'; c.fillRect(-2000, WIN_Y + 4, 5000, 2000); line(c, [-2000, WIN_Y + 4, 3000, WIN_Y + 4], 7);
}
function shWindow(c, t) {
  const open = E.out(inv(T.rasp, T.rasp + 0.15, t)), lean = E.back(inv(T.rasp + 0.05, T.rasp + 0.4, t));
  const cup = E.out(inv(T.oret, T.oret + 0.2, t)), shout = talking('i', t) ? mouthAt('i', t) : 0;
  c.save(); cam(c, 540, lerp(980, 930, inv(T.oret, T.a5, t)), lerp(1.25, 1.42, inv(T.oret, T.a5, t)), 0, 2 + shout * 14, t);
  windowShot(c, t, {
    shutters: open,
    f1in: open > 0.5 ? scIdle(t, { expr: 'scared', handL: [-60, -560], handR: [60, -560], handLk: 'open', handRk: 'open', armLFront: true, mouthOpenFixed: .6 }) : null,
    lean: (cc, sill) => {
      if (open < 0.3) return;
      const s = lerp(1.0, 1.18, lean), y = sill + 40 + 160 * s + lerp(220, 0, lean);
      const hl = cup > 0 ? [-60, -350] : [-260, -560], hr = cup > 0 ? [60, -350] : [260, -560];
      IDd(cc, 540, y, s, idIdle(t, { expr: shout > 0.05 ? 'shout' : 'happy', mouth: shout, handL: hl, handR: hr, handLk: 'open', handRk: 'open', armLFront: cup > 0 }));
    },
  });
  c.restore();
  boom(c, 'БАХ!', 760, 560, 110, '#ff8a1f', inv(T.rasp, T.rasp + 0.15, t) * (1 - inv(T.rasp + 0.9, T.rasp + 1.1, t)), 0.12);
  if (talking('i', t)) speedLines(c, W / 2, 900, t, { n: 40, r0: 520, col: 'rgba(255,255,255,0.55)', w: 8 });
  pip(c, t, 220, 1700, 150, inv(T.jas5, T.jas5 + 0.2, t), (cc) => withT(cc, 0, 300, 0.6, 0, () => drawScared(cc, scIdle(t, { expr: 'scared', pale: .5, sweat: 1, mouthOpenFixed: .5, hairUp: .6 }))), ['#7dd3fc', '#38bdf8']);
}
function shStare(c, t) {
  const tilt = 0.16 * E.back(inv(T.mine, T.mine + 0.4, t));
  c.save(); cam(c, 540, 900, lerp(1.3, 1.5, inv(T.a5, T.end5, t)), 0, 0.8, t);
  nightClearing(c, t, { y1: 1050, moon: [220, 280] });
  JSd(c, 540, 1660, 0.82, jIdle(t, { headTilt: tilt, glow: 0.4, look: [0, 0] }));
  fog(c, 1600, 200, 0.4, t);
  c.restore();
  bubble(c, 770, 560, 220, 170, [-40, -80, 150], inv(T.mine + 0.1, T.mine + 0.3, t), (cc) => text(cc, '?', 0, 4, 110, '#2f6fe0', { fam: 'Press', stroke: 0 }), { rot: 0.08 });
  sticker(c, '*сверчки*', W / 2, 1180, 46, '#8a8aa0', inv(T.end5, T.end5 + 0.15, t), -0.04);
}
function shFacepalm(c, t) {
  c.fillStyle = vgrad(c, 0, H, [[0, '#5b6bd6'], [1, '#3a2a86']]); c.fillRect(0, 0, W, H);
  const sl = E.io(inv(T.end5 + 0.15, 20.0, t));
  c.save(); cam(c, 540, 800, 2.05, 0, 0, t);
  SCd(c, 540, 1460, 1, scIdle(t, { expr: 'despair', handR: [20, lerp(-470, -400, sl)], handRk: 'open', blink: 1, headTilt: -0.06 }));
  c.restore();
  sticker(c, '*сверчки*', W / 2, 300, 54, '#8a8aa0', 1, 0.04);
}
// ------------------------------------------------------------------ 6. flash photos
function shHope(c, t) {
  const chuckle = Math.sin(t * 20) * 6 * bump(t, T.dumal, T.shutit + 0.4);
  c.save(); cam(c, 540, 820, lerp(1.85, 2.0, inv(20.05, 21.7, t)), 0, 1, t);
  interiorRoom(c, t, { win: [-420, 300, 460, 520], calendar: false, lampX: 1300, wind: .5, shutters: 1 });
  SCd(c, 540, 1480 + chuckle, 1, scIdle(t, { expr: 'nervous', sweat: 1, look: [0.8, 0], handL: [-120, -230], handR: [120, -230] }));
  c.restore();
  sticker(c, 'ПРАНК? 🙏', W / 2, 400, 80, '#2f6fe0', inv(T.dumal, T.dumal + 0.2, t), -0.06);
}
function shPhoneUp(c, t) {
  const up = E.back(inv(T.no - 0.05, T.no + 0.3, t)), on = t > T.no + 0.35;
  c.save(); cam(c, 540, 930, 1.55, 0, 1, t);
  windowShot(c, t, {
    lean: (cc, sill) => IDd(cc, 540, sill + 40 + 160 * 1.18, 1.18, idIdle(t, { expr: 'happy', handR: [lerp(170, 200, up), lerp(-170, -560, up)], handL: [-170, -170],
      hold: (c2, aL, aR) => phone(c2, aR[0], aR[1] - 40, 1.1, 0.1, { back: 1, flash: on ? 0.25 : 0 }) })),
  });
  c.restore();
  sticker(c, 'ВСПЫШКА: ВКЛ ⚡', W / 2, 420, 64, '#ff8a1f', inv(T.no + 0.3, T.no + 0.5, t), -0.05);
}
function shFlashes(c, t) {
  const f = flashAmt(t);
  const sub = t < 23.35 ? 'win' : t < 23.85 ? 'j1' : t < 24.55 ? 'win2' : 'j2';
  if (sub === 'win' || sub === 'win2') {
    c.save(); cam(c, 540, 930, sub === 'win' ? 1.5 : 1.42, 0, 2 + f * 10, t);
    windowShot(c, t, {
      f1in: sub === 'win' ? scIdle(t, { expr: 'scared', handL: [-60, -560], handR: [60, -560], handLk: 'open', handRk: 'open', armLFront: true, mouthOpenFixed: .6 }) : null,
      lean: (cc, sill) => {
        const x2 = sub === 'win2' ? 470 : 540;
        IDd(cc, x2, sill + 40 + 160 * 1.15, 1.15, idIdle(t, { expr: f > .3 ? 'happy' : 'dumb', handR: [210, -560 + Math.sin(t * 20) * 10], handL: [-170, -170],
          hold: (c2, aL, aR) => phone(c2, aR[0], aR[1] - 40, 1.1, 0.1, { back: 1, flash: f }) }));
        if (sub === 'win2') SCd(cc, 700, sill + 40 + 160 * 1.05, 1.05, scIdle(t, { expr: 'angry', vein: 1, lean: -0.15, handL: [-240, -480], handLk: 'open', armLFront: true, handR: [-90, -560], handRk: 'open' }));
      },
    });
    c.restore();
  } else {
    const z = sub === 'j1' ? 1.35 : 2.3;
    c.save(); cam(c, 540, sub === 'j1' ? 950 : 760, z, 0, f * 8, t);
    nightClearing(c, t, { y1: 1050, moon: [220, 280] });
    JSd(c, 540, 1660, 0.82, { t, glow: 1, look: [0, 0] });
    c.restore();
  }
  flash(c, f * 0.85);
  FLASHES.forEach((x, k) => boom(c, 'ЩЁЛК', k % 2 ? 300 : 790, k % 2 ? 1180 : 480, 84, '#2f6fe0', bump(t, x - 0.02, x + 0.3) * 1.3, k % 2 ? -0.15 : 0.15));
  if (t < 23.35) arrowLabel(c, 'ДОЛБОЁБ', 760, 1180, 560, 800, inv(T.dolb, T.dolb + 0.2, t), '#e0233a');
}
function shPhoto(c, t) {
  const lt = t - T.vsp;
  c.fillStyle = '#dfe6ff'; c.fillRect(0, 0, W, H);
  c.save(); cam(c, 540, 770, lerp(2.6, 2.45, E.out(clamp(lt / 0.3))), -0.05 * E.out(clamp(lt / 0.3)), 0, t);
  JSd(c, 540, 1660, 0.95, { t, glow: 0.2, look: [0, 0] });
  c.restore();
  cameraUI(c, t);
  c.save(); c.lineWidth = 7; c.strokeStyle = '#ffd23f'; c.strokeRect(330, 470, 420, 460); c.restore();
  flash(c, pulse(t, T.vsp + 0.05, 0.3));
  sticker(c, 'ФОТО СОХРАНЕНО ✅', W / 2, 1180, 58, '#1f9d55', inv(T.vsp + 0.2, T.vsp + 0.4, t), 0.03);
}
// ------------------------------------------------------------------ 7-9. run
function shRunOut(c, t) {
  const door = E.out(inv(T.vyb - 0.1, T.vyb + 0.05, t));
  c.save(); cam(c, lerp(640, 420, E.io(inv(25.9, T.ponesl, t))), 1150, 0.95, 0, 2 + pulse(t, T.vyb, .4) * 12, t);
  nightClearing(c, t, { y1: 980 });
  cabin(c, 100, 1400, 1.0, t, { doorOpen: door, shutters: 1, doorBang: pulse(t, T.vyb, .4) });
  JSd(c, 1050, 1500, 0.52, jIdle(t, { turn: -lerp(0, 0.7, inv(T.vyb + 0.3, T.vyb + 0.8, t)), glow: 1 }));
  const r1 = inv(T.vyb, T.vyb + 0.9, t), r2 = inv(T.vyb + 0.4, T.vyb + 1.3, t);
  if (r1 > 0) SCd(c, lerp(260, -60, E.out(r1)), lerp(1420, 1720, r1), lerp(0.55, 0.8, r1), scIdle(t, { pose: 'run', expr: 'scared', sweat: 1, mouthOpenFixed: .7, handL: [-140, -300 + Math.sin(t * 26) * 40], handR: [140, -300 - Math.sin(t * 26) * 40] }));
  if (r2 > 0) IDd(c, lerp(260, 100, E.out(r2)), lerp(1420, 1700, r2), lerp(0.55, 0.78, r2), idIdle(t, { pose: 'run', expr: 'happy', handL: [-240, -520 + Math.sin(t * 20) * 90], handR: [240, -520 - Math.sin(t * 20) * 90], handLk: 'open', handRk: 'open' }));
  c.restore();
  boom(c, 'БАХ!', 300, 760, 110, '#ff8a1f', inv(T.vyb - 0.05, T.vyb + 0.1, t) * (1 - inv(T.vyb + 0.7, T.vyb + 0.9, t)), -0.12);
}
function chaseActors(t, o = {}) {
  const A = [];
  A.push([o.jz || 3000, (c) => { const [x, y] = pp(o.jx || -40, o.jz || 3000); JSd(c, x, y, ps(o.jz || 3000) * 1.0, jIdle(t, { pose: 'walk', glow: 1 })); }]);
  if (o.idz) A.push([o.idz, (c) => { const [x, y] = pp(o.idx || 120, o.idz); IDd(c, x, y, ps(o.idz) * 1.2, o.idPose || idIdle(t, { pose: 'run', expr: 'happy', handL: [-240, -520 + Math.sin(t * 20) * 90], handR: [240, -520 - Math.sin(t * 20) * 90], handLk: 'open', handRk: 'open' })); }]);
  if (o.scz) A.push([o.scz, (c) => { const [x, y] = pp(o.scx || -120, o.scz); const lb = Math.sin(t * 5) > .3;
    SCd(c, x, y, ps(o.scz) * 1.2, scIdle(t, { pose: 'run', expr: 'scared', sweat: 1, mouthOpenFixed: .6, turn: lb ? -0.8 : 0, look: lb ? [-1, 0] : [0, 0], handL: [-140, -300 + Math.sin(t * 26) * 40], handR: [140, -300 - Math.sin(t * 26) * 40] })); }]);
  return A;
}
function shChase(c, t) {
  c.save(); cam(c, 540, 960, 1, 0, 4, t);
  pathScene(c, t, t * 900, chaseActors(t, { idz: 1150, scz: 820 }));
  c.restore();
  speedLines(c, W / 2, 900, t, { n: 24, r0: 560, col: 'rgba(255,255,255,0.35)', w: 6 });
}
function shBegi(c, t) {
  const talk = talking('s', t) ? mouthAt('s', t) : 0, pt = E.back(inv(T.beg - 0.1, T.beg + 0.15, t));
  sunburst(c, W / 2, 900, t, '#ff3b4f', '#d6233a', 18, 2.0);
  speedLines(c, W / 2, 900, t, { n: 60, r0: 300, col: 'rgba(255,255,255,0.8)', w: 9 });
  c.save(); cam(c, 540, 820, 1.75, 0, 6 + talk * 12, t);
  const bob = Math.abs(Math.sin(t * 13)) * 14;
  SCd(c, 540, 1500 - bob, 1, scIdle(t, { expr: 'scared', sweat: 1, mouth: Math.max(talk, 0.15), yell: 1, hairUp: .5,
    handR: pt > 0 ? [lerp(140, 300, pt), lerp(-300, -560, pt)] : [140, -300 - Math.sin(t * 26) * 40], handRk: pt > .5 ? 'point' : 'fist',
    handL: [-140, -300 + Math.sin(t * 26) * 40] }));
  c.restore();
  pip(c, t, 860, 660, 140, 1, (cc) => { cc.fillStyle = '#1a1446'; cc.fillRect(-200, -200, 400, 400); withT(cc, 0, 360, 0.36, 0, () => drawJason(cc, jIdle(t, { pose: 'walk', glow: 1 }))); }, ['#2a0812', '#4a0c1c'], '#ff2a3d');
}
function shStop(c, t) {
  const stop = t >= T.ost, k = inv(T.ost, T.ost + 0.15, t);
  const camz = Math.min(t, T.ost) * 900;
  c.save(); cam(c, 540, 960, 1 + 0.1 * E.out(k), 0, stop ? 0 : 3, t);
  pathScene(c, t, camz, chaseActors(stop ? T.ost : t, { idz: 900, idx: 0,
    idPose: stop ? idIdle(t, { expr: 'blank', look: [0, 1], headTilt: 0.08 }) : null }));
  c.restore();
  if (stop) {
    c.save(); c.globalAlpha = 0.25 * k; c.fillStyle = '#000'; c.fillRect(0, 0, W, H); c.restore();
    boom(c, 'СКРРР!', W / 2, 620, 120, '#ff8a1f', k, -0.08);
    withT(c, W / 2, 1150, E.back(k), 0, () => { rrect(c, -90, -90, 180, 180, 30); fillStroke(c, 'rgba(255,255,255,0.9)', 7); rrect(c, -46, -50, 30, 100, 8); fillStroke(c, INK, 0); rrect(c, 16, -50, 30, 100, 8); fillStroke(c, INK, 0); });
  }
}
function shLaces(c, t) {
  const loop = Math.sin(t * 8);
  c.save(); cam(c, 540, 1060, 1.05, 0, 1, t);
  pathScene(c, t, T.ost * 900, [[2200, (cc) => { const [x, y] = pp(120, lerp(2300, 2050, inv(T.shn, T.zav, t))); JSd(cc, x, y, ps(2200), jIdle(t, { pose: 'walk', glow: 1 })); }],
    [820, (cc) => { const [x, y] = pp(-20, 820); IDd(cc, x, y, ps(820) * 1.1, idIdle(t, { pose: 'squat', expr: 'serious', look: [0.3, 1], headTilt: 0.12, handL: [40 + loop * 14, -60], handR: [90 - loop * 14, -66] })); }]]);
  c.restore();
  sticker(c, 'ЗАВЯЗЫВАЕТ 🎀', W / 2, 590, 70, '#ff5cc8', inv(T.shn, T.shn + 0.15, t), -0.06);
}
function shWtf(c, t) {
  const spread = E.back(inv(T.zav, T.zav + 0.35, t));
  c.save(); cam(c, 540, 960, 1.04, 0, 1, t);
  pathScene(c, t, T.ost * 900, [[1900, (cc) => { const [x, y] = pp(40, 1900); JSd(cc, x, y, ps(1900), jIdle(t, { pose: 'walk', glow: 1 })); }],
    [1250, (cc) => { const [x, y] = pp(-150, 1250); IDd(cc, x, y, ps(1250) * 1.2, idIdle(t, { pose: 'squat', expr: 'serious', look: [0.3, 1], handL: [40, -60], handR: [90, -66] })); }]]);
  SCd(c, 820, 2150, 1.5, scIdle(t, { expr: 'shock', turn: -0.8, look: [-1, 0], sweat: 1, handL: [lerp(-150, -300, spread), lerp(-200, -560, spread)], handR: [lerp(150, 300, spread), lerp(-200, -560, spread)], handLk: 'open', handRk: 'open' }));
  c.restore();
  boom(c, '?!', 800, 640, 150, '#e0233a', inv(T.zav + 0.05, T.zav + 0.25, t), 0.1);
}
// ------------------------------------------------------------------ 10-14. the tree
function treeBg(c, t, o = {}) {
  nightClearing(c, t, { y1: o.y1 || 1120, moon: o.moon || [180, 260], r: 80 });
}
function shHide(c, t) {
  const peek = E.io(inv(33.9, 34.25, t)) * (1 - E.io(inv(34.7, 34.95, t)));
  c.save(); cam(c, lerp(620, 540, E.io(inv(33.35, 35.05, t))), 1150, 1.0, 0, 1, t);
  treeBg(c, t);
  bigTree(c, 540, 1760, 0.9);
  SCd(c, 420, 1780, 0.86, scIdle(t, { expr: 'scared', sweat: 1, turn: -0.9 * peek, look: [peek > .3 ? -1 : 0, 0], lean: -0.14 * peek, headDx: -20 * peek,
    handL: [-200, -330], handR: [200, -330], handLk: 'open', handRk: 'open' }));
  IDd(c, 700, 1790, 0.86, idIdle(t, { expr: 'dumb', look: [0, 1], handR: [40, -280], handL: [-170, -170], hold: (cc, aL, aR) => phone(cc, aR[0], aR[1] - 30, 1, 0, { screen: '#9fe3ff' }) }));
  glow(c, 700, 1320, 160, 'rgba(150,220,255,0.5)');
  c.restore();
  sticker(c, 'СТЕЛС-РЕЖИМ 🥷', W / 2, 580, 66, '#2f6fe0', inv(33.65, 33.85, t), -0.05);
}
function shPass(c, t) {
  const k = inv(35.05, 36.65, t);
  c.save(); cam(c, 540, 1150, lerp(1.04, 1.12, k), -0.03 * k, 1, t);
  treeBg(c, t);
  JSd(c, lerp(-200, 1300, k), 1560, 0.72, jIdle(t, { pose: 'walk', turn: 0.5, glow: 1 }));
  bigTree(c, 540, 1760, 0.9);
  SCd(c, 420, 1780, 0.86, scIdle(t, { expr: 'squeeze', puff: 1, sweat: 1, handL: [-200, -330], handR: [200, -330], handLk: 'open', handRk: 'open' }));
  IDd(c, 700, 1790, 0.86, idIdle(t, { expr: 'dumb', look: [0, 1], handR: [40, -280], handL: [-170, -170], hold: (cc, aL, aR) => phone(cc, aR[0], aR[1] - 30, 1, 0, { screen: '#9fe3ff' }) }));
  c.restore();
  for (let i = 0; i < 3; i++) { const st = 35.2 + i * 0.5; boom(c, 'ТОП', 200 + i * 340, 640 + (i % 2) * 90, 64, '#c9b8ff', bump(t, st, st + 0.45) * 1.2, (i % 2 ? 0.12 : -0.12), null); }
}
function twoShotBg(c, t, z, sh, birds) {
  cam(c, 560, 1120, z, 0, sh, t);
  treeBg(c, t, { y1: 1000, moon: [160, 200] });
  if (birds) particles(c, t, 9, i => ({ t0: birds + i * 0.03, life: 1.6, x0: 300 + hash(i) * 500, vx: (hash(i * 3) - .5) * 900 }), (cc, p, age, u) => {
    const x = p.x0 + p.vx * age, y = 760 - 700 * age, fl = Math.sin(t * 26 + p.x0) * 22;
    poly(cc, [x - 40, y - fl, x - 8, y - 6, x, y + 10, x + 8, y - 6, x + 40, y - fl, x, y + 2], '#1d1326', 0); });
  bigTree(c, 560, 2500, 2.0);
}
function shSneeze(c, t) {
  const b = inv(ws(12, 3), T.choo - 0.05, t), after = t >= T.choo, sn = E.out(inv(T.choo, T.choo + 0.08, t)) * (1 - E.io(inv(T.choo + 0.25, T.choo + 0.7, t)));
  const react = E.out(inv(T.gromko - 0.1, T.gromko + 0.3, t)), no = Math.sin(t * 16) * 0.35 * react * (after ? 0 : 1);
  c.save(); twoShotBg(c, t, lerp(1.25, 1.35, inv(36.65, T.choo, t)), after ? 22 * (1 - inv(T.choo, T.choo + 0.6, t)) : 1, after ? T.choo : 0);
  SCd(c, 360, 1820, 1.25, scIdle(t, { expr: after ? 'shock' : 'scared', sweat: 1, look: [1, 0], turn: 0.5 * react + no, pale: .3 * react, mouthOpenFixed: after ? .7 : 0,
    handR: [lerp(150, 230, react), lerp(-170, -420, react)], handRk: 'open', lean: after ? -0.08 : 0 }));
  IDd(c, 760, 1830, 1.25, idIdle(t, after ? { expr: 'sneeze', mouth: 0.95, headTilt: 0.12 * sn, headDy: 30 * sn }
    : { expr: b > 0.55 ? 'sneeze' : 'dumb', lid: lerp(0.42, 0.75, b), mouth: b * 0.5, headTilt: -0.14 * b, headDy: -16 * b }));
  if (after) particles(c, t, 26, i => ({ t0: T.choo, life: 0.5, a: (hash(i) - .5) * 2.2 }), (cc, p, age, u) =>
    circle(cc, 760 + 1.25 * 0 + Math.sin(p.a) * 520 * u, 1830 - 1.25 * 330 + Math.cos(p.a) * 160 * u - 60 * u, 9 * (1 - u * .6), `rgba(200,235,255,${1 - u})`, 0));
  c.restore();
  boom(c, 'А...', 820, 620, 80, '#fff', bump(t, 37.75, 38.35) * 1.2, -0.1, null);
  boom(c, 'А-А...', 780, 600, 96, '#fff', bump(t, 38.3, T.choo) * 1.2, 0.08, null);
  boom(c, 'АПЧХИ!!!', W / 2, 640, 140, '#3ec1ff', inv(T.choo, T.choo + 0.12, t) * (1 - inv(T.choo + 0.5, T.choo + 0.6, t)), -0.08);
}
function shShut(c, t) {
  const cl = E.out(inv(39.72, 39.9, t)), punch = E.out(inv(T.zatk, T.zatk + 0.15, t));
  c.save(); twoShotBg(c, t, 1.35 + 0.1 * punch, 2 + 6 * punch * (1 - inv(T.zatk + 0.2, T.zatk + 0.5, t)), 0);
  IDd(c, 760, 1830, 1.25, idIdle(t, { expr: 'blank', mouth: 0, look: [-0.6, 0], lid: 0.2 }));
  const tgt = [(760 - 360) / 1.25 + 0, -340];
  SCd(c, 360, 1820, 1.25, scIdle(t, { expr: 'hiss', vein: 1, look: [1, 0], turn: 0.5, lean: 0.05 * cl, handR: [lerp(150, tgt[0], cl), lerp(-170, tgt[1], cl)], handRk: 'open' }));
  c.restore();
  sticker(c, '🔇', 860, 760, 90, INK, inv(39.85, 40.05, t), 0.12);
}
function shTurn(c, t) {
  const k = inv(40.95, 41.45, t);
  sunburst(c, W / 2, 860, t, '#1a1446', '#24195a', 16, 0.3);
  c.save(); cam(c, 540, 800, lerp(2.1, 2.25, k), 0, 2, t);
  JSd(c, 540, 1640, 0.85, { t, turn: lerp(0.9, 0, E.out(k)), glow: lerp(0.3, 1.2, k), look: [lerp(1, 0, k), 0] });
  c.restore();
  boom(c, 'ХРУСТЬ', 760, 420, 80, '#fff', inv(41.0, 41.15, t), 0.12, null);
}
function shPlan(c, t) {
  const fin = E.back(inv(T.brat14 - 0.2, T.brat14 + 0.2, t)), sink = E.io(inv(43.0, 45.4, t));
  const tw = (t > 45.15 && t < 45.25) || (t > 45.45 && t < 45.52);
  c.save(); twoShotBg(c, t, lerp(1.3, 1.42, inv(41.45, 46, t)), 1, 0);
  SCd(c, 360, 1820 + sink * 70, 1.25, scIdle(t, { expr: 'despair', look: [1, 0], turn: 0.4, lid: tw ? 0.85 : 0, handL: [-150, -170], handR: [150, -170] }));
  IDd(c, 760, 1830, 1.25, idIdle(t, { expr: 'serious', look: [-0.7, 0], turn: -0.3, headTilt: -0.04, handL: [lerp(-170, -60, fin), lerp(-170, -560, fin)], handLk: 'point', armLFront: true }));
  c.restore();
  sticker(c, '💡', 880, 640, 110, INK, inv(T.brat14, T.brat14 + 0.15, t), 0.1, '#ffe14d');
  bubble(c, 330, 680, 360, 300, [80, 140, 230], inv(43.2, 43.45, t) * (1 - inv(44.95, 45.05, t)), (cc) => {
    poly(cc, [-90, 20, 0, -70, 90, 20], '#e8364f', 6); rrect(cc, -70, 20, 140, 100, 8); fillStroke(cc, '#ffd36b', 6);
    rrect(cc, -20, 60, 40, 60, 6); fillStroke(cc, '#8a4a2a', 5);
    withT(cc, 0, 0, 1, -0.15, () => { rrect(cc, -110, -24, 220, 50, 10); fillStroke(cc, '#fff', 5); text(cc, 'НИКОГО НЕТ', 0, 2, 26, '#e0233a', { stroke: 0 }); });
  }, { rot: -0.05 });
  sticker(c, '*тишина*', W / 2, 1180, 48, '#8a8aa0', inv(T.endDoma + 0.2, T.endDoma + 0.35, t), -0.03);
}
// ------------------------------------------------------------------ 15. jump scare
function shJump(c, t) {
  const k = inv(T.i15, T.i15 + 0.6, t);
  sunburst(c, W / 2, 860, t, '#5a0010', '#8a0a1e', 18, 3);
  c.save(); cam(c, 540, 780, lerp(3.2, 2.8, E.out(k)), 0, 26 * (1 - k), t);
  JSd(c, 540, 1640, 0.95, { t, glow: 1.4 });
  c.restore();
  speedLines(c, W / 2, 800, t, { n: 70, r0: 520, col: 'rgba(255,255,255,0.8)', w: 10 });
  flash(c, pulse(t, T.i15, 0.15) * 0.8, '255,40,40');
  boom(c, '!!!', 830, 640, 140, '#ffe14d', inv(T.i15, T.i15 + 0.12, t), 0.12);
}
function trioBg(c, t, z, x = 560, y = 1240, r = 0) {
  cam(c, x, y, z, r, 1, t);
  treeBg(c, t, { y1: 1080, moon: [880, 230] });
  bigTree(c, 900, 1700, 0.75);
}
const J3 = [190, 1880, 0.92], F1X = 600, F2X = 880, TY = 1760;
function shFrozen(c, t) {
  c.save(); trioBg(c, t, lerp(0.98, 1.04, inv(46.66, 48.85, t)), 560, 1240, -0.03);
  const tr = Math.sin(t * 60) * 3;
  SCd(c, F1X + tr, TY, 0.86, scIdle(t, { expr: 'frozen', pale: 0.8, hairUp: 1, sweat: 1, look: [-1, -0.3], handL: [-130, -150], handR: [130, -150] }));
  IDd(c, F2X, TY + 10, 0.86, idIdle(t, { expr: 'dumb', look: [-1, -0.6] }));
  JSd(c, J3[0], J3[1], J3[2], jIdle(t, { turn: 0.4, glow: 1, look: [1, 0.5] }));
  c.restore();
  spinner(c, F1X + 10, 560, 70, t, inv(47.2, 47.45, t));
}
// ------------------------------------------------------------------ 16. "take a photo of us, landscape"
function shGive(c, t) {
  const go = E.io(inv(48.95, T.prot - 0.1, t)), back = E.io(inv(T.tel + 0.45, T.bratan - 0.1, t));
  const reach = E.out(inv(T.prot - 0.1, T.prot + 0.35, t)) * (1 - E.io(inv(T.tel + 0.3, T.tel + 0.5, t))), handed = t > T.tel + 0.3;
  c.save(); trioBg(c, t, lerp(1.0, 1.06, inv(48.85, T.bratan, t)), 520, 1240, 0);
  const x2 = lerp(F2X, 430, go) + (F2X - 430) * back, moving = (go > 0 && go < 1) || (back > 0 && back < 1);
  SCd(c, F1X + Math.sin(t * 60) * 3, TY, 0.86, scIdle(t, { expr: 'frozen', pale: 0.7, hairUp: 0.8, sweat: 1, look: [back > 0 ? lerp(-1, 1, back) : -1, -0.3] }));
  JSd(c, J3[0], J3[1], J3[2], jIdle(t, { turn: 0.5, glow: 0.8, look: [1, 1], headTilt: 0.12 * E.io(inv(T.prot + 0.2, T.prot + 0.8, t)),
    handL: handed ? [-60, -720] : [-250, -440], holdL: handed ? (cc, x, y) => phone(cc, x + 30, y - 70, 1.6, 0.1, { back: 1 }) : null }));
  IDd(c, x2, TY + 10 + (moving ? -Math.abs(Math.sin(t * 9)) * 10 : 0), 0.86, idIdle(t, { pose: moving ? 'walk' : 'stand', expr: 'dumb', look: [back > 0 ? 1 : -1, -0.4], turn: back > 0 ? 0.3 : -0.3,
    handL: reach > 0.02 ? [lerp(-170, -330, reach), lerp(-170, -470, reach)] : [-170, -170], armLFront: true,
    hold: !handed ? (cc, aL, aR) => phone(cc, aL[0], aL[1] - 40, 1, -0.1, { screen: '#9fe3ff' }) : null }));
  c.restore();
  sticker(c, 'СПОКОЙНО 😌', W / 2, 560, 64, '#2f6fe0', inv(ws(16, 3), ws(16, 3) + 0.2, t) * (1 - inv(T.tel, T.tel + 0.1, t)), -0.05);
}
function shPose(c, t) {
  const gest = E.io(inv(T.tolko, T.tolko + 0.3, t));
  c.save(); trioBg(c, t, lerp(1.06, 1.12, inv(T.bratan, 54.75, t)), 540, 1240, 0);
  JSd(c, J3[0], J3[1], J3[2], jIdle(t, { turn: 0.15, glow: 0.7, look: [0.5, 1], headTilt: 0.1 * inv(T.tolko, 54.5, t),
    handL: [-60, -720], holdL: (cc, x, y) => phone(cc, x + 30, y - 70, 1.6, 0.1, { back: 1 }) }));
  SCd(c, F1X + Math.sin(t * 60) * 2, TY, 0.86, scIdle(t, { expr: 'frozen', pale: 0.6, hairUp: 0.8, sweat: 1, look: [0, 0], mouthOpenFixed: 0 }));
  const shx = (F1X + 0.86 * 104 - (F2X - 60)) / 0.86, shy = -300;
  IDd(c, F2X - 60, TY + 10, 0.86, idIdle(t, gest < 0.5 ? { expr: 'happy', handL: [shx, shy], handLk: 'open', handR: [150, -560], handRk: 'peace' }
    : { expr: 'happy', handL: [-110, -330], handR: [110, -330], handLk: 'point', handRk: 'point' }));
  c.restore();
  if (t < T.tolko) cameraUI(c, t, 0.55);
  rotateIcon(c, 820, 600, inv(T.gor - 0.1, T.gor + 0.1, t), inv(T.gor + 0.1, T.gor + 0.6, t));
}
// ------------------------------------------------------------------ 17. "why so angry? did your girlfriend dump you?"
function shSympathy(c, t) {
  const tilt = E.io(inv(T.dob, T.i17 + 0.2, t)), gaze = E.io(inv(T.i17 - 0.3, T.end17 - 0.3, t));
  c.save(); trioBg(c, t, lerp(1.15, 1.32, inv(54.75, T.end17, t)), lerp(560, 600, inv(54.75, T.end17, t)), 1220, 0);
  JSd(c, J3[0], J3[1], J3[2], jIdle(t, { turn: 0.3, glow: 0.6, look: [1, 0.5], handL: [-60, -720], holdL: (cc, x, y) => phone(cc, x + 30, y - 70, 1.6, 0.1, { back: 1 }) }));
  SCd(c, F1X + Math.sin(t * 60) * 2, TY, 0.86, scIdle(t, { expr: 'annoyed', pale: 0.4, look: [lerp(-1, 1, gaze), 0], turn: lerp(-0.4, 0.45, gaze) }));
  IDd(c, F2X, TY + 10, 0.86, idIdle(t, { expr: 'sympathy', headTilt: 0.22 * tilt, look: [-1, -0.5], turn: -0.35, handR: [40, -330], handRk: 'open', blush: 0.6 }));
  c.restore();
  sticker(c, '💔', 470, 620, 120, '#e0233a', inv(T.dev, T.dev + 0.15, t), -0.1, '#ffd1e3');
}
function shStareEnd(c, t) {
  const k = inv(T.end17 + 0.1, 59.5, t);
  sunburst(c, W / 2, 860, t, '#1a1446', '#221858', 16, 0.15);
  c.save(); cam(c, 540, 790, lerp(2.4, 2.8, E.io(k)), 0, 0.5, t);
  JSd(c, 540, 1640, 0.95, { t, glow: 0.35 + 0.25 * Math.sin(t * 3), look: [0, 0] });
  c.restore();
  sticker(c, '*сверчки*', W / 2, 1180, 50, '#8a8aa0', inv(T.end17 + 0.15, T.end17 + 0.3, t), 0.03);
}
// ------------------------------------------------------------------ 18. the doomed stare + final card
function shFinal(c, t) {
  const k = inv(59.5, DATA.dur, t), fl = flashAmt(t, [61.3, 65.25]);
  c.save(); cam(c, lerp(560, 520, k), lerp(900, 860, k), lerp(1.0, 1.14, E.io(k)), 0, 0.6, t);
  treeBg(c, t, { y1: 1020, moon: [880, 220] });
  JSd(c, 860, 1170, 0.5, jIdle(t, { glow: 0.5, turn: -0.1 }));
  IDd(c, 690, 1180, 0.48, idIdle(t, { expr: 'happy', handR: [150, -620], handL: [-120, -560], handLk: 'peace',
    hold: (cc, aL, aR) => phone(cc, aR[0], aR[1] - 40, 1.2, 0, { back: 1, flash: fl }) }));
  fog(c, 1180, 120, 0.35, t);
  SCd(c, 330, 1330, 1.75, scIdle(t, { expr: 'doomed', look: [0.05, 0], blink: blinkAt(t, 4, 3.4) }));
  c.restore();
  flash(c, fl * 0.35);
  finalCard(c, t);
}

// ------------------------------------------------------------------ timeline
const SHOTS = [
  [0.00, shCamp, 'cut', 0], [2.35, shChill, 'zoom', 0.25], [T.poka + 0.2, shSil, 'flash', 0.2], [T.jas, shBoss, 'flash', 0.12],
  [T.vur, shScream, 'zoom', 0.2], [7.36, shWave, 'whip', 0.25], [9.6, shInside, 'whip', 0.25], [13.3, shGenius, 'zoom', 0.2],
  [14.54, shWindow, 'whip', 0.2], [17.57, shStare, 'zoom', 0.2], [T.end5 + 0.12, shFacepalm, 'cut', 0], [20.05, shHope, 'whip', 0.2],
  [21.73, shPhoneUp, 'zoom', 0.2], [22.65, shFlashes, 'cut', 0], [T.vsp, shPhoto, 'flash', 0.12], [25.9, shRunOut, 'whip', 0.25],
  [27.43, shChase, 'zoom', 0.2], [28.85, shBegi, 'whip', 0.2], [30.9, shStop, 'cut', 0], [31.94, shLaces, 'zoom', 0.2],
  [32.40, shWtf, 'whip', 0.2], [33.35, shHide, 'whip', 0.25], [35.05, shPass, 'cut', 0], [36.65, shSneeze, 'zoom', 0.2],
  [39.7, shShut, 'cut', 0], [40.95, shTurn, 'flash', 0.12], [41.45, shPlan, 'whip', 0.2], [46.0, shJump, 'cut', 0],
  [46.66, shFrozen, 'zoom', 0.2], [48.85, shGive, 'whip', 0.25], [51.79, shPose, 'zoom', 0.2], [54.75, shSympathy, 'whip', 0.2],
  [58.39, shStareEnd, 'zoom', 0.25], [59.5, shFinal, 'flash', 0.2],
];
function shotIndex(t) { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1][0]) i++; return i; }
function drawShot(c, i, t) { c.save(); SHOTS[i][1](c, t); c.restore(); }
const offCtx = OFF.map(o => o.getContext('2d'));
function transition(c, kind, u, iA, iB, t) {
  offCtx[0].setTransform(1, 0, 0, 1, 0, 0); offCtx[1].setTransform(1, 0, 0, 1, 0, 0);
  drawShot(offCtx[0], iA, t); drawShot(offCtx[1], iB, t);
  const A = OFF[0], B = OFF[1];
  if (kind === 'whip') {
    const e = E.io(u), dx = e * W;
    for (let k = 0; k < 6; k++) { const o = (k - 2.5) * 40 * Math.sin(u * Math.PI); c.globalAlpha = k === 0 ? 1 : 0.35; c.drawImage(A, -dx + o, 0); c.drawImage(B, W - dx + o, 0); }
    c.globalAlpha = 1;
    speedLines(c, W / 2, H / 2, t, { n: 30, r0: 200, col: `rgba(255,255,255,${0.5 * Math.sin(u * Math.PI)})` });
  } else if (kind === 'zoom') {
    if (u < 0.5) { const s = 1 + E.in(u * 2) * 2.5; c.drawImage(A, W / 2 - W * s / 2, H / 2 - H * s / 2, W * s, H * s); }
    else { const s = 0.6 + 0.4 * E.out((u - .5) * 2); c.fillStyle = '#fff'; c.fillRect(0, 0, W, H); c.drawImage(B, W / 2 - W * s / 2, H / 2 - H * s / 2, W * s, H * s); }
    flash(c, Math.sin(u * Math.PI) * 0.6);
    speedLines(c, W / 2, H / 2, t, { n: 50, r0: 250, col: `rgba(255,255,255,${0.7 * Math.sin(u * Math.PI)})` });
  } else if (kind === 'flash') {
    c.drawImage(u < 0.5 ? A : B, 0, 0); flash(c, 1 - Math.abs(u - 0.5) * 2);
  }
}
function renderTime(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const i = shotIndex(t), [a, , kind, d] = SHOTS[i], nxt = SHOTS[i + 1];
  if (d > 0 && i > 0 && t < a + d / 2) transition(ctx, kind, (t - (a - d / 2)) / d, i - 1, i, t);
  else if (nxt && nxt[3] > 0 && t >= nxt[0] - nxt[3] / 2) transition(ctx, nxt[2], (t - (nxt[0] - nxt[3] / 2)) / nxt[3], i, i + 1, t);
  else drawShot(ctx, i, t);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  vignette(ctx, 0.35);
  drawTitle(ctx, t);
  drawHUD(ctx, t);
  drawSubs(ctx, t);
  flash(ctx, inv(DATA.dur - 0.3, DATA.dur, t), '0,0,0');
}
function renderFrame(f) { renderTime(f / FPS); }
const TESTS = {};
