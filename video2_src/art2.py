# Part 2 character art: same cel-shaded style as part 1 (video_src/art.py),
# extended with poseable arms, facial expressions and a third hero:
# Arkadiy Parovozov (curly hair, glass helmet, blue suit, red cape,
# "locomotive" warning-sign emblem in a red triangle).
import math, os, sys
from functools import lru_cache
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video_src"))
from art import INK, SKIN, SKIN_SH, T, poly, polyn, ell, line, mirror, PAL  # noqa: E402

PAL = dict(PAL)
PAL["ark"] = dict(suit=(44, 100, 214), suit_sh=(26, 62, 152), acc=(214, 32, 40), acc_sh=(150, 16, 26),
                  cape=(206, 26, 36), cape_in=(122, 12, 22))
HAIR_ARK = (178, 98, 40)
HAIR_ARK_SH = (128, 64, 24)


def rot(pts, px, py, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in pts]


def draw_arm(d, p, sl, angle, side, S, ox, oy):
    """side=-1 screen-left arm, +1 screen-right arm. angle>0 = raised outward."""
    px, py = 352 + sl, 478
    armU = [(338 + sl, 450), (392 + sl, 470), (365 + sl * .7, 770), (300 + sl * .7, 770), (305 + sl * .7, 560)]
    armF = [(300 + sl * .7, 760), (365 + sl * .7, 760), (352 + sl * .7, 900), (290 + sl * .7, 900)]
    fc = (322 + sl * .7, 927)
    U, Fo, C = rot(armU, px, py, angle), rot(armF, px, py, angle), rot([fc], px, py, angle)[0]
    if side > 0:
        U, Fo, C = mirror(U), mirror(Fo), (1000 - C[0], C[1])
    poly(d, U, p["suit"], S, ox, oy)
    poly(d, Fo, p["acc"], S, ox, oy)
    cx, cy = C
    ell(d, (cx - 48, cy - 47, cx + 48, cy + 48), p["acc"], S, ox, oy)
    a = math.radians(angle * (-1 if side > 0 else 1))
    line(d, [(cx - 30 * math.cos(a), cy - 12 - 30 * math.sin(a)), (cx + 30 * math.cos(a), cy - 12 + 30 * math.sin(a))], S, ox, oy, 2.5)


