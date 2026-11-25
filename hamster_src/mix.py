# Procedural score + sound effects, mixed under the processed voice. Output: build/mix.wav
import json, os, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
SR = 44100
DATA = json.loads(open(os.path.join(HERE, "data.js")).read().split("=", 1)[1].rstrip().rstrip(";"))
DUR = DATA["dur"]
N = int(DUR * SR) + SR
WD = DATA["words"]
WS = lambda i: WD[i]["s"]
WE = lambda i: WD[i]["e"]
P = [p for p, d in DATA["pauses"]]  # pause start times (final timeline)
rng = np.random.default_rng(11)

MUS = np.zeros((N, 2)); SFX = np.zeros((N, 2))

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
def nm(s):  # "D4" -> midi
    name, octv = s[:-1], int(s[-1]); return 12 * (octv + 1) + NOTE[name]

def tt(n): return np.arange(n) / SR
def lp(x, f, o=2): return sosfilt(butter(o, min(f, SR / 2 - 100), "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, min(b, SR / 2 - 100)], "band", fs=SR, output="sos"), x)
def env(n, a=0.005, r=0.05):
    e = np.ones(n); na, nr = max(1, min(n // 2, int(a * SR))), max(1, min(n // 2, int(r * SR)))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def noise(n): return rng.standard_normal(n)
def addat(s, i, x):
    m = max(0, min(len(x), len(s) - i)); s[i:i + m] += x[:m]

def put(bus, sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    bus[i:i + len(sig), 0] += sig * gain * np.sqrt(0.5 * (1 - pan)) * 1.414
    bus[i:i + len(sig), 1] += sig * gain * np.sqrt(0.5 * (1 + pan)) * 1.414
def mus(sig, t0, g=1.0, pan=0.0): put(MUS, sig, t0, g, pan)
def sfx(sig, t0, g=1.0, pan=0.0): put(SFX, sig, t0, g, pan)

def saw(f, n, det=(0,)):
    t = tt(n); s = np.zeros(n)
    for d in det: s += 2 * ((t * f * (1 + d) + rng.random()) % 1) - 1
    return s / len(det)
def sweep_noise(n, f0, f1, q=0.5, curve=None):
    """band-passed noise whose centre moves f0 -> f1 (chunked)"""
    x = noise(n); out = np.zeros(n); blk = 512
    for i in range(0, n, blk):
        u = i / max(1, n - 1) if curve is None else curve(i / max(1, n - 1))
        fc = f0 * (f1 / f0) ** u
        out[i:i + blk] = bp(x[max(0, i - 2048):i + blk], max(30, fc * (1 - q)), fc * (1 + q))[-len(x[i:i + blk]):]
    return out

# ================================================================ instruments
def musicbox(f, dur=1.4):
    n = int(dur * SR); t = tt(n)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 6) + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 10)
    return s * np.exp(-t * 3.5) * env(n, 0.002, 0.05)
def pluck(f, dur=0.6, bright=10):
    n = int(dur * SR); t = tt(n); s = np.zeros(n)
    for k in range(1, bright + 1):
        if f * k > 9000: break
        s += np.sin(2 * np.pi * f * k * t) / k * np.exp(-t * (2.5 + k * 1.6))
    return s * env(n, 0.002, 0.03)
def strings(freqs, dur, a=0.01, r=0.08, cut=2200):
    n = int(dur * SR); s = sum(saw(f, n, (-0.004, 0, 0.005)) for f in freqs)
    return lp(s, cut) * env(n, a, r) / max(1, len(freqs)) ** 0.5
def pad(freqs, dur, cut=1100, a=0.6, r=0.8):
    n = int(dur * SR); s = sum(saw(f, n, (-0.006, -0.002, 0.003, 0.007)) for f in freqs)
    return lp(lp(s, cut), cut) * env(n, a, r) / len(freqs) ** 0.5
def choir(freqs, dur, a=0.5, r=0.9):
    n = int(dur * SR); t = tt(n); s = np.zeros(n)
    for f in freqs:
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6)
        ph = np.cumsum(f * vib) / SR
        s += sum(2 * ((ph * (1 + d)) % 1) - 1 for d in (-0.005, 0, 0.006))
    s = bp(s, 550, 900) * 1.4 + bp(s, 1000, 1400) * 0.8 + lp(s, 400) * 0.4
    return s * env(n, a, r) / len(freqs) ** 0.5
def brass(freqs, dur, a=0.02, r=0.15):
    n = int(dur * SR); s = sum(saw(f, n, (-0.003, 0.004)) for f in freqs)
    t = tt(n); e = np.exp(-t * 5)
    return (lp(s, 3500) * e + lp(s, 700) * (1 - e)) * env(n, a, r) / len(freqs) ** 0.5
def epiano(freqs, dur):
    n = int(dur * SR); t = tt(n); s = np.zeros(n)
    for f in freqs:
        s += np.sin(2 * np.pi * f * t + 0.8 * np.exp(-t * 6) * np.sin(2 * np.pi * f * 2 * t)) * np.exp(-t * 1.8)
    return s * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)) * env(n, 0.003, 0.2) / len(freqs) ** 0.5
