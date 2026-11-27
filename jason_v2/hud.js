// Title hook, game-style HUD meters, karaoke subtitles, stickers, bubbles, picture-in-picture, onomatopoeia.

// ---------------------------------------------------------------- title hook
function drawTitle(c, t) {
  const a = inv(0.0, 0.25, t) * (1 - inv(2.9, 3.2, t));
  if (a <= 0) return;
  c.save();
  c.translate(W / 2, 250); c.scale(E.back(inv(0, .35, t)), E.back(inv(0, .35, t))); c.rotate(-0.025 + Math.sin(t * 3) * 0.01);
  c.globalAlpha = a;
  rrect(c, -500, -125, 1000, 250, 30); c.fillStyle = 'rgba(0,0,0,.35)'; c.save(); c.translate(10, 12); c.fill(); c.restore();
  rrect(c, -500, -125, 1000, 250, 30); fillStroke(c, '#fff', 8);
  text(c, 'ЗА НАМИ ПРИШЁЛ ДЖЕЙСОН,', 0, -52, 62, INK, { stroke: 0 });
  text(c, 'А МОЙ ДРУГ —', 0, 14, 54, INK, { stroke: 0 });
  text(c, 'ИДИОТ 🔪', 0, 80, 66, '#e0233a', { stroke: 0 });
  c.restore();
}

// ---------------------------------------------------------------- HUD meters
function hudMeter(c, slot, label, val, frac, col, appear, o = {}) {
  if (appear <= 0) return;
  const y = 176 + slot * 150, x = 70, w = W - 140, h = 128, t = o.t || 0;
  c.save();
  const s = E.back(clamp(appear));
  const [sx, sy] = o.shake ? shake(t, o.shake, 30, slot * 10) : [0, 0];
  c.translate(W / 2 + sx, y + h / 2 + sy); c.scale(s, s); c.translate(-W / 2, -(y + h / 2));
  rrect(c, x + 8, y + 10, w, h, 18); c.fillStyle = 'rgba(0,0,0,0.45)'; c.fill();
  rrect(c, x, y, w, h, 18); fillStroke(c, 'rgba(20,14,40,0.88)', 7, '#fff');
  text(c, label, x + 30, y + 36, 26, '#fff', { fam: 'Press', align: 'left', stroke: 0 });
  const g = o.glitch || 0;
  if (g > 0) for (const [dx, cc] of [[-6, 'rgba(255,0,60,0.8)'], [6, 'rgba(0,220,255,0.8)']])
    text(c, val, x + w - 30 + dx * g * (1 + Math.sin(t * 90)), y + 38, 30, cc, { fam: 'Press', align: 'right', stroke: 0 });
  text(c, val, x + w - 30, y + 38, 30, o.valCol || col, { fam: 'Press', align: 'right', stroke: 0 });
  const bx = x + 30, by = y + 70, bw = w - 60, bh = 34;
  rrect(c, bx, by, bw, bh, 6); fillStroke(c, '#2a2342', 5, '#fff');
  const f = clamp(frac, 0, 1);
  if (f > 0) {
    c.save(); rrect(c, bx + 5, by + 5, (bw - 10) * f, bh - 10, 3); c.clip();
    c.fillStyle = col; c.fillRect(bx, by, bw, bh);
    c.fillStyle = 'rgba(0,0,0,0.25)'; for (let i = bx + 5; i < bx + bw; i += 26) c.fillRect(i + 20, by, 6, bh);
    c.fillStyle = 'rgba(255,255,255,0.35)'; c.fillRect(bx, by + 5, bw, 7);
    c.restore();
  }
  if (o.flash) { rrect(c, x, y, w, h, 18); c.fillStyle = `rgba(255,255,255,${o.flash * .6})`; c.fill(); }
  c.restore();
}
function threatAt(t) {
  return kf(t, [[3.95, 0], [4.3, 20, E.out], [5.0, 20], [5.25, 45, E.out], [16.0, 45], [16.3, 70, E.out], [22.8, 70], [23.1, 85, E.out],
    [26.2, 85], [26.5, 92, E.out], [39.1, 92], [39.4, 99, E.out], [46.0, 99], [46.15, 999, E.out]]);
}
function drawHUD(c, t) {
  // threat level from Jason's first appearance until the photo request
  const ta = inv(3.95, 4.25, t) * (1 - inv(48.7, 48.95, t));
  if (ta > 0) {
    const v = threatAt(t), steps = [4.3, 5.25, 16.3, 23.1, 26.5, 39.4, 46.15];
    let fl = 0; steps.forEach(s => fl = Math.max(fl, pulse(t, s, 0.35)));
    const evil = v > 100, col = v < 30 ? '#ffd23f' : v < 70 ? '#ff8a1f' : '#ff2a3d';
    hudMeter(c, 0, 'УРОВЕНЬ УГРОЗЫ', Math.round(v) + '%', v / 100, col, ta,
      { t, flash: fl, shake: fl * 10 + (evil ? 7 : 0), glitch: evil ? 1 : (v > 90 ? .4 : 0), valCol: col });
  }
  // the friend's IQ
  const iq1 = inv(7.5, 7.75, t) * (1 - inv(9.45, 9.6, t));
  const iq2 = inv(42.6, 42.85, t) * (1 - inv(45.9, 46.0, t));
  if (iq1 > 0 || iq2 > 0) {
    const v = iq1 > 0 ? (t < 8.3 ? 3 : 2) : Math.round(kf(t, [[42.85, 2], [44.5, -1, E.lin]]));
    hudMeter(c, 1, 'IQ ДРУГА', String(v), Math.max(0.02, v / 100), '#3ec1ff', Math.max(iq1, iq2),
      { t, flash: Math.max(pulse(t, 8.3, .4), pulse(t, 44.5, .4)), shake: v < 0 ? 5 : 0, glitch: v < 0 ? .7 : 0, valCol: v < 0 ? '#ff2a3d' : '#3ec1ff' });
  }
  // chance to survive during the chase
  const ch = inv(27.45, 27.7, t) * (1 - inv(33.25, 33.4, t));
  if (ch > 0) {
    const v = Math.round(kf(t, [[27.6, 34], [29.6, 12, E.out], [31.34, 12], [31.6, 1, E.out]]));
    hudMeter(c, 1, 'ШАНС ВЫЖИТЬ', v + '%', v / 100, '#7dffb0', ch, { t, flash: pulse(t, 31.4, .4), shake: v < 3 ? 6 : 0, valCol: v < 10 ? '#ff2a3d' : '#7dffb0' });
  }
  // awkwardness during the photo request
  const aw = inv(49.0, 49.25, t) * (1 - inv(59.4, 59.55, t));
  if (aw > 0) {
    const v = Math.round(kf(t, [[49.2, 10], [51.9, 40, E.out], [53.6, 70, E.out], [57.6, 70], [58.0, 100, E.out], [58.3, 9999, E.out]]));
    hudMeter(c, 0, 'НЕЛОВКОСТЬ', v > 100 ? v + '%' : v + '%', v / 100, '#ff5cc8', aw,
      { t, flash: Math.max(pulse(t, 51.9, .4), pulse(t, 53.6, .4), pulse(t, 58.0, .4)), shake: v > 100 ? 7 : 0, glitch: v > 100 ? 1 : 0 });
  }
}

