# Procedural cinematic score + SFX, ducked under the voice.
import numpy as np, subprocess, os
SR = 44100
DUR = 65.5
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
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

# ---------------------------------------------------------------- arrangement (D minor)
pad([50, 57, 62], 0.0, 7.4, 0.07, cutoff=700, a=1.5)          # calm-ish but uneasy
pad([46, 53, 58], 3.7, 4.0, 0.06, cutoff=600)
glitch(3.65); whoosh(3.4, 0.5, 0.4)
alarm(7.0, 5.2, 0.12)
glitch(7.05, 0.4); sub_boom(7.1, 0.7)
pad([38, 45, 50, 53], 7.1, 5.6, 0.09, cutoff=500, a=0.3)
braam(9.94, 2.6, 0.45, 38)
sub_boom(10.6, 0.5)
whoosh(12.2, 0.5, 0.4); sub_boom(12.5, 0.4)
whoosh(13.0, 0.5, 0.5)
pad([50, 53, 57, 62], 13.0, 5.2, 0.08, cutoff=1200, a=1.2)
strings_trem(14.5, 3.5, [74, 77, 81], 0.05)
sub_boom(16.3, 0.7); whoosh(15.9, 0.5, 0.3, rev=True)
# action section
ostinato(17.9, 36.2, 38, 0.16)
for b in np.arange(17.9, 36.2, 0.5):
    kick(b, 0.5)
for b in np.arange(18.15, 36.2, 1.0):
    tom(b, 0.35, 160); tom(b + 0.25, 0.25, 120)
crowd(17.8, 4.8, 0.5)
pad([38, 45, 50], 17.9, 4.6, 0.07, cutoff=800)
pad([41, 48, 53], 22.4, 4.2, 0.07, cutoff=900)
for ts in np.arange(22.5, 26.4, 0.25):
    tick(ts, 0.22)
pad([34, 41, 46], 26.5, 3.1, 0.07); pad([36, 43, 48], 29.6, 2.7, 0.07); pad([38, 45, 50, 57], 32.3, 4.1, 0.08)
for c in (19.9, 22.4, 26.5, 29.6, 32.3):
    whoosh(c - 0.3, 0.45, 0.45)
sub_boom(26.5, 0.4)
# stop / strange
whoosh(36.0, 0.5, 0.4, rev=True); glitch(36.35, 0.45)
strings_trem(36.4, 3.2, [73, 74], 0.05)
pad([37, 44, 50], 36.4, 3.2, 0.06, cutoff=400, a=0.1)
# flyover
whoosh(39.2, 1.8, 0.9)
braam(39.5, 3.0, 0.4, 38)
whoosh(41.6, 0.5, 0.35)
pad([38, 45, 50, 53], 41.8, 2.0, 0.07, cutoff=600)
# searching
strings_trem(43.7, 2.1, [62, 65, 69], 0.05); sub_boom(43.7, 0.4)
for ts in np.arange(43.8, 45.7, 0.3): tick(ts, 0.18)
# Mark reveal: heroic lift to D major / B-flat
whoosh(45.5, 0.4, 0.4); sub_boom(45.8, 0.8)
pad([46, 53, 58, 62, 65], 45.8, 1.3, 0.11, cutoff=2000, a=0.05, r=0.6)
pad([50, 57, 62, 66, 69], 46.7, 1.6, 0.12, cutoff=2400, a=0.05, r=0.8)
kick(46.68, 0.7); kick(47.3, 0.7)
# phone
glitch(48.15, 0.3)
pad([38, 45, 50], 48.2, 10.4, 0.05, cutoff=500, a=0.5, r=1.0)
buzz(48.75, 1.6, 0.12)
ding(50.7, 0.12)
for ts in np.arange(52.9, 58.3, 0.5):
    tick(ts, 0.12)
strings_trem(54.4, 4.2, [69, 74], 0.035)
# question
glitch(58.55, 0.3)
for ts in np.arange(58.7, 60.4, 0.8): heartbeat(ts, 0.6)
whoosh(60.0, 0.5, 0.5, rev=True)
# final
braam(60.5, 5.0, 0.55, 38)
pad([38, 45, 50, 57, 62], 60.5, 5.0, 0.09, cutoff=1500, a=0.05, r=2.0)
kick(62.2, 0.8)
strings_trem(60.6, 4.9, [74, 77, 81, 86], 0.05)

mus = np.stack([L, R], 1)
# simple reverb: a few feedback delays
for dly, g in ((0.031, 0.35), (0.053, 0.3), (0.089, 0.25), (0.127, 0.2)):
    d = int(dly * SR)
    mus[d:] += mus[:-d] * g * 0.5

# duck under the voice
voice = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "voice.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True).stdout, dtype=np.float32).astype(np.float64)
v = np.zeros(N); v[:min(N, len(voice))] = voice[:N]
from scipy.signal import lfilter
envv = np.sqrt(lfilter([0.002], [1, -0.998], v ** 2))
envv = envv / (envv.max() + 1e-9)
duck = 1 - 0.55 * np.clip(envv * 3, 0, 1)
mus *= duck[:, None]
gk = np.interp(t, [0, 6.8, 7.1, 48.0, 48.6, 58.3, 58.6], [3.2, 3.2, 1.0, 1.0, 4.5, 4.5, 1.0])
mus *= gk[:, None]
mus /= np.abs(mus).max() + 1e-9
mus *= 0.42
mix = mus + np.stack([v, v], 1) * 1.0
mix /= max(1.0, np.abs(mix).max() / 0.97)
mix.astype(np.float32).tofile("mix.f32")
mus.astype(np.float32).tofile("music.f32")
print("ok", mix.shape)
