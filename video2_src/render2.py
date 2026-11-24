# "Неуязвимый 2: Аркадий Паровозов против Омни-Мэна" — procedural 9:16 renderer.
# Reuses the part-1 pipeline (video_src/render.py) so both parts share one look.
import math, random, sys, os, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video_src"))
import art2  # noqa: E402  (also puts video_src on sys.path)
from art2 import hero, closeup  # noqa: E402
import render as R  # noqa: E402
from art import INK, vgrad, cloud, skyline_layer  # noqa: E402
from render import cam, shake, text_img, paste_c, tint, speed_lines, ease, eout, lerp, YEL, BLU, RED  # noqa: E402

FONTS = os.path.join(HERE, "..", "video_src", "fonts")


@lru_cache(None)
def _font(name, size):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if name.startswith("Oswald"):
        try:
            f.set_variation_by_axes([700])
        except Exception:
            pass
    return f


R._font = _font
F = R.F
W, H, FPS = 1080, 1920, 30
DUR = 80.0
SKYBLUE = (120, 200, 255)

# =====================================================================  words / timing
FIX = {"Омнимена,": "Омни-Мэна,", "Омнимену": "Омни-Мэну", "Омнимен": "Омни-Мэн", "все": "всё", "еще": "ещё",
       "раздается": "раздаётся"}


def load_words():
    ws = []
    for ln in open(os.path.join(HERE, "words.txt"), encoding="utf-8"):
        a, b, w_ = ln.strip().split(" ", 2)
        w_ = w_.strip()
        a, b = float(a), float(b)
        if ws and (w_.startswith("-") or not any(ch.isalnum() for ch in w_)):
            ws[-1][1] = min(b, a + 0.4); ws[-1][2] += w_; continue
        ws.append([a, b, FIX.get(w_, w_)])
    # the whole message line is quoted in the voiceover
    return ws


WORDS = load_words()
# who speaks a quoted line (for speaker tags + mouth flaps)
LINES = [("ark", 24.2, 29.0), ("omni", 30.2, 31.9), ("ark", 33.4, 37.9), ("mark", 65.7, 67.6)]


def speaking(who, t):
    for w_, a, b in LINES:
        if w_ == who and a <= t < b:
            for wa, wb, _ in WORDS:
                if wa <= t < wb:
                    return int(t * 9) % 3 != 2
    return False


def mouth_for(who, t, idle="neutral"):
    return "open" if speaking(who, t) else idle


# =====================================================================  helpers

def put(dst, spr, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    paste_c(dst, spr, cx, cy, scale=scale, alpha=alpha, rot=rot)


def silhouette(spr, col=(10, 10, 20), rim=(255, 240, 180)):
    a = spr.getchannel("A")
    out = Image.new("RGBA", spr.size, rim + (0,))
    rimm = a.filter(ImageFilter.MaxFilter(9))
    out.putalpha(rimm)
    body = Image.new("RGBA", spr.size, col + (255,))
    body.putalpha(a)
    out.alpha_composite(body)
    return out


def rays_bg(c1, c2, cx=540, cy=760, n=24, grad=None, spin=0.0):
    im = vgrad(W, H, *grad).convert("RGB") if grad else Image.new("RGB", (W, H), c2)
    d = ImageDraw.Draw(im)
    for i in range(n):
        a0 = i / n * math.tau + spin
        a1 = a0 + math.tau / (2 * n)
        Rr = 3000
        if i % 2 == 0:
            d.polygon([(cx, cy), (cx + math.cos(a0) * Rr, cy + math.sin(a0) * Rr), (cx + math.cos(a1) * Rr, cy + math.sin(a1) * Rr)], fill=c1)
    return im


def ono(txt, size, fill=YEL, stroke=RED, sw=14):
    return text_img(txt, F("RussoOne.ttf", size), fill, stroke=sw, sfill=stroke)


def puffs(im, pts, col=(245, 245, 250)):
    """pts: list of (x, y, r, alpha) steam puffs (drawn with an ink outline)."""
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x, y, r, a in pts:
        if a <= 0 or r <= 1:
            continue
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(255 * a),), outline=(14, 12, 20, int(200 * a)), width=4)
    if im.mode == "RGBA":
        im.alpha_composite(ov); return im
    out = im.convert("RGBA"); out.alpha_composite(ov); return out.convert("RGB")


def steam_trail(path_fn, t, n=14, span=0.9, r0=26, r1=90, seed=3):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        age = (i / n) * span
        x, y = path_fn(t - age)
        jx, jy = rnd.uniform(-25, 25), rnd.uniform(-25, 25)
        k = age / span
        pts.append((x + jx * k * 3, y + jy * k * 3, lerp(r0, r1, k), 0.9 * (1 - k)))
    return pts[::-1]


def shockwave(d, cx, cy, k, rmax=900, col=(255, 255, 255), w=26):
    if 0 <= k <= 1:
        r = rmax * eout(k)
        ww = max(2, int(w * (1 - k)))
        d.ellipse([cx - r, cy - r * .55, cx + r, cy + r * .55], outline=col, width=ww)


def impact_frame(im, col=(220, 30, 40)):
    g = ImageOps.grayscale(im).point(lambda v: 255 if v < 110 else 0)
    out = Image.merge("RGB", (g, g, g))
    return Image.blend(out, Image.new("RGB", im.size, col), 0.25)


# =====================================================================  backgrounds

@lru_cache(None)
def sky_pan(variant="battle"):
    """Tall sky panorama with clouds and the city far below."""
    Wb, Hb = 2200, 4200
    if variant == "battle":
        im = vgrad(Wb, Hb, (24, 50, 120), (250, 160, 90)).convert("RGBA")
    else:
        im = vgrad(Wb, Hb, (40, 110, 210), (190, 225, 250)).convert("RGBA")
    d = ImageDraw.Draw(im)
    rnd = random.Random(11)
    for i in range(26):
        y = rnd.randint(200, 3200)
        cloud(d, rnd.randint(0, Wb), y, rnd.randint(70, 170),
              (255, 236, 220, 255) if y > 1800 else (230, 225, 240, 255))
    far, _ = skyline_layer(Wb, Hb, 3900, (120, 90, 110), (255, 200, 120), 41, 200, 600, 60, 140, outline=False, windows=True)
    im.alpha_composite(far)
    near, _ = skyline_layer(Wb, Hb, 4150, (70, 60, 84), (255, 220, 130), 43, 300, 800, 120, 240)
    im.alpha_composite(near)
    return im.convert("RGB")


@lru_cache(None)
def cloud_bank():
    im = Image.new("RGBA", (1600, 1300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(21)
    for i in range(40):
        x, y, r = rnd.randint(0, 1600), rnd.randint(500, 1300), rnd.randint(110, 230)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 238, 226, 255))
    for i in range(28):
        x, y, r = rnd.randint(0, 1600), rnd.randint(750, 1300), rnd.randint(100, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 196, 200, 255))
    return im


def panic_sky(t=0.0):
    return sky_pan("battle")


# =====================================================================  phone / message (bridge from part 1)
MSG_WORDS = "Если ты это читаешь — найди Марка Грейсона. Он единственный, кто может остановить моего отца.".split(" ")
MSG_T = {5: 4.24, 6: 4.74, 7: 5.16, 8: 5.96, 9: 6.18, 10: 6.96, 11: 7.08, 12: 7.34, 13: 7.92, 14: 8.20}


