# Part 2 score + SFX (same synth toolkit as video_src/music.py), ducked under the voice.
import numpy as np, subprocess, os
SR = 44100
DUR = 80.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(8)
L = np.zeros(N); R = np.zeros(N)

def midi(m): return 440 * 2 ** ((m - 69) / 12)

def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def add(sig, start, gain=1.0, pan=0.0):
    i0 = int(start * SR)
    if i0 >= N: return
    sig = sig[:N - i0]
    L[i0:i0 + len(sig)] += sig * gain * np.sqrt((1 - pan) / 2) * 1.414
    R[i0:i0 + len(sig)] += sig * gain * np.sqrt((1 + pan) / 2) * 1.414

def lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    # vectorised one-pole via lfilter-like loop in numpy chunks
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)

def saw(f, n, detune=(0,)):
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for d in detune:
        ph = (tt * f * (1 + d)) % 1
        s += 2 * ph - 1
    return s / len(detune)

def pad(notes, start, dur, gain, cutoff=900, a=1.0, r=1.5):
    n = int(dur * SR)
    s = np.zeros(n)
    for m in notes:
        s += saw(midi(m), n, (-0.004, 0, 0.005))
    s = lp(lp(s, cutoff), cutoff) * env_ar(n, a, r)
    add(s, start, gain, -0.3); add(s[::-1][::-1] * 0.9, start + 0.013, gain * 0.8, 0.3)

def sub_boom(start, gain=1.0, f0=90, f1=32, dur=1.8):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-tt * 2.2)
    nz = lp(rng.standard_normal(n), 1800) * np.exp(-tt * 9) * 0.6
    add(np.tanh((s + nz) * 1.6), start, gain)

def kick(start, gain=0.8):
    sub_boom(start, gain, 140, 45, 0.45)

def tom(start, gain=0.5, f=110):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-tt * 20))) / SR) * np.exp(-tt * 7)
    s += lp(rng.standard_normal(n), 2500) * np.exp(-tt * 30) * 0.3
    add(s, start, gain, rng.uniform(-.4, .4))

def whoosh(start, dur=0.6, gain=0.5, rev=False):
    n = int(dur * SR); tt = np.linspace(0, 1, n)
    nz = rng.standard_normal(n)
    e = np.sin(np.pi * tt) ** 2
    if rev: e = tt ** 3
    from scipy.signal import lfilter
    out = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        c = 300 + 5000 * e[i]
        a = np.exp(-2 * np.pi * c / SR)
        out[i:i + blk] = lfilter([1 - a], [1, -a], nz[i:i + blk])
    add(out * e * 2.5, start, gain, 0.0)

