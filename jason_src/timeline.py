# Builds the master timeline from the narration:
#  * word timings (faster-whisper large-v3) snapped to the real speech envelope
#  * script spelling for every word (captions show the script text, not ASR text)
#  * short comedic pauses inserted into existing silences
# Outputs: build/voice.wav (narration on the final timeline) and timeline.json.
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("BUILD", os.path.join(HERE, "build"))
SR = 44100
FPS = 30

# The narration, phrase by phrase, exactly as in the script (18 scenes).
SCRIPT = [
    "Мы с другом приехали отдохнуть в лес.",
    "Всё было нормально, пока за нами не пришёл сам Джейсон Вурхиз.",
    "И, сука, мой друг решил с ним познакомиться.",
    "Я говорю: Тихо! Это Джейсон! Не двигайся!",
    "А этот гений распахивает окно и орёт: Джейсон! Брат! А ты в Майнкрафт играешь?!",
    "Я думал, он шутит. Но нет, этот долбоёб начал фотографировать его со вспышкой!",
    "Мы выбежали из домика и понеслись по лесу.",
    "Я ору: Беги, блять!",
    "А он остановился шнурки завязывать!",
    "Мы спрятались за деревом.",
    "Джейсон проходит рядом.",
    "И тут мой друг громко чихает.",
    "Я ему: Заткнись!",
    "А он шепчет: Брат, может, скажем, что нас нет дома?",
    "И тут Джейсон появляется прямо перед нами.",
    "Мой друг спокойно протягивает ему телефон: Братан, сфоткай нас, только горизонтально.",
    "А потом добавляет: И чё такой злой? Девушка бросила?",
    "Я пережил Джейсона. Но своего друга я, блять, не переживу.",
]

# Quoted lines -> who says them on screen (1 = scared friend, 2 = idiot friend).
# (scene, first word, last word) 1-based word indices inside the scene phrase.
QUOTES = [
    (4, 3, 7, 1, "whisper"),
    (5, 8, 13, 2, "shout"),
    (8, 3, 4, 1, "shout"),
    (13, 3, 3, 1, "hiss"),
    (14, 4, 10, 2, "whisper"),
    (16, 7, 11, 2, "talk"),
    (17, 4, 9, 2, "talk"),
]

# Comedic pauses: (time in the ORIGINAL narration, inserted seconds). All inside silences.
GAPS = [
    (19.45, 0.50),   # after "...Майнкрафт играешь?!"  -> Jason just stares
    (38.55, 0.50),   # after "...громко чихает."       -> the sneeze lands
    (44.30, 0.45),   # after "...нас нет дома?"         -> dead silence before the jump scare
    (57.15, 0.75),   # after "Девушка бросила?"         -> long silent stare
]
TAIL = 1.5           # hold on the final title after the last word (room for the sad trombone)


def decode(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def env_db(a, sr, hop_s=0.01):
    hop = int(sr * hop_s)
    n = len(a) // hop
    rms = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms)


def snap(words, db):
    """Trim each ASR word to the voiced run around its loudness peak.
    ASR tends to glue the silence before a phrase onto its first word; growing the run
    outwards from the peak (tolerating short dips for plosives) drops breaths and tails."""
    out = []
    for s, e, w in words:
        i0, i1 = int(round(s * 100)), max(int(round(s * 100)) + 1, int(round(e * 100)))
        seg = db[i0:i1]
        if len(seg) == 0 or seg.max() < -58:
            out.append([s, e, w]); continue
        # a voiced run touching the span start that ends in a real pause is the previous
        # word's tail: skip it when another voiced run follows inside this span
        if seg[0] > -50:
            k = 0
            while k < len(seg) and seg[k] > -50: k += 1
            q = k
            while q < len(seg) and seg[q] <= -50: q += 1
            if q - k >= 12 and q < len(seg) - 2:
                i0 += q; seg = seg[q:]
            elif q - k >= 12:
                # nothing voiced left: the word really starts at the next onset
                j = i1
                while j < min(len(db), i1 + 40) and db[j] <= -45: j += 1
                out.append([j / 100.0, j / 100.0 + 0.1, w]); continue
        p = int(np.argmax(seg))
        thr = max(-50.0, seg[p] - 22.0)
        lo = p; dip = 0; k = p
        while k > 0:
            k -= 1
            if seg[k] > thr: lo = k; dip = 0
            else:
                dip += 1
                if dip > 8: break
        hi = p; dip = 0; k = p
        while k < len(seg) - 1:
            k += 1
            if seg[k] > thr: hi = k; dip = 0
            else:
                dip += 1
                if dip > 8: break
        ns, ne = (i0 + lo) / 100.0, (i0 + hi + 1) / 100.0
        if ne - ns < 0.08:
            ne = ns + 0.08
        out.append([ns, ne, w])
    return out


def shift(t):
    return t + sum(d for g, d in GAPS if t >= g)


def main():
    voice_src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "voice.mp3")
    asr = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "words_asr.json")))
    os.makedirs(BUILD, exist_ok=True)

    a16 = decode(voice_src, 16000)
    words = snap(asr, env_db(a16, 16000))

    tokens = [(si + 1, wi + 1, w) for si, ph in enumerate(SCRIPT) for wi, w in enumerate(ph.split())]
    assert len(tokens) == len(words), (len(tokens), len(words))

    # narration on the final timeline
    a = decode(voice_src, SR)
    parts, prev = [], 0
    for g, d in GAPS:
        i = int(g * SR)
        parts += [a[prev:i], np.zeros(int(d * SR), np.float32)]
        prev = i
    parts.append(a[prev:])
    total = sum(d for _, d in GAPS) + len(a) / SR + TAIL
    v = np.concatenate(parts)
    v = np.concatenate([v, np.zeros(int(total * SR) - len(v), np.float32)])
    import wave
    with wave.open(os.path.join(BUILD, "voice.wav"), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())

    # per-frame mouth-open value from the narration envelope
    n_frames = int(round(total * FPS))
    hop = SR // FPS
    env = []
    for f in range(n_frames):
        seg = v[f * hop:(f + 1) * hop]
        r = np.sqrt((seg ** 2).mean() + 1e-12) if len(seg) else 1e-6
        env.append(round(float(np.clip((20 * np.log10(r) + 46) / 26, 0, 1)), 3))

    out_words = []
    for (si, wi, txt), (s, e, _) in zip(tokens, words):
        out_words.append({"scene": si, "i": wi, "w": txt, "s": round(shift(s), 3), "e": round(shift(e), 3)})

    quotes = []
    for sc, w0, w1, who, mode in QUOTES:
        ws = [w for w in out_words if w["scene"] == sc and w0 <= w["i"] <= w1]
        quotes.append({"who": who, "mode": mode, "s": ws[0]["s"], "e": ws[-1]["e"]})

    json.dump({"duration": round(total, 3), "fps": FPS, "words": out_words, "quotes": quotes,
               "gaps": [[round(shift(g) - d, 3), d] for g, d in GAPS], "env": env},
              open(os.path.join(HERE, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("duration", round(total, 3), "frames", n_frames)
    for sc in range(1, 19):
        ws = [w for w in out_words if w["scene"] == sc]
        print(f"S{sc:02d} {ws[0]['s']:6.2f}-{ws[-1]['e']:6.2f}  " + " ".join(f"{w['w']}@{w['s']:.2f}" for w in ws))


if __name__ == "__main__":
    main()