def piano(freqs, dur):
    n = int(dur * SR); t = tt(n); s = np.zeros(n)
    for f in freqs:
        for k, g in ((1, 1), (2, .45), (3, .25), (4, .12), (5, .06)):
            s += g * np.sin(2 * np.pi * f * k * 1.0005 ** k * t) * np.exp(-t * (1.5 + k * 0.9))
    return s * env(n, 0.002, 0.15) / len(freqs) ** 0.5
def bass808(f, dur=0.9):
    n = int(dur * SR); t = tt(n)
    fr = f * (1 + 1.5 * np.exp(-t * 40))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 2.2)
    return np.tanh(s * 1.8) * env(n, 0.002, 0.08)
def kick(g=1.0, dur=0.45):
    n = int(dur * SR); t = tt(n); fr = 45 + 110 * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7) + lp(noise(n), 3000) * np.exp(-t * 80) * 0.3
    return np.tanh(s * 1.5) * g
def snare(dur=0.3):
    n = int(dur * SR); t = tt(n)
    return (bp(noise(n), 1500, 7000) * np.exp(-t * 18) * 0.9 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.5)
def clap(dur=0.3):
    n = int(dur * SR); t = tt(n); e = np.zeros(n)
    for k in range(3): i = int(k * 0.011 * SR); e[i:] += np.exp(-(t[: n - i]) * 60)
    e += np.exp(-t * 12) * 0.4
    return bp(noise(n), 900, 4000) * e * 0.8
def hat(dur=0.06, o=False):
    n = int((0.25 if o else dur) * SR); t = tt(n)
    return hp(noise(n), 7000) * np.exp(-t * (12 if o else 70)) * 0.5
def taiko(f=70, dur=1.0):
    n = int(dur * SR); t = tt(n); fr = f * (1 + 0.5 * np.exp(-t * 25))
    return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 4.5) + lp(noise(n), 900) * np.exp(-t * 20) * 0.5)
def boom(dur=2.5, f0=110, f1=30):
    n = int(dur * SR); t = tt(n); fr = f1 + (f0 - f1) * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 1.8) + lp(noise(n), 1500) * np.exp(-t * 6) * 0.7
    return np.tanh(s * 1.7)
def riser(dur, f0=200, f1=2400):
    n = int(dur * SR); t = tt(n); u = t / dur
    fr = f0 * (f1 / f0) ** (u ** 2)
    s = saw(1, n) * 0
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.4 + sweep_noise(n, 300, 6000, 0.3) * 0.8
    return s * u ** 2 * env(n, 0.01, 0.02)

# ================================================================ score
BPM = 120; BT = 60 / BPM
CH = {  # D minor family
    "Dm": ["D3", "F3", "A3"], "Bb": ["A#2", "D3", "F3"], "Gm": ["G2", "A#2", "D3"], "A": ["A2", "C#3", "E3"],
    "F": ["F2", "A2", "C3"], "C": ["C3", "E3", "G3"], "Am": ["A2", "C3", "E3"], "E": ["E2", "G#2", "B2"],
}
def chord(name, shift=0): return [midi(nm(x) + shift) for x in CH[name]]

# --- A: ironic music box lullaby (0 – 5.12)
mel = ["C6", "A5", "F5", "A5", "C6", "D6", "C6", "A5", "A#5", "G5", "E5", "G5", "A#5", "C6", "A#5", "G5",
       "A5", "F5", "C5", "F5", "A5", "C6"]
for i, m in enumerate(mel):
    t0 = 0.05 + i * 0.235
    if t0 > 5.05: break
    mus(musicbox(midi(nm(m)), 1.2), t0, 0.22, 0.2 * np.sin(i))
for i in range(11):
    t0 = 0.05 + i * 0.47
    mus(pluck(midi(nm(["F3", "C3", "A#2", "C3"][i % 4])), 0.5, 6), t0, 0.30)
    mus(musicbox(midi(nm(["A4", "G4", "F4", "E4"][i % 4])), 0.8), t0 + 0.235, 0.08, -0.3)
