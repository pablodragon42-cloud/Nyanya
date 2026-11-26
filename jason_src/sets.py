# Environments for the Jason short, in the reference's flat style.
# Everything is drawn in a neutral "day" palette and pushed through a light transform
# (dusk / moonlit night / warm interior / camera flash) so characters and sets match.
import math, random
from gfx import *


def light(mult, add):
    cache = {}
    def f(c):
        r = cache.get(c)
        if r is None:
            r = tuple(int(clamp(c[i] * mult[i] + add[i], 0, 255)) for i in range(3)) + tuple(c[3:])
            cache[c] = r
        return r
    return f

def light_mix(a, b, t):
    """blend two light transforms"""
    cache = {}
    def f(c):
        key = (c, round(t, 3))
        r = cache.get(key)
        if r is None:
            ca, cb = a(c), b(c)
            r = tuple(int(lerp(ca[i], cb[i], t)) for i in range(3)) + tuple(c[3:])
            cache[key] = r
        return r
    return f

DAY = light((1, 1, 1), (0, 0, 0))
DUSK = light((0.96, 0.80, 0.78), (18, 6, 14))
NIGHT = light((0.52, 0.60, 0.84), (8, 12, 30))
NIGHT_DK = light((0.40, 0.46, 0.68), (4, 8, 22))
INTERIOR = light((0.92, 0.80, 0.66), (18, 8, 0))
FLASH = light((1.15, 1.15, 1.2), (60, 60, 70))
LIGHTNING = light((0.9, 0.95, 1.1), (70, 80, 110))

SKY_NIGHT = [(0, (6, 10, 28)), (0.5, (18, 28, 60)), (1, (36, 50, 88))]
SKY_DUSK = [(0, (52, 44, 104)), (0.45, (170, 96, 128)), (0.8, (246, 160, 112)), (1, (252, 200, 130))]

TREE = ((48, 108, 84), (34, 82, 64))
TREE_DK = ((40, 90, 72), (28, 68, 54))
TRUNK = ((112, 76, 52), (84, 56, 38))
LOG = ((150, 98, 60), (118, 76, 44), (96, 60, 34))
ROOF = ((92, 70, 64), (70, 52, 48))
GROUND = (70, 104, 70)
DIRT = (150, 120, 88)


# ---------------------------------------------------------------- sky
def sky(fr, stops, t=0.0, stars=True, moon=(780, 330), moon_r=95, Lf=DAY, seed=3):
    fr.vgrad(stops)
    if stars:
        rnd = random.Random(seed)
        for i in range(70):
            x, y = rnd.random() * W, rnd.random() * H * .55
            tw = 0.6 + 0.4 * math.sin(t * (1.5 + rnd.random() * 3) + i)
            r = (1.2 + rnd.random() * 1.8) * SS
            c = (255, 255, 240, int(200 * tw))
            fr.d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=c)
    if moon:
        mx, my = moon
        x, y = mx * SS, my * SS
        R = moon_r * SS
        g = glow_sprite((200, 210, 255), 90).resize((int(R * 5.5), int(R * 5.5)), Image.BILINEAR)
        fr.im.paste(g, (int(x - R * 2.75), int(y - R * 2.75)), g)
        fr.d.ellipse([x - R, y - R, x + R, y + R], fill=(242, 238, 210))
        for dx, dy, rr in ((-.35, -.2, .22), (.3, .25, .16), (.1, -.45, .1), (-.15, .4, .12)):
            cx, cy, r2 = x + dx * R, y + dy * R, rr * R
            fr.d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(222, 216, 188))


# ---------------------------------------------------------------- vegetation
def pine(fr, x, y, h, w, cols, Lf, lw=3.5, trunk=True, ol=True):
    c, cs = Lf(cols[0]), Lf(cols[1])
    if trunk:
        tc = Lf(TRUNK[0])
        fr.poly([(x - w * .06, y - h * .16), (x + w * .06, y - h * .16), (x + w * .07, y), (x - w * .07, y)], tc, lw if ol else 0)
    tiers = 4
    left = []
    for i in range(tiers):
        f0 = i / tiers
        yb = y - h * .12 - h * .85 * f0
        yn = y - h * .12 - h * .85 * (f0 + 1 / tiers) + h * .07
        wb = w * .5 * (1 - f0 * .72)
        wn = wb * .42
        left += [(x - wb, yb), (x - wn, yn)]
    top = (x, y - h)
    right = [(2 * x - px, py) for px, py in left]
    pts = left + [top] + right[::-1]
    fr.poly(pts, c, lw if ol else 0)
    sh = [top] + right[::-1][: len(right)]
    sh = [top] + [(px, py) for px, py in right[::-1]] + [(x + w * .02, y - h * .12)]
    fr.polyn(sh, cs)
    if ol:
        fr.poly(pts, None, lw)


