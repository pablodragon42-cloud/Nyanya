# Frame compositor: scenes -> transitions -> captions / final title -> grade, grain, vignette.
#   python render.py still 12.5 30.1 ...        -> build/stills/f_XX.XX.png
#   python render.py range i0 i1 out.mp4        -> rendered video segment (no audio)
import os, sys, random, subprocess
import numpy as np
from PIL import Image, ImageDraw
from gfx import *
import scenes
from scenes import SCENES, WORDS, DUR, ws, we

BUILD = os.environ.get("BUILD", os.path.join(HERE, "build"))

# cut time -> transition (same vocabulary as the reference video)
CUTS = {2.35: "whip", 3.94: "glitch", 5.70: "punch", 7.36: "whip", 9.6: "whip", 13.3: "punch", 14.54: "whip", 32.40: "punch",
        17.57: "glitch", 20.05: "punch", 21.73: "whip", 25.9: "glitch", 27.43: "whip", 28.85: "punch", 30.9: "whip",
        33.35: "whip", 36.65: "punch", 40.95: "glitch", 46.04: "glitch", 46.66: "punch", 51.79: "punch", 59.5: "flash"}
WHIP_VERTICAL = {2.35}


# ------------------------------------------------------------------ captions (reference style)
def chunks():
    ws_ = [[w["s"], w["e"], w["w"]] for w in WORDS if w["scene"] < 18]
    out, cur = [], []
    for i, w_ in enumerate(ws_):
        cur.append(w_)
        end_punct = w_[2][-1] in ",.?!:"
        nxt_gap = ws_[i + 1][0] - w_[1] if i + 1 < len(ws_) else 9
        text_len = sum(len(x[2]) + 1 for x in cur)
        if end_punct or len(cur) >= 3 or text_len > 16 or nxt_gap > 0.3:
            out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for i, c in enumerate(out):
        st = c[0][0] - 0.05
        en = min(c[-1][1] + 0.35, out[i + 1][0][0] - 0.05) if i + 1 < len(out) else c[-1][1] + 0.5
        res.append((st, en, c))
    return res


CHUNKS = chunks()
_cap_cache = {}