# shimmer on the cute shot
mus(riser(0.6, 800, 3000) * 0.3, 2.45, 0.25)

# --- B: dark tension (5.4 – 9.45)
mus(pad([midi(nm("D2")), midi(nm("A2"))], 4.2, 500, 0.4, 0.3), 5.35, 0.45)
for k in range(8):
    t0 = 5.45 + k * 0.5
    mus(taiko(55, 0.8), t0, 0.35 if k % 2 == 0 else 0.18)
for k in range(16):
    t0 = 7.35 + k * 0.125
    mus(strings([midi(nm(["D4", "D4", "F4", "D4", "E4", "D4", "F4", "A4"][k % 8]))], 0.12, 0.005, 0.04, 2600), t0, 0.16, 0.3)

# --- C: trailer drive (9.45 – 19.92)
prog = ["Dm", "Bb", "Gm", "A"]
t = 9.45; bar = 0
while t < 19.85:
    name = prog[bar % 4]
    mus(pad(chord(name, 12), BT * 4 + 0.3, 1500, 0.05, 0.3), t, 0.20)
    mus(bass808(midi(nm({"Dm": "D2", "Bb": "A#1", "Gm": "G1", "A": "A1"}[name])), BT * 2), t, 0.45)
    mus(bass808(midi(nm({"Dm": "D2", "Bb": "A#1", "Gm": "G1", "A": "A1"}[name])), BT * 2), t + BT * 2, 0.35)
    for k in range(16):  # 16th ostinato
        f = chord(name, 24)[[0, 1, 2, 1][k % 4]]
        mus(strings([f], 0.1, 0.004, 0.04, 3000), t + k * BT / 4, 0.11, 0.35 * (1 if k % 2 else -1))
    for b in range(4):
        mus(kick(), t + b * BT, 0.55 if b % 2 == 0 else 0.0)
        if b % 2 == 1: mus(snare(), t + b * BT, 0.35)
        mus(taiko(80, 0.6), t + b * BT + BT / 2, 0.18)
        for h in range(2): mus(hat(), t + b * BT + h * BT / 2, 0.18)
    if bar % 2 == 0: mus(brass(chord(name, 12), 0.5), t, 0.22)
    t += BT * 4; bar += 1
# sneaky pizzicato on top during the return attempt
for k in range(20):
    mus(pluck(midi(nm(["D5", "F5", "E5", "C#5"][k % 4] if k % 2 == 0 else "A4")), 0.25, 8), 17.45 + k * 0.125, 0.18, 0.4)

# --- D: growth riser + drum roll (19.92 – 23.22)
mus(riser(2.8, 120, 1800), 20.0, 0.5)
mus(pad([midi(nm("D2")), midi(nm("D#2"))], 3.3, 600, 0.2, 0.2), 19.95, 0.4)
tr = 20.6
while tr < 23.1:
    gap = max(0.035, 0.22 * (1 - (tr - 20.6) / 2.6))
    mus(snare(0.15), tr, 0.18 + 0.25 * (tr - 20.6) / 2.6, 0.3 * np.sin(tr * 20)); tr += gap

# --- E: hell (23.22 – 32.63): choir, organ-ish pad, heavy drums
hell = [("Dm", 0), ("Bb", 0), ("Gm", 0), ("A", 0)]
t = 23.22; k = 0
while t < 32.6:
    name = hell[k % 4][0]
    d = min(BT * 4, 32.63 - t)
    mus(choir(chord(name, 12), d + 0.2, 0.15, 0.3), t, 0.30)
    mus(pad(chord(name, 0), d + 0.2, 900, 0.1, 0.3), t, 0.25)
    mus(bass808(midi(nm({"Dm": "D1", "Bb": "A#0", "Gm": "G1", "A": "A1"}[name])) * 2, d), t, 0.40)
    for b in range(4):
        tb = t + b * BT
        if tb > 32.6: break
        mus(taiko(60, 1.0), tb, 0.55 if b % 2 == 0 else 0.35)
        mus(kick(), tb, 0.35)
        if t > 26.9: mus(brass(chord(name, 12), 0.35), tb, 0.14 if b % 2 == 0 else 0.0)
    t += BT * 4; k += 1
# pause after the roar: drone only
mus(pad([midi(nm("D1")) * 2, midi(nm("A1")) * 2], 1.0, 300, 0.05, 0.6), P[0], 0.35)