def dead_tree(fr, x, y, h, Lf, lw=3.5, seed=1, col=(70, 56, 50)):
    rnd = random.Random(seed)
    c = Lf(col)
    w0 = h * .05
    fr.poly([(x - w0, y), (x - w0 * .5, y - h), (x + w0 * .4, y - h), (x + w0, y)], c, lw)
    for i in range(5):
        yy = y - h * (0.35 + 0.12 * i)
        side = 1 if i % 2 else -1
        L = h * (0.32 - 0.04 * i) * (0.8 + rnd.random() * .4)
        ex, ey = x + side * L, yy - L * (0.4 + rnd.random() * .3)
        fr.poly([(x, yy - 6), (ex, ey), (x, yy + 10)], c, lw * .8)
        fr.line([(ex, ey), (ex + side * L * .25, ey - L * .3)], lw * 1.4, c)


def bush(fr, x, y, s, cols, Lf, lw=3.0):
    c, cs = Lf(cols[0]), Lf(cols[1])
    for dx, dy, r in ((-.7, .1, .55), (0, -.25, .7), (.7, .1, .55)):
        fr.ell(x + dx * s, y + dy * s, r * s, r * s * .8, c, lw)
    fr.ell(x + .45 * s, y - .05 * s, .35 * s, .3 * s, cs, 0)


def forest_row(fr, y, x0, x1, hmin, hmax, cols, Lf, seed, lw=3.5, ol=True, gap=(0.55, 0.9), dead=0.12,
               origin=-6000, limit=9000):
    """a row of trees; the sequence always starts at a fixed origin so moving cameras see the same
    trees, and only those overlapping [x0, x1] are drawn"""
    rnd = random.Random(seed)
    x = origin
    while x < min(x1, limit):
        h = rnd.uniform(hmin, hmax)
        w = h * rnd.uniform(.42, .55)
        dy = rnd.uniform(-10, 10)
        isdead = rnd.random() < dead
        if x + w > x0:
            if isdead:
                dead_tree(fr, x, y + dy, h * .9, Lf, lw, seed=int(x))
            else:
                pine(fr, x, y + dy, h, w, cols, Lf, lw, ol=ol)
        x += w * rnd.uniform(*gap)


def ground(fr, y, Lf, col=GROUND, x0=-3000, x1=5000, depth=4000):
    fr.poly([(x0, y), (x1, y), (x1, y + depth), (x0, y + depth)], Lf(col), 0)


def fog(fr, y, h, a, col=(190, 205, 225), x0=-3000, x1=5000, t=0.0, n=10):
    """soft horizontal mist: overlapping bands with a bell-shaped opacity profile"""
    for i in range(n):
        k = (i + .5) / n
        yy = y - h * .5 + h * k
        hh = h / n * 1.5
        al = int(a * .45 * math.exp(-((k - .5) / .28) ** 2))
        if al <= 1: continue
        off = math.sin(t * .4 + i) * 40
        fr.poly([(x0 + off, yy), (x1 + off, yy), (x1 + off, yy + hh), (x0 + off, yy + hh)], col + (al,), 0)


def fog_screen(fr, y0, y1, a, col=(190, 205, 225)):
    """screen-space haze from y0 to y1 (alpha ramps up downward)"""
    n = 12
    for i in range(n):
        k = (i + .5) / n
        al = int(a * k)
        ya, yb = lerp(y0, y1, i / n) * SS, lerp(y0, y1, (i + 1) / n) * SS
        fr.d.rectangle([0, ya, W * SS, yb], fill=col + (al,))


# ---------------------------------------------------------------- props
def campfire(fr, x, y, t, Lf, s=1.0):
    for a in (-25, 25, 90):
        dx = math.cos(math.radians(a)) * 46 * s
        fr.poly([(x - dx, y - 6 * s + (8 if a == 90 else 0)), (x + dx, y - 22 * s), (x + dx + 6, y - 8 * s),
                 (x - dx + 6, y + 8 * s)], Lf((110, 72, 46)), 3 * s)
    for i, (sc, col) in enumerate(((1.0, (246, 120, 40)), (.68, (252, 196, 60)), (.38, (255, 240, 170)))):
        fl = []
        n = 9
        for j in range(n + 1):
            u = j / n
            ang = math.pi * u
            r = (60 * sc * s) * (0.6 + 0.4 * math.sin(u * math.pi))
            wob = math.sin(t * 9 + j * 1.7 + i) * 8 * s * sc
            if j in (2, 4, 6):
                r *= 1.6 + 0.3 * math.sin(t * 7 + j)
            fl.append((x - math.cos(ang) * 40 * sc * s, y - 10 * s - math.sin(ang) * r * 1.9 + wob))
        fr.poly(fl, col, 2.5 * s if i == 0 else 0)
    for k in range(3):
        ph = (t * 1.3 + k * .33) % 1
        fr.dot(x + math.sin(k * 3 + t * 2) * 30 * s, y - 80 * s - ph * 160 * s, 4 * s * (1 - ph), (255, 200, 90, int(255 * (1 - ph))))


