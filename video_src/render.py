import math, random, sys, os, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import art
from art import INK, vgrad, cloud, skyline_layer, car_shape, person, char_sprite, face_closeup

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 65.5
YEL = (255, 214, 0)
BLU = (30, 80, 210)
RED = (220, 30, 40)

def F(name, size):
    return _font(name, size)

@lru_cache(None)
def _font(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)

def ease(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def eout(x):
    x = min(1, max(0, x)); return 1 - (1 - x) ** 3

def lerp(a, b, t): return a + (b - a) * t

def cam(img, cx, cy, zoom, rot=0.0, out=(W, H)):
    """Crop a view centered at (cx,cy) of img, zoom=output px per source px."""
    ow, oh = out
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a = c / zoom; b = s / zoom; d_ = -s / zoom; e = c / zoom
    x0 = cx - (a * ow / 2 + b * oh / 2)
    y0 = cy - (d_ * ow / 2 + e * oh / 2)
    return img.transform(out, Image.AFFINE, (a, b, x0, d_, e, y0), resample=Image.BILINEAR)

def shake(t, amp, freq=13.0, seed=0):
    return (amp * (math.sin(t * freq * 2.1 + seed) + .5 * math.sin(t * freq * 3.7 + seed * 2)),
            amp * (math.cos(t * freq * 1.7 + seed * 3) + .5 * math.sin(t * freq * 4.3 + seed)))

def text_img(txt, font, fill, stroke=8, sfill=INK, spacing=0):
    f = font
    bb = f.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8 + spacing * len(txt), bb[3] - bb[1] + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if spacing:
        x = 4 - bb[0]
        for ch in txt:
            d.text((x, 4 - bb[1]), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
            x += f.getlength(ch) + spacing
    else:
        d.text((4 - bb[0], 4 - bb[1]), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im

def paste_c(dst, im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BILINEAR)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    dst.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

def tint(img, col, amt):
    return Image.blend(img, Image.new("RGB", img.size, col), amt)

def speed_lines(d, cx, cy, t, n=60, r0=380, col=(255, 255, 255), seed=1, w=6):
    rnd = random.Random(seed + int(t * 20))
    for i in range(n):
        a = rnd.random() * math.tau
        r1 = r0 + rnd.random() * 300
        r2 = r1 + 300 + rnd.random() * 900
        d.line([(cx + math.cos(a) * r1, cy + math.sin(a) * r1), (cx + math.cos(a) * r2, cy + math.sin(a) * r2)],
               fill=col, width=rnd.randint(2, w))

# =====================================================================  assets
SC_BIG = (1600, 3100)

@lru_cache(None)
def city_base(variant="day"):
    Wb, Hb = SC_BIG
    if variant == "day":
        sky = vgrad(Wb, Hb, (58, 140, 228), (196, 228, 250))
    else:  # panic: smoky orange
        sky = vgrad(Wb, Hb, (70, 50, 70), (240, 140, 70))
    im = sky.convert("RGBA")
    d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for i in range(7):
        cloud(d, rnd.randint(0, Wb), rnd.randint(150, 900), rnd.randint(60, 110),
              (255, 255, 255, 255) if variant == "day" else (90, 70, 80, 255))
    far, _ = skyline_layer(Wb, Hb, 1650, (150, 182, 222) if variant == "day" else (120, 90, 100), (190, 215, 240) if variant == "day" else (160, 120, 110),
                           11, 500, 1100, 90, 180, outline=False, windows=False)
    im.alpha_composite(far)
    mid, _ = skyline_layer(Wb, Hb, 1800, (226, 150, 110) if variant == "day" else (150, 80, 70), (255, 236, 170),
                           21, 450, 950, 150, 260)
    im.alpha_composite(mid)
    near, rects = skyline_layer(Wb, Hb, 1900, (92, 110, 160) if variant == "day" else (70, 60, 80), (255, 228, 140),
                                31, 900, 1400, 220, 380)
    # only keep near buildings at the edges (street opening in the middle)
    mask = Image.new("L", (Wb, Hb), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([0, 0, 470, Hb], fill=255)
    md.rectangle([1130, 0, Wb, Hb], fill=255)
    near.putalpha(Image.composite(near.getchannel("A"), Image.new("L", (Wb, Hb), 0), mask))
    im.alpha_composite(near)
    # street
    d = ImageDraw.Draw(im)
    vp = (800, 1640)
    d.polygon([(0, Hb), (Wb, Hb), (Wb, 1900), (0, 1900)], fill=(80, 80, 92))
    d.polygon([(-200, Hb), (Wb + 200, Hb), (1040, 1900), (560, 1900)], fill=(62, 62, 72), outline=INK)
    d.polygon([(0, 1900), (560, 1900), (-200, Hb), (0, Hb)], fill=(170, 165, 160), outline=INK)
    d.polygon([(Wb, 1900), (1040, 1900), (Wb + 200, Hb), (Wb, Hb)], fill=(170, 165, 160), outline=INK)
    for k in range(6):
        y0 = 1910 + (k ** 1.6) * 50
        y1 = y0 + 20 + k * 14
        def xat(y):
            return 800 + (0) * (y - 1900)
        d.rectangle([790 - k * 3, y0, 810 + k * 3, y1], fill=(250, 220, 90))
    screens = [(60, 900, 380, 1140), (1190, 820, 1540, 1080), (520, 1240, 760, 1400), (880, 1180, 1100, 1330)]
    for s in screens:
        d.rectangle([s[0] - 12, s[1] - 12, s[2] + 12, s[3] + 12], fill=(30, 30, 40), outline=INK, width=6)
    return im.convert("RGB"), screens


def draw_screen(d, s, mode, t, idx=0):
    x0, y0, x1, y1 = s
    w, h = x1 - x0, y1 - y0
    if mode == "ad":
        cols = [((40, 170, 230), (250, 210, 60)), ((240, 90, 140), (255, 255, 255)), ((60, 200, 120), (255, 255, 255)), ((250, 160, 40), (40, 40, 80))]
        bg, fg = cols[idx % 4]
        d.rectangle(s, fill=bg)
        r = h * .3
        cx = x0 + w * (.3 + .1 * math.sin(t * 2 + idx))
        d.ellipse([cx - r, y0 + h / 2 - r, cx + r, y0 + h / 2 + r], fill=fg)
        d.rectangle([x0 + w * .55, y0 + h * .3, x1 - w * .08, y0 + h * .42], fill=fg)
        d.rectangle([x0 + w * .55, y0 + h * .55, x1 - w * .2, y0 + h * .63], fill=fg)
    elif mode == "static":
        rnd = random.Random(int(t * 60) + idx)
        for yy in range(int(y0), int(y1), 6):
            g = rnd.randint(40, 240)
            d.rectangle([x0, yy, x1, yy + 6], fill=(g, g, g))
    else:  # alert
        on = (int(t * 4) % 2 == 0)
        d.rectangle(s, fill=(200, 16, 24) if on else (120, 6, 12))
        fs = int(h * .2)
        f = F("RussoOne.ttf", fs)
        for k, txt in enumerate(("ВНИМАНИЕ!", "ЭКСТРЕННО")):
            tw = f.getlength(txt)
            sc = min(1.0, (w * .9) / tw)
            ff = F("RussoOne.ttf", max(8, int(fs * sc)))
            tw = ff.getlength(txt)
            d.text((x0 + (w - tw) / 2, y0 + h * (.2 + .38 * k)), txt, font=ff, fill=(255, 255, 255))
        # triangle warning icon
        d.polygon([(x0 + 14, y1 - 14), (x0 + 44, y1 - 14), (x0 + 29, y1 - 44)], fill=YEL)


def people_layer(d, t, n, seed, y_feet, scale, run=False, col=(30, 26, 40)):
    rnd = random.Random(seed)
    for i in range(n):
        sp = rnd.uniform(60, 120) * (4 if run else 1) * rnd.choice((-1, 1))
        x = (rnd.uniform(-200, 1800) + sp * t) % 2000 - 200
        yf = y_feet + rnd.uniform(-60, 120)
        s = scale * (0.8 + (yf - y_feet + 60) / 400)
        person(d, x, yf, s, col, phase=t * (14 if run else 7) + i, run=run)


def city_frame(t, mode, people=True, run=False, variant="day", omni=None):
    base, screens = city_base(variant)
    im = base.copy()
    d = ImageDraw.Draw(im)
    for i, s in enumerate(screens):
        m = mode(i) if callable(mode) else mode
        draw_screen(d, s, m, t, i)
    if omni is not None:
        ox, oy, sc = omni
        spr = omni_spr(int(sc * 100))
        im.paste(spr, (int(ox - spr.width / 2), int(oy - spr.height / 2)), spr)
    if people:
        if variant != "day":
            # abandoned cars askew
            car_shape(d, 640, 2160, 1.5, (60, 150, 220))
            car_shape(d, 1020, 2240, 1.8, (230, 200, 60), flip=True)
            car_shape(d, 420, 2420, 2.2, (200, 60, 60))
        people_layer(d, t, 18 if run else 10, 7, 2050, 1.4, run=run)
    return im


@lru_cache(None)
def omni_spr(sc100):
    return char_sprite("omni", scale=sc100 / 100.0)

@lru_cache(None)
def mark_spr(sc100):
    return char_sprite("mark", scale=sc100 / 100.0)

@lru_cache(None)
def omni_big():
    return char_sprite("omni", scale=1.3)

@lru_cache(None)
def mark_big():
    return char_sprite("mark", scale=1.3)

@lru_cache(None)
def sky_up(variant="day"):
    """Looking up between skyscrapers."""
    Wb, Hb = 1400, 2300
    if variant == "day":
        im = vgrad(Wb, Hb, (40, 110, 210), (150, 200, 245)).convert("RGBA")
    else:
        im = vgrad(Wb, Hb, (40, 40, 70), (200, 120, 80)).convert("RGBA")
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for i in range(6):
        cloud(d, rnd.randint(0, Wb), rnd.randint(200, 1500), rnd.randint(70, 140),
              (255, 255, 255, 230) if variant == "day" else (110, 80, 90, 255))
    # converging building faces from left/right bottom
    cx = Wb / 2
    for side in (-1, 1):
        for k, (col, w0, top) in enumerate((((80, 96, 150), 520, 520), ((110, 128, 180), 380, 300), ((226, 150, 110), 260, 820))):
            xb = cx + side * (cx + 60 - k * 40)
            xi = cx + side * (cx - w0)
            xt_out = cx + side * (cx - 120 - k * 70)
            xt_in = cx + side * (cx - w0 - 40 + k * 60) * 0.55 + (1 - .55) * cx * 0
            xt_in = cx + side * (abs(xi - cx) * 0.45)
            pts = [(xb, Hb), (xi, Hb), (xt_in, top), (xt_out, top - 40)]
            d.polygon(pts, fill=col, outline=INK, width=6)
            # window rows converging
            for r in range(1, 14):
                f = r / 14
                ya = Hb + (top - Hb) * f
                xa = xi + (xt_in - xi) * f
                xo = xb + (xt_out - xb) * f
                d.line([(xa, ya), (xo, ya - 40 * f)], fill=(255, 230, 150) if k == 0 else (60, 70, 110), width=max(2, int(12 * (1 - f))))
    return im.convert("RGB")


@lru_cache(None)
def omni_face(eyes10, glow=False):
    return face_closeup("omni", W=W, H=H, cx=500, cy=300, zoom=6.0, eyes_dx=eyes10 / 10.0, glow=glow)

@lru_cache(None)
def omni_eyes(eyes10):
    return face_closeup("omni", W=W, H=H, cx=500, cy=300, zoom=14.0, eyes_dx=eyes10 / 10.0)

# =====================================================================  scenes

def s_street(t):
    lt = t
    bob = math.sin(lt * 9) * 6
    flick = (lambda i: "ad") if t < 2.85 else (lambda i: "static" if (int(t * 20) + i) % 3 else "ad")
    im = city_frame(t, flick, people=True)
    z = lerp(0.70, 0.78, ease(lt / 3.7))
    return cam(im, 800, 1720 + bob, z)


def s_screens(t):
    lt = t - 3.72
    im = city_frame(t, lambda i: "alert" if lt > 0.08 * i else "static", people=True)
    if lt < 1.4:
        z = lerp(0.76, 0.86, eout(lt / 1.4))
        dx, dy = shake(t, 4)
        out = cam(im, 800 + dx, 1680 + dy, z)
    else:
        # push into the big billboard on the right
        k = eout((lt - 1.4) / 1.8)
        out = cam(im, lerp(1365, 1365, k), lerp(950, 950, k), lerp(1.6, 2.6, k), rot=lerp(-4, 2, k))
    o = tint(out, (255, 0, 0), 0.08 + 0.06 * (int(t * 8) % 2))
    return o


@lru_cache(None)
def tv_omni():
    spr = char_sprite("omni", scale=1.0)
    return spr


def s_broadcast(t):
    lt = t - 7.1
    im = Image.new("RGB", (W, H), (20, 6, 10))
    d = ImageDraw.Draw(im)
    # diagonal hazard stripes background
    off = (t * 120) % 160
    for x in range(-2000, 2000, 160):
        d.polygon([(x + off, 0), (x + 80 + off, 0), (x + 80 + off + 1920, H), (x + off + 1920, H)], fill=(40, 8, 14))
    # broadcast panel
    panel = Image.new("RGB", (980, 860), (0, 0, 0))
    pd = ImageDraw.Draw(panel)
    g = vgrad(980, 860, (90, 10, 20), (20, 4, 10))
    panel.paste(g)
    zoom = lerp(1.0, 1.35, ease(lt / 5.0))
    destroy = t >= 9.94
    spr = tv_omni()
    if t >= 10.6:
        # face close-up inside screen
        f = omni_face(0, glow=False)
        fb = Image.new("RGB", f.size, (90, 10, 20)); fb.paste(f, (0, 0), f)
        k = eout((t - 10.6) / 1.9)
        fc = cam(fb, 540, 960 + 60, lerp(1.0, 1.25, k), out=(980, 860))
        panel = fc
    else:
        sc = 0.75 * zoom
        s2 = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
        hover = math.sin(t * 2) * 10
        panel.paste(s2, (490 - s2.width // 2, int(120 + hover)), s2)
    panel = tint(panel, (255, 30, 30), 0.25 if destroy else 0.12)
    # scanlines
    arr = np.asarray(panel).astype(np.int16)
    arr[::4] = (arr[::4] * 0.6).astype(np.int16)
    if destroy and (int(t * 15) % 5 == 0):
        sh = random.Random(int(t * 30)).randint(-30, 30)
        arr[:, :, 0] = np.roll(arr[:, :, 0], sh, axis=1)
    panel = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im.paste(panel, (50, 230))
    d.rectangle([50, 230, 1030, 1090], outline=(255, 255, 255), width=6)
    # header
    d.rectangle([0, 90, W, 200], fill=RED)
    d.text((40, 108), "ЭКСТРЕННЫЙ ВЫПУСК", font=F("RussoOne.ttf", 66), fill=(255, 255, 255))
    if int(t * 2) % 2 == 0:
        d.ellipse([930, 125, 970, 165], fill=(255, 255, 255))
    d.rectangle([70, 250, 230, 310], fill=RED)
    d.text((88, 254), "LIVE", font=F("RussoOne.ttf", 46), fill=(255, 255, 255))
    # lower third
    lt_txt = ("ОМНИ-МЭН БОЛЬШЕ", "НЕ ЗАЩИЩАЕТ ЗЕМЛЮ") if not destroy else ("УГРОЗА", "УНИЧТОЖЕНИЯ ГОРОДА")
    k = eout((t - (7.28 if not destroy else 9.94)) / 0.35)
    x = lerp(-1000, 0, k)
    d.rectangle([x, 1105, x + 1080, 1295], fill=(255, 255, 255))
    d.rectangle([x, 1105, x + 30, 1295], fill=RED)
    d.text((x + 60, 1112), lt_txt[0], font=F("RussoOne.ttf", 74), fill=RED if destroy else (20, 20, 30))
    d.text((x + 60, 1200), lt_txt[1], font=F("RussoOne.ttf", 74), fill=(20, 20, 30))
    # ticker
    d.rectangle([0, 1560, W, 1640], fill=(250, 200, 0))
    tick = "  •  СРОЧНО: ОМНИ-МЭН НАД ГОРОДОМ  •  ОСТАВАЙТЕСЬ В УКРЫТИЯХ  •  СЛЕДИТЕ ЗА ЭКСТРЕННЫМИ СООБЩЕНИЯМИ"
    tl = F("Oswald-Bold.ttf", 48).getlength(tick)
    tx = -((t * 260) % tl)
    for rep in range(3):
        d.text((tx + rep * tl, 1572), tick, font=F("Oswald-Bold.ttf", 48), fill=(20, 20, 20))
    if destroy:
        k = 1 - min(1, (t - 9.94) / 0.4)
        z = 1 + 0.05 * math.sin(t * 40) * k
        dx, dy = shake(t, 10 * (0.4 + k))
        im = cam(im, W / 2 + dx, H / 2 + dy, z)
    return im


def s_sky(t):
    lt = t - 12.5
    if t < 13.25:
        # people stop and look up (street)
        im = city_frame(t, "alert", people=True)
        z = 0.8
        tilt = ease((t - 12.9) / 0.35) * 300
        return cam(im, 800, 1700 - tilt, z)
    sky = sky_up("day").copy()
    d = ImageDraw.Draw(sky)
    tilt_k = eout((t - 13.25) / 0.9)
    cy = lerp(1500, 1050, tilt_k)
    # figure
    if t > 14.7:
        k = ease((t - 15.0) / 2.6)
        sc = lerp(0.06, 0.62, k)
        fx, fy = 700 + math.sin(t) * 20, lerp(820, 980, k)
        if t < 15.2:
            g = (t - 14.7) / 0.5
            r = 40 + 60 * math.sin(g * math.pi)
            d.ellipse([fx - r, fy - 6, fx + r, fy + 6], fill=(255, 255, 230))
            d.ellipse([fx - 6, fy - r, fx + 6, fy + r], fill=(255, 255, 230))
        spr = omni_spr(max(4, int(sc * 100)))
        sky.paste(spr, (int(fx - spr.width / 2), int(fy - spr.height * 0.45)), spr)
    z = lerp(0.85, 1.0, ease(lt / 5.4))
    if t > 16.3:
        z *= 1 + 0.25 * eout((t - 16.3) / 0.6)
        cy = lerp(cy, 1000, eout((t - 16.3) / 0.6))
    dx, dy = shake(t, 3)
    return cam(sky, 700 + dx, cy + dy, z)


def s_panic(t):
    lt = t - 17.9
    hover = math.sin(t * 2) * 15
    im = city_frame(t, "alert", people=True, run=True, variant="panic", omni=(800, 700 + hover, 0.32))
    d = ImageDraw.Draw(im)
    # dust/smoke puffs
    rnd = random.Random(9)
    for i in range(14):
        x = (rnd.uniform(0, 1600) + t * rnd.uniform(-40, 40)) % 1600
        y = rnd.uniform(1400, 2000)
        r = rnd.uniform(60, 160) * (1 + 0.1 * math.sin(t + i))
        d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=(120, 90, 90))
    dx, dy = shake(t, 9, 9)
    if t < 19.9:
        return cam(im, 800 + dx, 1650 + dy, lerp(0.72, 0.8, lt / 2))
    # low angle on abandoned cars
    k = (t - 19.9) / 2.5
    return cam(im, lerp(560, 760, k) + dx, 2150 + dy, lerp(1.25, 1.4, k), rot=-3)


def s_timer(t):
    lt = t - 22.4
    base, _ = city_base("panic")
    bg = cam(base, 800, 1500, 0.75).filter(ImageFilter.GaussianBlur(10))
    im = ImageEnhance.Brightness(bg).enhance(0.35)
    d = ImageDraw.Draw(im)
    remain = max(0, 300 - lt * 6)  # accelerated countdown for drama
    mm, ss = int(remain // 60), int(remain % 60)
    cs = int((remain * 100) % 100)
    beat = math.exp(-((lt % 0.6) / 0.12))
    R = 380 + 10 * beat
    cx, cy = 540, 820
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(80, 20, 20), width=26)
    frac = remain / 300
    d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * frac, fill=RED, width=26)
    txt = f"{mm:02d}:{ss:02d}"
    ti = text_img(txt, F("RussoOne.ttf", 230), (255, 255, 255), stroke=10)
    paste_c(im, ti, cx, cy - 20, scale=1 + 0.04 * beat)
    ti2 = text_img(f".{cs:02d}", F("RussoOne.ttf", 90), (255, 120, 120), stroke=6)
    paste_c(im, ti2, cx, cy + 150)
    lab = text_img("ВРЕМЯ ПОШЛО", F("RussoOne.ttf", 70), YEL, stroke=6)
    paste_c(im, lab, cx, 300, alpha=ease(lt / 0.4))
    z = lerp(1.0, 1.1, lt / 4)
    return cam(im, W / 2, H / 2, z)

# ---- choices
@lru_cache(None)
def choice_art(k):
    Wp, Hp = 980, 900
    if k == 0:
        im = vgrad(Wp, Hp, (60, 140, 220), (180, 220, 250)).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([140, 80, 840, Hp], fill=(200, 120, 90), outline=INK, width=8)
        d.rectangle([600, 85, 836, Hp], fill=(170, 96, 72))
        for y in range(130, 620, 90):
            for x in range(190, 800, 120):
                d.rectangle([x, y, x + 70, y + 55], fill=(255, 230, 150), outline=INK, width=4)
        d.rectangle([380, 640, 600, Hp], fill=(255, 220, 120), outline=INK, width=8)
        d.rectangle([150, 600, 830, 650], fill=(60, 70, 110), outline=INK, width=6)
        d.text((310, 597), "ВХОД", font=F("RussoOne.ttf", 42), fill=(255, 255, 255))
        d.rectangle([0, 860, Wp, Hp], fill=(120, 120, 130))
    elif k == 1:
        im = vgrad(Wp, Hp, (250, 150, 80), (255, 210, 140)).convert("RGBA")
        d = ImageDraw.Draw(im)
        sk, _ = skyline_layer(Wp, Hp, 420, (90, 70, 100), (255, 220, 140), 77, 80, 260, 40, 90, outline=False)
        im.alpha_composite(sk)
        d = ImageDraw.Draw(im)
        d.polygon([(0, 420), (Wp, 420), (Wp, Hp), (0, Hp)], fill=(110, 150, 90))
        d.polygon([(470, 420), (510, 420), (900, Hp), (80, Hp)], fill=(70, 70, 80), outline=INK, width=6)
        for i in range(8):
            y = 430 + (i ** 1.7) * 18
            d.rectangle([486 - i, y, 494 + i, y + 8 + i * 3], fill=(250, 220, 90))
        im = im.convert("RGB")
    else:
        im = vgrad(Wp, Hp, (90, 96, 104), (60, 64, 72)).convert("RGB")
        d = ImageDraw.Draw(im)
        for x in range(0, Wp, 140):
            d.line([(x, 0), (x, Hp)], fill=(70, 74, 82), width=4)
        d.rectangle([150, 250, 830, 860], fill=(40, 44, 50), outline=INK, width=8)
        for i in range(0, 680, 60):
            d.polygon([(150 + i, 250), (180 + i, 250), (150 + i + 30 - 30, 290)], fill=YEL)
        d.rectangle([150, 250, 830, 290], fill=YEL, outline=INK, width=6)
        for i in range(0, 700, 70):
            d.polygon([(150 + i, 250), (185 + i, 250), (150 + i + 5, 290), (150 + i - 30, 290)], fill=(20, 20, 20))
        d.ellipse([290, 330, 690, 730], fill=(120, 130, 140), outline=INK, width=10)
        d.ellipse([340, 380, 640, 680], fill=(100, 108, 118), outline=INK, width=6)
        d.line([(490, 400), (490, 660)], fill=INK, width=14)
        d.line([(360, 530), (620, 530)], fill=INK, width=14)
        d.rectangle([280, 80, 700, 200], fill=(40, 160, 70), outline=INK, width=6)
        d.text((330, 95), "УБЕЖИЩЕ", font=F("RussoOne.ttf", 76), fill=(255, 255, 255))
    return im


def s_choices(t):
    starts = (26.5, 29.6, 32.3)
    k = 0 if t < 29.6 else (1 if t < 32.3 else 2)
    lt = t - starts[k]
    base, _ = city_base("panic")
    bg = cam(base, 800, 1500, 0.78).filter(ImageFilter.GaussianBlur(14))
    im = ImageEnhance.Brightness(bg).enhance(0.35)
    d = ImageDraw.Draw(im)
    # header
    hdr = text_img("ТВОЙ ВЫБОР", F("RussoOne.ttf", 84), YEL, stroke=7)
    paste_c(im, hdr, W / 2, 150)
    # panel art with slow push
    pa = choice_art(k)
    pz = cam(pa, 490 + (k - 1) * 20 * lt, 450, lerp(1.0, 1.12, lt / 3.5), out=(940, 760))
    # draw animated elements
    pd = ImageDraw.Draw(pz)
    if k == 0:
        person(pd, lerp(80, 460, eout(lt / 1.6)), 740, 1.6, (20, 20, 30), phase=lt * 14, run=True)
    elif k == 1:
        for i in range(3):
            p = ((lt * 0.35 + i / 3) % 1)
            s = lerp(2.2, 0.3, p)
            x = lerp(470 + (i - 1) * 120, 480, p)
            y = lerp(800, 380, p)
            car_shape(pd, x, y, s * 0.5, [(220, 60, 60), (60, 150, 220), (240, 200, 60)][i])
            pd.ellipse([x - 40 * s, y - 20 * s, x - 20 * s, y - 8 * s], fill=(255, 40, 40))
        ar = (lt * 2) % 1
        pd.polygon([(700, 160 - 20 * ar), (780, 220 - 20 * ar), (700, 280 - 20 * ar)], fill=(255, 255, 255), outline=INK)
    else:
        ay = 360 + 20 * math.sin(lt * 8)
    sl = eout(lt / 0.35)
    px = int(lerp(W + 100, 70, sl)) if k else int(lerp(-1000, 70, sl))
    py = 260
    im.paste(pz, (px, py))
    d.rectangle([px - 6, py - 6, px + 946, py + 766], outline=(255, 255, 255), width=8)
    # letter badge
    letters = ("А", "Б", "В")
    labels = ("СПРЯТАТЬСЯ В ЗДАНИИ", "ПОКИНУТЬ ГОРОД", "НАЙТИ УБЕЖИЩЕ")
    bx, by = px + 60, py + 50
    d.ellipse([bx - 70, by - 70, bx + 70, by + 70], fill=YEL, outline=INK, width=8)
    li = text_img(letters[k], F("RussoOne.ttf", 100), BLU, stroke=0)
    paste_c(im, li, bx, by + 4)
    lb = text_img(labels[k], F("RussoOne.ttf", 64), (255, 255, 255), stroke=7)
    paste_c(im, lb, W / 2, py + 820, scale=min(1, 980 / lb.width), alpha=ease(lt / 0.3))
    # tabs
    for i in range(3):
        cx = 270 + i * 270
        act = i == k
        done = i < k
        col = YEL if act else ((120, 120, 130) if not done else (200, 200, 210))
        r = 62 if act else 48
        d.ellipse([cx - r, 1180 - r, cx + r, 1180 + r], fill=col, outline=INK, width=6)
        ti = text_img(letters[i], F("RussoOne.ttf", 70 if act else 52), BLU if act else (40, 40, 50), stroke=0)
        paste_c(im, ti, cx, 1183)
    return im


def s_strange(t):
    lt = t - 36.4
    frame = s_panic(21.5 + lt * 0.05)  # near-frozen time
    g = ImageOps.grayscale(frame).convert("RGB")
    k = ease(lt / 0.5)
    im = Image.blend(frame, g, 0.75 * k)
    im = tint(im, (20, 40, 90), 0.25 * k)
    im = cam(im, W / 2, H / 2, lerp(1.0, 1.18, ease(lt / 2.9)))
    arr = np.asarray(im).copy()
    pulse = (math.sin(lt * 6) > 0.6)
    if pulse:
        sh = 14
        arr[:, :, 0] = np.roll(arr[:, :, 0], sh, axis=1)
        arr[:, :, 2] = np.roll(arr[:, :, 2], -sh, axis=1)
    return Image.fromarray(arr)


def s_flyover(t):
    lt = t - 39.3
    sky = sky_up("day").copy()
    d = ImageDraw.Draw(sky)
    if t < 41.75:
        k = (t - 39.4) / 1.6
        spr = omni_big()
        sc = lerp(0.55, 1.5, ease(min(1, max(0, k))))
        s2 = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR).rotate(-12, expand=True)
        fx = lerp(450, 950, k)
        fy = lerp(2300, -900, k)
        if -0.1 < k < 1.1:
            speed_lines(d, 700, 1100, t, n=40, r0=500, col=(255, 255, 255), w=5)
            sky.paste(s2, (int(fx - s2.width / 2), int(fy - s2.height / 2)), s2)
        amp = 18 * math.exp(-((k - 0.5) ** 2) / 0.08)
        dx, dy = shake(t, amp + 2, 15)
        return cam(sky, 700 + dx, 1150 + dy, 0.95)
    # he flies away over the skyline, "you" in foreground looking up
    im = city_frame(t, "alert", people=False)
    d = ImageDraw.Draw(im)
    k = (t - 41.75) / 2.0
    spr = omni_spr(max(4, int(lerp(30, 6, k) * 1)))
    fx, fy = lerp(900, 1150, k), lerp(900, 600, k)
    im.paste(spr, (int(fx - spr.width / 2), int(fy - spr.height / 2)), spr)
    d.line([(fx - 300, fy + 250), (fx, fy + 20)], fill=(255, 255, 255), width=3)
    d.polygon([(380, 3100), (420, 2700), (560, 2600), (960, 2600), (1100, 2700), (1140, 3100)], fill=(16, 14, 24))
    d.ellipse([620, 2300, 900, 2660], fill=(16, 14, 24))
    return cam(im, 800, 1700, lerp(0.78, 0.82, k))


def s_eyes(t):
    lt = t - 43.7
    e = math.sin(lt * 3.2) * 1.0
    f = omni_eyes(int(round(e * 10)))
    bg = Image.new("RGB", (W, H), (30, 10, 14))
    bg.paste(f, (0, 0), f)
    im = cam(bg, W / 2, H / 2 + 60, lerp(1.0, 1.08, lt / 2))
    d = ImageDraw.Draw(im)
    # scanning sweep
    sy = (lt * 900) % (H + 400) - 200
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, sy, W, sy + 18], fill=(255, 40, 40, 120))
    for i in range(6):
        od.line([(0, sy - i * 30), (W, sy - i * 30)], fill=(255, 40, 40, 40 - i * 6), width=4)
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    # letterbox for cinematic feel
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 300], fill=(0, 0, 0))
    d.rectangle([0, H - 300, W, H], fill=(0, 0, 0))
    return im


