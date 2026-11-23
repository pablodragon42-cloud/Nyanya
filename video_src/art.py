# Original cel-shaded character + environment art (Invincible-inspired style).
import math, random
from PIL import Image, ImageDraw, ImageFilter

INK = (14, 12, 20)
SKIN = (233, 180, 140)
SKIN_SH = (196, 136, 102)

def T(pts, S, ox, oy):
    return [(ox + x * S, oy + y * S) for x, y in pts]

def poly(d, pts, fill, S, ox, oy, w=4.0):
    d.polygon(T(pts, S, ox, oy), fill=fill, outline=INK, width=max(1, int(w * S)))

def polyn(d, pts, fill, S, ox, oy):  # no outline (shading)
    d.polygon(T(pts, S, ox, oy), fill=fill)

def ell(d, box, fill, S, ox, oy, w=4.0):
    x0, y0, x1, y1 = box
    d.ellipse([ox + x0 * S, oy + y0 * S, ox + x1 * S, oy + y1 * S], fill=fill,
              outline=INK if w else None, width=max(1, int(w * S)) if w else 0)

def line(d, pts, S, ox, oy, w=4.0, fill=INK):
    d.line(T(pts, S, ox, oy), fill=fill, width=max(1, int(w * S)), joint="curve")

def mirror(pts):
    return [(1000 - x, y) for x, y in pts]

# ---------------------------------------------------------------- characters
PAL = {
    "omni": dict(suit=(244, 244, 248), suit_sh=(190, 196, 214), acc=(214, 28, 38),
                 acc_sh=(150, 14, 26), cape=(204, 24, 34), cape_in=(120, 10, 20)),
    "mark": dict(suit=(255, 206, 28), suit_sh=(214, 150, 10), acc=(38, 92, 214),
                 acc_sh=(20, 52, 150), cape=None, cape_in=None),
}