def msg_screen(sw, sh, t):
    scr = vgrad(sw, sh, (20, 24, 40), (50, 30, 60))
    d = ImageDraw.Draw(scr)
    S = sw / 484
    d.rectangle([0, 0, sw, 230 * S], fill=(30, 34, 50))
    d.ellipse([30 * S, 120 * S, 100 * S, 190 * S], fill=(60, 90, 200))
    d.text((50 * S, 128 * S), "?", font=F("RussoOne.ttf", int(46 * S)), fill=(255, 255, 255))
    d.text((120 * S, 130 * S), "Неизвестный", font=F("Oswald-Bold.ttf", int(40 * S)), fill=(255, 255, 255))
    d.text((sw - 150 * S, 60 * S), "21:51", font=F("Oswald-Bold.ttf", int(34 * S)), fill=(200, 200, 210))
    f = F("Oswald-Bold.ttf", int(44 * S))
    lh, maxw, x0, y0 = 60 * S, sw - 140 * S, 60 * S, 312 * S
    lines, cur, cw = [], [], 0
    sp = f.getlength(" ")
    for i, w_ in enumerate(MSG_WORDS):
        wl = f.getlength(w_)
        if cur and cw + sp + wl > maxw:
            lines.append(cur); cur, cw = [], 0
        cur.append((i, w_)); cw += (sp if cw else 0) + wl
    lines.append(cur)
    bh = len(lines) * lh + 50 * S
    d.rounded_rectangle([30 * S, 290 * S, sw - 40 * S, 290 * S + bh], radius=int(34 * S), fill=(245, 245, 250))
    for li, ln in enumerate(lines):
        x = x0
        for i, w_ in ln:
            wl = f.getlength(w_)
            on = i in MSG_T and t >= MSG_T[i] - 0.03
            if on:
                d.rounded_rectangle([x - 6, y0 + li * lh + 6 * S, x + wl + 6, y0 + li * lh + 56 * S], radius=8, fill=(255, 214, 0))
            d.text((x, y0 + li * lh), w_, font=f, fill=(200, 20, 30) if (on and i in (6, 7)) else (20, 20, 30))
            x += wl + sp
    # timer widget under the message (it keeps counting)
    remain = timer_remain(t)
    d.rounded_rectangle([30 * S, 330 * S + bh, sw - 40 * S, 450 * S + bh], radius=int(28 * S), fill=(120, 10, 20))
    d.text((60 * S, 350 * S + bh), "⏱" if False else "ОСТАЛОСЬ", font=F("Oswald-Bold.ttf", int(40 * S)), fill=(255, 200, 200))
    tt = f"{int(remain // 60):02d}:{int(remain % 60):02d}"
    d.text((sw - 200 * S, 345 * S + bh), tt, font=F("RussoOne.ttf", int(56 * S)), fill=(255, 255, 255))
    return scr


def timer_remain(t):
    return max(0.0, 240.0 + 4.0 - t) if t < 9.0 else max(0.0, 240.0 - (t - 9.0))


@lru_cache(None)
def blurred_city():
    base, _ = R.city_base("panic")
    return base


def phone_shot(t, cx, cy, sc, bright=0.55, blur=16):
    bg = cam(blurred_city(), 800, 1800, 0.9).filter(ImageFilter.GaussianBlur(blur))
    im = ImageEnhance.Brightness(bg).enhance(bright)
    d = ImageDraw.Draw(im)
    R.draw_hand(d, cx, cy, sc)
    R.draw_phone(im, cx, cy, sc, msg_screen, t)
    d = ImageDraw.Draw(im)
    R.draw_hand(d, cx, cy, sc, front=True)
    return im


# =====================================================================  scenes

def s_open(t):
    sc = lerp(1.3, 1.4, ease(t / 4.1))
    im = phone_shot(t, 540, 1050, sc)
    if t > 3.3:
        k = ease((t - 3.3) / 0.8)
        im = cam(im, 540, lerp(960, 760, k), lerp(1.0, 1.7, k))
    if t < 3.4:
        a = min(1, t / 0.25) * (1 - max(0, (t - 3.0) / 0.4))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rectangle([0, 60, W, 330], fill=(0, 0, 0, int(150 * a)))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        k = eout(t / 0.45)
        t1 = text_img("НЕУЯЗВИМЫЙ", F("RussoOne.ttf", 120), YEL, stroke=12, sfill=BLU)
        paste_c(im, t1, 540 - 60, 170, scale=min(1, 860 / t1.width) * lerp(1.5, 1, k), alpha=a)
        t2 = text_img("2", F("RussoOne.ttf", 190), (255, 255, 255), stroke=12, sfill=RED)
        if t > 0.35:
            k2 = eout((t - 0.35) / 0.3)
            paste_c(im, t2, 960, 175, scale=lerp(2.2, 1, k2), alpha=a * k2, rot=-8)
        t3 = text_img("АРКАДИЙ ПАРОВОЗОВ ПРОТИВ ОМНИ-МЭНА", F("Oswald-Bold.ttf", 46), (255, 255, 255), stroke=5)
        if t > 0.7:
            paste_c(im, t3, 540, 290, scale=min(1, 1000 / t3.width), alpha=a * ease((t - 0.7) / 0.3))
    if t < 0.5:
        im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, t / 0.5)
    return im


def s_msg(t):
    lt = t - 4.1
    sc = 2.35
    im = phone_shot(t, 540, 1240, sc, bright=0.4, blur=20)
    z = lerp(1.0, 1.08, lt / 4.7)
    if 4.74 <= t < 5.66:
        z *= 1 + 0.06 * eout((t - 4.74) / 0.2)
    dx, dy = shake(t, 4, 3)
    return cam(im, 540 + dx, 760 + dy, z)


def s_timer(t):
    lt = t - 8.8
    bg = cam(blurred_city(), 800, 1500, 0.75).filter(ImageFilter.GaussianBlur(10))
    im = ImageEnhance.Brightness(bg).enhance(0.3)
    d = ImageDraw.Draw(im)
    remain = timer_remain(t)
    beat = math.exp(-((lt % 1.0) / 0.12))
    Rr = 380 + 12 * beat
    cx, cy = 540, 860
    d.ellipse([cx - Rr, cy - Rr, cx + Rr, cy + Rr], outline=(80, 20, 20), width=26)
    d.arc([cx - Rr, cy - Rr, cx + Rr, cy + Rr], -90, -90 + 360 * (remain / 300), fill=RED, width=26)
    ti = text_img(f"{int(remain // 60):02d}:{int(remain % 60):02d}", F("RussoOne.ttf", 230), (255, 255, 255), stroke=10)
    paste_c(im, ti, cx, cy - 10, scale=1 + 0.05 * beat)
    lab = text_img("ОСТАЛОСЬ", F("RussoOne.ttf", 90), YEL, stroke=7)
    paste_c(im, lab, cx, 330, alpha=ease(lt / 0.3))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.12, lt / 2.3), rot=lerp(0, -2, lt / 2.3))