@lru_cache(None)
def mark_bg():
    im = vgrad(W, H, (255, 210, 60), (40, 90, 210)).convert("RGB")
    d = ImageDraw.Draw(im)
    cx, cy = 540, 760
    for i in range(24):
        a0 = i / 24 * math.tau
        a1 = a0 + math.tau / 48
        R = 3000
        d.polygon([(cx, cy), (cx + math.cos(a0) * R, cy + math.sin(a0) * R), (cx + math.cos(a1) * R, cy + math.sin(a1) * R)],
                  fill=(255, 235, 140) if i % 2 == 0 else (90, 140, 240))
    return im


def s_mark(t):
    lt = t - 45.8
    im = mark_bg().copy()
    d = ImageDraw.Draw(im)
    speed_lines(d, 540, 760, t, n=50, r0=500, col=(255, 255, 255), w=8)
    spr = mark_big()
    k = eout(lt / 0.9)
    sc = lerp(0.6, 0.78, k) * (1 + 0.04 * math.sin(lt * 3))
    s2 = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
    y = lerp(1400, 300, k)
    im.paste(s2, (540 - s2.width // 2, int(y)), s2)
    if t >= 46.6:
        k2 = eout((t - 46.6) / 0.3)
        n1 = text_img("МАРК", F("RussoOne.ttf", 200), YEL, stroke=12, sfill=BLU)
        n2 = text_img("ГРЕЙСОН", F("RussoOne.ttf", 170), YEL, stroke=12, sfill=BLU)
        paste_c(im, n1, 540, 1130, scale=lerp(1.6, 1.0, k2), alpha=k2)
        if t >= 47.25:
            k3 = eout((t - 47.25) / 0.3)
            paste_c(im, n2, 540, 1300, scale=lerp(1.6, 1.0, k3), alpha=k3)
    return cam(im, W / 2, H / 2, lerp(1.08, 1.0, eout(lt / 1)))


def draw_phone(im, cx, cy, sc, screen_fn, t):
    pw, ph = int(520 * sc), int(1060 * sc)
    ph_im = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph_im)
    d.rounded_rectangle([20, 20, 20 + pw, 20 + ph], radius=int(70 * sc), fill=(22, 22, 28), outline=INK, width=max(3, int(8 * sc)))
    sw, sh = pw - int(36 * sc), ph - int(36 * sc)
    scr = screen_fn(sw, sh, t)
    m = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, sw, sh], radius=int(54 * sc), fill=255)
    ph_im.paste(scr, (20 + int(18 * sc), 20 + int(18 * sc)), m)
    d.rounded_rectangle([20 + pw / 2 - 60 * sc, 20 + 34 * sc, 20 + pw / 2 + 60 * sc, 20 + 64 * sc], radius=int(15 * sc), fill=(0, 0, 0))
    im.paste(ph_im, (int(cx - ph_im.width / 2), int(cy - ph_im.height / 2)), ph_im)
    return (cx - pw / 2, cy - ph / 2, pw, ph)