def draw_character(d, kind, S=1.0, ox=0, oy=0, eyes_dx=0.0, glow=False):
    """Character in a 1000x1600 unit box, front facing, hovering hero pose."""
    p = PAL[kind]
    omni = kind == "omni"
    sl = 0 if omni else 22  # Mark is slimmer
    # cape
    if omni:
        cape = [(345, 440), (655, 440), (720, 700), (860, 1380), (790, 1420), (700, 1390),
                (600, 1440), (500, 1400), (400, 1450), (300, 1395), (210, 1430), (140, 1380), (280, 700)]
        poly(d, cape, p["cape"], S, ox, oy, 5)
        inner = [(400, 520), (600, 520), (700, 1360), (600, 1400), (500, 1370), (400, 1410), (300, 1360)]
        polyn(d, inner, p["cape_in"], S, ox, oy)
    # legs
    legL = [(398 + sl, 840), (497, 840), (488, 1200), (470, 1330), (425, 1330), (412 + sl * .5, 1200)]
    for leg in (legL, mirror(legL)):
        lc = p["suit"] if omni else p["acc"]
        poly(d, leg, lc, S, ox, oy)
    polyn(d, [(560, 850), (598 - sl, 850), (586 - sl * .5, 1190), (566, 1190)],
          p["suit_sh"] if omni else p["acc_sh"], S, ox, oy)
    bootL = [(410 + sl * .5, 1180), (490, 1180), (492, 1350), (500, 1395), (392 + sl * .5, 1395), (402 + sl * .5, 1350)]
    for b in (bootL, mirror(bootL)):
        poly(d, b, p["acc"], S, ox, oy)
    polyn(d, [(560, 1190), (585 - sl * .5, 1190), (590 - sl * .5, 1385), (565, 1385)], p["acc_sh"], S, ox, oy)
    # torso
    torso = [(340 + sl, 445), (660 - sl, 445), (640 - sl, 600), (612 - sl * .6, 830),
             (388 + sl * .6, 830), (360 + sl, 600)]
    poly(d, torso, p["suit"], S, ox, oy)
    polyn(d, [(560, 460), (650 - sl, 460), (632 - sl, 600), (606 - sl * .6, 822), (540, 822)],
          p["suit_sh"], S, ox, oy)
    # muscle lines
    line(d, [(420 + sl * .5, 610), (470, 630), (500, 615)], S, ox, oy, 3)
    line(d, [(500, 615), (530, 630), (580 - sl * .5, 610)], S, ox, oy, 3)
    line(d, [(500, 640), (500, 790)], S, ox, oy, 2.5)
    line(d, [(455, 700), (545, 700)], S, ox, oy, 2)
    line(d, [(460, 755), (540, 755)], S, ox, oy, 2)
    if not omni:
        # blue shoulder panels / collar of the yellow suit
        for sh in ([(342 + sl, 447), (455, 447), (420, 520), (360 + sl, 560)],):
            poly(d, sh, p["acc"], S, ox, oy, 3)
            poly(d, mirror(sh), p["acc"], S, ox, oy, 3)
    else:
        # red collar trim
        poly(d, [(440, 440), (560, 440), (540, 478), (460, 478)], p["acc"], S, ox, oy, 3)
    # belt
    poly(d, [(386 + sl * .6, 795), (614 - sl * .6, 795), (616 - sl * .6, 850), (384 + sl * .6, 850)],
         p["acc"] if omni else p["acc_sh"], S, ox, oy)
    if not omni:
        poly(d, [(470, 800), (530, 800), (530, 845), (470, 845)], p["suit"], S, ox, oy, 3)
    # arms
    armU = [(338 + sl, 450), (392 + sl, 470), (365 + sl * .7, 770), (300 + sl * .7, 770), (305 + sl * .7, 560)]
    armF = [(300 + sl * .7, 760), (365 + sl * .7, 760), (352 + sl * .7, 900), (290 + sl * .7, 900)]
    for a, f in ((armU, armF), (mirror(armU), mirror(armF))):
        poly(d, a, p["suit"], S, ox, oy)
        poly(d, f, p["acc"], S, ox, oy)
    polyn(d, [(640 - sl, 470), (662 - sl, 452), (695 - sl * .7, 560), (700 - sl * .7, 760), (672 - sl * .7, 760)],
          p["suit_sh"], S, ox, oy)
    for cx in (322 + sl * .7, 678 - sl * .7):
        ell(d, (cx - 48, 880, cx + 48, 975), p["acc"], S, ox, oy)
        line(d, [(cx - 30, 915), (cx + 30, 915)], S, ox, oy, 2.5)
    # neck
    poly(d, [(458, 365), (542, 365), (548, 448), (452, 448)], SKIN, S, ox, oy)
    polyn(d, [(500, 380), (544, 380), (547, 440), (500, 440)], SKIN_SH, S, ox, oy)
    # head
    head = [(428, 212), (572, 212), (570, 335), (535, 395), (465, 395), (430, 335)]
    poly(d, head, SKIN, S, ox, oy)
    polyn(d, [(540, 222), (568, 222), (566, 335), (533, 390), (515, 392)], SKIN_SH, S, ox, oy)
    ell(d, (412, 270, 440, 320), SKIN, S, ox, oy, 3)
    ell(d, (560, 270, 588, 320), SKIN_SH, S, ox, oy, 3)
    if omni:
        hair = [(418, 275), (420, 205), (455, 172), (520, 165), (570, 182), (585, 220), (582, 278),
                (568, 245), (548, 222), (500, 228), (455, 222), (432, 245)]
        poly(d, hair, (44, 40, 48), S, ox, oy)
        polyn(d, [(421, 230), (430, 252), (420, 272)], (150, 150, 160), S, ox, oy)
        polyn(d, [(579, 230), (570, 252), (580, 272)], (150, 150, 160), S, ox, oy)
        # eyes
        for ex in (465, 535):
            ell(d, (ex - 17, 280, ex + 17, 298), (250, 250, 250), S, ox, oy, 2)
            ell(d, (ex - 6 + eyes_dx * 9, 282, ex + 6 + eyes_dx * 9, 296),
                (230, 40, 30) if glow else (40, 30, 30), S, ox, oy, 0)
        line(d, [(440, 268), (488, 282)], S, ox, oy, 7)
        line(d, [(512, 282), (560, 268)], S, ox, oy, 7)
        line(d, [(500, 290), (494, 330), (506, 332)], S, ox, oy, 2.5)
        stache = [(452, 352), (478, 338), (500, 342), (522, 338), (548, 352), (556, 378),
                  (536, 364), (500, 358), (464, 364), (444, 378)]
        poly(d, stache, (30, 26, 30), S, ox, oy, 2)
        line(d, [(478, 375), (522, 375)], S, ox, oy, 2.5)
        line(d, [(450, 312), (458, 340)], S, ox, oy, 1.5)
        line(d, [(550, 312), (542, 340)], S, ox, oy, 1.5)
    else:
        # blue cowl with black goggle lenses
        cowl = [(422, 300), (420, 210), (455, 172), (520, 165), (572, 185), (582, 220), (580, 300),
                (560, 322), (520, 318), (500, 330), (480, 318), (440, 322)]
        poly(d, cowl, p["acc"], S, ox, oy)
        polyn(d, [(545, 190), (575, 210), (578, 298), (560, 316), (545, 316)], p["acc_sh"], S, ox, oy)
        for ex, sgn in ((462, -1), (538, 1)):
            lens = [(ex - 30, 270), (ex + 26, 276), (ex + 22, 304), (ex - 26, 298)] if sgn < 0 else \
                   [(ex - 26, 276), (ex + 30, 270), (ex + 26, 298), (ex - 22, 304)]
            poly(d, lens, (16, 18, 26), S, ox, oy, 3)
            polyn(d, [(ex - 18, 278), (ex - 4, 279), (ex - 10, 287), (ex - 20, 286)], (120, 150, 210), S, ox, oy)
        line(d, [(475, 368), (500, 372), (525, 366)], S, ox, oy, 3)
        line(d, [(500, 322), (496, 345), (506, 347)], S, ox, oy, 2)


