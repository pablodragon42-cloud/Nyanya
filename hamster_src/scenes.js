// Shot list + timeline. Times are seconds on the final (paused) voice track; word times come from DATA.
const DESK_Y = R.deskTop - 26;           // desk surface
const CAGE_HX = R.cageX + 120, CAGE_HY = DESK_Y - 26;  // hamster spot inside the cage
const GUY_X = 1080, GUY_Y = 1480;
const RUG = [1200, 1690];
const DOOR_SPOT = [300, 1600];
const HAM_BIG = 2.45;

function hamIdle(t, extra = {}) { return Object.assign({ t, blink: blinkAt(t, 1) }, extra); }
function guyIdle(t, extra = {}) { return Object.assign({ t, blink: blinkAt(t, 7, 2.7) }, extra); }

// ------------------------------------------------------------------ shared compositions
function deskScene(c, t, cam, o = {}) {
  c.save(); applyCam(c, cam);
  drawRoom(c, Object.assign({ t }, o.room || {}));
  if (o.guy) { drawChair(c, GUY_X, 1440, 1); withT(c, GUY_X, GUY_Y, 1, 0, () => drawGuy(c, o.guy)); }
  drawDesk(c, { t });
  drawDeskItems(c, Object.assign({ t }, o.items || {}));
  if (!o.noHeadphones) drawHeadphones(c, 1236, DESK_Y - 8, 0.55, 0.05);
  if (!o.noBag) drawFoodBag(c, 1330, DESK_Y, 0.75, Object.assign({ t }, o.bag || {}));
  drawCage(c, R.cageX, DESK_Y, { t, wheelSpin: o.wheelSpin || 0.4 });
  if (o.hamInCage) withT(c, CAGE_HX, CAGE_HY, o.hamScale || 0.45, 0, () => drawHamster(c, o.hamInCage));
  drawCageFront(c, R.cageX, DESK_Y, { doorGone: o.doorGone });
  if (o.extra) o.extra(c);
  c.restore();
}
function pip(c, t, cx, cy, r, appear, fn, col = '#fff') {
  if (appear <= 0) return;
  const s = E.back(clamp(appear));
  c.save(); c.translate(cx, cy); c.scale(s, s); c.rotate(-0.06);
  circle(c, 8, 12, r + 12, 'rgba(0,0,0,0.4)', 0);
  circle(c, 0, 0, r + 12, col, 0);
  c.beginPath(); c.arc(0, 0, r, 0, TAU); c.save(); c.clip();
  c.fillStyle = '#ffd6e6'; c.fillRect(-r, -r, r * 2, r * 2);
  sunburst(c, 0, 0, t, '#ffd6e6', '#ffc2d8', 14, 0.6);
  fn(c);
  c.restore();
  circle(c, 0, 0, r + 12, null, 7);
  c.restore();
}
function guyFace(c, o, s = 1, dy = 0) {   // guy head-and-shoulders inside a pip (centered)
  withT(c, 0, 430 * s + dy, s, 0, () => drawGuy(c, o));
}
function bubble(c, x, y, w, h, tail, appear, fn, o = {}) {
  if (appear <= 0) return;
  const s = E.back(clamp(appear));
  c.save(); c.translate(x, y); c.scale(s, s); c.rotate(o.rot || 0);
  c.beginPath(); rrect(c, -w / 2, -h / 2, w, h, 40);
  fillStroke(c, o.fill || '#fff', 8);
  c.beginPath(); c.moveTo(tail[0] - 30, h / 2 - 4); c.lineTo(tail[1], tail[2]); c.lineTo(tail[0] + 30, h / 2 - 4);
  c.closePath(); c.fillStyle = o.fill || '#fff'; c.fill(); c.lineWidth = 8; c.strokeStyle = INK; c.stroke();
  c.fillStyle = o.fill || '#fff'; c.fillRect(tail[0] - 26, h / 2 - 14, 52, 14);
  fn(c);
  c.restore();
}
function sticker(c, txt, x, y, px, col, appear, rot = -0.08, bg = '#fff') {
  if (appear <= 0) return;
  const s = E.back(clamp(appear));
  c.save(); c.translate(x, y); c.scale(s, s); c.rotate(rot);
  c.font = font(px); const w = c.measureText(txt).width + px * 0.9;
  rrect(c, -w / 2 + 8, -px * .75 + 10, w, px * 1.5, px * .4); c.fillStyle = 'rgba(0,0,0,.35)'; c.fill();
  rrect(c, -w / 2, -px * .75, w, px * 1.5, px * .4); fillStroke(c, bg, 7);
  text(c, txt, 0, 4, px, col, { stroke: 0 });
  c.restore();
}
function clockCard(c, t, lt, label) {
  sunburst(c, W / 2, 900, t, '#3b82f6', '#2563eb', 16, 1.5);
  const s = E.back(clamp(lt / 0.2));
  withT(c, W / 2, 860, s, Math.sin(lt * 20) * 0.08, () => {
    circle(c, 0, 0, 290, '#fff', 14); circle(c, 0, 0, 250, '#fff8e1', 0);
    for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; line(c, [Math.cos(a) * 210, Math.sin(a) * 210, Math.cos(a) * 240, Math.sin(a) * 240], 12); }
    const a1 = lt * 40, a2 = lt * 3.5;
    line(c, [0, 0, Math.sin(a1) * 200, -Math.cos(a1) * 200], 14, '#e0233a');
    line(c, [0, 0, Math.sin(a2) * 130, -Math.cos(a2) * 130], 20);
    circle(c, 0, 0, 20, INK, 0);
    poly(c, [-230, -250, -150, -330, -110, -270], '#e0233a', 8); poly(c, [230, -250, 150, -330, 110, -270], '#e0233a', 8);
  });
  withT(c, W / 2, 1300, E.back(clamp((lt - 0.08) / 0.2)), -0.05, () => {
    text(c, label, 0, 0, 104, '#ffe14d', { stroke: 22 });
  });
  speedLines(c, W / 2, 860, t, { n: 40, r0: 420, col: 'rgba(255,255,255,0.5)', w: 7 });
}