def draw_hero(d, kind, S=1.0, ox=0, oy=0, eyes_dx=0.0, glow=False, mouth="neutral", armL=0.0, armR=0.0, cape=True):
    """Character in a 1000x1500 unit box, front facing, hovering hero pose."""
    p = PAL[kind]
    omni, mark, ark = kind == "omni", kind == "mark", kind == "ark"
    sl = 0 if omni else (22 if mark else -16)
    if cape and p["cape"]:
        cp = [(345, 440), (655, 440), (720, 700), (860, 1380), (790, 1420), (700, 1390),
              (600, 1440), (500, 1400), (400, 1450), (300, 1395), (210, 1430), (140, 1380), (280, 700)]
        poly(d, cp, p["cape"], S, ox, oy, 5)
        polyn(d, [(400, 520), (600, 520), (700, 1360), (600, 1400), (500, 1370), (400, 1410), (300, 1360)], p["cape_in"], S, ox, oy)
    # legs
    legL = [(398 + sl, 840), (497, 840), (488, 1200), (470, 1330), (425, 1330), (412 + sl * .5, 1200)]
    lc, lcs = (p["acc"], p["acc_sh"]) if mark else (p["suit"], p["suit_sh"])
    for leg in (legL, mirror(legL)):
        poly(d, leg, lc, S, ox, oy)
    polyn(d, [(560, 850), (598 - sl, 850), (586 - sl * .5, 1190), (566, 1190)], lcs, S, ox, oy)
    bootL = [(410 + sl * .5, 1180), (490, 1180), (492, 1350), (500, 1395), (392 + sl * .5, 1395), (402 + sl * .5, 1350)]
    for b in (bootL, mirror(bootL)):
        poly(d, b, p["acc"], S, ox, oy)
    polyn(d, [(560, 1190), (585 - sl * .5, 1190), (590 - sl * .5, 1385), (565, 1385)], p["acc_sh"], S, ox, oy)
    # torso
    torso = [(340 + sl, 445), (660 - sl, 445), (640 - sl, 600), (612 - sl * .6, 830), (388 + sl * .6, 830), (360 + sl, 600)]
    poly(d, torso, p["suit"], S, ox, oy)
    polyn(d, [(560, 460), (650 - sl, 460), (632 - sl, 600), (606 - sl * .6, 822), (540, 822)], p["suit_sh"], S, ox, oy)
    line(d, [(420 + sl * .5, 610), (470, 630), (500, 615)], S, ox, oy, 3)
    line(d, [(500, 615), (530, 630), (580 - sl * .5, 610)], S, ox, oy, 3)
    line(d, [(500, 640), (500, 790)], S, ox, oy, 2.5)
    line(d, [(455, 700), (545, 700)], S, ox, oy, 2)
    line(d, [(460, 755), (540, 755)], S, ox, oy, 2)
    if mark:
        sh = [(342 + sl, 447), (455, 447), (420, 520), (360 + sl, 560)]
        poly(d, sh, p["acc"], S, ox, oy, 3)
        poly(d, mirror(sh), p["acc"], S, ox, oy, 3)
    elif omni:
        poly(d, [(440, 440), (560, 440), (540, 478), (460, 478)], p["acc"], S, ox, oy, 3)
    else:
        # red cape clasps + warning-sign emblem (black locomotive in a red triangle)
        for cx in (380, 620):
            ell(d, (cx - 22, 452, cx + 22, 496), (250, 210, 40), S, ox, oy, 3)
        poly(d, [(500, 500), (590, 660), (410, 660)], (214, 32, 40), S, ox, oy, 4)
        polyn(d, [(500, 530), (565, 645), (435, 645)], (255, 255, 255), S, ox, oy)
        loco = [(452, 632), (452, 600), (468, 600), (468, 585), (478, 585), (478, 600), (510, 600), (510, 580),
                (530, 580), (530, 600), (545, 600), (548, 632)]
        polyn(d, loco, (16, 14, 20), S, ox, oy)
        for wx in (468, 492, 528):
            ell(d, (wx - 9, 626, wx + 9, 644), (16, 14, 20), S, ox, oy, 0)
        ell(d, (466, 560, 482, 574), (16, 14, 20), S, ox, oy, 0)
    # belt
    poly(d, [(386 + sl * .6, 795), (614 - sl * .6, 795), (616 - sl * .6, 850), (384 + sl * .6, 850)],
         p["acc_sh"] if mark else p["acc"], S, ox, oy)
    if mark:
        poly(d, [(470, 800), (530, 800), (530, 845), (470, 845)], p["suit"], S, ox, oy, 3)
    if ark:
        poly(d, [(472, 800), (528, 800), (528, 845), (472, 845)], (250, 210, 40), S, ox, oy, 3)
    # arms
    draw_arm(d, p, sl, armL, -1, S, ox, oy)
    draw_arm(d, p, sl, armR, 1, S, ox, oy)
    # neck
    poly(d, [(458, 365), (542, 365), (548, 448), (452, 448)], SKIN, S, ox, oy)
    polyn(d, [(500, 380), (544, 380), (547, 440), (500, 440)], SKIN_SH, S, ox, oy)
    if ark:
        poly(d, [(420, 420), (580, 420), (590, 456), (410, 456)], (170, 180, 196), S, ox, oy, 3)  # helmet collar
    # head
    head = [(428, 212), (572, 212), (570, 335), (535, 395), (465, 395), (430, 335)]
    if ark:
        head = [(424, 214), (576, 214), (574, 335), (540, 398), (460, 398), (426, 335)]
    if ark:  # curls behind the head
        for cx, cy, r in ((410, 250, 34), (590, 250, 34), (405, 300, 26), (595, 300, 26)):
            ell(d, (cx - r, cy - r, cx + r, cy + r), HAIR_ARK, S, ox, oy, 3)
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
        for ex in (465, 535):
            ell(d, (ex - 17, 280, ex + 17, 298), (255, 120, 100) if glow else (250, 250, 250), S, ox, oy, 2)
            ell(d, (ex - 6 + eyes_dx * 9, 282, ex + 6 + eyes_dx * 9, 296), (230, 30, 20) if glow else (40, 30, 30), S, ox, oy, 0)
        line(d, [(440, 268), (488, 282)], S, ox, oy, 7)
        line(d, [(512, 282), (560, 268)], S, ox, oy, 7)
        line(d, [(500, 290), (494, 330), (506, 332)], S, ox, oy, 2.5)
        if mouth == "open":
            poly(d, [(470, 366), (530, 366), (524, 392), (476, 392)], (60, 14, 20), S, ox, oy, 2.5)
            polyn(d, [(474, 368), (526, 368), (524, 376), (476, 376)], (250, 250, 250), S, ox, oy)
        elif mouth == "grit":
            poly(d, [(468, 368), (532, 368), (530, 384), (470, 384)], (250, 250, 250), S, ox, oy, 2.5)
            line(d, [(470, 376), (530, 376)], S, ox, oy, 1.5)
        elif mouth == "smirk":
            line(d, [(474, 378), (510, 376), (536, 362)], S, ox, oy, 3)
        else:
            line(d, [(478, 375), (522, 375)], S, ox, oy, 2.5)
        stache = [(452, 352), (478, 338), (500, 342), (522, 338), (548, 352), (556, 378),
                  (536, 364), (500, 358), (464, 364), (444, 378)]
        if mouth == "smirk":
            stache = [(452, 354), (478, 340), (500, 343), (524, 336), (550, 344), (562, 366),
                      (538, 356), (500, 358), (464, 366), (444, 380)]
        poly(d, stache, (30, 26, 30), S, ox, oy, 2)
        line(d, [(450, 312), (458, 340)], S, ox, oy, 1.5)
        line(d, [(550, 312), (542, 340)], S, ox, oy, 1.5)
    elif mark:
        cowl = [(422, 300), (420, 210), (455, 172), (520, 165), (572, 185), (582, 220), (580, 300),
                (560, 322), (520, 318), (500, 330), (480, 318), (440, 322)]
        poly(d, cowl, p["acc"], S, ox, oy)
        polyn(d, [(545, 190), (575, 210), (578, 298), (560, 316), (545, 316)], p["acc_sh"], S, ox, oy)
        for ex, sgn in ((462, -1), (538, 1)):
            lens = [(ex - 30, 270), (ex + 26, 276), (ex + 22, 304), (ex - 26, 298)] if sgn < 0 else \
                   [(ex - 26, 276), (ex + 30, 270), (ex + 26, 298), (ex - 22, 304)]
            poly(d, lens, (16, 18, 26), S, ox, oy, 3)
            polyn(d, [(ex - 18, 278), (ex - 4, 279), (ex - 10, 287), (ex - 20, 286)], (120, 150, 210), S, ox, oy)
        if mouth == "open":
            poly(d, [(468, 352), (532, 352), (522, 388), (500, 392), (478, 388)], (60, 14, 20), S, ox, oy, 3)
            polyn(d, [(472, 354), (528, 354), (526, 362), (474, 362)], (250, 250, 250), S, ox, oy)
            polyn(d, [(484, 378), (516, 378), (510, 388), (490, 388)], (200, 80, 90), S, ox, oy)
        elif mouth == "grit":
            poly(d, [(472, 360), (528, 360), (526, 376), (474, 376)], (250, 250, 250), S, ox, oy, 2.5)
        else:
            line(d, [(475, 368), (500, 372), (525, 366)], S, ox, oy, 3)
        line(d, [(500, 322), (496, 345), (506, 347)], S, ox, oy, 2)
    else:  # Arkadiy
        for cx, cy, r in ((440, 200, 34), (478, 178, 36), (520, 176, 36), (560, 196, 34), (586, 228, 28),
                          (414, 228, 28), (460, 214, 26), (540, 212, 26), (500, 206, 26)):
            ell(d, (cx - r, cy - r, cx + r, cy + r), HAIR_ARK, S, ox, oy, 3)
        for cx, cy in ((470, 190), (530, 188), (565, 210)):
            line(d, [(cx - 12, cy + 4), (cx, cy - 8), (cx + 12, cy + 2)], S, ox, oy, 2, fill=HAIR_ARK_SH)
        for ex in (466, 534):
            ell(d, (ex - 18, 270, ex + 18, 300), (250, 250, 250), S, ox, oy, 2)
            ell(d, (ex - 8 + eyes_dx * 8, 274, ex + 8 + eyes_dx * 8, 296), (40, 110, 200), S, ox, oy, 0)
            ell(d, (ex - 3 + eyes_dx * 8, 280, ex + 3 + eyes_dx * 8, 290), (10, 10, 16), S, ox, oy, 0)
        line(d, [(444, 258), (468, 250), (488, 258)], S, ox, oy, 6, fill=HAIR_ARK_SH)
        line(d, [(512, 258), (532, 250), (556, 258)], S, ox, oy, 6, fill=HAIR_ARK_SH)
        line(d, [(500, 290), (492, 328), (506, 332)], S, ox, oy, 2.5)
        if mouth == "open":
            poly(d, [(462, 350), (538, 350), (530, 382), (500, 390), (470, 382)], (70, 16, 24), S, ox, oy, 3)
            polyn(d, [(466, 352), (534, 352), (532, 361), (468, 361)], (250, 250, 250), S, ox, oy)
            polyn(d, [(484, 374), (516, 374), (510, 386), (490, 386)], (210, 90, 100), S, ox, oy)
        elif mouth == "grit":
            poly(d, [(466, 354), (534, 354), (530, 374), (470, 374)], (250, 250, 250), S, ox, oy, 2.5)
            line(d, [(468, 364), (532, 364)], S, ox, oy, 1.5)
        else:  # smile
            poly(d, [(464, 350), (536, 350), (526, 370), (500, 376), (474, 370)], (250, 250, 250), S, ox, oy, 3)
        ell(d, (446, 318, 466, 330), (240, 150, 130), S, ox, oy, 0)
        ell(d, (534, 318, 554, 330), (220, 130, 110), S, ox, oy, 0)
        # glass helmet (translucent: drawn on its own layer and composited)
        base = d._image
        ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        bx = [ox + 378 * S, oy + 120 * S, ox + 622 * S, oy + 440 * S]
        od.ellipse(bx, fill=(200, 236, 255, 60), outline=(225, 245, 255, 235), width=max(1, int(7 * S)))
        ib = [ox + 400 * S, oy + 140 * S, ox + 600 * S, oy + 420 * S]
        od.arc(ib, 200, 250, fill=(255, 255, 255, 230), width=max(1, int(12 * S)))
        od.arc(ib, 258, 268, fill=(255, 255, 255, 230), width=max(1, int(10 * S)))
        base.alpha_composite(ov)


@lru_cache(maxsize=256)
def hero(kind, scale=0.5, mouth="neutral", armL=0.0, armR=0.0, eyes10=0, glow=False, ss=2):
    W, H = int(1000 * scale), int(1500 * scale)
    im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    draw_hero(d, kind, S=scale * ss, mouth=mouth, armL=armL, armR=armR, eyes_dx=eyes10 / 10, glow=glow)
    return im.resize((W, H), Image.LANCZOS)


@lru_cache(maxsize=64)
def closeup(kind, zoom=6.0, cx=500, cy=300, mouth="neutral", eyes10=0, glow=False, W=1080, H=1920, ss=2, armL=0.0, armR=0.0):
    im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    S = zoom * ss
    draw_hero(d, kind, S=S, ox=W * ss / 2 - cx * S, oy=H * ss / 2 - cy * S, mouth=mouth, eyes_dx=eyes10 / 10,
              glow=glow, armL=armL, armR=armR)
    return im.resize((W, H), Image.LANCZOS)
