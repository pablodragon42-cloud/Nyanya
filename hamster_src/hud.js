// Game-style HUD meters, title hook, Russian karaoke subtitles.

// ---------------------------------------------------------------- HUD meters
function hudMeter(c, slot, label, val, frac, col, appear, o = {}) {
  if (appear <= 0) return;
  const y = 176 + slot * 150, x = 70, w = W - 140, h = 128;
  const t = o.t || 0;
  c.save();
  const s = E.back(clamp(appear));
  const [sx, sy] = o.shake ? shake(t, o.shake, 30, slot * 10) : [0, 0];
  c.translate(W / 2 + sx, y + h / 2 + sy); c.scale(s, s); c.translate(-W / 2, -(y + h / 2));
  // panel
  rrect(c, x + 8, y + 10, w, h, 18); c.fillStyle = 'rgba(0,0,0,0.45)'; c.fill();
  rrect(c, x, y, w, h, 18); fillStroke(c, 'rgba(20,14,40,0.88)', 7, '#fff');
  // label
  text(c, label, x + 30, y + 36, 26, '#fff', { fam: 'Press', align: 'left', stroke: 0 });
  // value
  const g = o.glitch || 0;
  if (g > 0) {
    for (const [dx, cc] of [[-6, 'rgba(255,0,60,0.8)'], [6, 'rgba(0,220,255,0.8)']])
      text(c, val, x + w - 30 + dx * g * (1 + Math.sin(t * 90)), y + 38, 30, cc, { fam: 'Press', align: 'right', stroke: 0 });
  }
  text(c, val, x + w - 30, y + 38, 30, o.valCol || col, { fam: 'Press', align: 'right', stroke: 0 });
  // bar
  const bx = x + 30, by = y + 70, bw = w - 60, bh = 34;
  rrect(c, bx, by, bw, bh, 6); fillStroke(c, '#2a2342', 5, '#fff');
  const f = clamp(frac, 0, 1);
  if (f > 0) {
    c.save(); rrect(c, bx + 5, by + 5, (bw - 10) * f, bh - 10, 3); c.clip();
    c.fillStyle = col; c.fillRect(bx, by, bw, bh);
    // pixel segments
    c.fillStyle = 'rgba(0,0,0,0.25)';
    for (let i = bx + 5; i < bx + bw; i += 26) c.fillRect(i + 20, by, 6, bh);
    c.fillStyle = 'rgba(255,255,255,0.35)'; c.fillRect(bx, by + 5, bw, 7);
    c.restore();
  }
  if (o.icon) o.icon(c, x + w - 46, y - 6);
  if (o.flash) { rrect(c, x, y, w, h, 18); c.fillStyle = `rgba(255,255,255,${o.flash * .6})`; c.fill(); }
  c.restore();
}
function threatState(t) {
  // [time, percent]
  const K = [[9.45, 0], [9.62, 15, E.out], [12.6, 15], [12.9, 25, E.out], [15.7, 25], [16.0, 35, E.out],
    [20.9, 35], [22.6, 60, E.out], [25.4, 60], [26.4, 85, E.out], [29.1, 85], [29.5, 99, E.out], [37.6, 99], [37.85, 666, E.out]];
  return kf(t, K);
}
function drawHUD(c, t) {
  // threat level: from the cage door kick to the end of "Я тут главный"
  const ta = inv(9.45, 9.75, t) * (1 - inv(38.6, 38.85, t));
  if (ta > 0) {
    const v = threatState(t);
    const steps = [9.6, 12.85, 15.95, 22.6, 26.4, 29.45, 37.8];
    let fl = 0; steps.forEach(s => fl = Math.max(fl, pulse(t, s, 0.35)));
    const evil = t > 37.8;
    const col = v < 30 ? '#ffd23f' : v < 70 ? '#ff8a1f' : '#ff2a3d';
    hudMeter(c, 0, 'УРОВЕНЬ УГРОЗЫ', Math.round(v) + '%', v / 100, col, ta,
      { t, flash: fl, shake: fl * 10 + (evil ? 6 : 0), glitch: evil ? 1 : (v > 90 ? .4 : 0), valCol: evil ? '#ff2a3d' : col });
  }
  // hamster size: during the growth
  const sa = inv(20.95, 21.2, t) * (1 - inv(24.3, 24.55, t));
  if (sa > 0) {
    const g = kf(t, [[21.0, 0], [22.7, 1, E.in2]]);
    const cm = Math.round(lerp(12, 180, g));
    hudMeter(c, 1, 'РАЗМЕР ХОМЯКА', cm + ' СМ' + (g > .97 ? ' = ХОЛОДОС' : ''), g, '#3ec1ff', sa, {
      t, flash: pulse(t, 22.7, .4), shake: g > .95 ? 4 : 0, valCol: g > .97 ? '#7dffb0' : '#3ec1ff',
    });
  }
  // demon salary
  const da = inv(43.5, 43.75, t) * (1 - inv(46.0, 46.25, t));
  if (da > 0) {
    const n = t < 44.45 ? 0 : 1;
    hudMeter(c, 0, 'ЗАРПЛАТА ДЕМОНА', n ? '1 СЕМЕЧКА/МЕС' : '0 ₸', n ? 0.03 : 0, '#a3e635', da,
      { t, flash: Math.max(pulse(t, 44.45, .4), pulse(t, 45.1, .4)), shake: pulse(t, 45.1, .4) * 8 });
  }
  // rent debt
  const ra = inv(52.6, 52.85, t) * (1 - inv(56.1, 56.35, t));
  if (ra > 0) {
    const v = t < 55.0 ? Math.floor(lerp(0, 999999, inv(52.8, 55.0, t))) : -1;
    hudMeter(c, 0, 'ДОЛГ ЗА КВАРТИРУ', v < 0 ? '∞ ₸' : v.toLocaleString('ru-RU').replace(/ /g, ' ') + ' ₸', v < 0 ? 1 : v / 999999, '#ff2a3d', ra,
      { t, flash: pulse(t, 55.03, .4), shake: v < 0 ? 6 : 0, glitch: v < 0 ? .6 : 0 });
  }
}