// ------------------------------------------------------------------ SCENE 1: purchase, cute, rat, demand
function shIntro(c, t) {      // 0 – 1.2: guy talks to camera at his desk
  const z = kf(t, [[0, 1.08], [1.3, 1.28, E.out]]);
  const cam = { x: 1180, y: 1120, z, r: kf(t, [[0, -0.03], [1.3, 0.01]]) };
  const point = inv(0.9, 1.15, t);
  deskScene(c, t, cam, {
    guy: guyIdle(t, { mouth: mouthAt('n', t), round: roundAt(t), expr: 'neutral', headTilt: Math.sin(t * 3) * 0.04,
      handR: [lerp(150, 290, point), lerp(-170, -400, point)], handL: [-150, -175] }),
    hamInCage: hamIdle(t, { eyes: 'cute', look: [-.6, 0] }),
  });
}
function shopBg(c, t) {
  c.fillStyle = vgrad(c, 0, H, [[0, '#5eead4'], [1, '#14b8a6']]); c.fillRect(0, 0, W, H);
  c.save(); c.globalAlpha = .18; for (let x = 0; x < W; x += 80) { c.fillStyle = '#fff'; c.fillRect(x, 0, 40, H); } c.restore();
  // shop sign
  withT(c, W / 2, 560, 1, -0.03, () => {
    rrect(c, -380, -80, 760, 160, 30); fillStroke(c, '#ff5c8a', 10);
    text(c, 'ЗООМАГАЗИН', 0, 4, 96, '#fff', { stroke: 14 });
  });
  // shelves with other pets
  for (const y of [1240, 1720]) { rrect(c, -20, y, W + 40, 50, 10); fillStroke(c, '#a86b42', 8); }
  // fish bowl + parrot cage (simple)
  withT(c, 140, 1240, 1, 0, () => {
    circle(c, 0, -110, 110, 'rgba(147,210,255,0.6)', 8);
    withT(c, Math.sin(t * 2) * 30, -100, 1, 0, () => { ellipse(c, 0, 0, 36, 24, '#ff9f1c', 6); poly(c, [30, 0, 64, -22, 64, 22], '#ff9f1c', 6); circle(c, -14, -4, 5, INK, 0); });
  });
  withT(c, 950, 1240, 1, 0, () => {
    c.beginPath(); c.moveTo(-90, 0); c.lineTo(-90, -170); c.quadraticCurveTo(0, -300, 90, -170); c.lineTo(90, 0); fillStroke(c, null, 7);
    for (let i = -70; i <= 70; i += 28) line(c, [i, 0, i, -190 - (70 - Math.abs(i)) * .6], 4, '#c9a24a');
    ellipse(c, 0, -90, 34, 46, '#22c55e', 6); circle(c, -8, -110, 6, INK, 0); poly(c, [-30, -100, -56, -92, -30, -86], '#ffd23f', 4);
  });
}
function shShop(c, t) {         // 1.2 – 2.95: flashback, pet shop, price tag slam
  const lt = t - 1.2;
  const cam = 1 + lt * 0.05;
  c.save(); c.translate(W / 2, H / 2); c.scale(cam, cam); c.translate(-W / 2, -H / 2);
  shopBg(c, t);
  // hamster on the shelf
  const hop = Math.abs(Math.sin(lt * 6)) * (lt < 0.6 ? 20 : 0);
  withT(c, W / 2 - 40, 1240 - hop, 2.3, 0, () => drawHamster(c, hamIdle(t, { eyes: 'cute', cheeks: 0.25 + 0.15 * Math.sin(t * 12), pawL: [-30, -96], pawR: [30, -96],
    hold: (cc, pL, pR) => propSeed(cc, 0, -100, 0.9, 0.2) })));
  // price tag hanging, then slamming in on "500"
  const slam = inv(WS(5) - 0.05, WS(5) + 0.15, t);
  const tx = lerp(W / 2 + 230, W / 2, E.out(slam)), ty = lerp(980, 900, E.out(slam)), ts = lerp(0.9, 1.7, E.back(slam));
  withT(c, tx, ty, ts, lerp(0.25 + Math.sin(t * 4) * 0.1, -0.12, E.out(slam)), () => {
    line(c, [-60, -90, -40, -40], 4);
    poly(c, [-90, -40, 140, -40, 190, 30, 140, 100, -90, 100], '#ffe14d', 9);
    circle(c, -60, 30, 12, '#14b8a6', 6);
    text(c, '500 ₸', 55, 32, 70, '#e0233a', { stroke: 0 });
  });
  if (slam > 0) { flash(c, pulse(t, WS(5) + 0.1, 0.18) * 0.7); particles(c, t, 14, i => ({ t0: WS(5) + 0.1, life: 0.6, a: i / 14 * TAU }), (cc, p, age, u) => star4(cc, W / 2 + Math.cos(p.a) * (160 + 500 * E.out(u)), 900 + Math.sin(p.a) * (120 + 400 * E.out(u)), 30 * (1 - u), '#fff', u * 4)); }
  c.restore();
  sticker(c, 'ВСЕГО!', W / 2 + 280, 720, 54, '#e0233a', inv(WS(6), WS(6) + 0.2, t), 0.15);
}
function shCute(c, t) {        // 2.95 – 5.12: "Думал, будет милый питомец"
  const lt = t - 2.95;
  sunburst(c, W / 2, 900, t, '#ffd1e3', '#ffbcd6', 20, 0.25);
  // bokeh hearts
  particles(c, t, 26, i => ({ t0: 2.6 + hash(i) * 2.4, life: 2.2, x: hash(i + 3) * W, s: 30 + hash(i + 7) * 50 }), (cc, p, age, u) => {
    cc.save(); cc.globalAlpha = Math.sin(u * Math.PI) * .9; heart(cc, p.x + Math.sin(age * 3 + p.x) * 30, 1800 - age * 700, p.s, '#ff6fa3'); cc.restore();
  });
  // heart frame
  const fs = E.back(clamp(lt / 0.3));
  withT(c, W / 2, 940, fs * (1 + Math.sin(t * 5) * 0.02), 0, () => { heart(c, 0, 80, 420, '#fff', 12); heart(c, 0, 60, 380, '#ff9cc2', 0); });
  const sway = Math.sin(t * 3) * 0.06;
  withT(c, W / 2, 1230, 2.6 * fs, sway, () => drawHamster(c, hamIdle(t, { eyes: 'cute', blush: 1, cheeks: 0.15, pawL: [-26, -100], pawR: [26, -100], earWig: 0.15 })));
  for (let i = 0; i < 6; i++) star4(c, W / 2 + Math.cos(i + t * 1.5) * 360, 900 + Math.sin(i * 2 + t * 1.5) * 380, 26 + 12 * Math.sin(t * 6 + i), '#fff', t);
  sticker(c, 'МИЛАШКА ♥', W / 2, 420, 66, '#ff3d7f', inv(3.7, 3.95, t), 0.06);
}
function shRat(c, t) {         // 5.12 – 6.66: record scratch, "маленькая крыса"
  const lt = t - 5.12, insult = WS(14);
  // dark version of the same framing
  c.fillStyle = vgrad(c, 0, H, [[0, '#1e1b3a'], [1, '#3a1d4a']]); c.fillRect(0, 0, W, H);
  const z = kf(t, [[5.12, 1], [6.6, 1.25, E.io]]);
  c.save(); c.translate(W / 2, 1100); c.scale(z, z); c.translate(-W / 2, -1100);
  glow(c, W / 2, 900, 700, 'rgba(255,40,80,0.25)');
  const twitch = t > insult ? Math.sin(t * 70) * 0.03 : 0;
  withT(c, W / 2, 1230, 2.6, twitch, () => drawHamster(c, {
    t, eyes: t < 5.5 ? 'cute' : 'narrow', look: [kf(t, [[5.3, 0], [5.9, .9]]), 0.2], brow: kf(t, [[5.6, 0], [5.9, 1]]),
    pawL: [-26, -100], pawR: [26, -100], cheeks: 0.15 * (1 - inv(5.2, 5.5, t)), twitch: t > insult, frown: t > insult ? 1 : 0,
  }));
  c.restore();
  // "?!" offended
  sticker(c, '?!', 820, 640, 120, '#e0233a', inv(insult, insult + 0.15, t), 0.2);
  if (lt < 0.25) { // scratch glitch
    c.save(); c.globalAlpha = 0.6 * (1 - lt / 0.25);
    for (let i = 0; i < 10; i++) { c.fillStyle = i % 2 ? '#ff3d7f' : '#3ec1ff'; c.fillRect(0, hash(i + Math.floor(t * 60)) * H, W, 20 + hash(i * 3) * 60); }
    c.restore();
  }
  vignette(c, 0.7);
}
function shHour(c, t) { clockCard(c, t, t - 6.62, 'ЧЕРЕЗ 1 ЧАС'); }
function shDemand(c, t) {      // 7.32 – 9.45: stands up and demands an apartment
  const lt = t - 7.32;
  const cam = { x: CAGE_HX + 10, y: 1120, z: kf(t, [[7.32, 2.6], [9.4, 2.85]]) };
  const talk = t > 7.4 && t < 9.2 ? Math.abs(Math.sin(t * 13)) * 0.7 : 0;
  deskScene(c, t, cam, {
    noBag: false,
    hamInCage: hamIdle(t, { stand: 1, sq: 1.13, eyes: 'narrow', brow: 1, mouth: talk, yell: 1,
      pawL: [-70, -170 + Math.sin(t * 8) * 10], pawR: [96, -150],
      hold: (cc, pL, pR) => { withT(cc, pR[0] + 75, pR[1] - 5, 1, 0.2, () => { rrect(cc, -50, -70, 100, 120, 6); fillStroke(cc, '#fff', 5); for (let i = 0; i < 4; i++) line(cc, [-34, -48 + i * 26, 34, -48 + i * 26], 4, '#3b82f6'); rrect(cc, -20, -22, 40, 30, 2); fillStroke(cc, null, 4); }); } }),
  });
  bubble(c, W / 2, 470, 900, 300, [W / 2 - 40, 60, 220], inv(7.4, 7.6, t), cc => {
    text(cc, 'ХОЧУ ОТДЕЛЬНУЮ', 0, -60, 74, INK, { stroke: 0 });
    text(cc, 'КВАРТИРУ!', 0, 20, 92, '#e0233a', { stroke: 0 });
    text(cc, 'С РЕМОНТОМ И БАЛКОНОМ', 0, 96, 40, '#555', { stroke: 0 });
  }, { rot: Math.sin(t * 20) * 0.01 });
  pip(c, t, 210, 1640, 170, inv(8.55, 8.75, t), cc => guyFace(cc, guyIdle(t, { expr: 'shock', mouthOpenFixed: 0.8, sweat: 1 }), 0.9, 0));
}

