# Voice track: comedic pauses, character voice FX, word timings, lip-sync data.
# Output: build/voice_dry.wav, build/voice_fx.wav, data.js (words, mouths, keys)
import json, os, subprocess
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)
SR = 44100
FPS = 30

# ------------------------------------------------------------------ load
def load_mp3(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def save_wav(path, x):
    x = np.asarray(x, dtype=np.float32)
    ch = 1 if x.ndim == 1 else x.shape[1]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(ch),
                    "-i", "-", "-c:a", "pcm_s16le", path], input=x.tobytes(), check=True)

def ff_filter(x, af):
    """Run a mono float signal through an ffmpeg audio filter, same length out."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          "-af", af, "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                         input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    out = np.zeros(len(x)); n = min(len(x), len(y)); out[:n] = y[:n]
    return out

voice = load_mp3(os.path.join(HERE, "voice_original.mp3"))
DUR_ORIG = len(voice) / SR

# ------------------------------------------------------------------ words (script spelling)
raw_words = json.load(open(os.path.join(HERE, "words_whisper.json")))
words = []
for w in raw_words:
    txt = w["w"]
    if txt == "тинге.": txt = "тенге."
    if txt == "с" and words and words[-1]["w"] == "зарплату":
        continue  # whisper split "семечками" -> "с семечками"; script says "семечками"
    words.append(dict(s=w["s"], e=w["e"], w=txt))
for i, w in enumerate(words):
    if w["w"].startswith("семечками"):
        w["s"] = words[i - 1]["e"]

def find(seq, start=0):
    """Index of the first word sequence match (case/punct-insensitive) at or after start."""
    norm = lambda s: s.lower().strip(".,!?;:«»")
    seq = [norm(s) for s in seq.split()]
    for i in range(start, len(words) - len(seq) + 1):
        if all(norm(words[i + k]["w"]) == seq[k] for k in range(len(seq))):
            return i
    raise KeyError(seq)

# speaker spans (word index ranges, inclusive)
D0 = find("Кто позвал меня"); D1 = find("этот мир") + 1
H0 = find("Тихо блять я тут главный"); H1 = H0 + 4
M0 = find("Эй человек"); M1 = find("квартире бесплатно") + 1
C0 = find("Подпишись блять"); C1 = len(words) - 1
for i, w in enumerate(words):
    w["sp"] = "n"
    if D0 <= i <= D1: w["sp"] = "d"
    if H0 <= i <= H1 or M0 <= i <= M1 or C0 <= i <= C1: w["sp"] = "h"

# exact segment boundaries in original time (in clean digital silence, checked by RMS scan)
SEG = {
    "demon": (29.85, 32.625),
    "ham1": (35.00, 37.10),
    "mic": (49.25, 53.955),
    "ham2": (56.90, 58.16),
    "ham3": (58.16, DUR_ORIG),
}
# comedic pauses inserted into silences: (original time, seconds)
PAUSES = [
    (32.630, 0.65),   # after the demon's roar: echo tail, heavy breathing
    (34.970, 0.55),   # beat before "Тихо, блять, я тут главный"
    (37.150, 0.55),   # demon backs away in fear
    (41.280, 0.40),   # beat before "...зарплату семечками"
    (53.960, 0.35),   # after the mic announcement
    (56.850, 0.50),   # stare into the lens before "Подпишись"
    (58.160, 0.30),   # beat before "...твоя бабушка"
]
TAIL = 1.6  # outro after the last word

def remap(t):
    return t + sum(d for p, d in PAUSES if p <= t)

# ------------------------------------------------------------------ character FX (on original timeline)
fx = voice.copy()
dry = voice.copy()

def seg(a, b):
    return int(a * SR), int(b * SR)

def fade_mask(n, f=0.01):
    m = np.ones(n); k = int(f * SR)
    m[:k] = np.linspace(0, 1, k); m[-k:] = np.linspace(1, 0, k)
    return m

def reverb_ir(dur, decay, seed=3, bright=4000):
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * decay)
    sos = butter(2, bright, "low", fs=SR, output="sos")
    ir = sosfilt(sos, ir); ir[0] = 0
    return ir / np.sqrt(np.sum(ir ** 2))

wet_layers = []  # (orig_start, signal) reverb tails, mixed after the pauses are inserted

# Demon: ~-6 semitones, sub-octave layer, grit, big cave reverb
a, b = seg(*SEG["demon"])
x = voice[a:b]
p1 = ff_filter(x, "rubberband=pitch=0.74:pitchq=quality")
p2 = ff_filter(x, "rubberband=pitch=0.50:pitchq=quality")
d = p1 + 0.30 * p2
d = np.tanh(d * 1.7) / np.tanh(1.7)
sos = butter(2, [70, 7000], "band", fs=SR, output="sos")
d = sosfilt(sos, d) * 1.15
fx[a:b] = d * fade_mask(len(d))
wet_layers.append((SEG["demon"][0], fftconvolve(d, reverb_ir(2.2, 2.6))[: len(d) + int(1.4 * SR)] * 0.42))

# Hamster: a touch lower = tiny body, boss voice (keeps the male narrator timbre)
for key in ("ham1", "mic", "ham2", "ham3"):
    a, b = seg(*SEG[key])
    x = voice[a:b]
    h = ff_filter(x, "rubberband=pitch=0.90:pitchq=quality")
    if key == "mic":
        sos = butter(2, [220, 6500], "band", fs=SR, output="sos")
        h = np.tanh(sosfilt(sos, h) * 1.6) / np.tanh(1.6) * 0.95
        slap = np.zeros(len(h) + int(0.5 * SR))
        for dly, g in ((0.11, 0.32), (0.22, 0.16), (0.33, 0.07)):
            k = int(dly * SR); slap[k:k + len(h)] += h * g
        wet_layers.append((SEG[key][0], slap + np.pad(fftconvolve(h, reverb_ir(1.2, 4.5))[: len(h)] * 0.18,
                                                         (0, len(slap) - len(h)))))
    else:
        wet_layers.append((SEG[key][0], fftconvolve(h, reverb_ir(0.9, 6.0))[: len(h) + int(0.6 * SR)] * 0.12))
    fx[a:b] = h * fade_mask(len(h))

# ------------------------------------------------------------------ insert pauses
def with_pauses(x):
    out, last = [], 0
    for p, d in PAUSES:
        i = int(p * SR)
        out.append(x[last:i]); out.append(np.zeros(int(d * SR))); last = i
    out.append(x[last:])
    out.append(np.zeros(int(TAIL * SR)))
    return np.concatenate(out)

dry_n = with_pauses(dry)
fx_n = with_pauses(fx)
for t0, w in wet_layers:
    i = int(remap(t0) * SR)
    n = min(len(w), len(fx_n) - i)
    fx_n[i:i + n] += w[:n]
DUR = len(fx_n) / SR
save_wav(os.path.join(BUILD, "voice_dry.wav"), dry_n)
save_wav(os.path.join(BUILD, "voice_fx.wav"), fx_n)

def remap_start(t):
    for p, d in PAUSES:  # whisper starts can lead the audio by a few ms: keep them after a pause
        if p - 0.12 < t < p:
            return remap(p)
    return remap(t)

def remap_end(t):
    for p, d in PAUSES:  # ...and ends can overshoot into it
        if p <= t < p + 0.12:
            return remap(p) - d
    return remap(t)

for w in words:
    w["s"] = round(remap_start(w["s"]), 3); w["e"] = round(remap_end(w["e"]), 3)

# ------------------------------------------------------------------ lip-sync (per frame, per speaker)
NF = int(np.ceil(DUR * FPS))
win = int(0.032 * SR)
sos_v = butter(2, [200, 3500], "band", fs=SR, output="sos")
sos_lo = butter(2, [250, 1000], "band", fs=SR, output="sos")
sos_hi = butter(2, [1000, 3800], "band", fs=SR, output="sos")
vb = sosfilt(sos_v, dry_n); lo = sosfilt(sos_lo, dry_n); hi = sosfilt(sos_hi, dry_n)
db = np.full(NF, -120.0); ratio = np.zeros(NF)
for f in range(NF):
    c = int((f / FPS + 0.02) * SR)  # look slightly ahead: mouths lead the sound
    s0, s1 = max(0, c - win // 2), min(len(dry_n), c + win // 2)
    if s1 <= s0: continue
    db[f] = 20 * np.log10(np.sqrt(np.mean(vb[s0:s1] ** 2)) + 1e-9)
    el = np.mean(lo[s0:s1] ** 2); eh = np.mean(hi[s0:s1] ** 2)
    ratio[f] = el / (el + eh + 1e-12)

def speaker_at(t):
    for w in words:
        if w["s"] - 0.08 <= t <= w["e"] + 0.06:
            return w["sp"]
    return None

spk = [speaker_at(f / FPS) for f in range(NF)]
mouth = {"n": [0] * NF, "d": [0] * NF, "h": [0] * NF}
rnd = [0] * NF
# normalise per contiguous speaker run so loud and quiet lines both articulate
f = 0
while f < NF:
    sp = spk[f]; g = f
    while g < NF and spk[g] == sp: g += 1
    if sp:
        seg_db = db[f:g]; voiced = seg_db[seg_db > -60]
        ref = np.percentile(voiced, 90) if len(voiced) else -20
        med = np.median(ratio[f:g][seg_db > -60]) if len(voiced) else 0.5
        acc = 0.0
        for k in range(f, g):
            v = np.clip((db[k] - (ref - 22)) / 22, 0, 1) ** 1.3
            acc = v if v > acc else acc * 0.3 + v * 0.7
            mouth[sp][k] = round(float(acc), 3)
            rnd[k] = round(float(np.clip(0.5 + (ratio[k] - med) * 3.0, 0, 1)), 2)
    f = g
data = dict(fps=FPS, dur=round(DUR, 3), nf=NF, words=words, mouth=mouth, round=rnd,
            pauses=[[round(remap(p) - d, 3), d] for p, d in PAUSES])
with open(os.path.join(HERE, "data.js"), "w") as fh:
    fh.write("const DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
print("duration", DUR, "frames", NF)
for i, w in enumerate(words):
    print(i, w["s"], w["e"], w["sp"], w["w"])