MSG = [("Если ты это читаешь — ", 52.84, 54.0), ("найди Марка Грейсона. ", 54.4, 55.16),
       ("Он единственный, кто может остановить моего отца.", 55.54, 58.3)]

def wrap(txt, font, maxw):
    words = txt.split(" ")
    lines, cur = [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if font.getlength(cand) <= maxw:
            cur = cand
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines


def phone_screen(sw, sh, t):
    scr = vgrad(sw, sh, (20, 24, 40), (50, 30, 60))
    d = ImageDraw.Draw(scr)
    S = sw / 484
    if t < 49.6:
        return Image.new("RGB", (sw, sh), (8, 8, 12))
    d.text((sw / 2 - 90 * S, 90 * S), "21:47", font=F("Oswald-Bold.ttf", int(90 * S)), fill=(255, 255, 255))
    if t >= 50.7:
        k = eout((t - 50.7) / 0.35)
        y = lerp(-200, 260, k) * S if t < 52.5 else 150 * S
        bx0, bx1 = 22 * S, sw - 22 * S
        if t < 52.5:
            d.rounded_rectangle([bx0, y, bx1, y + 170 * S], radius=int(30 * S), fill=(235, 235, 240))
            d.ellipse([bx0 + 20 * S, y + 25 * S, bx0 + 80 * S, y + 85 * S], fill=(40, 180, 90))
            d.text((bx0 + 100 * S, y + 22 * S), "Неизвестный номер", font=F("Oswald-Bold.ttf", int(34 * S)), fill=(20, 20, 30))
            d.text((bx0 + 100 * S, y + 80 * S), "1 новое сообщение", font=F("Oswald-Bold.ttf", int(30 * S)), fill=(90, 90, 100))
        else:
            # chat view
            d.rectangle([0, 0, sw, 230 * S], fill=(30, 34, 50))
            d.ellipse([30 * S, 120 * S, 100 * S, 190 * S], fill=(60, 90, 200))
            d.text((50 * S, 128 * S), "?", font=F("RussoOne.ttf", int(46 * S)), fill=(255, 255, 255))
            d.text((120 * S, 130 * S), "Неизвестный", font=F("Oswald-Bold.ttf", int(40 * S)), fill=(255, 255, 255))
            full = "".join(m[0] for m in MSG)
            n = 0
            for txt, a, b in MSG:
                if t >= b: n += len(txt)
                elif t > a: n += int(len(txt) * (t - a) / (b - a)); break
                else: break
            shown = full[:n]
            f = F("Oswald-Bold.ttf", int(44 * S))
            lines = []
            for para in [shown]:
                lines = wrap(para, f, sw - 130 * S)
            if not lines or lines == [""]:
                lines = []
            lh = 60 * S
            bh = max(1, len(lines)) * lh + 50 * S
            y0 = 290 * S
            d.rounded_rectangle([30 * S, y0, sw - 40 * S, y0 + bh], radius=int(34 * S), fill=(245, 245, 250))
            for i, ln in enumerate(lines):
                hl = ("Марка" in ln or "Грейсона" in ln)
                d.text((60 * S, y0 + 22 * S + i * lh), ln, font=f, fill=(20, 20, 30))
            if n < len(full) and int(t * 4) % 2 == 0:
                # typing dots / caret
                d.rectangle([60 * S + (f.getlength(lines[-1]) if lines else 0) + 6, y0 + 30 * S + (max(1, len(lines)) - 1) * lh,
                             66 * S + (f.getlength(lines[-1]) if lines else 0) + 6, y0 + 70 * S + (max(1, len(lines)) - 1) * lh], fill=(40, 120, 240))
    return scr


def draw_hand(d, cx, cy, sc, front=False):
    s = sc
    if not front:
        d.polygon([(cx - 330 * s, cy + 1400 * s), (cx - 210 * s, cy + 300 * s), (cx + 150 * s, cy + 280 * s),
                   (cx + 320 * s, cy + 1400 * s)], fill=art.SKIN, outline=INK)
        d.polygon([(cx - 120 * s, cy + 1400 * s), (cx + 40 * s, cy + 320 * s), (cx + 150 * s, cy + 280 * s), (cx + 320 * s, cy + 1400 * s)], fill=art.SKIN_SH)
        d.rectangle([cx - 420 * s, cy + 900 * s, cx + 420 * s, cy + 1500 * s], fill=(50, 60, 100), outline=INK, width=8)
    else:
        for i in range(4):
            fy = cy - 80 * s + i * 120 * s
            d.rounded_rectangle([cx + 230 * s, fy, cx + 330 * s, fy + 100 * s], radius=int(45 * s), fill=art.SKIN, outline=INK, width=max(3, int(6 * s)))
        d.rounded_rectangle([cx - 330 * s, cy + 150 * s, cx - 230 * s, cy + 420 * s], radius=int(45 * s), fill=art.SKIN, outline=INK, width=max(3, int(6 * s)))


def s_phone(t):
    lt = t - 48.2
    base, _ = city_base("panic")
    bg = cam(base, 800, 1800, 0.9).filter(ImageFilter.GaussianBlur(16))
    im = ImageEnhance.Brightness(bg).enhance(0.6)
    d = ImageDraw.Draw(im)
    vib = 48.8 < t < 50.4
    dx, dy = (shake(t, 14, 30) if vib and (int(t * 6) % 3 != 2) else (0, 0))
    sc = lerp(0.95, 1.05, eout(lt / 2.3))
    draw_hand(d, 540 + dx * .3, 1000, sc)
    draw_phone(im, 540 + dx, 1000 + dy, sc, phone_screen, t)
    d = ImageDraw.Draw(im)
    draw_hand(d, 540 + dx * .3, 1000, sc, front=True)
    if vib:
        for side in (-1, 1):
            for i in range(3):
                x = 540 + side * (330 + i * 40) * sc
                d.arc([x - 40, 820 - i * 30, x + 40, 1180 + i * 30], 90 + side * 90 - 50, 90 + side * 90 + 50 if side < 0 else 50,
                      fill=(255, 255, 255), width=8)
    return im


def s_message(t):
    lt = t - 50.5
    base, _ = city_base("panic")
    bg = cam(base, 800, 1800, 0.9).filter(ImageFilter.GaussianBlur(16))
    im = ImageEnhance.Brightness(bg).enhance(0.45)
    d = ImageDraw.Draw(im)
    sc = lerp(1.3, 1.55, ease(lt / 8))
    yy = 1000 + lerp(0, 150, ease((t - 52.5) / 1.0))
    draw_hand(d, 540, yy, sc)
    draw_phone(im, 540, yy, sc, phone_screen, t)
    d = ImageDraw.Draw(im)
    draw_hand(d, 540, yy, sc, front=True)
    dx, dy = shake(t, 3, 3)
    return cam(im, W / 2 + dx, H / 2 + dy - 40, 1.0)


def s_question(t):
    lt = t - 58.6
    im = Image.new("RGB", (W, H), (6, 6, 10))
    d = ImageDraw.Draw(im)
    beat = math.exp(-((lt % 0.8) / 0.15))
    # thin red line
    d.rectangle([0, 958 - 2 * beat, W, 962 + 2 * beat], fill=(120 + int(100 * beat), 10, 20))
    if t > 58.9:
        k = eout((t - 58.9) / 0.4)
        a = text_img("А ТЕПЕРЬ", F("RussoOne.ttf", 90), (255, 255, 255), stroke=0, spacing=int(lerp(40, 10, k)))
        paste_c(im, a, 540, 820, alpha=k)
    if t > 59.28:
        k = eout((t - 59.28) / 0.4)
        b = text_img("ГЛАВНЫЙ ВОПРОС", F("RussoOne.ttf", 104), YEL, stroke=0, spacing=int(lerp(30, 4, k)))
        paste_c(im, b, 540, 1090, alpha=k, scale=min(1, 1000 / b.width))
    return im


@lru_cache(None)
def faceoff_bg():
    im = Image.new("RGB", (W, H), (0, 0, 0))
    top = vgrad(W, H, (120, 0, 10), (230, 50, 40))
    bot = vgrad(W, H, (255, 200, 30), (30, 70, 200))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (W, 0), (W, 820), (0, 1100)], fill=255)
    im = Image.composite(top, bot, m)
    return im


