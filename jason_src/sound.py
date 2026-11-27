# Procedural horror-comedy score + sound effects, mixed under the narration.
# Everything is synthesized here (no samples). Output: build/mix.wav (stereo, 44.1 kHz).
import json, os, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve, lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("BUILD", os.path.join(HERE, "build"))
SR = 44100
TL = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
DUR = TL["duration"]
N = int(SR * DUR)
rng = np.random.default_rng(13)


def ws(sc, i):
    return next(w["s"] for w in TL["words"] if w["scene"] == sc and w["i"] == i)


def we(sc, i):
    return next(w["e"] for w in TL["words"] if w["scene"] == sc and w["i"] == i)


# ------------------------------------------------------------------ buses
class Bus:
    def __init__(self):
        self.L = np.zeros(N); self.R = np.zeros(N)

    def add(self, sig, start, gain=1.0, pan=0.0):
        i0 = int(start * SR)
        if i0 >= N or len(sig) == 0: return
        if i0 < 0:
            sig = sig[-i0:]; i0 = 0
        sig = sig[:N - i0]
        gl, gr = np.sqrt((1 - pan) / 2) * 1.414, np.sqrt((1 + pan) / 2) * 1.414
        self.L[i0:i0 + len(sig)] += sig * gain * gl
        self.R[i0:i0 + len(sig)] += sig * gain * gr


MUS, SFX, AMB = Bus(), Bus(), Bus()


# ------------------------------------------------------------------ dsp helpers
def tt(d): return np.arange(int(d * SR)) / SR


def flt(x, kind, f, order=2):
    if kind == "bp":
        sos = butter(order, [max(20, f[0]), min(SR / 2 - 100, f[1])], "bandpass", fs=SR, output="sos")
    else:
        sos = butter(order, min(f, SR / 2 - 100), kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def env(n, a=0.005, r=0.1, hold=None):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def expdec(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def noise(d):
    return rng.standard_normal(int(d * SR))


def brown(d):
    x = np.cumsum(rng.standard_normal(int(d * SR)))
    x = flt(x, "highpass", 20)
    return x / (np.abs(x).max() + 1e-9)


def saw(f, d, ph=0.0):
    t = tt(d)
    if np.isscalar(f):
        x = (t * f + ph) % 1.0
    else:
        x = (np.cumsum(f) / SR + ph) % 1.0
    return 2 * x - 1


def sine(f, d, ph=0.0):
    t = tt(d)
    if np.isscalar(f):
        return np.sin(2 * np.pi * f * t + ph)
    return np.sin(2 * np.pi * np.cumsum(f) / SR + ph)


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


def midi(m): return 440.0 * 2 ** ((m - 69) / 12)


def karplus(f, d, decay=0.996, bright=0.5):
    n = int(d * SR)
    P = max(2, int(SR / f))
    exc = np.zeros(n)
    burst = rng.uniform(-1, 1, P)
    burst = flt(burst, "lowpass", 1500 + 6000 * bright)
    exc[:P] = burst
    a = np.zeros(P + 2); a[0] = 1; a[P] = -decay * .5; a[P + 1] = -decay * .5
    return lfilter([1.0], a, exc)


def reverb(x, secs=1.6, damp=3000, mix=0.3):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (secs / 5))
    ir = flt(ir, "lowpass", damp)
    ir /= np.sqrt((ir ** 2).sum())
    wet = fftconvolve(x, ir)[:len(x)]
    return x * (1 - mix) + wet * mix * 1.6


# ------------------------------------------------------------------ instruments / sfx
def pluck(m, d=1.2, g=1.0, bright=0.5):
    return karplus(midi(m), d, 0.997, bright) * g * env(int(d * SR), 0.002, 0.15)


def strum(notes, d=1.6, spread=0.018, g=1.0):
    out = np.zeros(int((d + spread * len(notes)) * SR))
    for i, m in enumerate(notes):
        s = pluck(m, d, 1.0)
        i0 = int(i * spread * SR)
        out[i0:i0 + len(s)] += s
    return norm(out, g)


def pizz(m, g=1.0):
    d = 0.35
    s = karplus(midi(m), d, 0.985, 0.3) * env(int(d * SR), 0.001, 0.08)
    return norm(s, g)


def drone(d, notes=(26, 33, 38), g=1.0):
    t = tt(d)
    out = np.zeros(len(t))
    for i, m in enumerate(notes):
        f = midi(m)
        for det in (-0.25, 0.25):
            out += saw(f * 2 ** (det / 12), d, rng.random())
        out += sine(f / 2, d) * 1.5
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)
    out = flt(out, "lowpass", 300) * (0.75 + 0.25 * lfo)
    return norm(out, g) * env(len(t), 1.2, 1.5)