// ------------------------------------------------------------------ SCENE 2: door kick, food, headphones, invoice
function shRampage(c, t) {     // 9.45 – 11.95: kicks the cage door, devours the food bag
  const kick = 9.52, jump0 = 9.8, dive = 10.22, pop = 11.32;
  const camx = kf(t, [[9.45, CAGE_HX], [9.9, CAGE_HX], [10.3, 1360, E.io]]);
  const [sx, sy] = shake(t, pulse(t, kick, 0.3) * 30 + (t > dive && t < pop ? 6 : 0), 25);
  const cam = { x: camx + sx, y: 1130 + sy, z: kf(t, [[9.45, 2.6], [10.3, 2.75], [11.3, 2.75], [11.5, 3.1, E.back]]) };
  // hamster position: in cage -> arc -> into bag -> pops out
  let hx = CAGE_HX, hy = CAGE_HY, hs = 0.45, rot = 0, vis = true;
  if (t > jump0) {
    const u = inv(jump0, dive, t);
    hx = lerp(CAGE_HX, 1330, u); hy = lerp(CAGE_HY, DESK_Y - 210, u) - Math.sin(u * Math.PI) * 140; rot = -u * 2.6;
  }
  if (t > dive) vis = false;
  if (t > pop) { vis = true; const u = inv(pop, pop + 0.25, t); hx = 1330; hy = DESK_Y - 4 - Math.sin(u * Math.PI) * 60; rot = 0; }
  const empty = kf(t, [[10.5, 0], [11.25, 1, E.in2]]);
  deskScene(c, t, cam, {
    doorGone: t > kick, bag: { empty, shake: t > dive && t < pop ? 1 : 0 },
    hamInCage: t < jump0 ? hamIdle(t, { stand: 1, sq: 1.1, eyes: 'narrow', brow: 1, pawL: [-60, -150], pawR: [70, -150], mouth: t > 9.47 && t < 9.6 ? 0.8 : 0, yell: 1 }) : null,
    extra: cc => {
      if (vis && t >= jump0) withT(cc, hx, hy, hs, rot, () => drawHamster(cc, hamIdle(t, {
        eyes: t > pop ? 'closed' : 'narrow', brow: t > pop ? 0 : 1, cheeks: t > pop ? 1 : 0, belly: t > pop ? 1 : 0,
        mouth: t > 11.6 && t < 11.85 ? 0.6 : 0, stand: t < dive })));
      // food crumbs spewing from the bag
      if (t > dive && t < pop + 0.2) {
        particles(cc, t, 60, i => ({ t0: dive + hash(i) * (pop - dive), life: 0.7, vx: (hash(i + 1) - .5) * 600, vy: -300 - hash(i + 2) * 500 }), (c2, p, age, u) => {
          const x = 1330 + p.vx * age, y = DESK_Y - 150 + p.vy * age + 900 * age * age;
          if (hash(p.vx) > .5) propSeed(c2, x, y, 0.35, age * 10); else circle(c2, x, y, 7, '#f2b84b', 3);
        });
      }
      if (t > 11.6 && t < 12.0) text(cc, 'ИК!', 1400, DESK_Y - 160, 40, '#fff', { stroke: 8 });
    },
  });
  // cage door flying into the lens
  if (t > kick && t < kick + 0.55) {
    const u = inv(kick, kick + 0.55, t);
    withT(c, lerp(540, 700, u), lerp(1000, 1100, u), lerp(2.5, 14, E.in2(u)), u * 5, () => cageDoor(c, 0, 0, 1, 0));
    flash(c, pulse(t, kick + 0.45, 0.12));
  }
  if (t > kick && t < kick + 0.4) text(c, 'БАХ!', 300, 700, 130, '#ffe14d', { stroke: 22 });
  if (t > 10.3 && t < 11.3) text(c, 'ХРУМ', 760 + Math.sin(t * 30) * 10, 620, 90, '#fff', { stroke: 18 });
}
function shPhones(c, t) {      // 11.95 – 13.62: eats the headphones
  const grab = 12.25, gone = 13.2;
  const [sx, sy] = shake(t, t > grab && t < gone ? 5 : 0, 30);
  const cam = { x: 1262 + sx, y: 1150 + sy, z: kf(t, [[11.95, 3.0], [13.6, 3.35]]) };
  const hx = kf(t, [[11.95, 1330], [12.2, 1290]]);
  const chew = t > grab && t < gone + 0.2 ? Math.abs(Math.sin(t * 22)) : 0;
  const eaten = inv(grab + 0.1, gone, t);
  deskScene(c, t, cam, {
    noHeadphones: true, bag: { empty: 1 }, doorGone: 1,
    extra: cc => {
      withT(cc, hx, DESK_Y - 4, 0.45, 0, () => drawHamster(cc, hamIdle(t, {
        eyes: 'narrow', brow: 1, cheeks: 0.6 + chew * 0.3, belly: 1, mouth: chew * 0.8,
        pawL: [-30, -112], pawR: [30, -112],
        hold: (c2) => { if (eaten < 1) drawHeadphones(c2, 0, -96 + 8, 0.9 * (1 - eaten * 0.9), Math.sin(t * 20) * 0.2); },
      })));
      if (t < grab) drawHeadphones(cc, 1236, DESK_Y - 8, 0.55, 0.05);
      // sparks + red bits
      if (t > grab && t < gone + 0.3) particles(cc, t, 36, i => ({ t0: grab + hash(i) * (gone - grab), life: 0.5, a: hash(i + 4) * TAU, sp: 200 + hash(i + 2) * 300 }), (c2, p, age, u) => {
        const x = hx + Math.cos(p.a) * p.sp * age, y = DESK_Y - 60 + Math.sin(p.a) * p.sp * age + 400 * age * age;
        if (hash(p.a) > .6) star4(c2, x, y, 14 * (1 - u), '#ffe14d', age * 10); else rrect(c2, x, y, 8, 8, 2), fillStroke(c2, GUY.phone, 2);
      });
    },
  });
  if (t > grab && t < gone) text(c, 'ЧАВК', 300 + Math.sin(t * 25) * 8, 700, 92, '#fff', { stroke: 18 });
  pip(c, t, 820, 560, 190, inv(12.4, 12.6, t), cc => guyFace(cc, guyIdle(t, { expr: 'shock', mouthOpenFixed: 0.9, handL: [-120, -400], handR: [120, -400] }), 0.9, 0));
}
function shSuka(c, t) {        // 13.62 – 15.0: "А потом, сука,"
  const s = WS(30);
  const z = t < s ? kf(t, [[13.62, 1.6], [14.6, 1.75]]) : kf(t, [[s, 1.75], [s + 0.12, 2.7, E.out]]);
  const [sx, sy] = shake(t, t > s ? 14 * (1 - inv(s, s + 0.6, t)) + 3 : 0, 30);
  deskScene(c, t, { x: GUY_X + sx, y: 1080 + sy, z }, {
    noBag: true, noHeadphones: true, doorGone: 1, items: { noCans: false },
    guy: guyIdle(t, { mouth: mouthAt('n', t), round: roundAt(t), expr: t > s - 0.05 ? 'angry' : 'dead', vein: t > s ? E.back(inv(s, s + 0.2, t)) : 0,
      handL: [-150, -175], handR: [150, -175] }),
  });
  if (t > s) { halftoneTint(c, '#ff3b3b', 0.35 * (1 - inv(s, s + 0.5, t)) + 0.1); speedLines(c, W / 2, 900, t, { n: 50, r0: 520, col: 'rgba(255,255,255,0.6)' }); }
}
function receiptLines() {
  return [['СЧЁТ №1', '', 1], ['Аренда клетки', '50 000 ₸'], ['Колесо (б/у)', '7 000 ₸'], ['Корм (съеден)', '12 000 ₸'],
    ['Наушники (вкусные)', '0 ₸'], ['Моральный ущерб', '99 999 ₸'], ['ИТОГО:', 'ВСЯ ТВОЯ ЗП', 2]];
}
function shInvoice(c, t) {     // 15.0 – 17.35: invoice for renting the cage
  const st = WS(36);
  c.fillStyle = '#3b2f66'; c.fillRect(0, 0, W, H);
  const z = kf(t, [[15.0, 2.9], [17.3, 3.1]]);
  deskScene(c, t, { x: 1400, y: 1210, z }, {
    noHeadphones: true, bag: { empty: 1 }, doorGone: 1,
    extra: cc => {
      // tiny calculator
      withT(cc, 1150, DESK_Y, 1, 0, () => { rrect(cc, -40, -70, 80, 70, 8); fillStroke(cc, '#4b5563', 5); rrect(cc, -30, -62, 60, 20, 3); fillStroke(cc, '#a3e635', 3); for (let i = 0; i < 6; i++) { rrect(cc, -28 + (i % 3) * 20, -36 + Math.floor(i / 3) * 16, 14, 11, 2); fillStroke(cc, '#e5e7eb', 2); } });
      withT(cc, 1290, DESK_Y - 4, 0.45, 0, () => drawHamster(cc, hamIdle(t, {
        eyes: 'normal', brow: 1, glasses: 1, belly: 0.6, smirk: 1, mouth: 0,
        pawL: [-80, -120 + Math.abs(Math.sin(t * 16)) * 20], pawR: [40, -150] })));
    },
  });
  // the receipt unrolling toward the camera
  const u = E.out(inv(15.1, 16.3, t));
  const len = 1500 * u;
  c.save(); c.translate(700, 300); c.rotate(-0.05);
  c.beginPath(); c.moveTo(-330, 0); c.lineTo(330, 0); c.lineTo(330, len);
  for (let x = 330; x >= -330; x -= 30) c.lineTo(x, len + ((x / 30) % 2 ? 18 : 0));
  c.closePath(); c.fillStyle = '#fffdf5'; c.fill(); c.lineWidth = 8; c.strokeStyle = INK; c.stroke();
  c.save(); c.clip();
  receiptLines().forEach(([a, b, kind], i) => {
    const y = 100 + i * 190;
    if (y > len) return;
    if (kind === 1) { text(c, a, 0, y, 76, INK, { stroke: 0 }); line(c, [-280, y + 60, 280, y + 60], 4, '#999'); return; }
    if (kind === 2) { text(c, a, -280, y - 20, 50, INK, { stroke: 0, align: 'left' }); text(c, b, 0, y + 50, 64, '#e0233a', { stroke: 0 }); return; }
    text(c, a, -280, y, 40, '#333', { stroke: 0, align: 'left', fam: 'Mont' }); text(c, b, 280, y, 42, INK, { stroke: 0, align: 'right' });
    c.save(); c.setLineDash([6, 10]); line(c, [-280, y + 40, 280, y + 40], 3, '#bbb'); c.restore();
  });
  c.restore();
  c.restore();
  // stamp
  const sa = inv(st, st + 0.12, t);
  if (sa > 0) {
    const sc = lerp(3, 1, E.out(sa));
    withT(c, 690, 1150, sc, -0.25, () => {
      c.globalAlpha = Math.min(1, sa * 2);
      rrect(c, -330, -90, 660, 180, 20); c.lineWidth = 14; c.strokeStyle = '#e0233a'; c.stroke();
      text(c, 'ОПЛАТИТЬ', 0, -20, 96, '#e0233a', { stroke: 0 }); text(c, 'СРОЧНО!', 0, 56, 56, '#e0233a', { stroke: 0 });
    });
    flash(c, pulse(t, st + 0.1, 0.12) * 0.5);
  }
}