def camp_chair(fr, x, y, Lf, s=1.0, front=False):
    """folding camping chair; backrest frames a sitting character (draw front=True after him)"""
    c, cs = Lf((60, 120, 90)), Lf((40, 90, 66))
    metal = Lf((96, 96, 104))
    P = lambda pts: [(x + px * s, y + py * s) for px, py in pts]
    if not front:
        for sx in (-1, 1):
            fr.line(P([(sx * 128, -400), (sx * 112, 0)]), 6 * s, metal)
            fr.line(P([(sx * 112, -150), (-sx * 100, 0)]), 6 * s, metal)
        fr.poly(P([(-126, -400), (126, -400), (116, -140), (-116, -140)]), c, 4 * s)
        fr.polyn(P([(30, -398), (126, -398), (116, -142), (30, -142)]), cs)
        fr.line(P([(-120, -330), (120, -330)]), 2.5 * s)
    else:
        fr.poly(P([(-124, -152), (124, -152), (118, -112), (-118, -112)]), c, 3.5 * s)
        for sx in (-1, 1):
            fr.poly(P([(sx * 150, -250), (sx * 104, -256), (sx * 106, -236), (sx * 152, -230)]), metal, 3 * s)
            fr.line(P([(sx * 128, -240), (sx * 122, -150)]), 6 * s, metal)
            fr.ell(x + sx * 140 * s, y - 210 * s, 14 * s, 18 * s, Lf((200, 50, 50)), 2.5 * s)


def log_seat(fr, x, y, Lf, s=1.0, half=210):
    c, cs = Lf(LOG[0]), Lf(LOG[1])
    fr.poly([(x - half * s, y - 80 * s), (x + half * s, y - 80 * s), (x + half * s, y), (x - half * s, y)], c, 3.5)
    fr.polyn([(x - half * s, y - 28 * s), (x + half * s, y - 28 * s), (x + half * s, y), (x - half * s, y)], cs)
    for i in range(3):
        fr.line([(x - half * s * .8 + i * 120 * s, y - 60 * s), (x - half * s * .5 + i * 120 * s, y - 52 * s)], 2.2)
    fr.ell(x + half * s, y - 40 * s, 24 * s, 40 * s, Lf((206, 164, 112)), 3)
    fr.ell(x + half * s, y - 40 * s, 11 * s, 19 * s, None, 2)


def car(fr, x, y, s, Lf, col=(196, 60, 56)):
    def P(pts): return [(x + px * s, y + py * s) for px, py in pts]
    fr.poly(P([(-230, 0), (230, 0), (240, -90), (150, -104), (84, -180), (-110, -180), (-170, -104), (-240, -90)]),
            Lf(col), 5 * s)
    fr.polyn(P([(60, -6), (230, -6), (238, -86), (150, -100), (84, -174), (60, -174)]), Lf(mix(col, (0, 0, 0), .25)))
    fr.poly(P([(-96, -166), (-14, -166), (-14, -108), (-150, -108)]), Lf((150, 200, 230)), 3.5 * s)
    fr.poly(P([(-2, -166), (76, -166), (130, -108), (-2, -108)]), Lf((150, 200, 230)), 3.5 * s)
    for wx in (-138, 138):
        fr.circ(x + wx * s, y, 50 * s, Lf((30, 30, 36)), 4 * s)
        fr.circ(x + wx * s, y, 22 * s, Lf((160, 160, 170)), 2.5 * s)
    fr.poly(P([(214, -70), (240, -70), (240, -50), (214, -50)]), Lf((250, 240, 180)), 2.5 * s)


# ---------------------------------------------------------------- cabin exterior
CAB = dict(w=760, h=380, roof=250, door_x=90, door_w=150, door_h=270, win_x=420, win_w=230, win_y=110, win_h=170)