def high_tension(d, g=1.0):
    t = tt(d)
    out = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * (1 + .3 * np.sin(2 * np.pi * 5.5 * t + i))
              for i, f in enumerate((1318, 1396, 1480)))
    return norm(flt(out, "bp", (900, 3000)), g) * env(len(t), 0.8, 0.8)


def braam(d=2.6, g=1.0, root=26):
    t = tt(d)
    out = np.zeros(len(t))
    for m in (root, root + 12, root + 19, root + 24):
        for det in (-.3, 0, .3):
            out += saw(midi(m) * 2 ** (det / 12), d)
    cut = 200 + 1800 * np.exp(-t / 0.35)
    # time-varying lowpass approximated by blending two filtered copies
    lo, hi = flt(out, "lowpass", 220), flt(out, "lowpass", 2000)
    k = np.clip((cut - 200) / 1800, 0, 1)
    out = lo * (1 - k) + hi * k
    out += sine(midi(root) / 2, d) * 3 * np.exp(-t / 1.2)
    return norm(out, g) * env(len(t), 0.02, 1.2) * np.exp(-t / 1.6)


def screech(d=0.7, g=1.0):
    t = tt(d)
    out = sum(saw(f * (1 + 0.004 * np.sin(2 * np.pi * 7 * t + i)), d) for i, f in enumerate((1180, 1250, 1330, 1410)))
    out = flt(out, "bp", (900, 5000)) * (1 + 0.6 * np.sin(2 * np.pi * 18 * t))
    return norm(out, g) * env(len(t), 0.01, 0.35)


def hit(g=1.0, f0=70, d=1.0):
    t = tt(d)
    f = f0 * np.exp(-t * 3) + 28
    s = sine(f, d) * np.exp(-t / 0.35)
    nz = flt(noise(d), "lowpass", 1800) * np.exp(-t / 0.05)
    return norm(s * 1.4 + nz * .6, g)


def thunder(g=1.0, d=3.5):
    t = tt(d)
    crack = flt(noise(d), "bp", (800, 6000)) * np.exp(-t / 0.08)
    rumble = flt(brown(d), "lowpass", 260) * (np.exp(-t / 1.2) * (1 + .5 * np.sin(2 * np.pi * 1.7 * t) ** 2))
    return norm(crack * .7 + rumble * 2, g) * env(len(t), 0.003, 0.8)


def heartbeat(g=1.0):
    d = 0.5
    t = tt(d)
    def thump(dd, f):
        tt_ = tt(dd)
        return sine(f * np.exp(-tt_ * 8) + 35, dd) * np.exp(-tt_ / 0.07)
    out = np.zeros(len(t))
    a = thump(0.25, 60); b = thump(0.25, 50)
    out[:len(a)] += a
    i = int(0.16 * SR); out[i:i + len(b)] += b * .7
    return norm(flt(out, "lowpass", 160), g)


def whoosh(d=0.35, g=1.0, up=True):
    t = tt(d)
    nz = noise(d)
    lo = flt(nz, "bp", (300, 1200)); hi = flt(nz, "bp", (1500, 6000))
    k = t / d if up else 1 - t / d
    out = lo * (1 - k) + hi * k
    return norm(out * np.sin(np.pi * t / d) ** 2, g)


def glitch_sfx(g=1.0, d=0.2):
    x = noise(d)
    x = np.round(x * 3) / 3
    x = flt(x, "bp", (600, 5000)) * (np.sign(np.sin(2 * np.pi * 60 * tt(d))) > 0)
    return norm(x, g) * env(len(x), 0.002, 0.05)


def wood_bang(g=1.0, d=0.5, f=(260, 700, 1500)):
    t = tt(d)
    exc = noise(d) * np.exp(-t / 0.012)
    out = sum(flt(exc, "bp", (fr * .85, fr * 1.15), 2) * w for fr, w in zip(f, (1.0, .7, .4)))
    out += sine(90 * np.exp(-t * 6) + 50, d) * np.exp(-t / 0.08)
    return norm(out, g)


def creak(d=0.6, g=1.0, f0=160):
    t = tt(d)
    f = f0 * (1 + 0.25 * np.sin(2 * np.pi * 1.3 * t)) * (1 + 0.04 * rng.standard_normal(len(t)).cumsum() / 300)
    x = saw(np.abs(f), d)
    x = (np.abs(np.sin(2 * np.pi * 34 * t)) ** 6) * x
    out = flt(x, "bp", (300, 1400)) + flt(x, "bp", (1800, 2600)) * .4
    return norm(out, g) * env(len(t), 0.03, 0.15)