// ------------------------------------------------------------------ SCENE 3: return to the pet shop, growth, blocked exit
function roomWide(c, t, cam, o, extra) {
  c.save(); applyCam(c, cam);
  drawRoom(c, Object.assign({ t }, o.room || {}));
  if (!o.noDesk) {
    drawDesk(c, { t }); drawDeskItems(c, Object.assign({ t }, o.items || {}));
    drawFoodBag(c, 1330, DESK_Y, 0.75, { empty: 1 });
    drawCage(c, R.cageX, DESK_Y, { t }); drawCageFront(c, R.cageX, DESK_Y, { doorGone: 1 });
  }
  if (extra) extra(c);
  c.restore();
}
function boxProp(c, x, y, s, label = 'ВОЗВРАТ') {
  withT(c, x, y, s, 0, () => {
    poly(c, [-110, -150, 110, -150, 100, 0, -100, 0], '#d4a373', 7);
    poly(c, [-110, -150, -150, -190, 70, -190, 110, -150], '#e9c08f', 6);
    text(c, label, 0, -78, 34, INK, { stroke: 0 }); text(c, '↩ ЗООМАГАЗИН', 0, -36, 20, '#8b5a2b', { stroke: 0 });
  });
}
function shReturn(c, t) {      // 17.35 – 19.92: sneaking up with a return box
  const lt = t - 17.35;
  const gx = kf(t, [[17.35, 380], [19.9, 860]]);
  const bob = Math.abs(Math.sin(lt * 7)) * 18;
  const cam = { x: kf(t, [[17.35, 800], [19.9, 1000]]), y: 1200, z: 0.82 };
  roomWide(c, t, cam, {}, cc => {
    withT(cc, RUG[0], RUG[1], 0.45, 0, () => drawHamster(cc, hamIdle(t, { eyes: 'closed', cheeks: 0.4 + 0.2 * Math.sin(t * 14), belly: 0.7,
      pawL: [-26, -100], pawR: [26, -100], hold: c2 => propSeed(c2, 0, -104, 0.8, 0.3) })));
    withT(cc, gx, 1720 - bob, 1.05, Math.sin(lt * 7) * 0.04, () => drawGuy(cc, guyIdle(t, { expr: 'determined', look: [1, 0.3],
      handL: [70, -250], handR: [230, -250], hold: c2 => boxProp(c2, 150, -180, 0.9) })));
  });
  bubble(c, 300, 560, 400, 300, [-40, -150, 230], inv(17.9, 18.1, t), cc => {
    withT(cc, 0, -10, 1, 0, () => { rrect(cc, -150, -60, 300, 150, 10); fillStroke(cc, '#5eead4', 6); rrect(cc, -160, -110, 320, 60, 12); fillStroke(cc, '#ff5c8a', 6); text(cc, 'ЗООМАГАЗИН', 0, -79, 30, '#fff', { stroke: 6 }); rrect(cc, -40, 10, 80, 80, 6); fillStroke(cc, '#a86b42', 6); });
    text(cc, 'ВЕРНУ ЗА 500 ₸', 0, 112, 30, INK, { stroke: 0 });
  });
}
// flying furniture during the growth
function flyers(c, t, t0) {
  const items = [
    [drawChair, 1080, 1440, -900, -1300, 2.2, 1], [drawLamp, 1450, DESK_Y, 700, -1500, -3, 1], [drawPlant, 1830, 1440, 900, -1100, 2.5, 1],
    [(cc, x, y, s, r) => drawBook(cc, x, y, s, r, '#3b82f6'), 1000, 1150, -600, -1400, 6, 1], [(cc, x, y, s, r) => drawBook(cc, x, y, s, r, '#22c55e'), 1500, 1100, 800, -1200, -5, 1],
    [(cc, x, y, s, r) => drawBook(cc, x, y, s, r, '#f97316'), 1250, 1000, -300, -1700, 7, 1],
    [(cc, x, y, s, r) => drawMonitor(cc, x, y, t, { screen: 'error' }), 840, DESK_Y, -1100, -900, -2, 1],
  ];
  items.unshift([(cc, x, y, s, r) => {
    cc.save(); cc.translate(x, y); cc.rotate(r); cc.translate(-1200, -1400);
    drawDesk(cc, { t }); drawDeskItems(cc, { t, noMonitor: 1 }); drawFoodBag(cc, 1330, DESK_Y, 0.75, { empty: 1 });
    drawCage(cc, R.cageX, DESK_Y, { t }); drawCageFront(cc, R.cageX, DESK_Y, { doorGone: 1 }); cc.restore();
  }, 1200, 1400, 1500, -700, 1.4, 1]);
  const a = t - t0;
  if (a < 0) return;
  items.forEach(([fn, x, y, vx, vy, spin, s], i) => {
    const d = a - i * 0.08; if (d < 0) { return; }
    fn(c, x + vx * d, y + vy * d + 1300 * d * d, s, spin * d);
  });
}
function shGrow(c, t) {        // 19.92 – 22.8: "Но эта мразь выросла до размеров холодильника"
  const mr = WS(45), g0 = 20.98, g1 = 22.65;
  const g = kf(t, [[g0, 0], [g1, 1, E.sio]]);
  const wob = t > g0 && t < g1 + .3 ? Math.sin(t * 40) * 0.04 * (1 - inv(g1, g1 + .3, t)) : 0;
  const hs = lerp(0.45, HAM_BIG, g) * (1 + wob);
  const amp = t < g0 ? (t > mr ? 6 : 2) : lerp(8, 34, g);
  const [sx, sy] = shake(t, amp, 22);
  let z, cy;
  if (t < g0) { z = t < mr ? kf(t, [[19.92, 2.6], [mr, 3.0]]) : kf(t, [[mr, 3.0], [mr + 0.1, 3.7, E.out]]); cy = RUG[1] - 60; }
  else {
    const wide = E.io(inv(g1 - 0.3, g1 + 0.12, t));
    z = lerp(1.66 / hs * (1 + 0.7 * g), 0.56, wide); cy = lerp(RUG[1] - 125 * hs, 1150, wide);
  }
  const hide = t > 21.4;  // desk + chair blown away
  roomWide(c, t, { x: lerp(RUG[0], 1250, E.io(inv(g1 - 0.3, g1 + 0.12, t))) + sx, y: cy + sy, z, r: wob * 0.5 },
    { noDesk: hide, room: { posterFall: E.in2(inv(21.6, 22.6, t)), noPlant: g > 0.3, signFall: 0 } }, cc => {
      if (hide) flyers(cc, t, 21.4);
      withT(cc, RUG[0], RUG[1], hs, 0, () => drawHamster(cc, {
        t, eyes: t > 20.15 ? 'glow' : 'narrow', glow: inv(20.15, 20.5, t), brow: 1,
        mouth: g > 0.1 && g < 0.95 ? 0.5 + 0.3 * Math.sin(t * 20) : 0, yell: 1, belly: 0.5,
        pawL: g > 0.1 ? [-110, -170] : [-30, -100], pawR: g > 0.1 ? [110, -170] : [30, -100] }));
      if (g > 0.95) { // size label next to the fridge
        withT(cc, 1700, 720, 1.2, 0.05, () => { rrect(cc, -230, -46, 460, 92, 20); fillStroke(cc, '#fff', 7); text(cc, '= ХОЛОДИЛЬНИК', 0, 3, 48, INK, { stroke: 0 }); });
      }
    });
  if (t > g0 && t < g1) { speedLines(c, W / 2, 1000, t, { n: 60, r0: 450, col: 'rgba(255,255,255,0.55)' }); }
  if (t > mr && t < g0) halftoneTint(c, '#ff2a3d', 0.25);
}
function shBlock(c, t) {       // 22.8 – 24.45: lands in front of the exit
  const j0 = 22.82, land = 23.22;
  const u = inv(j0, land, t);
  const hx = lerp(RUG[0], DOOR_SPOT[0], E.sio(u)), hy = lerp(RUG[1], DOOR_SPOT[1], u) - Math.sin(u * Math.PI) * 500;
  const sq = t < land ? 1.08 : 1 - 0.18 * pulse(t, land, 0.3) * Math.cos((t - land) * 30);
  const [sx, sy] = shake(t, pulse(t, land, 0.6) * 40, 20);
  const cam = { x: kf(t, [[22.8, 900], [23.2, 640, E.io]]) + sx, y: 1240 + sy, z: kf(t, [[22.8, 0.56], [23.3, 0.62], [24.4, 0.68]]) };
  roomWide(c, t, cam, { noDesk: true, room: { posterFall: 1, noPlant: true, signFall: E.in2(inv(23.45, 24.0, t)) } }, cc => {
    withT(cc, hx, hy, HAM_BIG * 1.02, 0, () => drawHamster(cc, {
      t, sq, eyes: t > land ? 'narrow' : 'glow', glow: t > land ? 0 : 1, brow: 1, smirk: t > land + 0.3 ? 1 : 0, belly: 0.5,
      pawL: t > land + 0.25 ? [30, -112] : [-110, -180], pawR: t > land + 0.25 ? [-30, -102] : [110, -180] }));
    // dust
    particles(cc, t, 18, i => ({ t0: land, life: 0.9, a: (i / 18) * Math.PI, sp: 300 + hash(i) * 300 }), (c2, p, age, uu) => {
      c2.save(); c2.globalAlpha = 1 - uu; circle(c2, DOOR_SPOT[0] + Math.cos(p.a) * p.sp * age * 2, DOOR_SPOT[1] - Math.sin(p.a) * p.sp * age * .4, 50 + 90 * uu, '#e8dcc8', 0); c2.restore();
    });
    // the guy in the foreground with the tiny box
    withT(cc, 1250, 2050, 1.15, 0, () => drawGuy(cc, guyIdle(t, { expr: 'scared', sweat: 1, look: [-1, 0], handL: [70, -250], handR: [210, -250],
      hold: c2 => boxProp(c2, 140, -180, 0.9) })));
  });
  if (t > land && t < land + 0.5) text(c, 'БУМ!', 540, 520, 150, '#ffe14d', { stroke: 24 });
}