# --- F: lounge for "спокойно" (33.3 – 35.62)
for i, (name, t0) in enumerate([("Fmaj7", 33.32), ("Em7", 34.0), ("Dm7", 34.62), ("Cmaj7", 35.1)]):
    fr = {"Fmaj7": ["F3", "A3", "C4", "E4"], "Em7": ["E3", "G3", "B3", "D4"], "Dm7": ["D3", "F3", "A3", "C4"], "Cmaj7": ["C3", "E3", "G3", "B3"]}[name]
    mus(epiano([midi(nm(x)) for x in fr], 0.9), t0, 0.32)
    mus(pluck(midi(nm(fr[0])) / 2, 0.6, 4), t0, 0.35)
for k in range(9):
    mus(hp(noise(int(0.05 * SR)), 5000) * np.exp(-tt(int(0.05 * SR)) * 60) * 0.5, 33.32 + k * 0.255, 0.2, 0.5)  # shaker
# --- G: silence in the pause before "Тихо, блять" (nothing scheduled)
# --- H: "Тихо, блять" low hit, "Я тут главный" hell drop
mus(boom(1.4, 70, 35), WS(76) - 0.02, 0.45)
g = WS(78)
mus(lp(boom(3.0, 120, 28), 160), g, 0.9)              # sub-only so "тут главный" stays clear
mus(choir(chord("Dm", 12) + [midi(nm("A4"))], 1.9, 0.5, 0.8), g, 0.35)
mus(brass(chord("Dm", 12), 1.0, 0.01, 0.6), WE(80) - 0.05, 0.4)
for b in range(3): mus(lp(taiko(55, 1.0), 300), g + b * 0.25, 0.5)
# --- I: sad trombone when the demon backs away
for i, (m, d) in enumerate([("D4", 0.16), ("C#4", 0.16), ("C4", 0.16), ("B3", 0.5)]):
    n = int(d * SR); tq = tt(n)
    vib = 1 + (0.02 * np.sin(2 * np.pi * 6 * tq) if i == 3 else 0)
    s = 2 * ((np.cumsum(midi(nm(m)) * vib) / SR) % 1) - 1
    wah = lp(s, 500) * (0.5 + 0.5 * np.cos(2 * np.pi * 3 * tq)) + lp(s, 1600) * (0.5 - 0.5 * np.cos(2 * np.pi * 3 * tq))
    mus(wah * env(n, 0.01, 0.05), 38.4 + sum([0.16, 0.16, 0.16][:i]), 0.35)

# --- J: boss groove (39.55 – 46.15) boom-bap + dark piano
BPM2 = 92; B2 = 60 / BPM2
t = 39.55; bar = 0
while t < 46.1:
    name = ["Dm", "Dm", "Bb", "A"][bar % 4]
    mus(piano(chord(name, 12), B2 * 2), t, 0.28)
    mus(piano(chord(name, 12), B2 * 2), t + B2 * 2.5, 0.18)
    mus(bass808(midi(nm({"Dm": "D2", "Bb": "A#1", "A": "A1"}[name])), B2 * 1.5), t, 0.45)
    for b in range(4):
        tb = t + b * B2
        if tb > 46.1: break
        if b in (0, 2): mus(kick(), tb, 0.55)
        if b == 2: mus(kick(), tb + B2 * 0.5, 0.35)
        if b in (1, 3): mus(snare(), tb, 0.35); mus(clap(), tb, 0.2)
        for h in range(2): mus(hat(), tb + h * B2 / 2, 0.16)
    t += B2 * 4; bar += 1
mus(brass(chord("Dm", 12), 0.6), 42.31, 0.22)  # "курьером"

# --- K: chase (46.15 – 47.9)
for k in range(28):
    tk = 46.15 + k * 0.0625
    mus(strings([midi(nm(["D5", "A4"][k % 2]))], 0.06, 0.003, 0.02, 4000), tk, 0.12, 0.3)
for b in range(7):
    mus(kick(), 46.15 + b * 0.25, 0.45); mus(snare(0.15), 46.15 + b * 0.25 + 0.125, 0.22)
# --- L: mafia theme (48.0 – 51.45): mandolin tremolo + accordion-ish pad, A minor
mel2 = [("E5", 0.45), ("A5", 0.45), ("C6", 0.3), ("B5", 0.3), ("A5", 0.3), ("C6", 0.3), ("A5", 0.3), ("B5", 0.3), ("A5", 0.3), ("F5", 0.3), ("G5", 0.3), ("E5", 0.6)]
tm = 48.0
for m, d in mel2:
    if tm > 51.4: break
    k = 0
    while k * 0.06 < d - 0.02:
        mus(pluck(midi(nm(m)), 0.12, 10), tm + k * 0.06, 0.10, 0.2); k += 1
    tm += d