def shutter(g=1.0):
    d = 0.16
    out = np.zeros(int(d * SR))
    for k0, amp in ((0.0, 1.0), (0.055, 0.8)):
        c = flt(noise(0.006), "highpass", 2500) * amp
        i = int(k0 * SR)
        out[i:i + len(c)] += c
    out += flt(noise(d), "bp", (1500, 4000)) * np.exp(-tt(d) / 0.03) * .3
    return norm(out, g)


def flash_whine(d=0.7, g=1.0):
    t = tt(d)
    f = 900 + 5200 * (t / d) ** 1.4
    return norm(sine(f, d) * env(len(t), 0.05, 0.05), g)


def record_scratch(g=1.0):
    d = 0.42
    t = tt(d)
    rate = 1 + 1.6 * np.sin(2 * np.pi * 7.5 * t) * np.exp(-t / 0.3)
    x = saw(220 * np.abs(rate) + 40, d) + noise(d) * .5
    x = flt(x, "bp", (500, 3500)) * np.abs(np.sin(2 * np.pi * 7.5 * t))
    return norm(x, g) * env(len(t), 0.003, 0.08)


def slap(g=1.0):
    d = 0.2
    t = tt(d)
    x = flt(noise(d), "bp", (900, 5000)) * np.exp(-t / 0.018) + sine(140 * np.exp(-t * 20) + 60, d) * np.exp(-t / 0.04) * .7
    return norm(x, g)


def ding(f=1568, g=1.0, d=1.4):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * r * t) * a * np.exp(-t / (0.9 / r ** .7)) for r, a in ((1, 1), (2.76, .5), (5.4, .25), (8.9, .1)))
    return norm(x, g) * env(len(t), 0.001, 0.2)


def pling(g=1.0):
    a = ding(1046, 1.0, 0.6); b = ding(1568, 1.0, 1.0)
    out = np.zeros(int(1.2 * SR))
    out[:len(a)] += a
    i = int(0.09 * SR); out[i:i + len(b)] += b
    return norm(out, g)


def crickets(d, g=1.0, rate=2.2, f=4600, seed=0):
    t = tt(d)
    r = np.random.default_rng(seed)
    gate = (np.sin(2 * np.pi * 30 * t) > 0.2) * ((t * rate + r.random()) % 1 < 0.28)
    x = np.sin(2 * np.pi * f * t) * gate
    return norm(flt(x, "bp", (3500, 6000)), g)


def wind(d, g=1.0, seed=0):
    t = tt(d)
    x = flt(noise(d), "bp", (180, 900))
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t + seed) * np.sin(2 * np.pi * 0.047 * t + seed * 2)
    return norm(x * lfo, g)


def campfire(d, g=1.0):
    t = tt(d)
    base = flt(noise(d), "lowpass", 500) * .25
    pops = np.zeros(len(t))
    for _ in range(int(d * 14)):
        i = rng.integers(0, len(t) - 800)
        c = flt(noise(0.012), "highpass", 1500) * rng.uniform(.3, 1)
        pops[i:i + len(c)] += c
    return norm(base + pops, g)