// ---------------------------------------------------------------- title hook (first seconds)
function drawTitle(c, t) {
  const a = inv(0.0, 0.25, t) * (1 - inv(2.75, 3.0, t));
  if (a <= 0) return;
  c.save();
  const s = E.back(inv(0, .35, t));
  c.translate(W / 2, 250); c.scale(s, s); c.rotate(-0.025 + Math.sin(t * 3) * 0.01);
  c.globalAlpha = a;
  rrect(c, -480, -120, 960, 240, 30); fillStroke(c, '#fff', 8);
  text(c, 'Я КУПИЛ ХОМЯКА,', 0, -50, 70, INK, { stroke: 0 });
  text(c, 'А ОН ОКАЗАЛСЯ', 0, 18, 52, INK, { stroke: 0 });
  text(c, 'НАЧАЛЬНИКОМ АДА 🔥', 0, 80, 58, '#e0233a', { stroke: 0 });
  c.restore();
}

// ---------------------------------------------------------------- subtitles
const SUBS = (() => {
  const chunks = []; let cur = null;
  WD.forEach((w, i) => {
    const prev = WD[i - 1];
    const brk = !cur || cur.words.length >= 3 || (cur.text + ' ' + w.w).length > 18 ||
      (prev && /[.!?]$/.test(prev.w)) || (prev && /,$/.test(prev.w) && cur.words.length >= 2) ||
      (prev && prev.sp !== w.sp) || (prev && w.s - prev.e > 0.35);
    if (brk) { cur = { words: [], text: '', sp: w.sp }; chunks.push(cur); }
    cur.words.push(i); cur.text = (cur.text + ' ' + w.w).trim();
  });
  chunks.forEach(ch => { ch.a = WS(ch.words[0]) - 0.06; });
  chunks.forEach((ch, k) => {
    const next = chunks[k + 1];
    ch.b = Math.min(next ? next.a : 1e9, WE(ch.words[ch.words.length - 1]) + 0.5);
  });
  return chunks;
})();
const SUB_COL = { n: '#ffe14d', h: '#ffa53d', d: '#ff3b3b' };
const SUB_TAG = { h: ['ХОМЯК', '#f5a63f'], d: ['ДЕМОН', '#d6273b'] };
function drawSubs(c, t, y = 1440) {
  const ch = SUBS.find(s => t >= s.a && t < s.b);
  if (!ch) return;
  const age = t - ch.a, px = ch.sp === 'd' ? 92 : 84;
  c.save();
  c.font = font(px);
  const words = ch.words.map(i => WD[i].w.toUpperCase());
  const space = px * 0.46;
  const widths = words.map(w => c.measureText(w).width);
  // wrap to max 2 lines
  let lines = [[0, words.length]];
  const total = widths.reduce((a, b) => a + b, 0) + space * (words.length - 1);
  if (total > 940 && words.length > 1) { const m = Math.ceil(words.length / 2); lines = [[0, m], [m, words.length]]; }
  const sc = lerp(0.7, 1, E.back(clamp(age / 0.16)));
  c.translate(W / 2, y); c.scale(sc, sc);
  // speaker tag
  if (SUB_TAG[ch.sp]) {
    const [tag, col] = SUB_TAG[ch.sp];
    const ty = -(lines.length * px * 1.12) / 2 - 74;
    rrect(c, -110, ty - 30, 220, 60, 30); fillStroke(c, col, 6);
    text(c, tag, 0, ty + 2, 36, '#fff', { stroke: 6 });
  }
  lines.forEach(([a, b], li) => {
    const lw = widths.slice(a, b).reduce((x, y) => x + y, 0) + space * (b - a - 1);
    let x = -lw / 2;
    const ly = (li - (lines.length - 1) / 2) * px * 1.12;
    for (let k = a; k < b; k++) {
      const wi = ch.words[k], wd = WD[wi];
      const active = t >= wd.s - 0.03 && t < wd.e + 0.05;
      const done = t >= wd.e;
      const pop = active ? 1 + 0.1 * bump(t, wd.s - 0.03, Math.min(wd.e, wd.s + 0.25)) + 0.04 : 1;
      const jit = ch.sp === 'd' ? shake(t, 5, 30, wi) : [0, 0];
      c.save(); c.translate(x + widths[k] / 2 + jit[0], ly + jit[1]); c.scale(pop, pop); c.rotate(active ? -0.03 : 0);
      text(c, words[k], 0, 0, px, active ? SUB_COL[ch.sp] : '#fff', { stroke: px * 0.24, shadow: 'rgba(0,0,0,0.55)' });
      c.restore();
      x += widths[k] + space;
    }
  });
  c.restore();
}