// ------------------------------------------------------------------ SCENE 4: portal, demon, "Я тут главный"
function hellLight(c, a) { halftoneTint(c, '#ff3355', a * 0.45); }
function shPortal(c, t) {      // 24.45 – 26.95: snap, portal opens
  const snap = 24.92, op = 25.3;
  const open = E.out(inv(op, 26.4, t));
  const camx = kf(t, [[24.45, 420], [25.2, 420], [25.6, 1000, E.io]]);
  const [sx, sy] = shake(t, open * 10 + pulse(t, op, .4) * 25, 20);
  const cam = { x: camx + sx, y: kf(t, [[24.45, 1150], [25.6, 1350]]) + sy, z: kf(t, [[24.45, 0.9], [25.2, 1.0], [25.6, 0.62, E.io], [26.9, 0.7]]) };
  roomWide(c, t, cam, { noDesk: true, room: { posterFall: 1, noPlant: true, signFall: 1, noRug: open > 0.05 } }, cc => {
    drawPortal(cc, RUG[0], RUG[1], 520, t, 'back', open);
    drawPortal(cc, RUG[0], RUG[1], 520, t, 'front', open);
    withT(cc, DOOR_SPOT[0], DOOR_SPOT[1], HAM_BIG, 0, () => drawHamster(cc, {
      t, eyes: 'narrow', brow: 1, smirk: 1, belly: 0.5, pawL: [30, -112], pawR: t > 24.6 ? [120, -230] : [-30, -102],
      hold: (c2, pL, pR) => { if (t > snap && t < snap + .3) { for (let i = 0; i < 6; i++) { const a = i / 6 * TAU; line(c2, [pR[0] + Math.cos(a) * 30, pR[1] + Math.sin(a) * 30, pR[0] + Math.cos(a) * 60, pR[1] + Math.sin(a) * 60], 6, '#ffe14d'); } } } }));
    withT(cc, 1650, 1950, 1.05, 0, () => drawGuy(cc, guyIdle(t, { expr: 'scared', sweat: 1, hairBlow: open, look: [-1, 0], handL: [-140, -440], handR: [140, -440] })));
  });
  hellLight(c, open);
  if (t > snap && t < snap + .35) text(c, 'ЩЁЛК', 760, 700, 90, '#fff', { stroke: 18 });
}
function demonAt(c, t, x, y, s, o, clipY) {
  c.save();
  if (clipY !== undefined) { c.beginPath(); c.rect(-5000, -5000, 12000, clipY + 5000); c.ellipse(RUG[0], RUG[1], 520, 166, 0, 0, TAU); c.clip(); }
  withT(c, x, y, s, 0, () => drawDemon(c, Object.assign({ t }, o)));
  c.restore();
}
function shRise(c, t) {        // 26.95 – 29.8: demon climbs out of the portal
  const r0 = 27.05, r1 = 29.0, roar = WS(64);
  const rise = lerp(1500, 0, E.out(inv(r0, r1, t)));
  const [sx, sy] = shake(t, 8 + pulse(t, r1, 0.5) * 30 + (t > roar ? 14 : 0), 20);
  const cam = { x: 1200 + sx, y: kf(t, [[26.95, 1450], [29.1, 950]]) + sy, z: kf(t, [[26.95, 0.75], [29.1, 0.56], [29.8, 0.6]]) };
  roomWide(c, t, cam, { noDesk: true, room: { posterFall: 1, noPlant: true, signFall: 1, noRug: true } }, cc => {
    drawPortal(cc, RUG[0], RUG[1], 520, t, 'back', 1);
    demonAt(cc, t, RUG[0], RUG[1] + rise, 1.12, { pose: t < 28.2 ? 'grip' : t > roar ? 'roar' : 'idle', spread: inv(roar, roar + 0.3, t), mouth: t > roar ? 0.4 : 0 }, RUG[1]);
    drawPortal(cc, RUG[0], RUG[1], 520, t, 'front', 1);
    // smoke
    particles(cc, t, 22, i => ({ t0: r0 + hash(i) * 2.5, life: 1.4, x: RUG[0] + (hash(i + 2) - .5) * 900 }), (c2, p, age, u) => {
      c2.save(); c2.globalAlpha = 0.5 * (1 - u); circle(c2, p.x, RUG[1] - age * 500, 80 + 140 * u, '#3a2236', 0); c2.restore();
    });
    // ceiling crack when the horns hit it
    if (t > r1) { c.save(); line(cc, [1000, 150, 1080, 220, 1050, 300, 1130, 360], 8); line(cc, [1400, 150, 1330, 230, 1380, 290], 8); c.restore(); }
  });
  hellLight(c, 1);
  vignette(c, 0.6, '40,0,0');
}
function shRoar(c, t) {        // 29.8 – 33.3: "КТО ПОЗВАЛ МЕНЯ В ЭТОТ МИР?!"
  const m = mouthAt('d', t), pz = DATA.pauses[0][0];
  const [sx, sy] = shake(t, 6 + m * 26, 26);
  const headY = RUG[1] - 1060 * 1.12;
  const cam = { x: RUG[0] + sx, y: headY + 140 + sy, z: kf(t, [[29.8, 1.05], [32.6, 1.35], [33.3, 1.42]]), r: Math.sin(t * 1.5) * 0.02 };
  // background: room in red + radial lines behind the demon
  c.save(); applyCam(c, cam); drawRoom(c, { t, posterFall: 1, noPlant: true, signFall: 1, noRug: true }); c.restore();
  hellLight(c, 1);
  c.save(); c.globalAlpha = 0.5 + m * 0.5; speedLines(c, W / 2, 760, t, { n: 70, r0: 300, col: 'rgba(255,200,120,0.6)', w: 14 }); c.restore();
  c.save(); applyCam(c, cam);
  demonAt(c, t, RUG[0], RUG[1], 1.12, { pose: 'roar', spread: 1, mouth: m, round: roundAt(t), headTilt: Math.sin(t * 2) * 0.05 });
  // fire breath / spit
  if (m > 0.3) particles(c, t, 50, i => ({ t0: 29.9 + hash(i) * 2.8, life: 0.6, a: Math.PI / 2 + (hash(i + 1) - .5) * 1.4, sp: 600 + hash(i + 2) * 900 }), (cc, p, age, u) => {
    const x = RUG[0] + Math.cos(p.a) * p.sp * age, y = headY + 95 + Math.sin(p.a) * p.sp * age * 0.6;
    circle(cc, x, y, 26 * (1 - u) + 6, `rgba(255,${120 + 120 * (1 - u)},20,${1 - u})`, 0);
  });
  // heavy breathing smoke in the pause
  if (t > pz) particles(c, t, 10, i => ({ t0: pz + i * 0.07, life: 0.8, s: i % 2 ? 1 : -1 }), (cc, p, age, u) => {
    cc.save(); cc.globalAlpha = .55 * (1 - u); circle(cc, RUG[0] + p.s * (24 + age * 260), headY + 62 + age * 160, 8 + 28 * u, '#cfc5d8', 0); cc.restore();
  });
  c.restore();
  vignette(c, 0.65, '60,0,0');
}
function teacup(c, x, y, s, rot) {
  withT(c, x, y, s, rot, () => {
    c.beginPath(); c.moveTo(-34, -30); c.lineTo(34, -30); c.quadraticCurveTo(32, 22, 0, 24); c.quadraticCurveTo(-32, 22, -34, -30); c.closePath(); fillStroke(c, '#fff', 5);
    c.beginPath(); c.arc(38, -8, 14, -1.4, 1.4); c.lineWidth = 6; c.strokeStyle = INK; c.stroke();
    ellipse(c, 0, -30, 34, 7, '#b45309', 4); line(c, [-10, -50, -4, -70, -10, -90], 4, 'rgba(255,255,255,0.7)');
  });
}
function shCalm(c, t) {        // 33.3 – 36.2: the hamster calmly sips tea
  const p2 = DATA.pauses[1][0];
  const z = t < p2 ? kf(t, [[33.3, 1.0], [p2, 1.15]]) : kf(t, [[p2, 1.15], [p2 + 0.55, 1.45, E.io]]);
  const faceY = DOOR_SPOT[1] - 150 * HAM_BIG;
  const cam = { x: DOOR_SPOT[0] + 60, y: lerp(faceY + 120, faceY + 40, inv(p2, p2 + .5, t)), z };
  const sip = bump(t, WS(74), WS(75) + 0.4);
  roomWide(c, t, cam, { noDesk: true, room: { posterFall: 1, noPlant: true, signFall: 1, noRug: true } }, cc => {
    withT(cc, DOOR_SPOT[0], DOOR_SPOT[1], HAM_BIG, 0, () => drawHamster(cc, {
      t, eyes: t < p2 ? 'narrow' : 'narrow', brow: t > p2 ? 1 : 0.3, belly: 0.5, blink: t < p2 ? blinkAt(t, 3, 1.6) : 0,
      pawL: [-40, -80], pawR: [lerp(62, 28, sip), lerp(-62, -92, sip)],
      hold: (c2, pL, pR) => { if (t < p2 + .2) teacup(c2, pR[0] - 12, pR[1] - 6, 0.85, -sip * 0.5); } }));
  });
  hellLight(c, 0.8);
  // demon still roaring off-screen: red flicker from the right
  glow(c, W + 200, 900, 900, 'rgba(255,80,40,0.35)', 0.7 + 0.3 * Math.sin(t * 9));
  if (t > p2) vignette(c, 0.6 * inv(p2, p2 + .4, t));
}
function shBoss(c, t) {        // 36.2 – 38.4: "Тихо, блять, я тут главный"
  const g = WS(78);
  const m = mouthAt('h', t);
  const faceY = DOOR_SPOT[1] - 150 * HAM_BIG;
  const boom = inv(g, g + 0.25, t);
  const [sx, sy] = shake(t, t > g ? 12 + 10 * (1 - boom) : 2, 26);
  const cam = { x: DOOR_SPOT[0] + 20 + sx, y: faceY + 20 + sy, z: t < g ? kf(t, [[36.2, 1.45], [g, 1.6]]) : kf(t, [[g, 1.6], [g + 0.15, 1.85, E.out]]) };
  if (t > g) {
    sunburst(c, W / 2, 900, t, '#2a0008', '#5c0012', 16, 0.8);
    fireBurst(c, W / 2, H + 40, W * 1.6, 1100 * E.out(boom), t, 1);
  }
  c.save(); applyCam(c, cam);
  if (t <= g) drawRoom(c, { t, posterFall: 1, noPlant: true, signFall: 1, noRug: true });
  withT(c, DOOR_SPOT[0], DOOR_SPOT[1], HAM_BIG, 0, () => drawHamster(c, {
    t, eyes: t > g ? 'glow' : 'narrow', glow: E.out(boom), brow: 1, mouth: m, round: roundAt(t), yell: t > g ? 1 : 0, belly: 0.5,
    horns: E.back(boom), pawL: [-40, -80], pawR: t < g ? [130, -200] : [110, -180] }));
  c.restore();
  if (t <= g) hellLight(c, 0.8);
  if (t > g) { speedLines(c, W / 2, 900, t, { n: 40, r0: 520, col: 'rgba(255,180,80,0.5)' }); flash(c, pulse(t, g, 0.2) * 0.8, '255,60,30'); }
  vignette(c, 0.5);
}
function shScared(c, t) {      // 38.4 – 39.0: the demon backs away in fear
  const lt = t - 38.38;
  const dx = lerp(1250, 1500, E.out(clamp(lt / 0.45))), ds = lerp(1.0, 0.86, E.out(clamp(lt / 0.45)));
  const cam = { x: 950, y: 1150, z: 0.55 };
  roomWide(c, t, cam, { noDesk: true, room: { posterFall: 1, noPlant: true, signFall: 1, noRug: true } }, cc => {
    drawPortal(cc, RUG[0], RUG[1], 520, t, 'back', 1 - clamp(lt / 0.5));
    withT(cc, DOOR_SPOT[0], DOOR_SPOT[1], HAM_BIG, 0, () => drawHamster(cc, { t, eyes: 'narrow', brow: 1, horns: 1, smirk: 1, belly: .5, pawL: [30, -112], pawR: [-30, -102] }));
    withT(cc, dx, 1700, ds, 0, () => drawDemon(cc, { t, pose: 'scared', scared: 1, look: -1, headTilt: 0.1 }));
  });
  hellLight(c, 0.6);
  sticker(c, 'ой...', 820, 560, 70, INK, inv(38.45, 38.6, t), 0.15);
}