for name, t0 in [("Am", 48.0), ("Am", 48.9), ("E", 49.8), ("Am", 50.6)]:
    mus(pad(chord(name, 12), 0.95, 1400, 0.05, 0.2), t0, 0.16)
    mus(pluck(chord(name, -12)[0], 0.7, 6), t0, 0.35)
# --- M: arena announcement (51.45 – 56.12)
t = 51.45; bar = 0
while t < 56.05:
    name = ["Dm", "Bb", "Gm", "A"][bar % 4]
    mus(brass(chord(name, 12), BT * 0.5), t, 0.2)
    mus(pad(chord(name, 0), BT * 4, 1000, 0.05, 0.2), t, 0.18)
    for b in range(4):
        tb = t + b * BT
        if tb > 56.05: break
        mus(kick(), tb, 0.5); mus(taiko(70, 0.6), tb + BT / 2, 0.2)
        if b % 2: mus(clap(), tb, 0.25)
    t += BT * 4; bar += 1
mus(boom(1.6, 90, 30), WS(115), 0.55)
# --- N/O: reaction stinger, stare drone + heartbeat
mus(strings([midi(nm(x)) for x in ["D5", "D#5", "A5"]], 0.8, 0.02, 0.4, 5000), 56.12, 0.2)
mus(pad([midi(nm("D1")) * 2, midi(nm("D#1")) * 2], 3.1, 350, 0.3, 0.4), 56.92, 0.4)
for k in range(3):
    hb = P[5] + 0.02 + k * 0.5
    if hb > 59.85: break
    mus(kick(0.9, 0.3), hb, 0.6); mus(kick(0.6, 0.3), hb + 0.16, 0.45)
# --- P: dark trap under the threat (59.88 – 64.75)
t = 59.88; bar = 0
while t < 64.7:
    name = ["Dm", "Bb", "Gm", "A"][bar % 4]
    mus(choir(chord(name, 12), BT * 4 + .1, 0.3, 0.3), t, 0.16)
    mus(bass808(midi(nm({"Dm": "D1", "Bb": "A#0", "Gm": "G1", "A": "A1"}[name])) * 2, BT * 3), t, 0.45)
    for b in range(8):
        tb = t + b * BT / 2
        if tb > 64.7: break
        mus(hat(), tb, 0.14); mus(hat(), tb + BT / 4, 0.08)
        if b in (0, 5): mus(kick(), tb, 0.45)
        if b in (2, 6): mus(clap(), tb, 0.3)
    t += BT * 4; bar += 1
# --- Q: "бабушка" hit, evil laugh, КОНЕЦ
bab = WS(131)
mus(boom(3.0, 130, 28), bab, 0.8)
mus(choir(chord("Dm", 12) + [midi(nm("D5"))], 2.0, 0.02, 1.2), bab, 0.4)
mus(brass(chord("Dm", 12), 0.8, 0.01, 0.5), bab, 0.35)
mus(boom(3.2, 140, 26), 65.35, 0.9)
mus(choir([midi(nm(x)) for x in ["D3", "A3", "D4", "F4"]], 1.0, 0.01, 0.9), 65.35, 0.45)
mus(brass([midi(nm(x)) for x in ["D3", "A3", "D4"]], 0.9, 0.01, 0.7), 65.35, 0.4)

# ================================================================ sound effects
def kaching():
    n = int(0.9 * SR); t = tt(n); s = np.zeros(n)
    for f, g in ((2093, 1), (2637, .7), (3520, .5), (4186, .3)):
        s += g * np.sin(2 * np.pi * f * t) * np.exp(-t * 4)
    k = int(0.09 * SR); s[k:] += s[:-k] * 0.8
    s[:int(0.03 * SR)] += bp(noise(int(0.03 * SR)), 1500, 6000) * 0.8
    return s * 0.35
def scratch(dur=0.32):
    n = int(dur * SR); t = tt(n)
    f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 4.5 * t))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + sweep_noise(n, 400, 3000, 0.4, lambda u: abs(np.sin(u * np.pi * 3))) * 0.8
    return s * env(n, 0.005, 0.05)
def whoosh(dur=0.35, up=True):
    n = int(dur * SR); u = np.linspace(0, 1, n)
    s = sweep_noise(n, 300 if up else 3000, 3000 if up else 300, 0.5)
    return s * np.sin(np.pi * u) ** 1.5 * 1.3