def s_lookup(t):
    lt = t - 11.1
    im = R.city_frame(t, "alert", people=True, run=False, variant="panic")
    tilt = eout((lt - 0.35) / 1.3) * 1050
    dx, dy = shake(t, 3)
    return cam(im, 800 + dx, 1750 - tilt + dy, lerp(0.8, 0.86, lt / 1.8))


@lru_cache(None)
def sky_up_p():
    return R.sky_up("panic")


def s_omni_approach(t):
    lt = t - 12.9
    if t < 14.0:
        sky = sky_up_p().copy()
        d = ImageDraw.Draw(sky)
        k = ease(lt / 1.1)
        fx, fy = 700 + 30 * math.sin(t * 1.3), lerp(760, 900, k)
        sc = lerp(0.08, 0.5, k)
        r = 60 + 40 * math.sin(t * 9)
        d.ellipse([fx - r * 2, fy - r * 2, fx + r * 2, fy + r * 2], fill=(255, 210, 170))
        spr = hero("omni", 0.6, "neutral")
        put(sky, spr, fx, fy + 80 * sc, scale=sc / 0.6 * 0.6)
        dx, dy = shake(t, 3)
        return cam(sky, 700 + dx, 1000 + dy, lerp(0.95, 1.05, lt / 1.1))
    # wide: Omni-Man closing in over the skyline
    k = (t - 14.0) / 1.6
    hover = math.sin(t * 2) * 12
    im = R.city_frame(t, "alert", people=True, run=True, variant="panic", omni=(lerp(900, 800, k), lerp(820, 1000, k) + hover, lerp(0.16, 0.42, ease(k))))
    dx, dy = shake(t, 7, 9)
    return cam(im, 800 + dx, lerp(1450, 1550, k) + dy, lerp(0.72, 0.8, k))


def s_horn(t):
    lt = t - 15.6
    sky = cam(panic_sky(), 1100, 2300 - lt * 30, 1.0)
    im = sky.copy()
    eyes = 0
    if t > 16.4:
        eyes = int(round(-8 * ease((t - 16.4) / 0.3)))
    if t > 17.05:
        eyes = int(round(lerp(-8, 9, ease((t - 17.05) / 0.25))))
    face = closeup("omni", zoom=2.6, cy=560, mouth="neutral", eyes10=eyes)
    hov = math.sin(t * 2) * 10
    im.paste(face, (0, int(160 + hov)), face)
    d = ImageDraw.Draw(im)
    if t > 16.95:
        k = (t - 16.95)
        for j in range(4):
            shockwave(d, 980, 260, (k - j * 0.18) / 0.9, rmax=1300, col=(255, 250, 230), w=22)
        b = ono("ТУ-ТУ-У-У!", 130, fill=(255, 255, 255), stroke=RED)
        kk = eout(k / 0.25)
        paste_c(im, b, 640, 330, scale=lerp(0.3, 1.0, kk) * (1 + 0.04 * math.sin(t * 40)) * min(1, 1000 / b.width), rot=8)
        dx, dy = shake(t, 22 * math.exp(-k * 1.5) + 3, 18)
        return cam(im, W / 2 + dx, H / 2 + dy, 1.0 + 0.03 * math.exp(-k * 2))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.06, lt / 1.4))


def ark_path_arrive(t):
    k = (t - 18.55) / 1.2
    return lerp(760, 540, ease(k)), lerp(560, 900, ease(k))


def s_ark_arrive(t):
    lt = t - 18.4
    if t < 19.75:
        base = cam(sky_pan("battle"), 1100, 1300, 0.9)
        im = base.convert("RGBA")
        cb = cloud_bank()
        burst = max(0, t - 18.55)
        # clouds part from the centre
        for side in (-1, 1):
            half = cb.crop((0, 0, 800, 1300)) if side < 0 else cb.crop((800, 0, 1600, 1300))
            off = side * 600 * eout(burst / 0.9)
            im.alpha_composite(half, (int(-260 + (0 if side < 0 else 800) + off), -380))
        if t > 18.55:
            k = ease((t - 18.55) / 1.2)
            x, y = ark_path_arrive(t)
            im = puffs(im, steam_trail(ark_path_arrive, t, n=12, span=0.7, r0=20, r1=80))
            spr = hero("ark", 0.8, "smile", 0, 165)
            put(im, spr, x, y, scale=lerp(0.25, 1.05, k), rot=lerp(25, 6, k))
            if t < 18.75:
                d = ImageDraw.Draw(im)
                r = 260 * (1 - (t - 18.55) / 0.2)
                d.ellipse([760 - r, 560 - r, 760 + r, 560 + r], fill=(255, 255, 240, 255))
        im = im.convert("RGB")
        d = ImageDraw.Draw(im)
        if t > 18.6:
            speed_lines(d, 540, 900, t, n=36, r0=520, col=(255, 255, 255), w=6)
        dx, dy = shake(t, 8 * math.exp(-max(0, t - 18.55) * 2) + 2, 14)
        return cam(im, W / 2 + dx, H / 2 + dy, 1.0)
    # hero intro card
    lt = t - 19.75
    im = rays_bg((236, 60, 60), (30, 80, 200), cy=700, spin=t * 0.15, grad=None)
    d = ImageDraw.Draw(im)
    speed_lines(d, 540, 700, t, n=40, r0=480, col=(255, 255, 255), w=7)
    k = eout(lt / 0.6)
    spr = hero("ark", 1.2, "smile", 0, 165)
    put(im, spr, 540, lerp(1500, 830, k) + 10 * math.sin(lt * 3), scale=0.85)
    n1 = ono("АРКАДИЙ", 190, fill=(255, 255, 255), stroke=RED)
    n2 = ono("ПАРОВОЗОВ", 170, fill=YEL, stroke=BLU)
    if t >= 19.8:
        k1 = eout((t - 19.8) / 0.25)
        paste_c(im, n1, 540, 1250, scale=min(1, 1000 / n1.width) * lerp(1.6, 1, k1), alpha=k1)
    if t >= 20.44:
        k2 = eout((t - 20.44) / 0.25)
        paste_c(im, n2, 540, 1440, scale=min(1, 1020 / n2.width) * lerp(1.6, 1, k2), alpha=k2)
    return cam(im, W / 2, H / 2, lerp(1.1, 1.0, eout(lt / 0.8)))


def s_ark_fly(t):
    lt = t - 21.3
    bgx = 600 + lt * 900
    im = cam(sky_pan("battle"), bgx % 1400 + 400, 2400, 1.0)
    d = ImageDraw.Draw(im)
    rnd = random.Random(int(t * 30))
    for i in range(26):
        y = rnd.randint(0, H)
        x = rnd.randint(-200, W)
        d.line([(x, y), (x + rnd.randint(200, 600), y)], fill=(255, 255, 255), width=rnd.randint(2, 6))
    ax = lerp(380, 470, ease(lt / 2.9)) + 8 * math.sin(t * 7)
    ay = 1000 + 20 * math.sin(t * 3)

    def path(tt):
        return (ax - (t - tt) * 900, ay + 15 * math.sin(tt * 9))
    im = puffs(im, steam_trail(path, t, n=12, span=0.8, r0=24, r1=70))
    # Omni-Man ahead, getting closer
    if t > 22.6:
        k = ease((t - 22.6) / 1.6)
        so = hero("omni", 0.7, "neutral")
        put(im, so, lerp(1250, 900, k), 900 + 10 * math.sin(t * 2), scale=lerp(0.3, 0.75, k))
    spr = hero("ark", 0.7, "grit", 170, 170)
    put(im, spr, ax, ay, scale=0.95, rot=-80)
    dx, dy = shake(t, 4, 10)
    z = 1.0 + (0.12 * eout((t - 23.5) / 0.3) if t > 23.5 else 0)
    return cam(im, W / 2 + dx, H / 2 + dy, z)