def char_sprite(kind, scale=0.5, ss=2, **kw):
    W, H = int(1000 * scale), int(1500 * scale)
    im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_character(d, kind, S=scale * ss, ox=0, oy=0, **kw)
    return im.resize((W, H), Image.LANCZOS)


def face_closeup(kind, W=1080, H=1920, cx=500, cy=300, zoom=9.0, ss=2, **kw):
    im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    S = zoom * ss
    draw_character(d, kind, S=S, ox=W * ss / 2 - cx * S, oy=H * ss / 2 - cy * S, **kw)
    return im.resize((W, H), Image.LANCZOS)

# ---------------------------------------------------------------- environments

def vgrad(W, H, top, bot):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / max(1, H - 1)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return im


def cloud(d, x, y, s, col, outline=None):
    for dx, dy, r in ((0, 0, 1), (-.9, .25, .7), (.9, .2, .75), (-.4, -.35, .7), (.45, -.3, .65), (1.6, .35, .5), (-1.6, .4, .5)):
        rr = r * s
        d.ellipse([x + dx * s - rr, y + dy * s - rr, x + dx * s + rr, y + dy * s + rr], fill=col)


def skyline_layer(W, H, base_y, col, win_col, seed, hmin, hmax, wmin, wmax, outline=True, windows=True, screens=None):
    rnd = random.Random(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = -20
    rects = []
    while x < W + 20:
        w = rnd.randint(wmin, wmax)
        h = rnd.randint(hmin, hmax)
        top = base_y - h
        d.rectangle([x, top, x + w, H], fill=col, outline=INK if outline else None, width=5 if outline else 0)
        # roof details
        if rnd.random() < .4:
            d.rectangle([x + w * .3, top - 30, x + w * .45, top], fill=col, outline=INK if outline else None, width=4 if outline else 0)
        if rnd.random() < .25:
            d.line([(x + w * .7, top), (x + w * .7, top - 90)], fill=INK if outline else col, width=5)
        if windows:
            sh = tuple(max(0, c - 28) for c in col)
            d.rectangle([x + w * .72, top + 5, x + w - 3, H], fill=sh)
            for wy in range(int(top + 25), H - 20, 42):
                for wx in range(int(x + 14), int(x + w - 18), 30):
                    if rnd.random() < .8:
                        d.rectangle([wx, wy, wx + 14, wy + 22], fill=win_col)
        rects.append((x, top, w, h))
        x += w + rnd.randint(-10, 18)
    return im, rects


def car_shape(d, x, y, s, col, flip=False):
    k = -1 if flip else 1
    def P(pts): return [(x + k * px * s, y + py * s) for px, py in pts]
    d.polygon(P([(-110, 0), (110, 0), (115, -40), (70, -48), (40, -85), (-50, -85), (-80, -48), (-115, -40)]),
              fill=col, outline=INK, width=max(2, int(5 * s)))
    d.polygon(P([(-40, -78), (-5, -78), (-5, -50), (-68, -50)]), fill=(150, 200, 230), outline=INK, width=max(1, int(3 * s)))
    d.polygon(P([(5, -78), (35, -78), (60, -50), (5, -50)]), fill=(150, 200, 230), outline=INK, width=max(1, int(3 * s)))
    for wx in (-65, 65):
        cx, cy = x + k * wx * s, y
        r = 24 * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 30, 36), outline=INK, width=max(1, int(3 * s)))
        r2 = 10 * s
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(160, 160, 170))


def person(d, x, y, s, col, phase=0.0, run=False):
    """Simple silhouette pedestrian, (x,y)=feet."""
    sw = math.sin(phase) * (0.6 if run else 0.3)
    hy = y - 170 * s
    d.ellipse([x - 16 * s, hy - 34 * s, x + 16 * s, hy - 2 * s], fill=col)
    d.polygon([(x - 20 * s, hy + 4 * s), (x + 20 * s, hy + 4 * s), (x + 14 * s, y - 78 * s), (x - 14 * s, y - 78 * s)], fill=col)
    for k in (1, -1):
        d.line([(x, y - 80 * s), (x + k * sw * 60 * s, y)], fill=col, width=int(20 * s))
        d.line([(x, hy + 10 * s), (x - k * sw * 55 * s, hy + 80 * s - (40 * s if run else 0))], fill=col, width=int(14 * s))