def cabin_ext(fr, x0, gy, Lf, t=0.0, door_open=0.0, shutters=0.0, win_light=1.0, inside=None, smoke=True):
    """cabin front wall from x0 (left) standing on ground y=gy. inside(fr) draws what is seen through
    the window opening before the wall is drawn around it."""
    c = CAB
    wx0, wy0 = x0 + c["win_x"], gy - c["h"] + c["win_y"]
    wx1, wy1 = wx0 + c["win_w"], wy0 + c["win_h"]
    dx0, dx1, dy0 = x0 + c["door_x"], x0 + c["door_x"] + c["door_w"], gy - c["door_h"]
    top = gy - c["h"]
    # chimney + smoke behind the roof
    fr.poly([(x0 + 560, top - 230), (x0 + 640, top - 230), (x0 + 640, top - 60), (x0 + 560, top - 60)], Lf((120, 110, 104)), 4)
    if smoke:
        for k in range(4):
            ph = (t * .25 + k * .25) % 1
            fr.dot(x0 + 600 + math.sin(ph * 6 + k) * 30, top - 250 - ph * 260, 22 + ph * 40, (200, 200, 210, int(90 * (1 - ph))))
    # what is behind the window / door openings
    fr.poly([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], Lf((255, 210, 120)) if win_light > .5 else Lf((60, 50, 40)), 0)
    if inside: inside(fr, (wx0, wy0, wx1, wy1))
    fr.poly([(dx0, dy0), (dx1, dy0), (dx1, gy), (dx0, gy)], Lf((255, 200, 110)) if win_light > .5 else Lf((40, 32, 28)), 0)
    # log wall around the openings
    L0, L1, L2 = Lf(LOG[0]), Lf(LOG[1]), Lf(LOG[2])
    pieces = [(x0, top, x0 + c["w"], wy0), (x0, wy1, x0 + c["w"], gy), (x0, wy0, wx0, wy1), (wx1, wy0, x0 + c["w"], wy1)]
    for (a, b, cc, d) in pieces:
        # cut the door opening out of the lower pieces
        if d > dy0 and b < gy:
            segs = [(a, b, min(cc, dx0), d), (max(a, dx1), b, cc, d)]
            if b < dy0:
                segs.append((max(a, dx0), b, min(cc, dx1), min(d, dy0)))
        else:
            segs = [(a, b, cc, d)]
        for (p, q, r, s_) in segs:
            if r - p > 1 and s_ - q > 1:
                fr.poly([(p, q), (r, q), (r, s_), (p, s_)], L0, 0)
    y = top
    k = 0
    while y < gy:
        fr.line([(x0, y), (x0 + c["w"], y)], 3)
        fr.poly([(x0 + c["w"] - 90, y + 4), (x0 + c["w"], y + 4), (x0 + c["w"], y + 30), (x0 + c["w"] - 90, y + 30)], L1 + (150,), 0)
        y += 34; k += 1
    # wall outline + log ends
    fr.poly([(x0, top), (x0 + c["w"], top), (x0 + c["w"], gy), (x0, gy)], None, 4.5)
    yy = top + 17
    while yy < gy:
        for ex in (x0 - 6, x0 + c["w"] + 6):
            fr.ell(ex, yy, 15, 16, Lf((196, 150, 100)), 3)
        yy += 34
    # door
    if door_open < 0.02:
        fr.poly([(dx0, dy0), (dx1, dy0), (dx1, gy), (dx0, gy)], Lf((122, 80, 48)), 4)
        for i in range(1, 4):
            fr.line([(dx0 + i * c["door_w"] / 4, dy0 + 8), (dx0 + i * c["door_w"] / 4, gy - 8)], 2.4)
        fr.circ(dx1 - 22, gy - 130, 7, Lf((220, 190, 90)), 2)
    else:
        k = clamp(door_open)
        ww = c["door_w"] * (1 - k * .82)
        fr.poly([(dx0, dy0), (dx0 + ww, dy0 + 18 * k), (dx0 + ww, gy + 10 * k), (dx0, gy)], Lf((122, 80, 48)), 4)
    fr.poly([(dx0 - 10, dy0 - 12), (dx1 + 10, dy0 - 12), (dx1 + 10, dy0), (dx0 - 10, dy0)], L2, 3.5)
    # window frame, mullions, shutters
    fc = Lf((110, 72, 44))
    fr.poly([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], None, 5)
    if shutters < 0.02:
        fr.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], 6, fc)
        fr.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], 6, fc)
        fr.poly([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], None, 5)
        fr.poly([(wx0 + 10, wy0 + 10), (wx0 + 40, wy0 + 10), (wx0 + 14, wy0 + 52)], (255, 255, 255, 70), 0)
    else:
        k = clamp(shutters)
        hw = (wx1 - wx0) / 2
        for side, ax in ((-1, wx0), (1, wx1)):
            ww = hw * math.cos(k * math.pi * .48)
            ex = ax + side * (hw * .05 + hw * (1 - math.cos(k * math.pi * .48)) * .0)
            pts = [(ax, wy0), (ax - side * ww, wy0 + 8 * k), (ax - side * ww, wy1 - 8 * k), (ax, wy1)]
            if k > .5:
                ww2 = hw * math.sin((k - .5) * math.pi) * .9
                pts = [(ax, wy0), (ax + side * ww2, wy0 - 10), (ax + side * ww2, wy1 + 10), (ax, wy1)]
            fr.poly(pts, fc, 4)
    fr.poly([(wx0 - 14, wy1), (wx1 + 14, wy1), (wx1 + 14, wy1 + 16), (wx0 - 14, wy1 + 16)], L2, 3.5)
    # roof
    rc, rs = Lf(ROOF[0]), Lf(ROOF[1])
    rp = [(x0 - 70, top + 10), (x0 + c["w"] / 2, top - c["roof"]), (x0 + c["w"] + 70, top + 10), (x0 + c["w"] + 70, top + 40),
          (x0 - 70, top + 40)]
    fr.poly(rp, rc, 4.5)
    fr.polyn([(x0 + c["w"] / 2, top - c["roof"] + 6), (x0 + c["w"] + 66, top + 12), (x0 + c["w"] + 66, top + 36),
              (x0 + c["w"] / 2, top + 36)], rs)
    for i in range(1, 6):
        yy = top - c["roof"] + c["roof"] * i / 6
        hw = (c["w"] / 2 + 70) * i / 6
        fr.line([(x0 + c["w"] / 2 - hw, yy + 8), (x0 + c["w"] / 2 + hw, yy + 8)], 2.4)
    fr.poly(rp, None, 4.5)
    # porch step + lantern
    fr.poly([(dx0 - 40, gy - 4), (dx1 + 40, gy - 4), (dx1 + 50, gy + 26), (dx0 - 50, gy + 26)], L1, 3.5)
    lx, ly = dx1 + 52, dy0 + 40
    fr.line([(lx, ly - 40), (lx, ly - 18)], 3)
    fr.glow(lx, ly, 160, (255, 200, 110), 0.55 * win_light)
    fr.poly([(lx - 14, ly - 18), (lx + 14, ly - 18), (lx + 18, ly + 22), (lx - 18, ly + 22)],
            Lf((255, 220, 140)) if win_light > .5 else Lf((90, 80, 60)), 3)