def glitch(start, gain=0.35):
    n = int(0.25 * SR)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(rng.choice([200, 900, 1700, 3000], n // 400 + 1).repeat(400)[:n]) / SR))
    s *= (rng.random(n // 600 + 1) > .3).repeat(600)[:n]
    add(s * env_ar(n, 0.005, 0.05), start, gain)

def braam(start, dur=3.5, gain=0.6, root=38):
    n = int(dur * SR)
    s = sum(saw(midi(m), n, (-0.006, 0, 0.007)) for m in (root, root + 7, root + 12))
    tt = np.arange(n) / SR
    s = lp(s, 600) * np.tanh(4 * np.exp(-tt * 0.8)) * env_ar(n, 0.02, 1.2)
    add(np.tanh(s * 2), start, gain)
    sub_boom(start, gain)

def tick(start, gain=0.25):
    n = int(0.03 * SR)
    add(lp(rng.standard_normal(n), 6000) * np.exp(-np.arange(n) / SR * 200), start, gain, 0.2)

def heartbeat(start, gain=0.7):
    sub_boom(start, gain, 70, 40, 0.35); sub_boom(start + 0.22, gain * 0.7, 70, 40, 0.35)

def alarm(start, dur, gain=0.18):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = np.where((tt * 2) % 1 < .5, 853, 960)  # two-tone emergency alert
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    add(s * env_ar(n, 0.05, 0.4), start, gain)

def buzz(start, dur, gain=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.5 + np.sin(2 * np.pi * 75 * tt)
    gate = ((tt % 0.55) < 0.38).astype(float)
    add(lp(s, 400) * gate * env_ar(n, 0.01, 0.05), start, gain)

def ding(start, gain=0.35):
    n = int(1.2 * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1318 * tt) + 0.6 * np.sin(2 * np.pi * 1975 * tt)) * np.exp(-tt * 5)
    add(s, start, gain); add(s, start + 0.12, gain * 0.6)

def crowd(start, dur, gain=0.25):
    n = int(dur * SR)
    from scipy.signal import lfilter
    s = lfilter([1], [1, -0.97], rng.standard_normal(n)) * 0.05
    s = s - lp(s, 300)
    mod = 0.6 + 0.4 * np.sin(np.arange(n) / SR * 3.1) * np.sin(np.arange(n) / SR * 1.3)
    add(s * mod * env_ar(n, 0.5, 0.8), start, gain)

def ostinato(start, end, root, gain=0.18, bpm=120, cutoff=1400):
    step = 60 / bpm / 2
    pat = [0, 0, 12, 0, 0, 10, 0, 7]
    k = 0; ts = start
    while ts < end:
        n = int(step * 0.95 * SR)
        s = saw(midi(root + pat[k % 8]), n, (-0.003, 0.003))
        s = lp(s, cutoff) * np.exp(-np.arange(n) / SR * 6)
        add(s, ts, gain, 0.25 if k % 2 else -0.25)
        k += 1; ts += step

def strings_trem(start, dur, notes, gain=0.08):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = sum(saw(midi(m), n, (-0.003, 0.004)) for m in notes)
    s = lp(s, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * tt)) * env_ar(n, 0.8, 0.6)
    add(s, start, gain)


# ---------------------------------------------------------------- part-2 extras
def train_horn(start, dur=1.4, gain=0.5):
    """Steam-locomotive whistle chord."""
    n = int(dur * SR); tt = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * tt)
    s = sum(saw(1, n) * 0 + (2 * ((tt * f * vib) % 1) - 1) for f in (311.1, 370.0, 466.2))
    s += 0.25 * lp(rng.standard_normal(n), 3000)
    s = lp(lp(s, 2600), 2600)
    e = env_ar(n, 0.06, 0.35) * (0.85 + 0.15 * np.sin(np.pi * np.clip(tt / dur, 0, 1)))
    add(np.tanh(s * 1.5) * e, start, gain)


def punch(start, gain=0.7):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    nz = lp(rng.standard_normal(n), 3500) * np.exp(-tt * 30)
    add(np.tanh(nz * 3), start, gain * 0.6)
    sub_boom(start, gain, 120, 38, 0.8)


def wind(start, dur, gain=0.15):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = lp(rng.standard_normal(n), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * tt))
    add(s * env_ar(n, 0.8, 0.8), start, gain, 0.2)


def riser(start, dur, gain=0.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 200 + 1600 * (tt / dur) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + lp(rng.standard_normal(n), 4000) * 0.4
    add(s * (tt / dur) ** 2, start, gain)


def brass(notes, start, dur, gain=0.1):
    n = int(dur * SR)
    s = sum(saw(midi(m), n, (-0.003, 0.004)) for m in notes)
    tt = np.arange(n) / SR
    cut = 900 + 2600 * np.exp(-tt * 3)
    out = np.zeros(n)
    for i in range(0, n, 2048):
        out[i:i + 2048] = lp(s[i:i + 2048], float(cut[i]))
    add(np.tanh(out * 1.5) * env_ar(n, 0.03, 0.4), start, gain)


# ---------------------------------------------------------------- arrangement
# bridge from part 1: same D-minor drone, clock ticking
pad([38, 45, 50, 57], 0.0, 9.2, 0.08, cutoff=700, a=0.6)
strings_trem(1.5, 7.4, [69, 74], 0.035)
for ts in np.arange(0.5, 11.0, 1.0): tick(ts, 0.16)
whoosh(4.0, 0.4, 0.3)
glitch(8.75, 0.3)
for ts in np.arange(9.0, 11.0, 1.0): heartbeat(ts, 0.6)
# look up / Omni-Man approaches
whoosh(11.0, 0.6, 0.45, rev=True)
braam(12.9, 2.8, 0.5, 38)
pad([38, 45, 50, 53], 12.9, 2.8, 0.08, cutoff=600, a=0.2)
wind(12.9, 6.0, 0.12)
whoosh(13.9, 0.5, 0.4)
# "но внезапно" - suck-out then the horn
riser(15.7, 1.25, 0.18)
train_horn(16.95, 1.5, 0.55)
sub_boom(16.95, 0.8)
# Arkadiy - heroic D major
whoosh(18.35, 0.5, 0.5); sub_boom(18.55, 0.7)
ostinato(18.4, 30.0, 50, 0.13, bpm=140, cutoff=2000)
for b in np.arange(18.4, 30.0, 60 / 140): kick(b, 0.45)
for b in np.arange(18.4 + 60 / 280, 30.0, 120 / 140): tom(b, 0.25, 180)
for c, ch in ((18.4, [50, 57, 62, 66]), (19.75, [55, 62, 67, 71]), (21.3, [50, 57, 62, 66]), (24.2, [52, 59, 64, 67]),
              (27.0, [55, 62, 67, 71]), (28.5, [57, 64, 69, 73])):
    brass(ch, c, 1.5, 0.07)
brass([62, 66, 69, 74], 19.8, 1.4, 0.08)
whoosh(21.2, 0.5, 0.4); wind(21.3, 3.0, 0.15)
# "ты ещё кто такой?" - menace
glitch(30.15, 0.35); sub_boom(30.2, 0.6)
pad([38, 44, 50], 30.2, 3.2, 0.08, cutoff=450, a=0.1)
braam(32.0, 1.6, 0.4, 38)
# "я Аркадий Паровозов!"
brass([50, 57, 62, 66], 33.4, 1.8, 0.08); kick(33.4, 0.6)
brass([55, 62, 67, 71], 35.3, 1.6, 0.08); kick(35.3, 0.6)
brass([57, 64, 69, 73, 76], 36.94, 1.2, 0.1); kick(36.94, 0.8); sub_boom(36.94, 0.6)
# smirk -> battle (D minor, 150 bpm)
strings_trem(38.0, 1.4, [62, 63], 0.04)
whoosh(39.3, 0.6, 0.6)
ostinato(39.4, 59.4, 38, 0.15, bpm=150, cutoff=1600)
for b in np.arange(39.4, 59.4, 0.4): kick(b, 0.5)
for b in np.arange(39.6, 59.4, 0.8): tom(b, 0.3, 150); tom(b + 0.2, 0.22, 110)
for c, ch in ((39.4, [38, 45, 50]), (43.9, [41, 48, 53]), (46.3, [34, 41, 46]), (49.8, [36, 43, 48]), (54.7, [38, 45, 50, 53])):
    pad(ch, c, 4.6, 0.07, cutoff=900, a=0.1)
whoosh(40.6, 0.7, 0.6)                      # charge
whoosh(42.0, 1.0, 0.5)                      # dodge pass (slow-mo)
whoosh(44.85, 0.7, 0.5, rev=True)           # wind-up
punch(45.6, 0.95); glitch(45.6, 0.3)        # БАМ
whoosh(45.8, 0.5, 0.4)
wind(46.3, 3.5, 0.18)
for c in (47.0, 47.85, 48.7, 49.4): punch(c, 0.55); whoosh(c - 0.25, 0.3, 0.3)
whoosh(50.2, 0.6, 0.5)                      # grab attempt
train_horn(52.35, 0.45, 0.4)                # toot! max speed
riser(51.9, 1.0, 0.15)
sub_boom(53.05, 0.9); whoosh(52.9, 0.9, 0.7)  # sonic boom
strings_trem(54.7, 2.6, [74, 75], 0.04)
punch(57.4, 0.6)                            # catch
whoosh(58.1, 0.5, 0.5, rev=True)            # fist pulls back
# another figure
glitch(59.45, 0.3)
riser(59.5, 3.7, 0.16)
pad([46, 53, 58, 62], 59.5, 3.8, 0.08, cutoff=1500, a=1.0)
strings_trem(59.6, 3.6, [74, 77, 81], 0.05)
# Mark reveal
whoosh(63.0, 0.4, 0.4); sub_boom(63.2, 0.8)
brass([46, 53, 58, 62, 65], 63.2, 0.9, 0.11); brass([50, 57, 62, 66, 69], 64.08, 1.0, 0.12)
kick(63.5, 0.7); kick(64.08, 0.7)
punch(65.78, 0.45); punch(66.54, 0.45)
pad([50, 57, 62, 66], 64.8, 3.0, 0.07, cutoff=1500)
# slow head turn
glitch(67.75, 0.3)
pad([37, 44, 50], 67.8, 2.9, 0.08, cutoff=380, a=0.2)
for ts in np.arange(67.9, 70.6, 0.9): heartbeat(ts, 0.7)
# 1 vs 2
braam(70.6, 4.0, 0.55, 38)
ostinato(70.6, 76.8, 38, 0.13, bpm=150, cutoff=1400)
for b in np.arange(70.6, 76.8, 0.4): kick(b, 0.45)
pad([38, 45, 50, 57], 70.6, 4.2, 0.08, cutoff=1200)
whoosh(70.4, 0.5, 0.4); punch(73.2, 0.5)
riser(74.7, 2.2, 0.18); glitch(74.65, 0.3)
pad([41, 48, 53, 57], 74.7, 2.2, 0.08, cutoff=1400)
# to be continued
braam(76.9, 3.1, 0.6, 38)
pad([38, 45, 50, 57, 62], 76.9, 3.1, 0.09, cutoff=1500, a=0.05, r=2.0)
strings_trem(77.0, 3.0, [74, 77, 81, 86], 0.05)

mus = np.stack([L, R], 1)
for dly, g in ((0.031, 0.35), (0.053, 0.3), (0.089, 0.25), (0.127, 0.2)):
    d = int(dly * SR)
    mus[d:] += mus[:-d] * g * 0.5

voice = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "voice.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True).stdout, dtype=np.float32).astype(np.float64)
v = np.zeros(N); v[:min(N, len(voice))] = voice[:N]
from scipy.signal import lfilter
envv = np.sqrt(lfilter([0.002], [1, -0.998], v ** 2))
envv = envv / (envv.max() + 1e-9)
duck = 1 - 0.55 * np.clip(envv * 3, 0, 1)
mus *= duck[:, None]
mus /= np.abs(mus).max() + 1e-9
mus *= 0.42
vpk = np.abs(v).max() + 1e-9
v = v / vpk * 0.8
mix = mus + np.stack([v, v], 1)
mix /= max(1.0, np.abs(mix).max() / 0.97)
mix.astype(np.float32).tofile("mix.f32")
print("ok", mix.shape)