def s_ark_shout(t):
    lt = t - 24.2
    if t < 27.0:
        im = rays_bg((60, 110, 230), (30, 70, 190), cy=700, spin=t * 0.1)
        face = closeup("ark", zoom=3.3, cy=330, mouth=mouth_for("ark", t, "smile"), eyes10=-4)
        im.paste(face, (0, 0), face)
        z = lerp(1.0, 1.1, lt / 2.8)
        if t > 24.28 and t < 24.6:
            z *= 1 + 0.06 * (1 - (t - 24.28) / 0.32)
        dx, dy = shake(t, 3, 6)
        return cam(im, W / 2 + dx, H / 2 + dy, z)
    # two-shot: Arkadiy points at Omni-Man
    lt = t - 27.0
    im = cam(sky_pan("battle"), 1100 + lt * 20, 2500, 1.0)
    so = hero("omni", 0.9, "neutral", eyes10=-8) if True else None
    put(im, so, 820, 900 + 10 * math.sin(t * 2), scale=0.85)
    sa = hero("ark", 0.9, mouth_for("ark", t, "smile"), 0, 95)
    put(im, sa, 300, 1050 + 12 * math.sin(t * 2.4), scale=0.85)
    z = lerp(1.0, 1.08, lt / 3.2)
    if t > 26.98 and t < 27.4:
        z *= 1 + 0.08 * (1 - (t - 26.98) / 0.42)
    return cam(im, W / 2, H / 2, z, rot=lerp(-2, 1, lt / 3.2))


def s_omni_who(t):
    lt = t - 30.2
    im = cam(panic_sky(), 1000, 1800, 1.1)
    im = tint(im, (120, 0, 10), 0.25)
    face = closeup("omni", zoom=4.2, cy=300, mouth=mouth_for("omni", t, "neutral"), eyes10=8)
    im.paste(face, (0, 60), face)
    return cam(im, W / 2, H / 2, lerp(1.05, 1.15, lt / 1.8), rot=lerp(4, 2, lt / 1.8))


@lru_cache(None)
def faceoff_bg():
    top = vgrad(W, H, (120, 0, 10), (230, 50, 40))
    bot = vgrad(W, H, (40, 110, 230), (20, 40, 140))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (W, 0), (W, 820), (0, 1100)], fill=255)
    return Image.composite(top, bot, m)


def s_faceoff(t):
    lt = t - 32.0
    im = faceoff_bg().copy()
    d = ImageDraw.Draw(im)
    k = eout(lt / 0.4)
    o = closeup("omni", zoom=2.2, cy=420, mouth="neutral", eyes10=8, W=W, H=1000)
    a = closeup("ark", zoom=2.2, cy=420, mouth="smile", eyes10=-6, W=W, H=1000)
    mo = Image.new("L", (W, 1000), 0)
    ImageDraw.Draw(mo).polygon([(0, 0), (W, 0), (W, 820), (0, 1000)], fill=255)
    oa = o.copy(); oa.putalpha(Image.composite(o.getchannel("A"), Image.new("L", o.size, 0), mo))
    im.paste(oa, (int(lerp(-600, -180, k)), 0), oa)
    mb = Image.new("L", (W, 1000), 0)
    ImageDraw.Draw(mb).polygon([(0, 280), (W, 0), (W, 1000), (0, 1000)], fill=255)
    aa = a.copy(); aa.putalpha(Image.composite(a.getchannel("A"), Image.new("L", a.size, 0), mb))
    im.paste(aa, (int(lerp(W + 400, 200, k)), 860), aa)
    rnd = random.Random(int(t * 12))
    pts = [(i * W / 12, 1100 + (820 - 1100) * (i / 12) + rnd.uniform(-25, 25)) for i in range(13)]
    d.line(pts, fill=(255, 255, 255), width=16)
    d.line(pts, fill=(180, 220, 255), width=6)
    vs = ono("VS", 220, fill=YEL, stroke=INK)
    paste_c(im, vs, 540, 960, scale=lerp(2.5, 1, eout((lt - 0.2) / 0.3)) if lt > 0.2 else 0.01, alpha=1 if lt > 0.2 else 0)
    return cam(im, W / 2, H / 2, lerp(1.0, 1.05, lt / 1.4))


def s_ark_intro(t):
    lt = t - 33.4
    if t < 35.3:
        im = rays_bg((236, 60, 60), (30, 80, 200), cy=650, spin=-t * 0.12)
        face = closeup("ark", zoom=2.8, cy=380, mouth=mouth_for("ark", t, "smile"))
        im.paste(face, (0, 0), face)
        z = lerp(1.0, 1.08, lt / 1.9)
        if 33.9 < t < 34.3:
            z *= 1 + 0.05 * (1 - (t - 33.9) / 0.4)
        return cam(im, W / 2, H / 2, z)
    lt = t - 35.3
    im = rays_bg((60, 120, 240), (24, 50, 150), cy=500, spin=t * 0.2)
    d = ImageDraw.Draw(im)
    fist = 165 if t > 36.9 else lerp(20, 60, ease(lt / 1.2))
    spr = hero("ark", 1.4, mouth_for("ark", t, "grit"), 0, fist)
    # emblem glow
    gl = 0.5 + 0.5 * math.sin(t * 8)
    if t > 36.9:
        gl = 1.0
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    ex, ey = 540, 821
    r = 160 + 60 * gl
    gd.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(255, 220, 120, int(120 * gl)))
    g = g.filter(ImageFilter.GaussianBlur(40))
    im = im.convert("RGBA")
    put(im, spr, 540, 1000, scale=0.85 * lerp(1.0, 1.06, lt / 2.7))
    im.alpha_composite(g)
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    if t > 36.94:
        speed_lines(d, 540, 800, t, n=50, r0=560, col=(255, 255, 255), w=8)
    z = lerp(1.0, 1.06, lt / 2.7)
    if 36.94 < t < 37.4:
        z *= 1 + 0.1 * (1 - (t - 36.94) / 0.46)
    return cam(im, W / 2, H / 2 + 60, z, rot=-3)


def s_omni_smirk(t):
    lt = t - 38.0
    im = cam(panic_sky(), 900, 2000, 1.2)
    im = ImageEnhance.Brightness(tint(im, (90, 0, 10), 0.4)).enhance(0.7)
    face = closeup("omni", zoom=5.5, cy=320, mouth="smirk" if t > 38.4 else "neutral", eyes10=0)
    im.paste(face, (0, 40), face)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 260], fill=(0, 0, 0)); d.rectangle([0, H - 260, W, H], fill=(0, 0, 0))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.1, lt / 1.4))