# ---------------------------------------------------------------- cabin interior
def interior(fr, Lf, win=(140, 420, 640, 980), outside=None, curtains=1.0, shutters=0.0, t=0.0, wind=0.0,
             calendar=True, lantern=(870, 1180), floor_y=1560):
    """interior log wall facing camera with a window; outside(fr, rect) draws the view through it."""
    x0, y0, x1, y1 = win
    if outside: outside(fr, win)
    L0, L1, L2 = Lf(LOG[0]), Lf(LOG[1]), Lf(LOG[2])
    WX0, WX1, WY0 = -1500, 2600, -1200
    for (a, b, c_, d) in ((WX0, WY0, WX1, y0), (WX0, y1, WX1, floor_y), (WX0, y0, x0, y1), (x1, y0, WX1, y1)):
        fr.poly([(a, b), (c_, b), (c_, d), (a, d)], L0, 0)
    y = WY0 + (y0 - WY0) % 40
    while y < floor_y:
        if not (y0 < y < y1):
            fr.line([(WX0, y), (WX1, y)], 3)
        else:
            fr.line([(WX0, y), (x0, y)], 3)
            fr.line([(x1, y), (WX1, y)], 3)
        y += 40
    # floor
    fr.poly([(WX0, floor_y), (WX1, floor_y), (WX1, floor_y + 1400), (WX0, floor_y + 1400)], Lf((104, 68, 42)), 4)
    for i in range(-20, 30):
        fr.line([(540 + i * 90, floor_y), (540 + i * 230, floor_y + 1400)], 2.4)
    # window frame
    fc = Lf((110, 72, 44))
    fr.poly([(x0 - 22, y0 - 22), (x1 + 22, y0 - 22), (x1 + 22, y0), (x0 - 22, y0)], fc, 4)
    fr.poly([(x0 - 30, y1), (x1 + 30, y1), (x1 + 30, y1 + 26), (x0 - 30, y1 + 26)], fc, 4)
    fr.poly([(x0 - 22, y0), (x0, y0), (x0, y1), (x0 - 22, y1)], fc, 4)
    fr.poly([(x1, y0), (x1 + 22, y0), (x1 + 22, y1), (x1, y1)], fc, 4)
    if shutters < 0.02:
        fr.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], 9, fc)
        fr.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], 9, fc)
        fr.poly([(x0 + 14, y0 + 14), (x0 + 70, y0 + 14), (x0 + 20, y0 + 90)], (255, 255, 255, 40), 0)
    else:
        k = clamp(shutters)
        hw = (x1 - x0) / 2
        for side, ax in ((-1, x0), (1, x1)):
            ang = k * 80
            ww = hw * math.cos(math.radians(ang))
            sk = hw * math.sin(math.radians(ang)) * .25
            pts = [(ax, y0), (ax - side * ww, y0 - sk), (ax - side * ww, y1 + sk), (ax, y1)]
            fr.poly(pts, None, 4)
            fr.line([(ax, (y0 + y1) / 2), (ax - side * ww, (y0 + y1) / 2)], 7, fc)
            fr.line([(ax - side * ww, y0 - sk), (ax - side * ww, y1 + sk)], 9, fc)
    # curtains (red check), billow with wind
    cc, cd = Lf((200, 48, 52)), Lf((150, 26, 34))
    for side, ax in ((-1, x0 - 30), (1, x1 + 30)):
        cw = 120 * curtains + 30
        bil = wind * 70 * (0.6 + 0.4 * math.sin(t * 9 + side))
        inner = ax - side * cw
        pts = [(ax + side * 26, y0 - 60), (inner, y0 - 60), (inner - side * bil * .6, (y0 + y1) / 2),
               (inner - side * bil, y1 + 60), (ax + side * 26, y1 + 60)]
        fr.poly(pts, cc, 4)
        for i in range(1, 4):
            xx = lerp(ax + side * 26, inner, i / 4)
            fr.line([(xx, y0 - 56), (xx - side * bil * i / 4, y1 + 56)], 5, cd)
        for j in range(1, 6):
            yy = lerp(y0 - 60, y1 + 60, j / 6)
            fr.line([(ax + side * 26, yy), (inner - side * bil * (j / 6), yy)], 3, cd)
    fr.poly([(x0 - 180, y0 - 74), (x1 + 180, y0 - 74), (x1 + 180, y0 - 58), (x0 - 180, y0 - 58)], Lf((90, 60, 40)), 3)
    # calendar: "13"
    if calendar:
        cx, cy = x1 + 330, y0 + 40
        fr.poly([(cx - 70, cy - 40), (cx + 70, cy - 40), (cx + 70, cy + 120), (cx - 70, cy + 120)], Lf((240, 236, 226)), 4)
        fr.poly([(cx - 70, cy - 40), (cx + 70, cy - 40), (cx + 70, cy - 6), (cx - 70, cy - 6)], Lf((196, 36, 40)), 4)
        fr.circ(cx, cy - 52, 6, Lf((60, 60, 60)), 2)
        tx, ty = fr.Tp(cx, cy + 58)
        f = font("RussoOne.ttf", max(8, int(78 * fr.z)))
        fr.d.text((tx, ty), "13", font=f, fill=Lf((196, 36, 40)), anchor="mm")
    # antlers trophy
    ax, ay = x1 + 330, y0 - 210
    fr.poly([(ax - 40, ay - 30), (ax + 40, ay - 30), (ax + 50, ay + 40), (ax - 50, ay + 40)], Lf((120, 80, 50)), 4)
    for side in (-1, 1):
        pts = [(ax + side * 20, ay - 30), (ax + side * 70, ay - 110), (ax + side * 60, ay - 60), (ax + side * 110, ay - 120),
               (ax + side * 80, ay - 40), (ax + side * 30, ay - 10)]
        fr.poly(pts, Lf((236, 226, 200)), 3.5)
    # table + lantern
    lx, ly = lantern
    fr.poly([(lx - 220, ly + 40), (lx + 220, ly + 40), (lx + 240, ly + 70), (lx - 240, ly + 70)], Lf((130, 86, 52)), 4)
    for sx in (-1, 1):
        fr.poly([(lx + sx * 200 - 14, ly + 70), (lx + sx * 200 + 14, ly + 70), (lx + sx * 196 + 12, ly + 400),
                 (lx + sx * 196 - 12, ly + 400)], Lf((110, 72, 44)), 3.5)
    fr.glow(lx, ly - 30, 420, (255, 190, 100), 0.45)
    fr.poly([(lx - 34, ly + 40), (lx + 34, ly + 40), (lx + 28, ly + 26), (lx - 28, ly + 26)], Lf((70, 70, 76)), 3)
    fr.poly([(lx - 26, ly + 26), (lx + 26, ly + 26), (lx + 30, ly - 50), (lx - 30, ly - 50)], Lf((255, 228, 150)), 3.5)
    fl = 1 + .08 * math.sin(t * 13)
    fr.poly([(lx, ly - 30 - 24 * fl), (lx + 9, ly - 14), (lx, ly - 4), (lx - 9, ly - 14)], (255, 160, 60), 0)
    fr.poly([(lx - 36, ly - 50), (lx + 36, ly - 50), (lx + 20, ly - 70), (lx - 20, ly - 70)], Lf((70, 70, 76)), 3)
    fr.line([(lx - 20, ly - 70), (lx, ly - 96), (lx + 20, ly - 70)], 3)