// ------------------------------------------------------------------ SCENE 5: throne, courier, salary
function drawThrone(c, x, y, t) {
  // a pile of the guy's furniture
  withT(c, x, y, 1, 0, () => {
    // bottom: desk upside down
    rrect(c, -480, -120, 960, 120, 14); fillStroke(c, '#a86b42', 8);
    rrect(c, -440, -200, 40, 90, 8); fillStroke(c, '#5b3a29', 6); rrect(c, 400, -200, 40, 90, 8); fillStroke(c, '#5b3a29', 6);
    // fridge lying + books + monitor
    rrect(c, -420, -330, 560, 210, 30); fillStroke(c, '#eef3f8', 8); line(c, [-220, -330, -220, -120], 7);
    drawMonitor(c, 300, -120, t, { screen: 'error' });
    drawBook(c, -380, -380, 1, 0.2, '#3b82f6'); drawBook(c, 360, -170, 1, -0.4, '#22c55e');
    drawHeadphones(c, 260, -360, 0.8, 0.3);
    // energy drink cans
    for (let i = 0; i < 3; i++) { rrect(c, -150 + i * 46, -410, 36, 80, 8); fillStroke(c, i % 2 ? '#38bdf8' : '#a3e635', 6); }
    // gaming chair on top
    drawChair(c, 0, -330, 1.25);
    // red carpet down the pile
    poly(c, [-90, -330, 90, -330, 160, 0, -160, 0], 'rgba(220,30,50,0.85)', 0);
  });
}
function throneComp(c, t, cam, o = {}) {
  c.save(); applyCam(c, cam);
  drawRoom(c, { t, posterFall: 1, noPlant: true, signFall: 1, noRug: true });
  drawThrone(c, 1000, 1700, t);
  const hp = o.ham || {};
  withT(c, 1000, 1700 - 330 - 130, 1.55, 0, () => drawHamster(c, Object.assign({ t, crown: !hp.fedora, chain: 1, eyes: 'narrow', brow: 0.6, belly: .5, blink: blinkAt(t, 5) }, hp)));
  if (o.demon) withT(c, o.demon.x, 1760, o.demon.s || 0.72, 0, () => drawDemon(c, Object.assign({ t, courier: 1, noWings: 1 }, o.demon.o)));
  if (o.extra) o.extra(c);
  c.restore();
}
function idCard(c, t, a, stampT) {
  if (a <= 0) return;
  const s = E.back(clamp(a));
  c.save(); c.translate(W / 2, 1000); c.scale(s, s); c.rotate(-0.05);
  rrect(c, -420, -260, 840, 520, 36); fillStroke(c, '#fff', 10);
  rrect(c, -420, -260, 840, 110, 36); fillStroke(c, '#e0233a', 0); rrect(c, -420, -260, 840, 520, 36); fillStroke(c, null, 10);
  text(c, 'ПРОПУСК № 666', 0, -205, 54, '#fff', { stroke: 8 });
  rrect(c, -380, -120, 260, 320, 20); fillStroke(c, '#fde68a', 6);
  c.save(); rrect(c, -380, -120, 260, 320, 20); c.clip(); withT(c, -250, 640, 0.6, 0, () => drawDemon(c, { t: 0, courier: 1, noWings: 1 })); c.restore();
  rrect(c, -380, -120, 260, 320, 20); fillStroke(c, null, 6);
  text(c, 'ИМЯ: ДЕМОН', -80, -80, 40, INK, { stroke: 0, align: 'left' });
  text(c, 'ОТДЕЛ:', -80, -10, 34, '#666', { stroke: 0, align: 'left' });
  text(c, 'АД•ДОСТАВКА', -80, 40, 42, '#e0233a', { stroke: 0, align: 'left' });
  text(c, 'ДОЛЖНОСТЬ:', -80, 110, 34, '#666', { stroke: 0, align: 'left' });
  text(c, 'КУРЬЕР', -80, 165, 60, INK, { stroke: 0, align: 'left' });
  const sa = inv(stampT, stampT + 0.12, t);
  if (sa > 0) withT(c, 200, -40, lerp(2.5, 1, E.out(sa)), 0.3, () => {
    c.globalAlpha = Math.min(1, sa * 2); circle(c, 0, 0, 120, null, 0);
    c.beginPath(); c.arc(0, 0, 120, 0, TAU); c.lineWidth = 12; c.strokeStyle = '#16a34a'; c.stroke();
    text(c, 'ПРИНЯТ', 0, 6, 54, '#16a34a', { stroke: 0 });
  });
  c.restore();
}
function shThrone(c, t) {      // 38.95 – 43.05: one minute later: the throne, the courier contract
  if (t < 39.55) { clockCard(c, t, t - 38.95, 'ЧЕРЕЗ 1 МИНУТУ'); return; }
  const enter = WS(84);
  const cam = {
    x: kf(t, [[39.55, 1000], [enter, 1000], [enter + 0.6, 1250, E.io]]),
    y: kf(t, [[39.55, 1500], [40.5, 1050, E.io], [enter + 0.6, 1150]]),
    z: kf(t, [[39.55, 1.05], [40.5, 0.95], [enter + 0.6, 0.58, E.io]]),
  };
  const dx = kf(t, [[enter, 2500], [enter + 0.7, 1730, E.out]]);
  const walk = t > enter && t < enter + 0.7 ? Math.abs(Math.sin(t * 12)) * 30 : 0;
  throneComp(c, t, cam, {
    ham: { pawL: [-30, -104], pawR: t > 42.6 ? [kf(t, [[42.6, 120], [42.75, 150]]), kf(t, [[42.6, -200], [42.75, -60]])] : [30, -104], smirk: 1 },
    demon: { x: dx, s: 0.72, o: { pose: 'present', headDy: -walk, mouth: 0 } },
    extra: cc => {
      if (t > enter) withT(cc, dx - 150 * 0.72, 1760 - 720 * 0.72, 0.72, 0.1, () => { rrect(cc, -100, -130, 200, 260, 8); fillStroke(cc, '#fff', 6); text(cc, 'ДОГОВОР', 0, -90, 30, INK, { stroke: 0 }); for (let i = 0; i < 6; i++) line(cc, [-70, -40 + i * 28, 70, -40 + i * 28], 4, '#9ca3af'); });
    },
  });
  vignette(c, 0.45);
  idCard(c, t, inv(WS(89) - 0.05, WS(89) + 0.15, t) * (1 - inv(43.0, 43.15, t)), 42.62);
}
function shSalary(c, t) {      // 43.05 – 46.15: paid in sunflower seeds
  const flick = 43.62, catchT = 44.45, bow = WS(93);
  const cam = { x: kf(t, [[43.05, 1250], [catchT, 1350]]), y: 1150, z: kf(t, [[43.05, 0.6], [catchT, 0.66], [bow, 0.66], [bow + 0.2, 0.78, E.back]]) };
  const happy = t > catchT;
  throneComp(c, t, cam, {
    ham: { smirk: 1, pawL: [-30, -104], pawR: t > flick - 0.2 && t < flick + 0.2 ? [140, -150] : [30, -104] },
    demon: { x: 1730, s: 0.72, o: { pose: 'catch', headTilt: t > bow ? 0.25 * Math.abs(Math.sin((t - bow) * 8)) : 0, mouth: happy ? 0.25 : 0 } },
    extra: cc => {
      // the seed's flight
      if (t > flick && t < catchT + 0.05) {
        const u = inv(flick, catchT, t);
        const x0 = 1000 + 140 * 1.55, y0 = 1240 - 150 * 1.55, x1 = 1730, y1 = 1760 - 650 * 0.72;
        propSeed(cc, lerp(x0, x1, u), lerp(y0, y1, u) - Math.sin(u * Math.PI) * 420, 1.6, u * 20);
      }
      if (happy) {
        propSeed(cc, 1730, 1760 - 640 * 0.72, 1.6, 0.3);
        star4(cc, 1730 + 60, 1760 - 700 * 0.72, 30 + 10 * Math.sin(t * 10), '#ffe14d', t * 3);
        // tears of joy
        for (const s of [-1, 1]) line(cc, [1730 + s * 36, 1760 - 1070 * 0.72, 1730 + s * 44, 1760 - 980 * 0.72 + ((t * 300) % 80)], 10, '#7dd3fc');
      }
    },
  });
  vignette(c, 0.45);
  if (happy) sticker(c, 'СПАСИБО, БОСС!', 760, 620, 50, '#e0233a', inv(catchT + 0.1, catchT + 0.3, t), 0.12);
}