def s_final(t):
    lt = t - 60.5
    im = faceoff_bg().copy()
    d = ImageDraw.Draw(im)
    o = omni_spr(70)
    m = mark_spr(70)
    k = eout(lt / 0.6)
    hov = math.sin(t * 2) * 10
    # omni top-left (cropped to upper body region), mark bottom-right
    im.paste(o, (int(lerp(-500, -60, k)), int(-20 + hov)), o)
    im.paste(m, (int(lerp(W + 200, 400, k)), int(1230 - hov)), m)
    # lightning split line
    rnd = random.Random(int(t * 12))
    pts = []
    for i in range(13):
        x = i * W / 12
        y = 1100 + (820 - 1100) * (x / W) + rnd.uniform(-25, 25)
        pts.append((x, y))
    d.line(pts, fill=(255, 255, 255), width=16)
    d.line(pts, fill=(180, 220, 255), width=6)
    # title
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle([0, 560, W, 1360], fill=(0, 0, 0, int(120 * ease(lt / 0.5))))
    im = Image.alpha_composite(im.convert("RGBA"), shade).convert("RGB")
    items = [("А ТЫ БЫ", 60.72, 120, (255, 255, 255), INK, 720),
             ("РИСКНУЛ", 61.1, 150, (255, 255, 255), INK, 870),
             ("ИСКАТЬ", 61.74, 130, (255, 255, 255), INK, 1020),
             ("НЕУЯЗВИМОГО?", 62.2, 150, YEL, BLU, 1200)]
    for txt, ts, size, col, sc_, y in items:
        if t >= ts:
            kk = eout((t - ts) / 0.25)
            ti = text_img(txt, F("RussoOne.ttf", size), col, stroke=12, sfill=sc_)
            sc = min(1.0, 1020 / ti.width)
            if txt.startswith("НЕУЯЗ"):
                sc *= 1 + 0.03 * math.sin(t * 6)
            paste_c(im, ti, 540, y, scale=sc * lerp(1.8, 1.0, kk), alpha=kk)
    z = lerp(1.0, 1.06, lt / 5)
    out = cam(im, W / 2, H / 2, z)
    if t > DUR - 0.6:
        out = Image.blend(out, Image.new("RGB", (W, H), (0, 0, 0)), (t - (DUR - 0.6)) / 0.6)
    return out