def s_charge(t):
    lt = t - 39.4
    im = cam(panic_sky(), 1100, 2300, 1.0)
    d = ImageDraw.Draw(im)
    speed_lines(d, 540, 900, t, n=70, r0=300, col=(255, 240, 230), w=7)
    k = (lt / 2.2) ** 2
    spr = hero("omni", 0.9, "grit", 150, 150, glow=True)
    put(im, spr, 540 + 30 * math.sin(t * 6), lerp(900, 1100, k), scale=lerp(0.25, 2.6, k))
    dx, dy = shake(t, 4 + 18 * k, 16)
    return cam(im, W / 2 + dx, H / 2 + dy, 1.0)


def s_dodge(t):
    lt = t - 41.6
    # slow-motion ramp in the middle of the dodge
    if lt < 0.6:
        st = lt
    elif lt < 1.8:
        st = 0.6 + (lt - 0.6) * 0.25
    else:
        st = 0.9 + (lt - 1.8) * 1.2
    im = cam(sky_pan("battle"), 900 + st * 300, 2000, 1.0)
    im = im.convert("RGBA")
    ay = 1000 - 360 * ease((st - 0.35) / 0.4)
    ax = 540
    sa = hero("ark", 0.8, "grit", 30, 30)
    put(im, sa, ax, ay, scale=0.9, rot=lerp(0, 18, ease((st - 0.35) / 0.4)))
    # Omni-Man streaks through where Arkadiy was
    ox = lerp(-500, 1600, st / 1.6)
    so = hero("omni", 0.8, "grit", 165, 165)
    for i in range(5):
        put(im, so, ox - i * 70, 1040, scale=0.95, rot=-80, alpha=1.0 if i == 0 else 0.25 - i * 0.04)
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    for i in range(12):
        y = 900 + i * 22
        d.line([(ox - 900, y), (ox - 300, y)], fill=(255, 255, 255), width=3)
    if 0.6 < lt < 1.8:
        im = tint(im, (40, 60, 120), 0.18)
    return cam(im, W / 2, H / 2, lerp(1.0, 1.08, lt / 2.3))


def s_punch(t):
    lt = t - 43.9
    if t < 44.9:
        im = rays_bg((60, 110, 230), (20, 50, 150), cy=700, spin=t * 0.4)
        face = closeup("ark", zoom=2.2, cy=500, mouth="grit", armL=120)
        im.paste(face, (0, 0), face)
        return cam(im, W / 2, H / 2, lerp(1.0, 1.1, lt / 1.0), rot=lerp(0, -4, lt))
    if t < 45.6:
        k = (t - 44.9) / 0.7
        im = cam(panic_sky(), 1100, 2200, 1.0)
        d = ImageDraw.Draw(im)
        speed_lines(d, 540, 900, t, n=80, r0=200, col=(255, 255, 255), w=8)
        so = hero("omni", 0.8, "open", 10, 10)
        put(im, so, 540, 900, scale=0.8)
        # giant red glove rushing to camera
        r = lerp(60, 700, k ** 2)
        d.ellipse([540 - r, 1200 - r - k * 300, 540 + r, 1200 + r - k * 300], fill=(214, 32, 40), outline=INK, width=int(8 + 20 * k))
        d.arc([540 - r * .7, 1200 - r * .7 - k * 300, 540 + r * .7, 1200 + r * .7 - k * 300], 200, 340, fill=INK, width=int(4 + 12 * k))
        return cam(im, W / 2, H / 2, 1.0)
    if t < 45.75:
        base = cam(panic_sky(), 1100, 2200, 1.0)
        so = hero("omni", 0.8, "open", 40, 40)
        put(base, so, 540, 900, scale=0.9, rot=15)
        im = impact_frame(base)
        b = ono("БАМ!", 280, fill=YEL, stroke=RED)
        paste_c(im, b, 540, 600, scale=1.1, rot=-10)
        return im
    k = (t - 45.75) / 0.55
    im = cam(panic_sky(), 1100, 2200, 1.0)
    d = ImageDraw.Draw(im)
    shockwave(d, 540, 900, k * 1.2, rmax=1100, col=(255, 255, 255), w=30)
    so = hero("omni", 0.8, "open", 60, 60)
    put(im, so, lerp(540, 820, k), lerp(900, 380, k), scale=lerp(0.9, 0.2, k), rot=lerp(15, 260, k))
    b = ono("БАМ!", 280, fill=YEL, stroke=RED)
    paste_c(im, b, 540, 600, scale=lerp(1.1, 1.25, k), rot=-10, alpha=1 - k * 0.6)
    dx, dy = shake(t, 25 * (1 - k) + 3, 20)
    return cam(im, W / 2 + dx, H / 2 + dy, 1.0)


def s_aerial(t):
    lt = t - 46.3
    cy = lerp(3300, 2200, ease(lt / 3.5))
    im = cam(sky_pan("battle"), 1100, cy, lerp(0.75, 0.9, lt / 3.5))
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    trail_o, trail_a = [], []
    for i in range(18):
        tt = t - i * 0.03
        a = tt * 3.2
        trail_o.append((540 + math.cos(a) * 260, 900 + math.sin(a * 1.3) * 300 - (tt - 46.3) * 60))
        trail_a.append((540 + math.cos(a + math.pi) * 260, 900 + math.sin(a * 1.3 + math.pi) * 300 - (tt - 46.3) * 60))
    d.line(trail_o, fill=(255, 255, 255, 220), width=10)
    d.line(trail_o, fill=(220, 40, 40, 255), width=4)
    im = puffs(im, [(x, y, 10 + i * 2.5, 0.8 * (1 - i / 18)) for i, (x, y) in enumerate(trail_a)])
    so = hero("omni", 0.4, "grit", 150, 150)
    sa = hero("ark", 0.4, "grit", 150, 150)
    put(im, so, trail_o[0][0], trail_o[0][1], scale=0.55, rot=math.degrees(t * 3.2) % 360 - 180)
    put(im, sa, trail_a[0][0], trail_a[0][1], scale=0.55, rot=math.degrees(t * 3.2 + math.pi) % 360 - 180)
    im = im.convert("RGB")
    d = ImageDraw.Draw(im)
    for c in (47.0, 47.85, 48.7, 49.4):
        k = (t - c) / 0.45
        if 0 <= k <= 1:
            shockwave(d, 540, 900 - (c - 46.3) * 60, k, rmax=700, col=(255, 250, 220), w=24)
            if k < 0.15:
                im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.5)
                d = ImageDraw.Draw(im)
    dx, dy = shake(t, 5, 8)
    return cam(im, W / 2 + dx, H / 2 + dy, 1.0)


def s_grab(t):
    lt = t - 49.8
    im = cam(panic_sky(), 900 + lt * 120, 2000, 1.0)
    d = ImageDraw.Draw(im)
    speed_lines(d, 540, 700, t, n=40, r0=500, col=(255, 255, 255), w=5)
    sa = hero("ark", 0.7, "grit", 20, 20)
    put(im, sa, 560 + 40 * math.sin(t * 5), 560, scale=lerp(0.5, 0.55, lt))
    k = ease(lt / 2.1)
    so = hero("omni", 1.0, "grit", 120, 120, eyes10=0)
    put(im, so, 540, lerp(1700, 1350, k), scale=lerp(1.3, 1.55, k))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.08, lt / 2.1), rot=lerp(-3, 3, lt / 2.1))