// ------------------------------------------------------------------ SCENE 6: escape, mafia, microphone, rent
function shEscape(c, t) {      // 46.15 – 47.85: tries to run away
  const lt = t - 46.15;
  const gx = lerp(1700, 620, inv(46.15, 47.85, t));
  const cam = { x: gx + 120, y: 1350, z: 0.95 };
  roomWide(c, t, cam, { noDesk: true, room: { posterFall: 1, noPlant: true, signFall: 1, noRug: true } }, cc => {
    particles(cc, t, 20, i => ({ t0: 46.15 + i * 0.08, life: 0.6 }), (c2, p, age, u) => {
      const px = lerp(1700, 620, inv(46.15, 47.85, p.t0)) + 60;
      c2.save(); c2.globalAlpha = 0.7 * (1 - u); circle(c2, px + age * 120, 1700 - age * 80, 40 + 60 * u, '#e8dcc8', 0); c2.restore();
    });
    withT(cc, gx, 1700, 1.0, 0, () => { cc.scale(-1, 1); drawGuy(cc, guyIdle(t, { pose: 'run', expr: 'scared', sweat: 1, lean: 0.18, mouthOpenFixed: 0.6,
      handL: [-60 + Math.sin(t * 26) * 120, -280], handR: [60 - Math.sin(t * 26) * 120, -260] })); });
  });
  speedLines(c, W / 2, 1000, t, { n: 30, r0: 600, col: 'rgba(255,255,255,0.4)', w: 6 });
  vignette(c, 0.4);
}
function spotlight(c, x, y, r, a = 0.85, x2, y2, r2) {
  c.save();
  c.fillStyle = `rgba(5,0,15,${a})`;
  c.beginPath(); c.rect(0, 0, W, H); c.moveTo(x + r, y); c.ellipse(x, y, r, r * 1.1, 0, 0, TAU);
  if (r2) { c.moveTo(x2 + r2, y2); c.ellipse(x2, y2, r2, r2 * 1.3, 0, 0, TAU); }
  c.fill('evenodd');
  for (const [px, py, pr, k] of [[x, y, r, 1.1], [x2, y2, r2, 1.3]]) {
    if (!pr) continue;
    const g = c.createRadialGradient(px, py, pr * .82, px, py, pr * 1.05); g.addColorStop(0, 'rgba(5,0,15,0)'); g.addColorStop(1, `rgba(5,0,15,${a})`);
    c.fillStyle = g; c.beginPath(); c.ellipse(px, py, pr * 1.05, pr * k * 1.05, 0, 0, TAU); c.fill();
  }
  c.restore();
}
function shMafia(c, t) {       // 47.85 – 51.45: spotlight, fedora, the microphone
  const off = 47.92, micT = WS(101) + 0.15, tap = WS(104) - 0.1;
  const cam = { x: 1000, y: kf(t, [[47.85, 1250], [51.4, 1230]]), z: kf(t, [[47.85, 0.85], [49.4, 1.0], [51.4, 1.2]]) };
  const hasMic = t > micT;
  throneComp(c, t, cam, {
    ham: { fedora: 1, crown: 0, eyes: 'narrow', brow: 1, smirk: hasMic ? 0 : 1, pawL: [-30, -104],
      pawR: hasMic ? [70, -150] : [30, -104],
      hold: (cc, pL, pR) => {
        if (!hasMic) propSeed(cc, 26, -102, 0.8, 1.3);
        else propMic(cc, pR[0], pR[1] - 10, 1.1, -0.35);
        if (t > tap && t < tap + 0.25) for (let i = 0; i < 3; i++) { cc.beginPath(); cc.arc(pR[0] - 20, pR[1] - 60, 30 + i * 22, -2.4, -0.8); cc.lineWidth = 5; cc.strokeStyle = '#fff'; cc.stroke(); }
      } },
    extra: cc => {
      // the guy frozen mid-run near the door
      withT(cc, 600, 1850, 1.0, 0, () => { cc.scale(-1, 1); drawGuy(cc, { t: 0.13, pose: 'run', expr: 'shock', lean: 0.18, sweat: 1, handL: [-150, -280], handR: [150, -300] }); });
    },
  });
  if (t > off) {
    const sp = E.out(inv(off, off + 0.15, t));
    // compute screen pos of hamster face
    const fx = (1000 - cam.x) * cam.z + W / 2, fy = (1240 - 160 * 1.55 - cam.y) * cam.z + H / 2;
    const gx2 = (600 - cam.x) * cam.z + W / 2, gy2 = (1850 - 330 - cam.y) * cam.z + H / 2;
    spotlight(c, fx, fy + 60, lerp(1400, 360 * cam.z / 0.85, sp), 0.82, gx2, gy2, 260 * cam.z * E.out(inv(off + 0.25, off + 0.4, t)));
    glow(c, fx, fy + 60, 420 * cam.z, 'rgba(255,230,170,0.35)', sp);
    if (t > off && t < off + 0.3) text(c, 'ЩЁЛК', 780, 520, 80, '#fff', { stroke: 16 });
    sticker(c, 'ПУШИСТАЯ МАФИЯ', W / 2, 330, 64, '#e0233a', inv(WS(99), WS(99) + 0.2, t) * (1 - inv(49.7, 49.9, t)), -0.05, '#111');
  }
  if (t > tap && t < tap + 0.5) text(c, 'ТУК-ТУК', 300, 760, 70, '#fff', { stroke: 14 });
}
function stageBg(c, t) {
  c.fillStyle = vgrad(c, 0, H, [[0, '#1a0b2e'], [1, '#4c0b2e']]); c.fillRect(0, 0, W, H);
  c.save(); c.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 4; i++) {
    const a = Math.sin(t * 1.4 + i * 1.7) * 0.5, x0 = (i + .5) * W / 4;
    c.save(); c.translate(x0, -100); c.rotate(a);
    const g = c.createLinearGradient(0, 0, 0, 2200); g.addColorStop(0, i % 2 ? 'rgba(255,60,120,0.35)' : 'rgba(80,160,255,0.35)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = g; c.beginPath(); c.moveTo(-30, 0); c.lineTo(30, 0); c.lineTo(320, 2200); c.lineTo(-320, 2200); c.closePath(); c.fill(); c.restore();
  }
  c.restore();
}
function shAnnounce(c, t) {    // 51.45 – 56.12: "Эй, человек! А кто разрешил тебе жить в моей квартире бесплатно?!"
  const m = mouthAt('h', t), bes = WS(115);
  const z = t < bes ? kf(t, [[51.45, 1.25], [bes, 1.5]]) : kf(t, [[bes, 1.5], [bes + 0.12, 2.1, E.out]]);
  const [sx, sy] = shake(t, t > bes ? 14 : 3 + m * 5, 26);
  const hy = 1240;
  const cam = { x: 1000 + sx, y: hy - 160 * 1.55 + 60 + sy, z };
  stageBg(c, t);
  c.save(); applyCam(c, cam);
  drawThrone(c, 1000, 1700, t);
  withT(c, 1000, hy, 1.55, 0, () => drawHamster(c, {
    t, fedora: 1, chain: 1, eyes: t > bes ? 'glow' : 'narrow', glow: t > bes ? 1 : 0, brow: 1, belly: .5, mouth: m, round: roundAt(t), yell: 1,
    pawL: t < WS(107) ? [-150, -190] : [-30, -104], pawR: [70, -150],
    hold: (cc, pL, pR) => propMic(cc, pR[0], pR[1] - 10, 1.1, -0.35) }));
  c.restore();
  // confetti + echo rings
  particles(c, t, 40, i => ({ t0: 51.4 + hash(i) * 4.5, life: 1.5, x: hash(i + 1) * W, col: ['#ffe14d', '#ff5c8a', '#3ec1ff', '#a3e635'][i % 4] }), (cc, p, age, u) => {
    withT(cc, p.x + Math.sin(age * 4 + p.x) * 40, -40 + age * 900, 1, age * 6, () => { cc.fillStyle = p.col; cc.fillRect(-10, -6, 20, 12); });
  });
  if (m > 0.4) { c.save(); c.globalAlpha = 0.3; for (let i = 0; i < 3; i++) { c.beginPath(); c.arc(W / 2 + 170, 900, 120 + i * 60 + (t * 300) % 60, -0.9, 0.9); c.lineWidth = 8; c.strokeStyle = '#fff'; c.stroke(); } c.restore(); }
  vignette(c, 0.5);
}
function shReact(c, t) {       // 56.12 – 56.92: the guy, terrified
  const [sx, sy] = shake(t, 6, 30);
  c.fillStyle = '#ffe14d'; c.fillRect(0, 0, W, H);
  sunburst(c, W / 2, 1000, t, '#ffd23f', '#ffb703', 18, 0.6);
  withT(c, W / 2 + sx, 1950 + sy, 2.4, 0, () => drawGuy(c, guyIdle(t, { expr: 'scared', sweat: 1, mouth: mouthAt('n', t), round: roundAt(t), handL: [-150, -380], handR: [150, -380] })));
  speedLines(c, W / 2, 900, t, { n: 50, r0: 560, col: 'rgba(255,255,255,0.7)' });
}