def night_view(fr, rect, t, Lf=NIGHT, jason=None, cam_off=0.0):
    """what is seen through a window from inside: night forest + fog (+ callback for Jason)"""
    x0, y0, x1, y1 = rect
    fr.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], (14, 22, 48), 0)
    hz = y0 + (y1 - y0) * .62
    fr.poly([(x0, y0 + (y1 - y0) * .2), (x1, y0 + (y1 - y0) * .2), (x1, y1), (x0, y1)], (24, 36, 70), 0)
    rnd = random.Random(5)
    for i in range(14):
        xx = x0 - 40 + i * (x1 - x0 + 80) / 13 + cam_off * .3
        h = rnd.uniform(.35, .6) * (y1 - y0)
        pine(fr, xx, hz + 20, h, h * .45, TREE_DK, NIGHT_DK, 2.5, ol=True)
    fr.poly([(x0, hz + 10), (x1, hz + 10), (x1, y1), (x0, y1)], NIGHT((60, 90, 70)), 0)
    if jason: jason(fr, rect, hz)
    fog(fr, hz + 30, 120, 60, x0=x0, x1=x1, t=t, n=4)


# ---------------------------------------------------------------- big hiding tree
def big_tree(fr, x, gy, Lf, w=440, h=2200):
    c, cs, cd = Lf((104, 72, 52)), Lf((80, 54, 38)), Lf((60, 40, 28))
    # roots
    for side in (-1, 1):
        fr.poly([(x + side * w * .3, gy - 160), (x + side * w * .78, gy + 6), (x + side * w * .5, gy + 14), (x + side * w * .2, gy)],
                c, 4)
    trunk = [(x - w / 2, gy), (x - w * .46, gy - h * .4), (x - w * .42, gy - h), (x + w * .42, gy - h), (x + w * .46, gy - h * .4),
             (x + w / 2, gy)]
    fr.poly(trunk, c, 5)
    fr.polyn([(x + w * .12, gy), (x + w * .14, gy - h), (x + w * .42, gy - h), (x + w * .46, gy - h * .4), (x + w / 2, gy)], cs)
    rnd = random.Random(9)
    for i in range(16):
        bx = x + rnd.uniform(-w * .38, w * .38)
        by = gy - rnd.uniform(60, h * .9)
        L = rnd.uniform(80, 220)
        fr.line([(bx, by), (bx + rnd.uniform(-12, 12), by - L)], 3, cd)
    fr.ell(x - w * .1, gy - 640, 34, 48, cd, 3.5)
    fr.ell(x - w * .1, gy - 640, 16, 26, Lf((40, 26, 18)), 0)