SCENES = [(0.0, s_street), (3.72, s_screens), (7.1, s_broadcast), (12.5, s_sky), (17.9, s_panic),
          (22.4, s_timer), (26.5, s_choices), (36.4, s_strange), (39.3, s_flyover), (43.7, s_eyes),
          (45.8, s_mark), (48.2, s_phone), (50.5, s_message), (58.6, s_question), (60.5, s_final)]

# cut time -> transition type
CUTS = {3.72: "glitch", 7.1: "glitch", 10.6: "punch", 12.5: "flash", 13.25: "whip", 17.9: "punch", 19.9: "whip",
        22.4: "glitch", 26.5: "flash", 29.6: "whip", 32.3: "whip", 36.4: "glitch", 39.3: "flash", 41.75: "whip",
        43.7: "punch", 45.8: "flash", 48.2: "glitch", 50.5: "punch", 52.5: "flash", 58.6: "glitch", 60.5: "flash"}

# =====================================================================  captions
FIX = {"Омнимен": "Омни-Мэн", "землю,": "Землю,"}

def load_words():
    ws = []
    for ln in open(os.path.join(HERE, "words.txt"), encoding="utf-8"):
        a, b, w_ = ln.strip().split(" ", 2)
        w_ = w_.strip()
        a, b = float(a), float(b)
        if w_.startswith("-") and ws:
            ws[-1][1] = b; ws[-1][2] += w_; continue
        if w_ in ("–", "-", "—"):
            continue
        ws.append([a, b, FIX.get(w_, w_)])
    return ws