def s_speed(t):
    lt = t - 51.9
    if t < 52.9:
        im = rays_bg((80, 160, 255), (20, 60, 180), cy=700, spin=t * 0.8)
        d = ImageDraw.Draw(im)
        speed_lines(d, 540, 700, t, n=60, r0=420, col=(255, 255, 255), w=7)
        face = closeup("ark", zoom=3.0, cy=330, mouth="grit", eyes10=0)
        im.paste(face, (0, 0), face)
        if t > 52.4:
            im = puffs(im, [(540 + math.cos(a) * 520 * (t - 52.4) * 2, 1400 + math.sin(a) * 200 * (t - 52.4) * 2, 120, 0.85)
                            for a in np.linspace(0, math.tau, 9)])
        dx, dy = shake(t, 6 if t > 52.4 else 2, 16)
        return cam(im, W / 2 + dx, H / 2 + dy, lerp(1.0, 1.12, lt))
    lt = t - 52.9
    im = cam(sky_pan("battle"), 1100, 2500, 1.0)
    d = ImageDraw.Draw(im)
    # Omni-Man grabs empty air
    so = hero("omni", 0.6, "open", 110, 110)
    put(im, so, 300, 1150, scale=0.75)
    k = min(1, lt / 0.7)
    hx = lerp(500, 1300, ease(k))
    for i in range(10):
        y = 900 + i * 14
        d.line([(lerp(-200, 380, ease(k)), y), (hx - 80, y + (i - 5) * 3)], fill=(90, 170, 255) if i % 2 else (255, 255, 255), width=10)
    im = puffs(im, [(lerp(-100, hx, j / 12) , 960 + random.Random(j).uniform(-50, 50), 40 + j * 4, 0.6) for j in range(12)])
    d = ImageDraw.Draw(im)
    for j in range(3):
        kk = (lt - 0.15 - j * 0.12) / 0.6
        if 0 <= kk <= 1:
            r = 120 + 500 * eout(kk)
            d.ellipse([700 - r * .35, 960 - r, 700 + r * .35, 960 + r], outline=(255, 255, 255), width=max(2, int(18 * (1 - kk))))
    if lt < 0.7:
        sa = hero("ark", 0.6, "grit", 170, 170)
        put(im, sa, hx, 960, scale=0.7, rot=-82)
    b = ono("ВЖУХ!", 170, fill=(255, 255, 255), stroke=BLU)
    if lt > 0.2:
        paste_c(im, b, 760, 620, scale=lerp(0.5, 1.0, eout((lt - 0.2) / 0.2)) * min(1, 900 / b.width), rot=6)
    dx, dy = shake(t, 10 * math.exp(-lt * 2), 18)
    return cam(im, W / 2 + dx, H / 2 + dy, lerp(1.0, 1.06, lt / 1.8))


def s_first_time(t):
    lt = t - 54.7
    im = cam(panic_sky(), 900, 2100, 1.15)
    im = tint(im, (100, 0, 10), 0.35)
    face = closeup("omni", zoom=4.8, cy=300, mouth="grit" if t > 55.9 else "neutral", eyes10=-3)
    im.paste(face, (0, 40), face)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 240], fill=(0, 0, 0)); d.rectangle([0, H - 240, W, H], fill=(0, 0, 0))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.14, ease(lt / 2.6)))


def s_catch(t):
    lt = t - 57.3
    im = cam(panic_sky(), 1000, 2600 - lt * 40, 1.0)
    d = ImageDraw.Draw(im)
    fist = lerp(60, 165, ease((t - 58.1) / 0.5))
    so = hero("omni", 1.2, "grit", 35, fist, eyes10=-6)
    sa = hero("ark", 0.6, "grit", 60 + 25 * math.sin(t * 12), 60 + 25 * math.cos(t * 12))
    put(im, so, 640, 1080, scale=1.0)
    put(im, sa, 140 + 8 * math.sin(t * 15), 1500, scale=0.9, rot=4)
    d = ImageDraw.Draw(im)
    d.ellipse([124 - 60, 1175 - 60, 124 + 60, 1175 + 60], fill=(214, 28, 38), outline=INK, width=6)
    d.line([(90, 1160), (158, 1160)], fill=INK, width=4)
    if t > 58.1:
        k = (t - 58.1) / 0.5
        if k < 1:
            d.ellipse([820 - 200 * k, 430 - 200 * k, 820 + 200 * k, 430 + 200 * k], outline=(255, 255, 255), width=8)
    z = lerp(1.05, 1.0, lt / 2.2)
    dx, dy = shake(t, 4 + (8 if t > 58.1 else 0), 12)
    return cam(im, W / 2 + dx, H / 2 + dy - 60, z, rot=-4)


def mark_path(t):
    k = (t - 59.6) / 3.4
    return 540 + 30 * math.sin(t), lerp(560, 760, ease(k))


def s_figure(t):
    lt = t - 59.5
    if 60.9 <= t < 61.7:
        im = cam(panic_sky(), 1000, 2600, 1.0)
        face = closeup("omni", zoom=3.6, cy=320, mouth="grit", eyes10=int(round(lerp(-6, 10, ease((t - 60.9) / 0.4)))))
        im.paste(face, (0, 40), face)
        return cam(im, W / 2, H / 2, lerp(1.0, 1.05, (t - 60.9) / 0.8))
    base = cam(sky_pan("battle"), 1100, 1500, 0.95)
    im = base.convert("RGBA")
    x, y = mark_path(t)
    k = ease(lt / 3.6)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r = 260 + 80 * math.sin(t * 4)
    gd.ellipse([x - r, y - r * 1.4, x + r, y + r * 1.4], fill=(255, 230, 150, 170))
    for i in range(16):
        a = i / 16 * math.tau + t * 0.2
        gd.polygon([(x, y), (x + math.cos(a) * 1600, y + math.sin(a) * 1600), (x + math.cos(a + 0.08) * 1600, y + math.sin(a + 0.08) * 1600)],
                   fill=(255, 240, 200, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    im.alpha_composite(glow)
    sil = silhouette(hero("mark", 0.8, "neutral"))
    put(im, sil, x, y, scale=lerp(0.35, 0.8, k))
    cb = cloud_bank()
    off = 400 * eout(lt / 2.0)
    im.alpha_composite(cb, (int(-260 - off), 520))
    return cam(im.convert("RGB"), W / 2, H / 2, lerp(1.0, 1.12, k))


@lru_cache(None)
def mark_bg():
    return rays_bg((255, 235, 140), (90, 140, 240), cy=760, grad=((255, 210, 60), (40, 90, 210)))


def s_mark_reveal(t):
    lt = t - 63.2
    im = mark_bg().copy()
    d = ImageDraw.Draw(im)
    speed_lines(d, 540, 760, t, n=50, r0=500, col=(255, 255, 255), w=8)
    k = eout(lt / 0.7)
    spr = hero("mark", 1.3, "neutral")
    put(im, spr, 540, lerp(1700, 860, k) + 12 * math.sin(lt * 3), scale=0.78)
    if t >= 63.5:
        k2 = eout((t - 63.5) / 0.25)
        n1 = text_img("МАРК", F("RussoOne.ttf", 200), YEL, stroke=12, sfill=BLU)
        paste_c(im, n1, 540, 1250, scale=lerp(1.6, 1.0, k2), alpha=k2)
    if t >= 64.08:
        k3 = eout((t - 64.08) / 0.25)
        n2 = text_img("ГРЕЙСОН", F("RussoOne.ttf", 170), YEL, stroke=12, sfill=BLU)
        paste_c(im, n2, 540, 1430, scale=lerp(1.6, 1.0, k3), alpha=k3)
    return cam(im, W / 2, H / 2, lerp(1.08, 1.0, eout(lt / 1)))


def s_mark_shout(t):
    lt = t - 64.8
    im = rays_bg((255, 220, 90), (40, 90, 210), cy=650, spin=t * 0.3)
    d = ImageDraw.Draw(im)
    if t > 65.7:
        speed_lines(d, 540, 650, t, n=60, r0=460, col=(255, 255, 255), w=8)
    face = closeup("mark", zoom=3.4, cy=330, mouth=mouth_for("mark", t, "grit"))
    im.paste(face, (0, 0), face)
    z = lerp(1.0, 1.08, lt / 3)
    amp = 2
    for c in (65.78, 66.54):
        if c <= t < c + 0.4:
            z *= 1 + 0.07 * (1 - (t - c) / 0.4); amp = 14
    dx, dy = shake(t, amp, 18)
    return cam(im, W / 2 + dx, H / 2 + dy, z)


def s_omni_turn(t):
    lt = t - 67.8
    im = cam(panic_sky(), 1000, 2400, 1.1)
    im = ImageEnhance.Brightness(tint(im, (90, 0, 10), 0.35)).enhance(0.8)
    k = ease(lt / 2.6)
    face = closeup("omni", zoom=4.0, cy=310, cx=lerp(470, 515, k), mouth="grit",
                   eyes10=int(round(lerp(0, 10, k))), glow=t > 69.6)
    im.paste(face, (0, 40), face)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 240], fill=(0, 0, 0)); d.rectangle([0, H - 240, W, H], fill=(0, 0, 0))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.15, k), rot=lerp(0, -5, k))