def clang():
    n = int(1.2 * SR); t = tt(n); s = np.zeros(n)
    for f, d in ((523, 3), (1187, 4), (1840, 5), (2650, 7), (3510, 9)):
        s += np.sin(2 * np.pi * f * t) * np.exp(-t * d)
    return (s * 0.25 + bp(noise(n), 2000, 8000) * np.exp(-t * 40)) * 0.8
def crunch(dur, rate=14):
    n = int(dur * SR); s = np.zeros(n); t0 = 0.0
    while t0 < dur:
        m = int(0.05 * SR); i = int(t0 * SR)
        b = bp(noise(m), 1500 + rng.random() * 2500, 7000) * np.exp(-tt(m) * 50)
        s[i:i + m] += b[: max(0, min(m, n - i))]
        t0 += 1 / rate * (0.6 + rng.random() * 0.8)
    return s
def burp():
    n = int(0.35 * SR); t = tt(n)
    f = 95 + 20 * np.sin(2 * np.pi * 9 * t)
    s = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return bp(s, 200, 1200) * (np.abs(noise(n)) * 0.3 + 0.7) * env(n, 0.02, 0.1) * 0.9
def zap(dur=0.12):
    n = int(dur * SR); t = tt(n)
    s = np.sign(np.sin(2 * np.pi * (400 + rng.random() * 600) * t)) * 0.3 + hp(noise(n), 3000) * 0.4
    return s * np.exp(-t * 25)
def paper(dur):
    n = int(dur * SR); s = hp(noise(n), 2500); am = (rng.random(n // 400 + 1) ** 3).repeat(400)[:n]
    return s * am * env(n, 0.02, 0.1) * 0.7
def thud(f=70, dur=0.4):
    n = int(dur * SR); t = tt(n)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 14) + lp(noise(n), 1200) * np.exp(-t * 40) * 0.6
def stamp(): s = thud(90, 0.4); s[: int(0.02 * SR)] += bp(noise(int(0.02 * SR)), 800, 4000); return s
def rumble(dur):
    n = int(dur * SR); s = lp(noise(n), 90, 4) * 6
    return s * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * tt(n))) * env(n, 0.3, 0.4)
def crash(dur=1.2):
    n = int(dur * SR); t = tt(n)
    s = lp(noise(n), 6000) * np.exp(-t * 5) * 0.7
    for k in range(10):
        i = int(rng.random() * 0.5 * SR); m = int(0.3 * SR); f = 2000 + rng.random() * 4000
        addat(s, i, np.sin(2 * np.pi * f * tt(m)) * np.exp(-tt(m) * 15) * 0.25)
    return s
def snap():
    n = int(0.08 * SR); t = tt(n)
    return hp(noise(n), 2500) * np.exp(-t * 90) * 1.2 + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 80) * 0.3
def portal_hum(dur):
    n = int(dur * SR); t = tt(n)
    s = lp(saw(48, n, (-0.01, 0.01)), 250) * 0.6
    s += sweep_noise(n, 200, 1200, 0.3, lambda u: 0.5 + 0.5 * np.sin(u * 40)) * 0.35
    for k in range(int(dur * 4)):
        i = int(rng.random() * n)
        addat(s, i, zap(0.06) * 0.5)
    return s * env(n, 0.3, 0.5)
def growl(dur, f=55):
    n = int(dur * SR); t = tt(n)
    fr = f * (1 + 0.1 * np.sin(2 * np.pi * 3 * t) + 0.05 * lp(noise(n), 20) * 5)
    s = 2 * ((np.cumsum(fr) / SR) % 1) - 1
    s = bp(s * (0.6 + 0.4 * np.abs(lp(noise(n), 30)) * 4), 80, 900)
    return np.tanh(s * 2) * env(n, 0.2, 0.4)
def slurp():
    n = int(0.45 * SR); return sweep_noise(n, 400, 2500, 0.2) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * tt(n))) * env(n, 0.03, 0.1)
def clink():
    n = int(0.4 * SR); t = tt(n)
    return (np.sin(2 * np.pi * 3100 * t) + 0.6 * np.sin(2 * np.pi * 4700 * t)) * np.exp(-t * 14) * 0.3
def fire(dur):
    n = int(dur * SR); s = bp(noise(n), 300, 3000) * 0.6
    for k in range(int(dur * 25)):
        i = int(rng.random() * n); m = int(0.01 * SR); addat(s, i, hp(noise(m), 2000) * 1.5)
    return s * env(n, 0.05, 0.6)
def ticks(dur, rate=16):
    n = int(dur * SR); s = np.zeros(n); m = int(0.015 * SR)
    for k in range(int(dur * rate)):
        i = int(k / rate * SR); addat(s, i, hp(noise(m), 3000) * np.exp(-tt(m) * 300) * (1 if k % 2 else 0.6))
    return s