# ---------------------------------------------------------------- forest path (perspective)
class Persp:
    """simple perspective for the path shots: world (X, Z) on the ground -> screen."""
    def __init__(self, horizon=860, f=900, cam_h=420, cx=540):
        self.hz, self.f, self.ch, self.cx = horizon, f, cam_h, cx

    def p(self, X, Z, Y=0.0):
        z = max(Z, 1.0)
        return (self.cx + X / z * self.f, self.hz + (self.ch - Y) / z * self.f)

    def s(self, Z):
        return self.f / max(Z, 1.0)


def path_scene(fr, t, Lf, pz, cam_z, seed=11, path_w=520, jason_draw=None, chars=()):
    """forest path receding to the horizon. cam_z = camera travel along the path."""
    fr.poly([(-2000, pz.hz - 6), (3000, pz.hz - 6), (3000, 4000), (-2000, 4000)], Lf((58, 92, 62)), 0)
    # path trapezoid
    pts = [pz.p(-path_w / 2, 40), pz.p(path_w / 2, 40), pz.p(path_w * .5, 9000), pz.p(-path_w * .5, 9000)]
    fr.poly(pts, Lf(DIRT), 0)
    fr.polyn([pz.p(0, 40), pz.p(path_w / 2, 40), pz.p(path_w * .5, 9000), pz.p(0, 9000)], Lf((132, 104, 76)))
    rnd = random.Random(seed)
    items = []
    span = 9000
    for i in range(70):
        side = -1 if i % 2 else 1
        X = side * rnd.uniform(path_w * .7, path_w * 3.2)
        Z0 = rnd.uniform(0, span)
        Z = (Z0 - cam_z) % span + 60
        h = rnd.uniform(900, 1500)
        items.append((Z, "tree", X, h, rnd.random() < 0.12, i))
    for i in range(12):
        Z = (rnd.uniform(0, span) - cam_z) % span + 60
        items.append((Z, "stone", rnd.uniform(-path_w * .45, path_w * .45), 0, False, i))
    for c in chars:
        items.append((c[0], "char", c, 0, False, 0))
    items.sort(key=lambda it: -it[0])
    for Z, kind, X, h, dead, i in items:
        if kind == "char":
            X[1](fr, X[0]); continue
        sx, sy = pz.p(X, Z) if kind != "char" else (0, 0)
        sc = pz.s(Z)
        if kind == "tree":
            haze = clamp((Z - 1500) / 6000)
            Lt = light_mix(Lf, lambda c: (28, 40, 70) + tuple(c[3:]), haze * .85)
            if dead:
                dead_tree(fr, sx, sy, h * sc, Lt, max(.8, 3.5 * min(1, sc * 1.2)), seed=i)
            else:
                pine(fr, sx, sy, h * sc, h * sc * .5, TREE, Lt, max(.8, 3.5 * min(1, sc * 1.2)))
        elif kind == "stone":
            r = 16 * sc
            fr.ell(sx, sy, r * 1.6, r, Lf((96, 88, 80)), 2.5 * min(1, sc * 2))