def s_trio(t):
    lt = t - 70.6
    im = cam(sky_pan("battle"), 1100, 2700, lerp(1.0, 0.85, ease(lt / 4.1)))
    d = ImageDraw.Draw(im)
    k = eout(lt / 0.8)
    hov = math.sin(t * 2) * 10
    so = hero("omni", 0.8, "grit", 20, 20, glow=True)
    sa = hero("ark", 0.6, "grit", 0, 0)
    sm = hero("mark", 0.6, "grit", 0, 0)
    put(im, sa, lerp(-200, 230, k), 1250 + hov, scale=0.9)
    put(im, sm, lerp(1300, 850, k), 1250 - hov, scale=0.9)
    put(im, so, 540, 780 + hov * 0.6, scale=1.0)
    rnd = random.Random(int(t * 14))
    for (x0, y0) in ((260, 1050), (820, 1050)):
        pts = [(lerp(x0, 540, i / 8) + rnd.uniform(-18, 18), lerp(y0, 860, i / 8) + rnd.uniform(-18, 18)) for i in range(9)]
        if lt > 0.8:
            d.line(pts, fill=(255, 255, 255), width=8)
            d.line(pts, fill=(255, 200, 80), width=3)
    if t > 73.2:
        ti = ono("1 ПРОТИВ 2", 150, fill=YEL, stroke=INK)
        paste_c(im, ti, 540, 1600, scale=min(1, 1000 / ti.width) * lerp(1.6, 1, eout((t - 73.2) / 0.3)))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.04, lt / 4.1))


def s_who_wins(t):
    lt = t - 74.7
    im = Image.new("RGB", (W, H), (10, 8, 14))
    o = closeup("omni", zoom=3.0, cy=320, mouth="grit", glow=True, W=W, H=900)
    bgo = vgrad(W, 900, (150, 0, 10), (60, 0, 10)); bgo.paste(o, (0, 0), o)
    a = closeup("ark", zoom=2.4, cy=330, mouth="grit", W=540, H=1000)
    bga = vgrad(540, 1000, (40, 100, 230), (10, 30, 100)); bga.paste(a, (0, 0), a)
    m = closeup("mark", zoom=2.4, cy=330, mouth="grit", W=540, H=1000)
    bgm = vgrad(540, 1000, (255, 200, 40), (40, 80, 200)); bgm.paste(m, (0, 0), m)
    k1, k2, k3 = (eout((lt - s) / 0.3) for s in (0.0, 0.15, 0.3))
    im.paste(bgo, (0, int(lerp(-900, 0, k1))))
    im.paste(bga, (int(lerp(-540, 0, k2)), 920))
    im.paste(bgm, (int(lerp(W, 540, k3)), 920))
    d = ImageDraw.Draw(im)
    d.line([(0, 910), (W, 910)], fill=(255, 255, 255), width=16)
    d.line([(540, 910), (540, H)], fill=(255, 255, 255), width=16)
    if t > 75.2:
        q = ono("КТО ПОБЕДИТ?", 140, fill=(255, 255, 255), stroke=RED)
        paste_c(im, q, 540, 910, scale=min(1, 1020 / q.width) * lerp(1.7, 1, eout((t - 75.2) / 0.3)))
    return cam(im, W / 2, H / 2, lerp(1.0, 1.05, lt / 2.2))


def s_tbc(t):
    lt = t - 76.9
    im = Image.new("RGB", (W, H), (6, 6, 10))
    d = ImageDraw.Draw(im)
    for kind, x, sc in (("ark", 220, 0.55), ("omni", 540, 0.7), ("mark", 860, 0.55)):
        sil = silhouette(hero(kind, 0.6, "neutral"), col=(14, 12, 22), rim=(220, 40, 50) if kind == "omni" else (90, 160, 255))
        put(im, sil, x, 1300 if kind != "omni" else 1150, scale=sc / 0.6 * 0.75, alpha=ease(lt / 0.8))
    beat = math.exp(-((lt % 0.9) / 0.15))
    d.rectangle([0, 600 - 2 * beat, W, 604 + 2 * beat], fill=(150 + int(90 * beat), 20, 30))
    if t > 76.94:
        k = eout((t - 76.94) / 0.4)
        a = text_img("ПРОДОЛЖЕНИЕ", F("RussoOne.ttf", 120), (255, 255, 255), stroke=0, spacing=int(lerp(40, 6, k)))
        paste_c(im, a, 540, 420, alpha=k, scale=min(1, 1000 / a.width))
    if t > 77.84:
        k = eout((t - 77.84) / 0.4)
        b = text_img("СЛЕДУЕТ...", F("RussoOne.ttf", 130), YEL, stroke=0, spacing=int(lerp(30, 6, k)))
        paste_c(im, b, 540, 790, alpha=k, scale=min(1, 1000 / b.width))
    out = cam(im, W / 2, H / 2, lerp(1.0, 1.05, lt / 3.1))
    if t > DUR - 0.9:
        out = Image.blend(out, Image.new("RGB", (W, H), (0, 0, 0)), min(1, (t - (DUR - 0.9)) / 0.9))
    return out