def cap_img(ci, active):
    key = (ci, active)
    if key in _cap_cache: return _cap_cache[key]
    st, en, c = CHUNKS[ci]
    f = font("Oswald-Bold.ttf", 104)
    words = [w_[2].upper() for w_ in c]
    space = 26
    widths = [f.getlength(w_) for w_ in words]
    tw = sum(widths) + space * (len(words) - 1)
    im = Image.new("RGBA", (int(tw) + 60, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 30
    for i, w_ in enumerate(words):
        col = YEL if i == active else (255, 255, 255)
        d.text((x, 20), w_, font=f, fill=col, stroke_width=10, stroke_fill=INK)
        x += widths[i] + space
    _cap_cache[key] = im
    return im


def draw_captions(im, t):
    if t >= 59.45: return im
    for ci, (st, en, c) in enumerate(CHUNKS):
        if st <= t < en:
            act = -1
            for i, w_ in enumerate(c):
                if t >= w_[0] - 0.03: act = i
            ci_im = cap_img(ci, act)
            k = eout((t - st) / 0.1)
            sc = lerp(0.75, 1.0, k) * min(1.0, 1000 / ci_im.width)
            paste_c(im, ci_im, W / 2, 1390, scale=sc)
    return im


# ------------------------------------------------------------------ final title (reference's closing card style)
TITLE = [  # (scene-18 word indices, y, size, colour)
    ((1, 2), 1120, 98, WHITE), ((3,), 1232, 98, WHITE),
    ((4, 5, 6), 1392, 84, WHITE), ((7, 8), 1498, 92, WHITE), ((9, 10), 1640, 132, YEL)]
_title_cache = {}


def word18(i):
    return next(w for w in WORDS if w["scene"] == 18 and w["i"] == i)


def draw_title(im, t):
    d = ImageDraw.Draw(im, "RGBA")
    a = clamp((t - 59.5) / 0.4)
    for i in range(24):
        y0 = 980 + i * 40
        d.rectangle([0, y0, W, y0 + 40], fill=(0, 0, 0, int(a * 190 * (i / 23) ** 1.2)))
    for idxs, y, size, col in TITLE:
        f = font("RussoOne.ttf", size)
        words = [word18(i)["w"].upper() for i in idxs]
        widths = [f.getlength(w_) for w_ in words]
        space = size * 0.28
        tw = sum(widths) + space * (len(words) - 1)
        scale = min(1.0, 1010 / tw)
        x = W / 2 - tw * scale / 2
        for i, w_ in zip(idxs, words):
            ts = word18(i)["s"] - 0.04
            if t >= ts:
                k = eout((t - ts) / 0.14)
                key = (w_, size, col)
                if key not in _title_cache:
                    _title_cache[key] = text_img(w_, f, col, stroke=10)
                ti = _title_cache[key]
                sc = scale * lerp(1.35, 1.0, k)
                ww = f.getlength(w_) * scale
                paste_c(im, ti, x + ww / 2, y, scale=sc, alpha=clamp(k * 1.5))
            x += (f.getlength(w_) + space) * scale
    return im


# ------------------------------------------------------------------ transitions + post
def transitions(im, t, fi):
    for c, kind in CUTS.items():
        dt = t - c
        if -0.12 < dt < 0.22:
            if kind == "flash" and dt >= 0:
                im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), max(0, 0.85 * (1 - dt / 0.2)))
            elif kind == "punch" and dt >= 0:
                z = 1 + 0.15 * (1 - eout(dt / 0.22))
                im = im.resize((int(W * z), int(H * z)), Image.BILINEAR).crop(
                    (int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
            elif kind == "whip":
                amt = 1 - abs(dt) / 0.15 if abs(dt) < 0.15 else 0
                if amt > 0:
                    a = np.asarray(im).astype(np.float32)
                    acc = np.zeros_like(a)
                    n = 8
                    for i in range(n):
                        acc += np.roll(a, int((i - n / 2) * 22 * amt), axis=0 if c in WHIP_VERTICAL else 1)
                    im = Image.fromarray((acc / n).astype(np.uint8))
            elif kind == "glitch":
                amt = 1 - abs(dt) / 0.15 if abs(dt) < 0.15 else 0
                if amt > 0:
                    a = np.asarray(im).copy()
                    rnd = random.Random(fi)
                    sh = int(30 * amt)
                    a[:, :, 0] = np.roll(a[:, :, 0], sh, axis=1)
                    a[:, :, 2] = np.roll(a[:, :, 2], -sh, axis=1)
                    for _ in range(8):
                        y0 = rnd.randint(0, H - 80); h = rnd.randint(10, 80)
                        a[y0:y0 + h] = np.roll(a[y0:y0 + h], rnd.randint(-120, 120), axis=1)
                    im = Image.fromarray(a)
    return im


def scene_at(t):
    fn = SCENES[0][1]
    for st, f in SCENES:
        if t >= st: fn = f
    return fn


def frame_at(t, fi):
    fr = Frame()
    info = scene_at(t)(fr, t) or {}
    im = fr.finish()
    im = transitions(im, t, fi)
    fl = info.get("flash", 0)
    if fl > 0.01:
        im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), clamp(fl))
    if info.get("title"):
        im = draw_title(im, t)
    else:
        im = draw_captions(im, t)
    return grain_vignette(im, fi, info.get("vig", 1.0), info.get("grade"))


def render_range(i0, i1, path):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(i0, i1):
        p.stdin.write(frame_at(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "still":
        out = os.path.join(BUILD, "stills"); os.makedirs(out, exist_ok=True)
        for ts in sys.argv[2:]:
            t = float(ts)
            frame_at(t, int(t * FPS)).save(os.path.join(out, f"f_{t:05.2f}.png"))
    else:
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