def cabin_lower(fr, x0, gy, Lf, margin=16):
    """redraw the wall under the window (to hide the legs of someone leaning out of it)"""
    c = CAB
    wx0 = x0 + c["win_x"]; wx1 = wx0 + c["win_w"]
    wy1 = gy - c["h"] + c["win_y"] + c["win_h"]
    a, b = wx0 - margin, wx1 + margin
    fr.poly([(a, wy1), (b, wy1), (b, gy), (a, gy)], Lf(LOG[0]), 0)
    y = gy - c["h"]
    while y < gy:
        if y > wy1:
            fr.line([(a, y), (b, y)], 3)
        y += 34
    fr.poly([(wx0 - 14, wy1), (wx1 + 14, wy1), (wx1 + 14, wy1 + 16), (wx0 - 14, wy1 + 16)], Lf(LOG[2]), 3.5)


def window_rect(x0, gy):
    c = CAB
    wx0, wy0 = x0 + c["win_x"], gy - c["h"] + c["win_y"]
    return (wx0, wy0, wx0 + c["win_w"], wy0 + c["win_h"])


def birds(fr, t, t0, x0, y0, n=7, Lf=None, seed=4, speed=420):
    """crows flying up and away after t0"""
    if t < t0: return
    rnd = random.Random(seed)
    k = t - t0
    for i in range(n):
        bx = x0 + rnd.uniform(-160, 160) + (rnd.uniform(.4, 1) * speed * k) * (1 if i % 2 else -1)
        by = y0 + rnd.uniform(-60, 60) - rnd.uniform(.6, 1.2) * speed * k
        s = rnd.uniform(14, 24)
        fl = math.sin(t * 22 + i * 1.7)
        fr.poly([(bx - s * 2, by - fl * s), (bx - s * .4, by - s * .2), (bx, by + s * .4), (bx + s * .4, by - s * .2),
                 (bx + s * 2, by - fl * s), (bx, by + s * .1)], (20, 20, 28), 0)


HAZE = (30, 44, 80)
FAR1 = light_mix(NIGHT, lambda c: HAZE + tuple(c[3:]), .6)
FAR2 = light_mix(NIGHT, lambda c: HAZE + tuple(c[3:]), .3)
DFAR1 = light_mix(DUSK, lambda c: (120, 80, 120) + tuple(c[3:]), .6)
DFAR2 = light_mix(DUSK, lambda c: (110, 70, 100) + tuple(c[3:]), .3)
SIL = light((0.10, 0.11, 0.16), (6, 8, 16))
MASK_SIL = light((0.42, 0.46, 0.6), (8, 10, 24))