// ------------------------------------------------------------------ SCENE 7: straight into the lens
function hamCloseBg(c, t, dark) {
  c.fillStyle = vgrad(c, 0, H, [[0, '#14061f'], [1, dark ? '#3a0010' : '#2a0b3e']]); c.fillRect(0, 0, W, H);
  glow(c, W / 2, 1000, 900, 'rgba(255,40,60,0.25)');
}
function shStare(c, t) {       // 56.92 – 59.88: "А потом посмотрела прямо на меня..." + the stare
  const p = DATA.pauses[5][0];
  const z = kf(t, [[56.92, 1.6], [p, 2.3, E.io], [p + 0.5, 2.7]]);
  const beat = t > p ? 1 + 0.03 * pulse((t - p) % 0.5, 0, 0.2) : 1;
  hamCloseBg(c, t, false);
  c.save(); c.translate(W / 2, 930); c.scale(z * beat, z * beat);
  const look = kf(t, [[56.92, -1], [57.6, 0, E.io]]);
  withT(c, 0, 260, 1.55, 0, () => drawHamster(c, {
    t, fedora: 1, chain: 1, eyes: 'narrow', brow: 1, belly: .5, look: [look, 0], twitch: t > p + 0.2, smirk: t < p ? 1 : 0,
    pawL: [-30, -104], pawR: [70, -150], hold: (cc, pL, pR) => propMic(cc, pR[0], pR[1] - 10, 1.1, -0.35) }));
  c.restore();
  vignette(c, 0.6 + 0.2 * inv(p, p + 0.4, t));
}
function subButton(c, t, a, clicked) {
  if (a <= 0) return;
  const s = E.back(clamp(a));
  c.save(); c.translate(W / 2, 1700); c.scale(s * (clicked > 0 && clicked < 0.15 ? 0.9 : 1), s);
  rrect(c, -330, -70, 660, 140, 70); fillStroke(c, clicked > 0 ? '#6b7280' : '#e0233a', 8);
  text(c, clicked > 0 ? 'ВЫ ПОДПИСАНЫ ✓' : 'ПОДПИСАТЬСЯ', -30, 4, 54, '#fff', { stroke: 0 });
  // bell
  withT(c, 250, 0, 1, Math.sin(t * 30) * 0.3 * (clicked > 0 ? 1 : 0), () => {
    c.beginPath(); c.moveTo(-26, 20); c.quadraticCurveTo(-26, -34, 0, -34); c.quadraticCurveTo(26, -34, 26, 20); c.closePath(); fillStroke(c, '#ffe14d', 5);
    circle(c, 0, 26, 8, '#ffe14d', 4);
  });
  c.restore();
  // pointer paw
  if (clicked >= 0) {
    const u = clicked > 0 ? 1 : inv(60.4, 60.85, t);
    withT(c, lerp(900, 600, E.out(u)), lerp(1950, 1730, E.out(u)), 1.2, -0.4, () => {
      limb(c, [0, 0, 0, 160], 34, HAM.fur, 6); circle(c, 0, 0, 24, HAM.paw, 6);
    });
  }
}
function grandmaCage(c, t, bab) {
  const u = inv(bab - 0.15, bab + 0.05, t);
  const sw = Math.sin((t - bab) * 12) * 0.08 * (1 - inv(bab, bab + 1.2, t));
  withT(c, 800, lerp(-500, 1330, E.out(u)), 1.35, sw, () => {
    drawCage(c, -145, 0, { t, noBowl: 1 });
    // knitting basket inside: yarn + needles + glasses
    circle(c, -40, -60, 34, '#c084fc', 5); line(c, [-70, -90, -10, -30], 4, '#7c3aed'); line(c, [-20, -100, 30, -50], 5, '#d4d4d8');
    c.beginPath(); c.arc(50, -50, 16, 0, TAU); c.arc(90, -50, 16, 0, TAU); c.lineWidth = 4; c.strokeStyle = INK; c.stroke();
    drawCageFront(c, -145, 0, {});
    withT(c, 0, -205, 1, Math.sin(t * 4) * 0.12, () => { line(c, [0, 0, 0, 30], 4); rrect(c, -120, 30, 240, 74, 14); fillStroke(c, '#fff', 6); text(c, 'БАБУШКА', 0, 69, 40, '#e0233a', { stroke: 0 }); });
  });
}
function shSubscribe(c, t) {   // 59.88 – 64.75: "Подпишись, блять. Иначе следующим питомцем будет твоя бабушка."
  const m = mouthAt('h', t), bab = WS(131);
  const zA = kf(t, [[59.88, 2.75], [61.4, 2.95], [62.0, 2.3, E.io], [63.5, 2.2], [bab - 0.1, 1.75, E.io], [bab + 0.1, 1.95, E.out]]);
  const ox = kf(t, [[63.5, 0], [bab - 0.1, -230, E.io]]);
  const [sx, sy] = shake(t, t > bab ? 14 * (1 - inv(bab, bab + .6, t)) + 2 : 1, 26);
  hamCloseBg(c, t, true);
  if (t > 61.5) fireBurst(c, W / 2, H + 40, W * 1.6, 500 * inv(61.5, 62.5, t), t, 0.8);
  c.save(); c.translate(W / 2 + sx + ox, 920 + sy); c.scale(zA, zA);
  const gl = inv(61.6, 62.8, t);
  withT(c, 0, 260, 1.55, 0, () => drawHamster(c, {
    t, fedora: 1, chain: 1, eyes: gl > 0.05 ? 'glow' : 'narrow', glow: gl, brow: 1, belly: .5, mouth: m, round: roundAt(t), look: [t > 63.6 ? 0.8 : 0, 0], smirk: t > bab + 0.5 ? 1 : 0,
    pawL: [-30, -104], pawR: [70, -150], hold: (cc, pL, pR) => propMic(cc, pR[0], pR[1] - 10, 1.1, -0.35) }));
  c.restore();
  if (t > bab - 0.15) grandmaCage(c, t, bab);
  vignette(c, 0.55);
  const btnA = inv(60.1, 60.35, t) * (1 - inv(61.6, 61.85, t));
  subButton(c, t, btnA, t > 60.85 ? t - 60.85 : (t > 60.4 ? 0 : -1));
  if (t > bab && t < bab + 0.5) flash(c, pulse(t, bab, 0.25) * 0.6, '255,40,40');
}
function shEnd(c, t) {         // 64.75 – end: evil laugh, КОНЕЦ
  const k = 65.35;
  if (t < k) {
    hamCloseBg(c, t, true);
    fireBurst(c, W / 2, H + 40, W * 1.6, 500, t, 0.8);
    const bob = Math.abs(Math.sin(t * 16)) * 14;
    const zz = 1.95 - (t - 64.75) * 0.3;
    c.save(); c.translate(W / 2 - 230, 920); c.scale(zz, zz);
    withT(c, 0, 260 - bob, 1.55, 0, () => drawHamster(c, { t, fedora: 1, chain: 1, eyes: 'glow', glow: 1, brow: 1, belly: .5, mouth: 0.55 + 0.35 * Math.abs(Math.sin(t * 16)), yell: 1,
      pawL: [-30, -104], pawR: [70, -150], hold: (cc, pL, pR) => propMic(cc, pR[0], pR[1] - 10, 1.1, -0.35) }));
    c.restore();
    grandmaCage(c, t, WS(131));
    vignette(c, 0.55);
    text(c, 'ХА-ХА-ХА', W / 2, 520, 110, '#ff3b3b', { stroke: 20 });
    return;
  }
  const u = inv(k, k + 0.25, t);
  c.fillStyle = '#0b0610'; c.fillRect(0, 0, W, H);
  glow(c, W / 2, 900, 700, 'rgba(255,30,50,0.4)');
  withT(c, W / 2, 900, lerp(3, 1, E.out(u)), -0.04, () => text(c, 'КОНЕЦ', 0, 0, 220, '#e0233a', { stroke: 26, scol: '#fff', fam: 'Rubik' }));
  flash(c, pulse(t, k, 0.2));
  flash(c, inv(DATA.dur - 0.35, DATA.dur, t), '0,0,0');
}

// ------------------------------------------------------------------ timeline
// [start, function, transition-in, transition length]
const SHOTS = [
  [0.00, shIntro, 'cut', 0],
  [1.20, shShop, 'zoom', 0.3],
  [2.95, shCute, 'flash', 0.25],
  [5.12, shRat, 'cut', 0],
  [6.62, shHour, 'spin', 0.25],
  [7.32, shDemand, 'zoom', 0.25],
  [9.45, shRampage, 'flash', 0.15],
  [11.95, shPhones, 'whip', 0.25],
  [13.62, shSuka, 'whip', 0.25],
  [15.0, shInvoice, 'whip', 0.25],
  [17.35, shReturn, 'zoom', 0.3],
  [19.92, shGrow, 'zoom', 0.2],
  [22.80, shBlock, 'cut', 0],
  [24.45, shPortal, 'whip', 0.25],
  [26.95, shRise, 'flash', 0.2],
  [29.80, shRoar, 'zoom', 0.2],
  [33.30, shCalm, 'whip', 0.3],
  [36.20, shBoss, 'zoom', 0.2],
  [38.38, shScared, 'whip', 0.2],
  [38.95, shThrone, 'spin', 0.25],
  [43.05, shSalary, 'cut', 0],
  [46.15, shEscape, 'whip', 0.25],
  [47.85, shMafia, 'flash', 0.15],
  [51.45, shAnnounce, 'zoom', 0.25],
  [56.12, shReact, 'whip', 0.2],
  [56.92, shStare, 'zoom', 0.3],
  [59.88, shSubscribe, 'flash', 0.15],
  [64.75, shEnd, 'cut', 0],
];
function shotIndex(t) { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1][0]) i++; return i; }
function drawShot(c, i, t) { c.save(); SHOTS[i][1](c, t); c.restore(); }
const offCtx = OFF.map(o => o.getContext('2d'));
function transition(c, kind, u, iA, iB, t) {
  // render both shots offscreen, then composite
  offCtx[0].setTransform(1, 0, 0, 1, 0, 0); offCtx[1].setTransform(1, 0, 0, 1, 0, 0);
  drawShot(offCtx[0], iA, t); drawShot(offCtx[1], iB, t);
  const A = OFF[0], B = OFF[1];
  if (kind === 'whip') {
    const e = E.io(u), dx = e * W;
    for (let k = 0; k < 6; k++) {
      const o = (k - 2.5) * 40 * Math.sin(u * Math.PI);
      c.globalAlpha = k === 0 ? 1 : 0.35;
      c.drawImage(A, -dx + o, 0); c.drawImage(B, W - dx + o, 0);
    }
    c.globalAlpha = 1;
    speedLines(c, W / 2, H / 2, t, { n: 30, r0: 200, col: `rgba(255,255,255,${0.5 * Math.sin(u * Math.PI)})` });
  } else if (kind === 'zoom') {
    if (u < 0.5) { const s = 1 + E.in(u * 2) * 2.5; c.drawImage(A, W / 2 - W * s / 2, H / 2 - H * s / 2, W * s, H * s); }
    else { const s = 0.6 + 0.4 * E.out((u - .5) * 2); c.fillStyle = '#fff'; c.fillRect(0, 0, W, H); c.drawImage(B, W / 2 - W * s / 2, H / 2 - H * s / 2, W * s, H * s); }
    flash(c, Math.sin(u * Math.PI) * 0.6);
    speedLines(c, W / 2, H / 2, t, { n: 50, r0: 250, col: `rgba(255,255,255,${0.7 * Math.sin(u * Math.PI)})` });
  } else if (kind === 'flash') {
    c.drawImage(u < 0.5 ? A : B, 0, 0); flash(c, 1 - Math.abs(u - 0.5) * 2);
  } else if (kind === 'spin') {
    c.drawImage(A, 0, 0);
    c.save(); c.translate(W / 2, H / 2); c.rotate((1 - E.out(u)) * 2.5); const s = E.out(u) * 1.0 + 0.001;
    c.scale(s, s); c.beginPath(); c.arc(0, 0, H * .62, 0, TAU); c.clip(); c.drawImage(B, -W / 2, -H / 2); c.restore();
  }
}
function renderTime(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  const i = shotIndex(t);
  const [a, , kind, d] = SHOTS[i];
  const nxt = SHOTS[i + 1];
  if (d > 0 && i > 0 && t < a + d / 2) transition(ctx, kind, (t - (a - d / 2)) / d, i - 1, i, t);
  else if (nxt && nxt[3] > 0 && t >= nxt[0] - nxt[3] / 2) transition(ctx, nxt[2], (t - (nxt[0] - nxt[3] / 2)) / nxt[3], i, i + 1, t);
  else drawShot(ctx, i, t);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  drawTitle(ctx, t);
  drawHUD(ctx, t);
  drawSubs(ctx, t);
}
function renderFrame(f) { renderTime(f / FPS); }

const TESTS = {
  chars() {
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#6a5acd'; ctx.fillRect(0, 0, W, H);
    withT(ctx, 270, 500, 1.3, 0, () => drawHamster(ctx, { t: 0 }));
    withT(ctx, 780, 500, 1.3, 0, () => drawHamster(ctx, { t: 0, eyes: 'narrow', brow: 1, mouth: 0.7, pawR: [90, -150], crown: 1, chain: 1 }));
    withT(ctx, 300, 1880, 0.95, 0, () => drawGuy(ctx, { t: 0, headphones: 1, expr: 'neutral', mouth: 0.5 }));
  },
};