def alarm(dur=0.5):
    n = int(dur * SR); t = tt(n); f = np.where((t * 24).astype(int) % 2, 2400, 1900)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.15 * env(n, 0.01, 0.05)
def pop():
    n = int(0.12 * SR); t = tt(n); f = 600 + 900 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
def ding(f=1760):
    n = int(1.0 * SR); t = tt(n)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4)) * np.exp(-t * 3) * 0.35
def squeak():
    n = int((0.08 + rng.random() * 0.07) * SR); t = tt(n)
    f = (1800 + rng.random() * 900) * (1 + 0.3 * t / t[-1]) * (1 + 0.04 * np.sin(2 * np.pi * 40 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.01, 0.03) * 0.35
def feedback(dur=0.6):
    n = int(dur * SR); t = tt(n)
    return np.sin(2 * np.pi * 2650 * t * (1 + 0.003 * np.sin(2 * np.pi * 6 * t))) * (t / dur) ** 2 * env(n, 0.05, 0.08) * 0.25
def taps(dur, rate, f0=1200, g=0.5):
    n = int(dur * SR); s = np.zeros(n); m = int(0.04 * SR)
    for k in range(int(dur * rate)):
        i = int(k / rate * SR); addat(s, i, bp(noise(m), f0, f0 * 3) * np.exp(-tt(m) * 80) * g)
    return s

# --- scene 1
sfx(pop(), 0.02, 0.3)
sfx(kaching(), WS(5) + 0.1, 0.9)
sfx(whoosh(0.3), 1.05, 0.4)
for k in range(6): sfx(ding(2400 + k * 300), 2.95 + k * 0.12, 0.15, 0.3 * np.sin(k))   # sparkles
sfx(scratch(), 5.10, 0.9)
sfx(thud(60, 0.5), WS(14), 0.4)
sfx(ticks(0.7, 18), 6.62, 0.6); sfx(alarm(0.35), 6.98, 0.5)
for k in range(12):
    tq = 7.45 + k * 0.15 + rng.random() * 0.05
    if tq < 9.15: sfx(squeak(), tq, 0.5, 0.2)
sfx(pop(), 7.4, 0.4); sfx(pop(), 8.55, 0.4)
# --- scene 2
sfx(clang(), 9.52, 0.7); sfx(boom(0.8, 140, 50), 9.52, 0.5); sfx(whoosh(0.5), 9.5, 0.4)
sfx(whoosh(0.3), 9.8, 0.3)
sfx(crunch(1.1, 16), 10.22, 0.8)
sfx(pop(), 11.32, 0.5); sfx(burp(), 11.6, 0.8)
sfx(crunch(0.95, 12), 12.25, 0.75)
for k in range(5): sfx(zap(0.1), 12.35 + k * 0.18, 0.35, 0.3 * (k % 2 * 2 - 1))
sfx(whoosh(0.2), WS(30) - 0.08, 0.5); sfx(boom(0.9, 120, 45), WS(30), 0.55)
sfx(paper(1.2), 15.1, 0.5)
sfx(kaching(), WS(33), 0.6)
sfx(stamp(), WS(36), 0.9)
# --- scene 3
sfx(taps(2.4, 7, 900, 0.35), 17.45, 0.6)
sfx(pop(), 17.9, 0.35)
sfx(rumble(4.6), 20.1, 0.9)
sfx(growl(0.8, 70), WS(45), 0.35)
for k, tq in enumerate([21.4, 21.48, 21.56, 21.64, 21.72, 21.8, 21.88]): sfx(whoosh(0.35), tq, 0.3, 0.6 * np.sin(k * 2))
sfx(crash(1.4), 21.9, 0.6, -0.4); sfx(crash(1.2), 22.25, 0.5, 0.4)
sfx(whoosh(0.4), 22.82, 0.5)
sfx(boom(2.2, 110, 30), 23.22, 1.0)
sfx(zap(0.3), 23.45, 0.4); sfx(crash(0.9), 24.0, 0.5, -0.5)
# --- scene 4
sfx(snap(), 24.92, 0.9)
sfx(boom(1.5, 80, 30), 25.3, 0.6); sfx(whoosh(0.8), 25.2, 0.5)
sfx(portal_hum(8.0), 25.3, 0.35)
sfx(growl(2.2, 48), 27.0, 0.45); sfx(rumble(2.3), 27.0, 0.7)
sfx(crash(1.0), 29.0, 0.5); sfx(boom(1.2, 90, 35), 29.0, 0.5)
sfx(growl(2.9, 42), 29.85, 0.12)   # roar bed under the demon line
for k in range(2): sfx(growl(0.3, 60), P[0] + 0.05 + k * 0.32, 0.35)  # heavy breathing
sfx(slurp(), WS(74), 0.6)
sfx(clink(), P[1] + 0.05, 0.6)
sfx(lp(boom(2.5, 100, 28), 200), WS(78), 0.6); sfx(fire(1.4), WE(80) - 0.1, 0.6)
sfx(whoosh(0.4, False), 38.38, 0.4)
# --- scene 5
sfx(ticks(0.6, 18), 38.95, 0.6); sfx(alarm(0.3), 39.3, 0.4)
for k in range(4): sfx(thud(45, 0.4), WS(84) + k * 0.17, 0.5)
sfx(pop(), WS(89) - 0.05, 0.6); sfx(stamp(), 42.62, 0.8)
sfx(whoosh(0.25), 43.6, 0.4); sfx(ding(2093), 44.45, 0.6); sfx(kaching(), WS(93), 0.7)
# --- scene 6
sfx(taps(1.7, 18, 1500, 0.4), 46.15, 0.6); sfx(whoosh(0.4), 46.1, 0.4)
sfx(thud(55, 0.6), 47.92, 0.9); sfx(hp(noise(int(0.02 * SR)), 1000) * 0.8, 47.92, 0.6)
sfx(thud(55, 0.5), 48.2, 0.6)
sfx(whoosh(0.25), WS(101), 0.3)
sfx(thud(90, 0.25), 50.42, 0.7); sfx(thud(90, 0.25), 50.57, 0.7); sfx(feedback(0.55), 50.65, 0.7)
for k in range(10): sfx(pop(), 51.5 + k * 0.45, 0.12, np.sin(k * 3))   # confetti poppers
sfx(whoosh(0.2), WS(115) - 0.1, 0.4)
sfx(whoosh(0.3), 56.05, 0.4)
# --- scene 7
sfx(pop(), 60.12, 0.5); sfx(hp(noise(int(0.015 * SR)), 2000), 60.85, 0.6); sfx(ding(1568), 60.9, 0.5)
sfx(boom(1.0, 70, 35), 61.48, 0.35)
sfx(whoosh(0.25), WS(131) - 0.15, 0.5); sfx(clang(), WS(131) + 0.05, 0.45)
sfx(fire(2.5), 61.6, 0.25)
sfx(scratch(0.2), 64.75, 0.0)

# ================================================================ mix
def reverb(x, dur=1.8, decay=3.0, wet=0.25):
    n = int(dur * SR); t = tt(n)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = lp(noise(n), 5000) * np.exp(-t * decay); ir[0] = 0; ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x + out * wet

raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(BUILD, "voice_fx.wav"), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
voice = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
V = np.zeros(N); V[: len(voice)] = voice[:N]
pk = np.max(np.abs(V)); V = V / pk * 0.89

# sidechain ducking from the voice envelope
e = np.abs(V); win = int(0.02 * SR)
e = np.convolve(e, np.ones(win) / win, mode="same")
sm = np.zeros_like(e); a_att, a_rel = np.exp(-1 / (0.01 * SR)), np.exp(-1 / (0.35 * SR))
# fast IIR envelope follower (vectorised in blocks)
blk = 256; acc = 0.0
for i in range(0, N, blk):
    m = e[i:i + blk].max()
    acc = m if m > acc else acc * (a_rel ** blk) + m * (1 - a_rel ** blk)
    sm[i:i + blk] = acc
duck = 1 - 0.55 * np.clip(sm / 0.08, 0, 1)

MUSr = reverb(MUS, 1.6, 2.8, 0.22)
SFXr = reverb(SFX, 1.2, 4.0, 0.15)
mpk = np.max(np.abs(MUSr)); MUSr = MUSr / mpk
spk = np.max(np.abs(SFXr)); SFXr = SFXr / spk
out = np.zeros((N, 2))
out += MUSr * duck[:, None] * 0.30
out += SFXr * (1 - 0.35 * np.clip(sm / 0.08, 0, 1))[:, None] * 0.42
out += V[:, None] * 0.95
out = np.tanh(out * 1.05) / np.tanh(1.05)
out = out[: int(DUR * SR)]
out *= 0.97 / np.max(np.abs(out))
fade = int(0.3 * SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-c:a", "pcm_s16le", os.path.join(BUILD, "mix.wav")], input=out.astype(np.float32).tobytes(), check=True)
print("mix ok", out.shape[0] / SR)