def birds_chirp(d, g=1.0):
    out = np.zeros(int(d * SR))
    for _ in range(int(d * 2.5)):
        i = rng.integers(0, len(out) - SR // 2)
        dd = rng.uniform(.05, .12)
        tt_ = tt(dd)
        f = rng.uniform(2500, 4200) * (1 + 0.4 * np.sin(2 * np.pi * rng.uniform(8, 20) * tt_))
        c = sine(f, dd) * np.sin(np.pi * tt_ / dd)
        out[i:i + len(c)] += c * rng.uniform(.3, 1)
    return norm(out, g)


def owl(g=1.0):
    out = np.zeros(int(1.6 * SR))
    for k0, dd, f in ((0, .35, 400), (.5, .7, 380)):
        tt_ = tt(dd)
        c = sine(f * (1 + .02 * np.sin(2 * np.pi * 6 * tt_)), dd) * np.sin(np.pi * tt_ / dd) ** 1.5
        c += flt(noise(dd), "bp", (300, 600)) * .1 * np.sin(np.pi * tt_ / dd)
        i = int(k0 * SR); out[i:i + len(c)] += c
    return norm(out, g)


def step_heavy(g=1.0):
    d = 0.35
    t = tt(d)
    x = sine(70 * np.exp(-t * 10) + 40, d) * np.exp(-t / 0.07) + flt(noise(d), "bp", (200, 1800)) * np.exp(-t / 0.05) * .5
    return norm(x, g)


def step_run(g=1.0):
    d = 0.12
    t = tt(d)
    x = flt(noise(d), "bp", (500, 4000)) * np.exp(-t / 0.03) + sine(110 * np.exp(-t * 18) + 60, d) * np.exp(-t / 0.03) * .5
    return norm(x, g)


def breath_heavy(g=1.0):
    d = 1.4
    t = tt(d)
    x = flt(noise(d), "bp", (250, 1100))
    e = np.sin(np.pi * np.clip(t / .6, 0, 1)) ** 2 * (t < .6) + .7 * np.sin(np.pi * np.clip((t - .7) / .7, 0, 1)) ** 2 * (t >= .7)
    return norm(x * e, g)


def sneeze(g=1.0):
    """cartoon 'a-a-APCHHI!': two rising breathy inhales, then a sharp ch-burst into a voiced 'ee'"""
    out = np.zeros(int(1.3 * SR))
    for k0, dd, f0 in ((0.0, .26, 700), (0.36, .3, 900)):
        tt_ = tt(dd)
        src = saw(150 + 60 * tt_ / dd, dd) * .35 + noise(dd) * .8
        v = flt(src, "bp", (f0, f0 * 1.6)) + flt(src, "bp", (f0 * 1.8, f0 * 2.6)) * .5
        i = int(k0 * SR); out[i:i + len(v)] += v * np.sin(np.pi * tt_ / dd) * (.5 + .5 * tt_ / dd)
    k = 0.78
    ch = flt(noise(0.09), "bp", (2200, 6500)) * np.exp(-tt(0.09) / 0.03) * 2.5
    i = int(k * SR); out[i:i + len(ch)] += ch
    dd = .34
    tt_ = tt(dd)
    src = saw(260 * np.exp(-tt_ * 1.2), dd) + noise(dd) * .4
    vowel = flt(src, "bp", (250, 420)) + flt(src, "bp", (2000, 2900)) * .6
    i = int((k + .05) * SR); out[i:i + len(vowel)] += vowel * np.exp(-tt_ / .12) * 1.6
    return norm(out, g)


def wings(g=1.0, d=1.6):
    out = np.zeros(int(d * SR))
    for _ in range(26):
        i = rng.integers(0, int((d - .2) * SR))
        c = flt(noise(0.06), "bp", (200, 1200)) * np.sin(np.pi * tt(0.06) / 0.06)
        out[i:i + len(c)] += c * rng.uniform(.4, 1)
    for k0 in (0.1, 0.45, 0.9):
        dd = .3
        tt_ = tt(dd)
        src = saw(720 * (1 - .25 * tt_ / dd), dd) + noise(dd) * .3
        caw = flt(src, "bp", (900, 2200)) * np.sin(np.pi * tt_ / dd) ** .6
        i = int(k0 * SR); out[i:i + len(caw)] += caw * .9
    return norm(out, g)


def boop(g=1.0, f=880):
    d = .12
    t = tt(d)
    return norm(sine(f * (1 + .5 * (t < .05)), d) * env(len(t), .002, .05), g)


def tape_stop(x, d=0.35):
    n = len(x)
    nd = int(d * SR)
    rate = np.linspace(1, 0, nd) ** 1.5
    pos = np.cumsum(rate)
    seg_ = np.interp(pos, np.arange(n), x)
    return seg_


def sad_trombone(g=1.0):
    notes = [(70, .21), (69, .21), (68, .21), (67, .8)]
    out = np.zeros(int(2.4 * SR))
    k0 = 0.0
    for i, (m, dd) in enumerate(notes):
        tt_ = tt(dd)
        f = midi(m - 12) * (1 + (0.012 * np.sin(2 * np.pi * 5.5 * tt_) * (tt_ > .25) if i == 3 else 0))
        x = saw(f, dd) * .6 + saw(f * 1.005, dd) * .4
        wah = np.clip(np.sin(np.pi * np.minimum(tt_ / dd, 1)) * 1.2, 0, 1)
        lo, hi = flt(x, "lowpass", 400), flt(x, "lowpass", 2200)
        v = lo * (1 - wah) + hi * wah
        v *= env(len(tt_), .03, .08)
        j = int(k0 * SR); out[j:j + len(v)] += v
        k0 += dd + .03
    return norm(out, g)


def sad_melody(g=1.0):
    # soft "aww" violin line
    out = np.zeros(int(2.0 * SR))
    k0 = 0
    for m, dd in ((76, .45), (74, .45), (72, .9)):
        tt_ = tt(dd)
        f = midi(m) * (1 + .006 * np.sin(2 * np.pi * 5.5 * tt_))
        x = saw(f, dd) * .5 + sine(f, dd)
        x = flt(x, "lowpass", 2500) * env(len(tt_), .12, .2)
        j = int(k0 * SR); out[j:j + len(x)] += x
        k0 += dd
    return norm(out, g)


def taiko(g=1.0):
    d = .5
    t = tt(d)
    x = sine(90 * np.exp(-t * 9) + 45, d) * np.exp(-t / .16) + flt(noise(d), "bp", (100, 900)) * np.exp(-t / .03) * .4
    return norm(x, g)


# ------------------------------------------------------------------ the arrangement
def arrange():
    t_poka = ws(2, 4); t_jas = ws(2, 10); t_vur = ws(2, 11)
    # ---- cozy opening (dusk) with tape-stop at "пока"
    cozy = np.zeros(int((t_poka + .05) * SR) + SR)
    prog = [[55, 59, 62, 67], [50, 57, 62, 66], [52, 55, 59, 64], [48, 55, 60, 64]]
    beat = 0.47
    tcur = 0.05
    bi = 0
    while tcur < t_poka + .05:
        ch = prog[(bi // 2) % 4]
        for j, m in enumerate((ch[0], ch[2], ch[1], ch[3]) if bi % 2 == 0 else (ch[3], ch[1], ch[2], ch[0] + 12)):
            s = pluck(m, 1.1, .8, .55)
            i = int((tcur + j * beat / 2) * SR)
            if i < len(cozy):
                cozy[i:i + len(s)] += s[:len(cozy) - i]
        tcur += beat * 2
        bi += 1
    cut = int(t_poka * SR)
    tail = tape_stop(cozy[cut:cut + int(.6 * SR)], 0.4)
    cozy = np.concatenate([cozy[:cut], tail])
    cozy = reverb(cozy, 1.2, 3500, .25)
    MUS.add(norm(cozy, .5), 0)
    AMB.add(campfire(t_poka + .4, .22) * env(int((t_poka + .4) * SR), .3, .4), 0, pan=.1)
    AMB.add(birds_chirp(t_poka, .12), 0, pan=-.4)
    # ---- night ambience for the rest of the film
    night0 = t_poka + .15
    AMB.add(wind(DUR - night0, .22, 1) * env(int((DUR - night0) * SR), 1.0, 1.0), night0, pan=-.2)
    AMB.add(wind(DUR - night0, .16, 2) * env(int((DUR - night0) * SR), 1.0, 1.0), night0, pan=.3)
    AMB.add(crickets(DUR - night0, .05, 2.3, 4600, 1), night0, pan=.5)
    AMB.add(crickets(DUR - night0, .04, 1.7, 5100, 2), night0, pan=-.5)
    # ---- Jason arrives
    MUS.add(drone(9.0, g=.45), night0)
    for k, tb in enumerate(np.arange(night0 + .4, t_jas, 0.62)):
        SFX.add(heartbeat(.55 + .1 * k), tb)
    SFX.add(thunder(.62), t_jas - .02)
    MUS.add(braam(3.0, .7), t_jas)
    SFX.add(whoosh(.3, .35), t_vur - .15)
    MUS.add(screech(.8, .5), t_vur)
    SFX.add(hit(.6), t_vur)
    # ---- the wave: an ironic happy strum
    SFX.add(whoosh(.3, .35), 7.36 - .15)
    MUS.add(strum([55, 59, 62, 67, 71], 1.5, .02, .38), ws(3, 4) - .05, pan=.3)
    SFX.add(boop(.18, 1320), ws(3, 5))
    # ---- interior: clock ticks + pizzicato tension
    SFX.add(whoosh(.3, .35), 9.6 - .15)
    for k, tb in enumerate(np.arange(9.7, 13.25, 0.5)):
        SFX.add(flt(noise(.015), "bp", (2000, 5000)) * .5 * (1 if k % 2 else .7), tb, .16, pan=.4)
    for k, tb in enumerate(np.arange(9.75, 13.2, 0.25)):
        m = [45, 48, 45, 52, 45, 48, 51, 50][k % 8]
        MUS.add(pizz(m, .32), tb, pan=-.2)
    MUS.add(drone(4.0, (21, 28, 33), .3), 9.6)
    # ---- "гений" + the window
    SFX.add(hit(.3, 60, .6), 13.3)
    SFX.add(ding(2093, .32), ws(5, 3) + .05, pan=.2)
    SFX.add(whoosh(.3, .35), 14.54 - .15)
    t_rasp = ws(5, 4)
    SFX.add(wood_bang(.9), t_rasp, pan=-.2)
    SFX.add(wood_bang(.7, .4, (320, 900, 1700)), t_rasp + .05, pan=.25)
    SFX.add(creak(.5, .3, 180), t_rasp + .1)
    SFX.add(whoosh(.6, .4, False), t_rasp)
    # Jason stares; awkward crickets; facepalm slap
    SFX.add(glitch_sfx(.35), 17.57 - .05)
    t_end5 = we(5, 14)
    AMB.add(crickets(1.1, .32, 3.0, 4400, 5), t_end5 + .05, pan=.2)
    SFX.add(slap(.45), t_end5 + .2)
    # ---- the flash montage
    SFX.add(hit(.3, 60, .6), 20.05)
    for k, tb in enumerate(np.arange(20.15, 21.7, 0.24)):
        MUS.add(pizz([57, 60, 64, 60][k % 4], .25), tb, pan=.2)
    SFX.add(whoosh(.3, .35), 21.73 - .15)
    t_no = ws(6, 5)
    SFX.add(flash_whine(.7, .12), t_no + .05, pan=.3)
    SFX.add(boop(.25, 1760), t_no + .35)
    flashes = [22.85, 23.2, 23.45, 24.05, 24.35, 24.62, ws(6, 13) + .05]
    for k, f in enumerate(flashes):
        SFX.add(shutter(.55), f - .01, pan=.15 * (-1) ** k)
        SFX.add(flt(noise(.25), "highpass", 3000) * np.exp(-tt(.25) / .06) * .2, f)
    MUS.add(drone(3.6, (26, 32, 38), .35), 22.6)
    SFX.add(hit(.55), 23.35); SFX.add(hit(.65), 24.55)
    MUS.add(screech(.5, .35), 24.55)
    SFX.add(ding(1318, .28, 1.6), ws(6, 13) + .12)
    # ---- the chase
    SFX.add(glitch_sfx(.35), 25.9 - .05)
    t_vyb = ws(7, 2)
    SFX.add(wood_bang(1.0, .6, (180, 520, 1200)), t_vyb - .06)
    t_ost = ws(9, 3)
    bpm = 168
    step = 60 / bpm / 2
    tb = t_vyb + .1
    k = 0
    chase = np.zeros(int((t_ost - t_vyb + 1) * SR))
    while tb < t_ost:
        i = int((tb - t_vyb) * SR)
        if k % 4 == 0 or k % 8 == 6:
            s = taiko(1.0); chase[i:i + len(s)] += s[:len(chase) - i]
        m = [38, 38, 41, 38, 43, 38, 41, 36][k % 8]
        v = saw(midi(m), .12) * env(int(.12 * SR), .003, .05)
        v = flt(v, "lowpass", 900)
        chase[i:i + len(v)] += v[:len(chase) - i] * .35
        tb += step
        k += 1
    MUS.add(norm(chase, .6), t_vyb)
    for k, tb in enumerate(np.arange(t_vyb + .2, t_ost, 0.19)):
        SFX.add(step_run(.18), tb, pan=.2 * (-1) ** k)
    SFX.add(whoosh(.3, .35), 27.43 - .15)
    SFX.add(hit(.35, 60, .6), 28.85)
    SFX.add(whoosh(.3, .35), 30.9 - .15)
    # ---- record scratch: he stopped to tie his laces
    SFX.add(record_scratch(.75), t_ost - .05)
    AMB.add(crickets(2.0, .28, 3.2, 4500, 7), t_ost + .3, pan=-.2)
    for k, tb in enumerate(np.arange(ws(9, 4) + .05, 33.3, 0.45)):
        SFX.add(pizz(72 + (k % 2) * 3, .22), tb, pan=.2)
    for tb in np.arange(31.7, 33.35, 0.62):
        SFX.add(step_heavy(.45), tb, pan=.2)
    SFX.add(hit(.35, 60, .6), 32.40)
    # ---- hiding behind the tree
    SFX.add(whoosh(.3, .35), 33.35 - .15)
    MUS.add(drone(3.4, (26, 33, 39), .4), 33.35)
    hb = 33.5
    gap = .7
    while hb < 36.6:
        SFX.add(heartbeat(.6), hb); hb += gap; gap = max(.42, gap * .93)
    for k, tb in enumerate(np.arange(35.1, 36.7, 0.55)):
        SFX.add(step_heavy(.8), tb, pan=-.6 + k * .4)
    SFX.add(breath_heavy(.35), 35.3, pan=0)
    # ---- the sneeze
    SFX.add(hit(.35, 60, .6), 36.65)
    t_choo = we(12, 6) + 0.30
    MUS.add(high_tension(t_choo - 37.0, .22), 37.0)
    sn = sneeze(.95)
    SFX.add(sn, t_choo - 0.80)
    MUS.add(braam(1.8, .5, 29), t_choo)
    SFX.add(wings(.6), t_choo + .1, pan=.3)
    # ---- "заткнись", Jason turns
    SFX.add(slap(.55), 39.85)
    SFX.add(hit(.3, 60, .5), ws(13, 3))
    SFX.add(glitch_sfx(.35), 40.9)
    SFX.add(creak(.4, .45, 120), 41.0)
    SFX.add(hit(.5), 41.2)
    # ---- the genius plan
    MUS.add(drone(3.4, (26, 33), .25), 41.5)
    SFX.add(pling(.38), ws(14, 4) - .1, pan=.2)
    AMB.add(crickets(1.1, .3, 3.0, 4700, 9), 44.95, pan=.3)
    # ---- jump scare
    t_i = ws(15, 1)
    SFX.add(glitch_sfx(.5), t_i - .03)
    MUS.add(braam(3.0, 1.0, 26), t_i)
    MUS.add(screech(.9, .7), t_i)
    SFX.add(hit(1.0, 80, 1.2), t_i)
    SFX.add(thunder(.5, 2.5), t_i + .02)
    SFX.add(hit(.45), 46.66)
    for k, tb in enumerate(np.arange(46.9, 48.9, 0.45)):
        SFX.add(heartbeat(.6), tb)
    MUS.add(drone(3.0, (26, 32, 38), .35), 46.8)
    # ---- strolling over with the phone
    for k, tb in enumerate(np.arange(49.0, 51.8, 0.3)):
        MUS.add(pizz([60, 64, 67, 64, 62, 65, 69, 65][k % 8], .28), tb, pan=.15)
    SFX.add(boop(.3, 990), ws(16, 6) + .25)
    SFX.add(hit(.3, 60, .5), 51.79)
    MUS.add(strum([60, 64, 67, 72], 1.4, .02, .22), 51.84, pan=-.2)
    SFX.add(whoosh(.35, .3), ws(16, 11) - .05)
    SFX.add(boop(.25, 1480), ws(16, 11) + .45)
    # ---- "девушка бросила?" + the stare
    MUS.add(sad_melody(.26), ws(17, 8) - .3)
    t_end17 = we(17, 9)
    AMB.add(crickets(1.3, .3, 2.6, 4500, 11), t_end17 + .1, pan=-.2)
    SFX.add(owl(.25), t_end17 + .3, pan=-.6)
    SFX.add(hit(.4, 55, 1.0), 59.45)
    # ---- the doomed finale
    fin = np.zeros(int(6.5 * SR))
    for k, (ch, tt0) in enumerate(((([45, 52, 57, 60]), 0.0), ([43, 50, 55, 59], 1.4), ([41, 48, 53, 57], 2.8))):
        s = strum(ch, 2.2, .03, 1.0)
        i = int(tt0 * SR); fin[i:i + len(s)] += s[:len(fin) - i]
    MUS.add(norm(reverb(fin, 1.6, 3000, .3), .32), 59.67)
    for f in (61.3, 65.25):
        SFX.add(shutter(.5), f - .01, pan=.4)
    SFX.add(hit(.42, 55, 1.2), we(18, 10) + .02)
    SFX.add(sad_trombone(.42), we(18, 10) + .14, pan=.1)


# ------------------------------------------------------------------ cartoon-version gags (stickers, HUD, pops)
def bloop(g=1.0, f0=320, f1=980, d=0.09):
    t = tt(d)
    return norm(sine(np.geomspace(f0, f1, len(t)), d) * env(len(t), .002, .04), g)


def buzzer(g=1.0):
    d = 0.32
    t = tt(d)
    x = np.sign(np.sin(2 * np.pi * 110 * t)) + np.sign(np.sin(2 * np.pi * 116 * t)) * .6
    return norm(flt(x, "lowpass", 1800) * env(len(t), .005, .05), g)


def slurp(g=1.0):
    d = 0.45
    t = tt(d)
    x = flt(noise(d), "bp", (500, 2200)) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * t)) ** 2
    return norm(x * env(len(t), .03, .1), g)


def blip(g=1.0):
    a, b = boop(1.0, 1320), boop(1.0, 1760)
    out = np.zeros(int(.2 * SR)); out[:len(a)] += a; i = int(.07 * SR); out[i:i + len(b)] += b
    return norm(out, g)


def bonk(g=1.0):
    d = .3
    t = tt(d)
    return norm(sine(520 * np.exp(-t * 6) + 180, d) * np.exp(-t / .08), g)


def gags():
    if os.environ.get("CARTOON") != "1":
        return
    pops = [1.15, 6.95, 7.4, ws(4, 3), ws(4, 4) + .05, ws(5, 13) + .1, 20.4, ws(6, 5) + .3, ws(6, 8), ws(9, 4) + .02,
            ws(9, 5) + .05, 33.65, 39.85, 43.2, ws(16, 3), ws(17, 8)]
    for k, p in enumerate(pops):
        SFX.add(bloop(.32, 300 + 40 * (k % 4), 900 + 80 * (k % 3)), p, pan=.25 * (-1) ** k)
    SFX.add(ding(1568, .3), 2.75, pan=-.2)
    SFX.add(buzzer(.35), ws(2, 4) + .02)
    for p in (3.95, 7.5, 27.45, 49.0, 4.3, 5.25, 16.3, 23.1, 26.5, 39.4, 8.3, 44.5, 51.9, 53.6, 58.0):
        SFX.add(blip(.18), p, pan=.4)
    SFX.add(slurp(.3), 12.7)
    SFX.add(bonk(.35), 47.2)
    SFX.add(bonk(.3), 47.75)
    SFX.add(ding(2093, .25, 1.0), ws(6, 13) + .3)


def main():
    arrange()
    gags()
    import wave as wv
    with wv.open(os.path.join(BUILD, "voice.wav")) as f:
        v = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float64) / 32768
    v = np.concatenate([v, np.zeros(max(0, N - len(v)))])[:N]
    # echo on the idiot shouting out of the window
    q = next(q for q in TL["quotes"] if q["mode"] == "shout" and q["who"] == 2)
    seg_ = np.zeros(N)
    a, b = int(q["s"] * SR), int((q["e"] + .1) * SR)
    seg_[a:b] = v[a:b]
    echo = np.zeros(N)
    for dl, g in ((.34, .32), (.68, .16), (1.02, .08)):
        d = int(dl * SR)
        echo[d:] += seg_[:N - d] * g
    echo = flt(echo, "lowpass", 2200)
    # voice envelope for ducking
    e = np.abs(v)
    e = flt(e, "lowpass", 8)
    e = np.clip(e / (np.percentile(e[e > 1e-4], 90) + 1e-9), 0, 1)
    duck = 1 - 0.62 * e
    vL = vR = v * 1.0
    # the punchline "не переживу" plays over silence: music out, ambience down, then boom + trombone
    t = np.arange(N) / SR
    p0, p1 = ws(18, 9) - 0.25, we(18, 10) + 0.02
    gate = np.clip(np.minimum((p0 + 0.15 - t) / 0.15, (t - p1) / 0.05), 0, 1)
    musL = reverb(MUS.L, 1.8, 3000, .18) * duck * gate
    musR = reverb(MUS.R, 1.8, 3000, .18) * duck * gate
    AMB.L *= 0.35 + 0.65 * gate; AMB.R *= 0.35 + 0.65 * gate
    sfxL = reverb(SFX.L, 1.2, 4000, .12) * (1 - .45 * e)
    sfxR = reverb(SFX.R, 1.2, 4000, .12) * (1 - .45 * e)
    ambL, ambR = AMB.L * (1 - .3 * e), AMB.R * (1 - .3 * e)
    L = vL + echo + musL * .55 + sfxL * .6 + ambL * .5
    R = vR + echo + musR * .55 + sfxR * .6 + ambR * .5
    # master: loudness-ish normalisation + soft limiter
    rms = np.sqrt(np.mean(np.concatenate([L, R]) ** 2))
    gain = 0.16 / max(rms, 1e-9)
    L, R = np.tanh(L * gain * 1.1) / 1.1 * 0.97, np.tanh(R * gain * 1.1) / 1.1 * 0.97
    st = np.stack([L, R], 1)
    fade = int(.35 * SR)
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    with wave.open(os.path.join(BUILD, "mix.wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    print("mix written", os.path.join(BUILD, "mix.wav"), f"{DUR:.2f}s")


if __name__ == "__main__":
    main()