def chunks():
    ws = load_words()
    out, cur = [], []
    for i, w_ in enumerate(ws):
        cur.append(w_)
        end_punct = w_[2][-1] in ",.?!"
        nxt_gap = ws[i + 1][0] - w_[1] if i + 1 < len(ws) else 9
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

CHUNKS = None
NO_CAP = [(46.55, 48.25), (52.7, 58.5), (58.5, 66)]

@lru_cache(maxsize=64)
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
        col = YEL if i == active else (255, 255, 255)
        d.text((x, 20), w_, font=f, fill=col, stroke_width=10, stroke_fill=INK)
        x += widths[i] + space
    return im

def draw_captions(im, t):
    global CHUNKS
    if CHUNKS is None: CHUNKS = chunks()
    for a, b in NO_CAP:
        if a <= t < b: return im
    for ci, (st, en, c) in enumerate(CHUNKS):
        if st <= t < en:
            act = -1
            for i, w_ in enumerate(c):
                if t >= w_[0] - 0.03: act = i
            ci_im = cap_img(ci, act)
            k = eout((t - st) / 0.1)
            sc = lerp(0.75, 1.0, k)
            sc *= min(1.0, 1000 / ci_im.width)
            paste_c(im, ci_im, W / 2, 1390, scale=sc)
    return im

# =====================================================================  post
_rng = np.random.default_rng(1)
GRAIN = [(_rng.normal(0, 7, (H // 2, W // 2))).astype(np.float32) for _ in range(6)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.38 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)).clip(0.45, 1).astype(np.float32)[..., None]

def post(im, t, fi):
    # transitions
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
                        acc += np.roll(a, int((i - n / 2) * 18 * amt), axis=0 if c in (13.25,) else 1)
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
    im = draw_captions(im, t)
    a = np.asarray(im).astype(np.float32)
    g = GRAIN[fi % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    a = a * VIG + g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def frame_at(t, fi):
    fn = SCENES[0][1]
    for st, f in SCENES:
        if t >= st: fn = f
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
        for ts in sys.argv[2:]:
            t = float(ts)
            frame_at(t, int(t * FPS)).save(os.path.join(HERE, "stills2", f"f_{t:05.2f}.png"))
    else:
        i0, i1, path = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        render_range(i0, i1, path)