// ---------------------------------------------------------------- subtitles (karaoke, speaker tags for quotes)
const SUBS = (() => {
  const chunks = []; let cur = null;
  WD.forEach((w, i) => {
    if (w.sc === 18) return;      // the last line becomes the big final card
    const prev = WD[i - 1];
    const brk = !cur || cur.words.length >= 3 || (cur.text + ' ' + w.w).length > 18 ||
      (prev && /[.!?:]$/.test(prev.w)) || (prev && /,$/.test(prev.w) && cur.words.length >= 2) ||
      (prev && prev.sp !== w.sp) || (prev && w.s - prev.e > 0.35);
    if (brk) { cur = { words: [], text: '', sp: w.sp }; chunks.push(cur); }
    cur.words.push(i); cur.text = (cur.text + ' ' + w.w).trim();
  });
  chunks.forEach(ch => { ch.a = WS(ch.words[0]) - 0.06; });
  chunks.forEach((ch, k) => { const next = chunks[k + 1]; ch.b = Math.min(next ? next.a : 1e9, WE(ch.words[ch.words.length - 1]) + 0.5); });
  return chunks;
})();
const SUB_COL = { n: '#ffe14d', s: '#ff6b7f', i: '#ffd23f' };
const SUB_TAG = { s: ['Я', '#ee3b4f'], i: ['ДРУГ', '#2f6fe0'] };
function drawSubs(c, t, y = 1440) {
  const ch = SUBS.find(s => t >= s.a && t < s.b);
  if (!ch) return;
  const age = t - ch.a, loud = ch.sp !== 'n', px = loud ? 92 : 84;
  c.save();
  c.font = font(px);
  const words = ch.words.map(i => WD[i].w.toUpperCase());
  const space = px * 0.46, widths = words.map(w => c.measureText(w).width);
  let lines = [[0, words.length]];
  const total = widths.reduce((a, b) => a + b, 0) + space * (words.length - 1);
  if (total > 940 && words.length > 1) { const m = Math.ceil(words.length / 2); lines = [[0, m], [m, words.length]]; }
  const sc = lerp(0.7, 1, E.back(clamp(age / 0.16))) * Math.min(1, 980 / Math.max(...lines.map(([a, b]) => widths.slice(a, b).reduce((x, y) => x + y, 0) + space * (b - a - 1))));
  c.translate(W / 2, y); c.scale(sc, sc);
  if (SUB_TAG[ch.sp]) {
    const [tag, col] = SUB_TAG[ch.sp];
    const ty = -(lines.length * px * 1.12) / 2 - 74;
    c.font = font(36); const tw = Math.max(120, c.measureText(tag).width + 70);
    rrect(c, -tw / 2, ty - 30, tw, 60, 30); fillStroke(c, col, 6);
    text(c, tag, 0, ty + 2, 36, '#fff', { stroke: 6 });
  }
  lines.forEach(([a, b], li) => {
    const lw = widths.slice(a, b).reduce((x, y) => x + y, 0) + space * (b - a - 1);
    let x = -lw / 2;
    const ly = (li - (lines.length - 1) / 2) * px * 1.12;
    for (let k = a; k < b; k++) {
      const wi = ch.words[k], wd = WD[wi];
      const active = t >= wd.s - 0.03 && t < wd.e + 0.05;
      const pop = active ? 1 + 0.1 * bump(t, wd.s - 0.03, Math.min(wd.e, wd.s + 0.25)) + 0.04 : 1;
      const jit = ch.sp === 'i' && /!/.test(wd.w) ? shake(t, 5, 30, wi) : [0, 0];
      c.save(); c.translate(x + widths[k] / 2 + jit[0], ly + jit[1]); c.scale(pop, pop); c.rotate(active ? -0.03 : 0);
      text(c, words[k], 0, 0, px, active ? SUB_COL[ch.sp] : '#fff', { stroke: px * 0.24, shadow: 'rgba(0,0,0,0.55)' });
      c.restore();
      x += widths[k] + space;
    }
  });
  c.restore();
}