SCENES = [(0.0, s_open), (4.1, s_msg), (8.8, s_timer), (11.1, s_lookup), (12.9, s_omni_approach), (15.6, s_horn),
          (18.4, s_ark_arrive), (21.3, s_ark_fly), (24.2, s_ark_shout), (30.2, s_omni_who), (32.0, s_faceoff),
          (33.4, s_ark_intro), (38.0, s_omni_smirk), (39.4, s_charge), (41.6, s_dodge), (43.9, s_punch),
          (46.3, s_aerial), (49.8, s_grab), (51.9, s_speed), (54.7, s_first_time), (57.3, s_catch),
          (59.5, s_figure), (63.2, s_mark_reveal), (64.8, s_mark_shout), (67.8, s_omni_turn), (70.6, s_trio),
          (74.7, s_who_wins), (76.9, s_tbc)]

CUTS = {4.1: "punch", 8.8: "glitch", 11.1: "whip", 12.9: "whip", 14.0: "flash", 15.6: "punch", 18.4: "flash",
        19.75: "flash", 21.3: "whip", 24.2: "punch", 27.0: "whip", 30.2: "glitch", 32.0: "flash", 33.4: "punch",
        35.3: "flash", 38.0: "glitch", 39.4: "whip", 41.6: "whip", 43.9: "punch", 44.9: "whip", 46.3: "flash",
        49.8: "whip", 51.9: "punch", 52.9: "flash", 54.7: "glitch", 57.3: "punch", 59.5: "flash", 60.9: "glitch",
        61.7: "glitch", 63.2: "flash", 64.8: "punch", 67.8: "glitch", 70.6: "flash", 74.7: "glitch", 76.9: "glitch"}
VERT_WHIP = {11.1, 12.9}

# =====================================================================  captions


def chunks():
    ws = WORDS
    out, cur = [], []
    for i, w_ in enumerate(ws):
        cur.append(w_)
        end_punct = w_[2].rstrip("»")[-1:] in (",", ".", "?", "!")
        nxt_gap = ws[i + 1][0] - w_[1] if i + 1 < len(ws) else 9
        text_len = sum(len(x[2]) + 1 for x in cur)
        if end_punct or len(cur) >= 3 or text_len > 16 or nxt_gap > 0.3:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    res = []
    for i, c in enumerate(out):
        st = c[0][0] - 0.05
        en = min(c[-1][1] + 0.35, out[i + 1][0][0] - 0.05) if i + 1 < len(out) else c[-1][1] + 0.5
        res.append((st, en, c))
    return res


CHUNKS = chunks()
NO_CAP = [(4.15, 8.75), (19.75, 21.3), (63.45, 64.8), (75.15, 76.9), (76.9, 81)]
SPEAKER = {"ark": ("АРКАДИЙ", SKYBLUE), "omni": ("ОМНИ-МЭН", (255, 110, 100)), "mark": ("МАРК", YEL)}


@lru_cache(maxsize=128)
def cap_img(ci, active):
    st, en, c = CHUNKS[ci]
    f = F("Oswald-Bold.ttf", 104)
    words = [w_[2].upper() for w_ in c]
    space = 26
    widths = [f.getlength(w_) for w_ in words]
    tw = sum(widths) + space * (len(words) - 1)
    im = Image.new("RGBA", (int(tw) + 60, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 30
    for i, w_ in enumerate(words):
        d.text((x, 20), w_, font=f, fill=YEL if i == active else (255, 255, 255), stroke_width=10, stroke_fill=INK)
        x += widths[i] + space
    return im


@lru_cache(None)
def tag_img(who):
    name, col = SPEAKER[who]
    ti = text_img(name, F("RussoOne.ttf", 46), (255, 255, 255), stroke=0)
    im = Image.new("RGBA", (ti.width + 50, ti.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=18, fill=col + (255,), outline=INK, width=5)
    tf = text_img(name, F("RussoOne.ttf", 46), INK, stroke=0)
    im.alpha_composite(tf, (25, 12))
    return im


def draw_captions(im, t):
    for a, b in NO_CAP:
        if a <= t < b:
            return im
    for ci, (st, en, c) in enumerate(CHUNKS):
        if st <= t < en:
            act = -1
            for i, w_ in enumerate(c):
                if t >= w_[0] - 0.03:
                    act = i
            ci_im = cap_img(ci, act)
            k = eout((t - st) / 0.1)
            sc = lerp(0.75, 1.0, k) * min(1.0, 1000 / ci_im.width)
            paste_c(im, ci_im, W / 2, 1460, scale=sc)
            for who, a, b in LINES:
                if a <= c[0][0] < b:
                    paste_c(im, tag_img(who), W / 2, 1345)
    return im


def draw_hud(im, t):
    if not (11.1 <= t < 74.7) or 19.75 <= t < 21.3 or 63.2 <= t < 64.8:
        return im
    rem = timer_remain(t)
    txt = f"{int(rem // 60):02d}:{int(rem % 60):02d}"
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([36, 70, 300, 160], radius=24, fill=(150, 10, 20), outline=INK, width=5)
    if int(t * 2) % 2 == 0:
        d.ellipse([58, 100, 88, 130], fill=(255, 255, 255))
    d.text((104, 80), txt, font=F("RussoOne.ttf", 60), fill=(255, 255, 255))
    return im


# =====================================================================  post
_rng = np.random.default_rng(2)
GRAIN = [(_rng.normal(0, 7, (H // 2, W // 2))).astype(np.float32) for _ in range(6)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.38 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)).clip(0.45, 1).astype(np.float32)[..., None]
del yy, xx


def post(im, t, fi):
    for c, kind in CUTS.items():
        dt = t - c
        if -0.12 < dt < 0.22:
            if kind == "flash" and dt >= 0:
                im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), max(0, 0.85 * (1 - dt / 0.2)))
            elif kind == "punch" and dt >= 0:
                im = cam(im, W / 2, H / 2, 1 + 0.15 * (1 - eout(dt / 0.22)))
            elif kind == "whip":
                amt = 1 - abs(dt) / 0.15 if abs(dt) < 0.15 else 0
                if amt > 0:
                    a = np.asarray(im).astype(np.float32)
                    acc = np.zeros_like(a)
                    n = 8
                    for i in range(n):
                        acc += np.roll(a, int((i - n / 2) * 18 * amt), axis=0 if c in VERT_WHIP else 1)
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
    im = draw_hud(im, t)
    im = draw_captions(im, t)
    a = np.asarray(im).astype(np.float32)
    g = np.repeat(np.repeat(GRAIN[fi % 6], 2, 0), 2, 1)[..., None]
    a = a * VIG + g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def frame_at(t, fi):
    fn = SCENES[0][1]
    for st, f in SCENES:
        if t >= st:
            fn = f
    return post(fn(t).convert("RGB"), t, fi)


def render_range(i0, i1, path):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(i0, i1):
        p.stdin.write(frame_at(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "still":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for ts in sys.argv[2:]:
            t = float(ts)
            frame_at(t, int(t * FPS)).save(os.path.join(HERE, "stills", f"f_{t:05.2f}.png"))
    elif sys.argv[1] == "sheet":
        ts = [float(x) for x in sys.argv[2:]]
        th = [frame_at(t, int(t * FPS)).resize((270, 480)) for t in ts]
        cols = 6
        rows = (len(th) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 270, rows * 480))
        for i, im in enumerate(th):
            sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
        sheet.save(os.path.join(HERE, "stills", "sheet.png"))
    else:
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