// ---------------------------------------------------------------- graphic gags
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
// big comic onomatopoeia with a spiky burst behind
function boom(c, txt, x, y, px, col, appear, rot = -0.1, burst = '#fff') {
  if (appear <= 0) return;
  const s = E.back(clamp(appear)) * (1 + 0.04 * Math.sin(appear * 40));
  c.save(); c.translate(x, y); c.scale(s, s); c.rotate(rot);
  if (burst) {
    c.font = font(px); const w = c.measureText(txt).width * .62 + px * .6, h = px * 1.15;
    c.beginPath();
    for (let i = 0; i < 28; i++) { const a = i / 28 * TAU, r = i % 2 ? 0.78 : 1.12 + 0.15 * hash(i + px); c.lineTo(Math.cos(a) * w * r, Math.sin(a) * h * r); }
    c.closePath(); fillStroke(c, burst, 8);
  }
  text(c, txt, 0, 0, px, col, { stroke: px * 0.22, shadow: 'rgba(0,0,0,0.4)' });
  c.restore();
}
function bubble(c, x, y, w, h, tail, appear, fn, o = {}) {
  if (appear <= 0) return;
  const s = E.back(clamp(appear));
  c.save(); c.translate(x, y); c.scale(s, s); c.rotate(o.rot || 0);
  rrect(c, -w / 2, -h / 2, w, h, 40); fillStroke(c, o.fill || '#fff', 8);
  c.beginPath(); c.moveTo(tail[0] - 30, h / 2 - 4); c.lineTo(tail[1], tail[2]); c.lineTo(tail[0] + 30, h / 2 - 4);
  c.closePath(); c.fillStyle = o.fill || '#fff'; c.fill(); c.lineWidth = 8; c.strokeStyle = INK; c.stroke();
  c.fillStyle = o.fill || '#fff'; c.fillRect(tail[0] - 26, h / 2 - 14, 52, 14);
  fn(c);
  c.restore();
}
function pip(c, t, cx, cy, r, appear, fn, bg = ['#ffd6e6', '#ffc2d8'], ring = '#fff') {
  if (appear <= 0) return;
  const s = E.back(clamp(appear));
  c.save(); c.translate(cx, cy); c.scale(s, s); c.rotate(-0.06);
  circle(c, 8, 12, r + 12, 'rgba(0,0,0,0.4)', 0);
  circle(c, 0, 0, r + 12, ring, 0);
  c.beginPath(); c.arc(0, 0, r, 0, TAU); c.save(); c.clip();
  sunburst(c, 0, 0, t, bg[0], bg[1], 14, 0.6);
  fn(c);
  c.restore();
  circle(c, 0, 0, r + 12, null, 7);
  c.restore();
}
// arrow label pointing at someone ("ДОЛБОЁБ")
function arrowLabel(c, txt, x, y, tx, ty, appear, col = '#e0233a') {
  if (appear <= 0) return;
  const s = E.back(clamp(appear)), wob = Math.sin(appear * 30) * 6;
  c.save(); c.globalAlpha = clamp(appear * 2);
  const ax = lerp(x, tx, .78) + wob, ay = lerp(y, ty, .78);
  limb(c, [x, y + 40, ax, ay], 16, '#fff', 6);
  const an = Math.atan2(ay - y - 40, ax - x);
  withT(c, ax, ay, 1, an, () => poly(c, [26, 0, -20, -30, -20, 30], '#fff', 6));
  c.restore();
  sticker(c, txt, x, y, 64, col, appear, -0.08, '#fff');
}
function spinner(c, x, y, r, t, appear) {      // "frozen" loading wheel above the scared friend
  if (appear <= 0) return;
  const s = E.back(clamp(appear));
  c.save(); c.translate(x, y); c.scale(s, s);
  circle(c, 0, 0, r + 26, 'rgba(20,14,40,0.85)', 6);
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * TAU + Math.floor(t * 12) / 12 * TAU, k = ((i + 12) % 12) / 12;
    c.save(); c.rotate(a); rrect(c, r * .45, -7, r * .5, 14, 7); c.fillStyle = `rgba(255,255,255,${0.2 + 0.8 * k})`; c.fill(); c.restore();
  }
  c.restore();
  sticker(c, 'НЕ ОТВЕЧАЕТ', x, y + r + 70, 40, '#e0233a', appear, 0.04);
}
function rotateIcon(c, cx, cy, appear, turn) {
  if (appear <= 0) return;
  const s = E.back(clamp(appear)) * 1.3;
  c.save(); c.translate(cx, cy); c.scale(s, s);
  circle(c, 0, 0, 130, 'rgba(255,255,255,0.92)', 7);
  c.save(); c.rotate(-Math.PI / 2 * E.back(clamp(turn)));
  rrect(c, -40, -70, 80, 140, 16); fillStroke(c, '#22222c', 6); rrect(c, -30, -56, 60, 104, 8); fillStroke(c, '#5ab4ff', 0);
  c.restore();
  c.beginPath(); c.arc(0, 0, 100, -2.6, -0.7); c.lineWidth = 16; c.strokeStyle = INK; c.lineCap = 'round'; c.stroke();
  c.lineWidth = 9; c.strokeStyle = '#ffd23f'; c.stroke();
  withT(c, Math.cos(-0.7) * 100, Math.sin(-0.7) * 100, 1, 0.9, () => poly(c, [0, -26, 26, 10, -22, 14], '#ffd23f', 6));
  c.restore();
}
function cameraUI(c, t, a = 1) {
  c.save(); c.globalAlpha = a;
  for (const [x, y, sx, sy] of [[90, 240, 1, 1], [990, 240, -1, 1], [90, 1700, 1, -1], [990, 1700, -1, -1]]) line(c, [x, y + sy * 100, x, y, x + sx * 100, y], 10, '#fff');
  circle(c, 90, 150, 14, Math.sin(t * 8) > 0 ? '#ff2a3d' : '#7a1020', 0);
  text(c, 'ФОТО', 130, 152, 34, '#fff', { stroke: 6, align: 'left' });
  circle(c, W / 2, 1780, 70, '#fff', 8); circle(c, W / 2, 1780, 54, null, 5);
  c.restore();
}
function finalCard(c, t) {
  // the last line of the narration as a big stacked card (word-by-word)
  const L = [[[1, 2], 1080, 96, '#fff'], [[3], 1192, 104, '#fff'], [[4, 5, 6], 1340, 80, '#fff'], [[7, 8], 1452, 96, '#ff6b7f'], [[9, 10], 1600, 128, '#ffe14d']];
  const a = inv(59.5, 59.9, t);
  c.save(); c.globalAlpha = a; c.fillStyle = vgrad(c, 940, H, [[0, 'rgba(18,10,40,0)'], [0.35, 'rgba(18,10,40,0.75)'], [1, 'rgba(18,10,40,0.92)']]); c.fillRect(0, 940, W, H - 940); c.restore();
  for (const [idx, y, px, col] of L) {
    c.font = font(px);
    const words = idx.map(i => WD[_WI['18:' + i]].w.toUpperCase());
    const ws_ = words.map(w => c.measureText(w).width), sp = px * .3, tw = ws_.reduce((p, q) => p + q, 0) + sp * (words.length - 1);
    const sc = Math.min(1, 1000 / tw);
    let x = W / 2 - tw * sc / 2;
    idx.forEach((i, k) => {
      const st = ws(18, i) - 0.04;
      if (t >= st) {
        const u = clamp((t - st) / 0.16);
        withT(c, x + ws_[k] * sc / 2, y, sc * lerp(1.5, 1, E.back(u)), -0.03, () => text(c, words[k], 0, 0, px, col, { stroke: px * 0.24, shadow: 'rgba(0,0,0,0.55)' }));
      }
      x += (ws_[k] + sp) * sc;
    });
  }
}
