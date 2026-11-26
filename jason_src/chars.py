# Front-view 2D puppets in the reference's flat style (angular shapes, ink outlines,
# a darker cel-shade strip on the screen-right side of every part).
# Coordinates: character-local units, y down, origin on the ground between the feet.
import math
from gfx import *

SKIN = (233, 180, 140)
SKIN_SH = (196, 136, 102)
MOUTH_IN = (74, 20, 28)
TONGUE = (214, 96, 100)
TOOTH = (250, 248, 240)
EYE_W = (250, 250, 250)
PUPIL = (30, 22, 22)
SWEAT = (150, 205, 255)


def rotp(p, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def quad(a, b, wa, wb):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    return [(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb),
            (b[0] - nx * wb, b[1] - ny * wb), (a[0] - nx * wa, a[1] - ny * wa)]


def shade_quad(a, b, wa, wb, k0=0.2):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    if nx < 0 or (abs(nx) < 1e-6 and ny < 0):
        nx, ny = -nx, -ny
    return [(a[0] + nx * wa * k0, a[1] + ny * wa * k0), (b[0] + nx * wb * k0, b[1] + ny * wb * k0),
            (b[0] + nx * wb, b[1] + ny * wb), (a[0] + nx * wa, a[1] + ny * wa)]


def ik2(a, t, l1, l2, side, out=True, fore=False):
    dx, dy = t[0] - a[0], t[1] - a[1]
    d = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / d, dy / d
    if d >= l1 + l2:
        return (a[0] + ux * l1, a[1] + uy * l1), (a[0] + ux * (l1 + l2), a[1] + uy * (l1 + l2))
    if fore:
        k = l1 / (l1 + l2)
        return (a[0] + dx * k, a[1] + dy * k), t
    ca = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    al = math.acos(ca)
    best, bs = None, -1e18
    for sg in (1, -1):
        c, s = math.cos(al * sg), math.sin(al * sg)
        jx, jy = a[0] + (ux * c - uy * s) * l1, a[1] + (ux * s + uy * c) * l1
        sc = (side * jx if out else -side * jx) + 0.3 * jy
        if sc > bs:
            bs, best = sc, (jx, jy)
    return best, t


POSE = dict(x=0.0, y=0.0, s=1.0, flip=False, bob=0.0, hip=0.0, lean=0.0,
            ht=0.0, hx=0.0, hy=0.0, hdx=0.0, hdy=0.0, breath=0.0,
            la=None, ra=None, law=None, raw=None, lel=True, rel=True,
            lh="fist", rh="fist", lhr=None, rhr=None, llayer=1, rlayer=1,
            lf=(0.0, 0.0), rf=(0.0, 0.0), lfore=True, rfore=True,
            flash=0.0, screen=0.0, hair_up=0.0, sway=0.0, maskL=None)

FACE = dict(eo=1.0, eol=None, eor=None, lid=None, look=(0.0, 0.0), lookl=None, lookr=None, ps=1.0,
            eyes="normal", brow=0.0, browa=0.0, browl=None, browr=None,
            mouth="line", mo=0.0, smile=0.0, mw=1.0,
            sweat=0.0, blush=0.0, pale=0.0, tear=0.0, vein=0.0, bags=0.0, puff=0.0,
            glint=0.0, glint_col=(235, 240, 255), wrinkle=0.0)


def IDENT(c):
    return c


class Puppet:
    foot_h = 22; shoe_w = 26; stance = 34
    thigh = 150; shin = 150; hip_x = 30
    thigh_w = (22, 19); shin_w = (19, 16)
    torso_h = 235; sh_x = 60; sh_dy = 16
    upper = 118; fore = 112; up_w = (16, 14); fo_w = (14, 12); hand_r = 16
    neck_h = 24; neck_w = 15; head_c = 62
    pupil_r = 5.5; eye_x = 21; eye_y = -4; eye_rx = 12; eye_ry = 14
    brow_y = -26; brow_len = 24; brow_w = 6.0; mouth_y = 38; mouth_w = 14
    def_lid = 0.0

    # ------------------------------------------------------------ anchors (neutral body coords)
    def ynn(self):
        return -(self.foot_h + self.thigh + self.shin + self.torso_h)

    def anchor(self, name, side=1):
        yn = self.ynn()
        hc = yn - self.neck_h - self.head_c
        return {"head": (0.0, hc), "mouth": (0.0, hc + self.mouth_y), "eyes": (0.0, hc + self.eye_y),
                "chest": (0.0, yn + 90), "belly": (0.0, yn + 170), "shoulder": (side * self.sh_x, yn + self.sh_dy),
                "hang": (side * (self.sh_x + 22), yn + self.sh_dy + self.upper + self.fore - 3),
                "top": (0.0, hc - 110), "hip": (0.0, -(self.foot_h + self.thigh + self.shin))}[name]

    def wpt(self, x, y, s, name, side=1):
        a = self.anchor(name, side)
        return (x + s * a[0], y + s * a[1])

    # ------------------------------------------------------------ helpers (local -> world)
    def P_(self, pts):
        return [self.Wp(p) for p in pts]

    def poly(self, pts, fill, w=4.0):
        self.fr.poly(self.P_(pts), None if fill is None else self.L(fill), w * self.s)

    def polyn(self, pts, fill):
        self.fr.polyn(self.P_(pts), self.L(fill))

    def line(self, pts, w=3.0, col=INK):
        self.fr.line(self.P_(pts), w * self.s, col)

    def ell(self, c, rx, ry, fill, w=3.0, rot=0.0, n=28):
        self.poly(ellipse_pts(c[0], c[1], rx, ry, rot, n), fill, w)

    # head-local versions
    def Hd(self, q):
        return self.Hm(q)

    def hpoly(self, pts, fill, w=3.0):
        self.poly([self.Hm(p) for p in pts], fill, w)

    def hpolyn(self, pts, fill):
        self.polyn([self.Hm(p) for p in pts], fill)

    def hline(self, pts, w=3.0, col=INK):
        self.line([self.Hm(p) for p in pts], w, col)

    def hell(self, c, rx, ry, fill, w=3.0, rot=0.0, n=28):
        self.hpoly(ellipse_pts(c[0], c[1], rx, ry, rot, n), fill, w)

    def hdot(self, c, r, fill):
        x, y = self.Wp(self.Hm(c))
        self.fr.dot(x, y, r * self.s, self.L(fill) if len(fill) == 3 else fill)

    # ------------------------------------------------------------ main draw
    def draw(self, fr, pose=None, face=None, light=None, t=0.0):
        P = dict(POSE); P.update(pose or {})
        F = dict(FACE); F.update(face or {})
        if F["lid"] is None: F["lid"] = self.def_lid
        self.L = light or IDENT
        self.P, self.F, self.fr, self.t = P, F, fr, t
        s = P["s"]; X, Y = P["x"], P["y"]; fl = -1.0 if P["flip"] else 1.0
        self.s, self.fl, self.X, self.Y = s, fl, X, Y
        self.Wp = lambda p: (X + fl * s * p[0], Y + s * p[1])
        hip_h = self.foot_h + self.thigh + self.shin
        self.hip_h = hip_h
        hc = (P["sway"], -hip_h + P["hip"] - P["bob"])
        lean = P["lean"]

        def U(p):
            q = rotp((p[0], p[1] + hip_h), lean)
            return (q[0] + hc[0], q[1] + hc[1])
        self.U = U
        yn = -hip_h - self.torso_h
        self.yn = yn
        br = P["breath"]

        # head mapping
        pivot = U((0.0, yn - self.neck_h - br))
        hang = lean + P["ht"]
        hdx, hdy = P["hdx"], P["hdy"]
        hc_ = self.head_c

        def Hm(q):
            r = rotp((q[0] + hdx, q[1] - hc_ + hdy), hang)
            return (pivot[0] + r[0], pivot[1] + r[1])
        self.Hm = Hm

        # arms (solve first, draw in layers)
        arms = {}
        for side, key in ((-1, "l"), (1, "r")):
            S = U((side * self.sh_x, yn + self.sh_dy - br))
            if P[key + "aw"] is not None:
                wx, wy = P[key + "aw"]
                T = ((wx - X) / (fl * s), (wy - Y) / s)
            elif P[key + "a"] is not None:
                T = U(P[key + "a"])
            else:
                T = U((side * (self.sh_x + 22), yn + self.sh_dy + self.upper + self.fore - 3 - br))
            el, wr = ik2(S, T, self.upper, self.fore, side, P[key + "el"])
            arms[side] = (S, el, wr, P[key + "layer"], P[key + "h"], P[key + "hr"])

        for side in (-1, 1):
            if arms[side][3] == 0:
                self.draw_arm(side, *arms[side])
        self.draw_legs(P, U)
        self.draw_back(U, yn)
        self.draw_neck(U, yn, pivot)
        self.draw_torso(U, yn)
        for side in (-1, 1):
            if arms[side][3] == 1:
                self.draw_arm(side, *arms[side])
        self.draw_head(F)
        for side in (-1, 1):
            if arms[side][3] == 2:
                self.draw_arm(side, *arms[side])
        self.after(F)

    def after(self, F):
        pass

    def draw_back(self, U, yn):
        pass

    # ------------------------------------------------------------ legs
    def draw_legs(self, P, U):
        for side, key in ((-1, "l"), (1, "r")):
            fx, fy = P[key + "f"]
            hipj = U((side * self.hip_x, -self.hip_h))
            ank = (side * self.stance + fx, -self.foot_h + fy)
            knee, ank = ik2(hipj, ank, self.thigh, self.shin, side, True, P[key + "fore"])
            self.draw_leg(side, hipj, knee, ank)
            self.draw_shoe(side, ank)

    def draw_leg(self, side, hipj, knee, ank):
        c, cs = self.pants
        self.poly(quad(knee, ank, *self.shin_w), c)
        self.polyn(shade_quad(knee, ank, *self.shin_w), cs)
        self.poly(quad(hipj, knee, *self.thigh_w), c)
        self.polyn(shade_quad(hipj, knee, *self.thigh_w), cs)

    def draw_shoe(self, side, a):
        x, y = a
        w, h = self.shoe_w, self.foot_h
        c, cs = self.shoes
        pts = [(x - w * .8, y - 2), (x + w * .8, y - 2), (x + w, y + h * .55), (x + w * .9, y + h + 2),
               (x - w * .9, y + h + 2), (x - w, y + h * .55)]
        self.poly(pts, c, 3.5)
        self.polyn([(x + w * .25, y), (x + w * .8, y), (x + w, y + h * .55), (x + w * .9, y + h), (x + w * .25, y + h)], cs)
        self.poly([(x - w * .95, y + h * .7), (x + w * .95, y + h * .7), (x + w * .9, y + h + 2), (x - w * .9, y + h + 2)],
                  self.sole, 3)

    # ------------------------------------------------------------ arms + hands
    def draw_arm(self, side, S, el, wr, layer, hand, hr):
        self.draw_upper(side, S, el)
        self.draw_fore(side, el, wr)
        ang = math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0])) - 90 if hr is None else hr
        self.draw_hand(side, wr, ang, hand)

    def draw_upper(self, side, S, el):
        c, cs = self.sleeve
        self.poly(quad(S, el, *self.up_w), c)
        self.polyn(shade_quad(S, el, *self.up_w), cs)

    def draw_fore(self, side, el, wr):
        c, cs = self.sleeve
        self.poly(quad(el, wr, *self.fo_w), c)
        self.polyn(shade_quad(el, wr, *self.fo_w), cs)
        d = (wr[0] - el[0], wr[1] - el[1]); L = math.hypot(*d) or 1
        a = (wr[0] - d[0] / L * 16, wr[1] - d[1] / L * 16)
        self.poly(quad(a, wr, self.fo_w[1] + 1.5, self.fo_w[1] + 1.5), self.cuff, 3)

    def hand_pts(self, wr, ang, pts):
        return [(wr[0] + rotp(p, ang)[0], wr[1] + rotp(p, ang)[1]) for p in pts]

    def finger(self, wr, ang, a, b, w, col):
        A = self.hand_pts(wr, ang, [a])[0]; B = self.hand_pts(wr, ang, [b])[0]
        self.poly(quad(A, B, w, w * .9) , col, 3)
        self.ell(B, w * .9, w * .9, col, 0)
        # outline the rounded tip
        dx, dy = B[0] - A[0], B[1] - A[1]
        a0 = math.atan2(dy, dx) - math.pi / 2
        self.line(ellipse_pts(B[0], B[1], w * .9, w * .9, 0, 10, a0, a0 + math.pi), 3)

    def draw_hand(self, side, wr, ang, kind):
        r = self.hand_r
        sk, sks = self.skin_cols()
        if kind in ("phone", "phoneb"):
            self.draw_phone(side, wr, ang, kind == "phoneb")
            return
        if kind == "can":
            self.draw_can(side, wr, ang)
            return
        if kind == "machete":
            self.draw_machete(side, wr, ang)
            return
        c = (0, r * .85)
        if kind == "open" or kind == "wave":
            spread = 1.0 if kind == "open" else 1.35
            for i, a in enumerate((-28, -9, 9, 28)):
                aa = math.radians(a * spread)
                base = (math.sin(aa) * r * .55, r * 1.2)
                tip = (math.sin(aa) * r * (1.2 + .25 * spread), r * (2.15 + (.2 if i in (1, 2) else 0)))
                self.finger(wr, ang, base, tip, r * .25, sk)
            self.finger(wr, ang, (side * -r * .55, r * .7), (side * -r * 1.25, r * 1.15), r * .27, sk)
            self.poly(self.hand_pts(wr, ang, ellipse_pts(0, r * .9, r * .78, r * .82, 0, 20)), sk, 3)
            return
        if kind in ("point", "shush"):
            self.finger(wr, ang, (side * -r * .25, r * 1.2), (side * -r * .25, r * 2.6), r * .3, sk)
        if kind == "peace":
            self.finger(wr, ang, (-r * .35, r * 1.2), (-r * .75, r * 2.6), r * .28, sk)
            self.finger(wr, ang, (r * .25, r * 1.2), (r * .55, r * 2.6), r * .28, sk)
        if kind == "thumb":
            self.finger(wr, ang, (side * -r * .5, r * .9), (side * -r * 1.35, r * .2), r * .3, sk)
        self.poly(self.hand_pts(wr, ang, ellipse_pts(c[0], c[1], r * .95, r * .98, 0, 24)), sk, 3)
        self.polyn(self.hand_pts(wr, ang, ellipse_pts(c[0] + r * .35, c[1], r * .5, r * .85, 0, 16)), sks)
        if kind in ("fist", "grab", "thumb", "point", "shush", "peace"):
            self.line(self.hand_pts(wr, ang, [(-r * .55, r * 1.2), (r * .55, r * 1.2)]), 2.4)

    def draw_phone(self, side, wr, ang, back):
        r = self.hand_r
        sk, sks = self.skin_cols()
        pw, ph = r * 1.0, r * 1.85
        a = ang if self.P[("l" if side < 0 else "r") + "hr"] is None else ang
        c = (0, r * 1.3)
        body = self.hand_pts(wr, a, [(c[0] - pw, c[1] - ph), (c[0] + pw, c[1] - ph), (c[0] + pw, c[1] + ph),
                                     (c[0] - pw, c[1] + ph)])
        self.poly(body, (28, 28, 34), 3)
        if back:
            lens = self.hand_pts(wr, a, [(c[0] - pw * .45, c[1] - ph * .7)])[0]
            self.ell(lens, r * .28, r * .28, (60, 64, 80), 2)
            fl = self.hand_pts(wr, a, [(c[0] + pw * .3, c[1] - ph * .72)])[0]
            self.ell(fl, r * .16, r * .16, (255, 250, 210) if self.P["flash"] > 0.05 else (150, 150, 140), 1.5)
            self.flash_pt = fl
        else:
            scr = self.hand_pts(wr, a, [(c[0] - pw * .78, c[1] - ph * .85), (c[0] + pw * .78, c[1] - ph * .85),
                                       (c[0] + pw * .78, c[1] + ph * .85), (c[0] - pw * .78, c[1] + ph * .85)])
            self.polyn(scr, mix((70, 110, 190), (220, 235, 255), self.P["screen"]))
            self.flash_pt = self.hand_pts(wr, a, [(c[0], c[1] - ph * .7)])[0]
        # fingers wrapping the phone
        for yy in (c[1] - ph * .1, c[1] + ph * .35):
            p = self.hand_pts(wr, a, [(c[0] + side * pw * 1.05, yy)])[0]
            self.ell(p, r * .32, r * .26, sk, 2.4)
        p = self.hand_pts(wr, a, [(c[0] - side * pw * 1.05, c[1] + ph * .15)])[0]
        self.ell(p, r * .3, r * .4, sk, 2.4)

    def draw_can(self, side, wr, ang):
        r = self.hand_r
        sk, _ = self.skin_cols()
        c = (0, r * 1.1)
        body = self.hand_pts(wr, 0, [(c[0] - r * .75, c[1] - r * 1.3), (c[0] + r * .75, c[1] - r * 1.3),
                                     (c[0] + r * .75, c[1] + r * 1.2), (c[0] - r * .75, c[1] + r * 1.2)])
        self.poly(body, (210, 40, 44), 3)
        band = self.hand_pts(wr, 0, [(c[0] - r * .75, c[1] - r * .2), (c[0] + r * .75, c[1] - r * .2),
                                     (c[0] + r * .75, c[1] + r * .25), (c[0] - r * .75, c[1] + r * .25)])
        self.polyn(band, (245, 245, 245))
        top = self.hand_pts(wr, 0, [(c[0] - r * .7, c[1] - r * 1.45), (c[0] + r * .7, c[1] - r * 1.45),
                                    (c[0] + r * .75, c[1] - r * 1.3), (c[0] - r * .75, c[1] - r * 1.3)])
        self.poly(top, (190, 190, 196), 2.5)
        p = self.hand_pts(wr, 0, [(c[0] + side * r * .8, c[1] + r * .2)])[0]
        self.ell(p, r * .5, r * .55, sk, 2.6)

    def draw_machete(self, side, wr, ang):
        pass

    def skin_cols(self):
        pale = self.F["pale"]
        return mix(SKIN, (214, 226, 236), pale), mix(SKIN_SH, (170, 186, 204), pale)

    # ------------------------------------------------------------ neck / torso (per character)
    def draw_neck(self, U, yn, pivot):
        sk, sks = self.skin_cols()
        a = U((0, yn + 10)); b = pivot
        self.poly(quad(a, b, self.neck_w, self.neck_w), sk, 3.5)
        self.polyn(shade_quad(a, b, self.neck_w, self.neck_w, 0.1), sks)

    def draw_torso(self, U, yn):
        pass

    # ------------------------------------------------------------ face parts
    def feat(self, x, y):
        """feature position with head turn / nod applied"""
        hx, hy = self.P["hx"], self.P["hy"]
        return (x + hx * 15 - abs(hx) * x * 0.12, y + hy * 11)

    def eye(self, side, F):
        hx = self.P["hx"]
        cx, cy = self.feat(side * self.eye_x, self.eye_y)
        rx = self.eye_rx * (1 - 0.38 * max(0.0, side * hx))
        ry = self.eye_ry
        eo = F["eo"]
        if side < 0 and F["eol"] is not None: eo = F["eol"]
        if side > 0 and F["eor"] is not None: eo = F["eor"]
        st = F["eyes"]
        if st == "squeeze":
            self.hline([(cx - side * rx * 1.1, cy - ry * .7), (cx + side * rx * .7, cy), (cx - side * rx * 1.1, cy + ry * .7)], 4.2)
            return
        if st == "closed" or eo < 0.07:
            self.hline([(cx - rx * 1.05, cy), (cx, cy + ry * .38), (cx + rx * 1.05, cy)], 4.2)
            return
        if st == "happy":
            self.hline([(cx - rx, cy + ry * .25), (cx, cy - ry * .45), (cx + rx, cy + ry * .25)], 4.2)
            return
        if st == "wide":
            rx *= 1.22; ry *= 1.22
        ryy = ry * eo
        self.hpoly(ellipse_pts(cx, cy, rx, ryy, 0, 30), EYE_W, 2.6)
        look = F["look"]
        if side < 0 and F["lookl"] is not None: look = F["lookl"]
        if side > 0 and F["lookr"] is not None: look = F["lookr"]
        pr = self.pupil_r * F["ps"] * (0.55 if st == "wide" else 1.0)
        mx, my = max(0.0, rx - pr * 1.1), max(0.0, ryy - pr * 1.1)
        px, py = cx + look[0] * mx, cy + look[1] * my
        self.hpolyn(ellipse_pts(px, py, pr, min(pr, ryy * .95), 0, 18), PUPIL)
        lid = F["lid"]
        if lid > 0.02 and st != "wide":
            sk, _ = self.skin_cols()
            R = ryy * 1.14
            y0 = -R + 2 * R * lid
            y0 = clamp(y0, -R * .98, R * .98)
            sa = y0 / R
            a_l, a_r = math.pi - math.asin(sa), math.asin(sa) + 2 * math.pi
            pts = [(cx + math.cos(a) * rx * 1.14, cy + math.sin(a) * R)
                   for a in [a_l + (a_r - a_l) * i / 20 for i in range(21)]]
            self.hpolyn(pts, sk)
            xl = cx + math.cos(a_l) * rx * 1.14; xr = cx + math.cos(a_r) * rx * 1.14
            self.hline([(xl, cy + y0), (cx, cy + y0 + ry * .12), (xr, cy + y0)], 3.6)

    def brows(self, F):
        for side in (-1, 1):
            rz = F["browl"] if side < 0 and F["browl"] is not None else F["browr"] if side > 0 and F["browr"] is not None else F["brow"]
            a = F["browa"]
            cx, cy = self.feat(side * self.eye_x, self.brow_y - rz)
            inner = (cx - side * self.brow_len * .5, cy + a * .5)
            outer = (cx + side * self.brow_len * .5, cy - a * .5)
            mid = ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2 - 2.5)
            self.hline([inner, mid, outer], self.brow_w)

    def mouth(self, F, cx=None, cy=None, w=None):
        mx, my = self.feat(0, self.mouth_y)
        if cx is not None: mx, my = cx, cy
        w = (w or self.mouth_w) * F["mw"]
        k = F["mouth"]; op = F["mo"]; sm = F["smile"]
        if F["puff"] > 0.01:
            sk, _ = self.skin_cols()
            for side in (-1, 1):
                self.hell((mx + side * w * 1.7, my - 6), 11 * F["puff"], 10 * F["puff"], sk, 2.4)
            self.hell((mx, my), w * .25, w * .2, MOUTH_IN, 2.4)
            return
        if k == "o":
            self.hell((mx, my), w * .38 + op * w * .2, w * .45 + op * w * .35, MOUTH_IN, 3)
            return
        if k == "teeth":
            hh = w * .42
            pts = [(mx - w * 1.1, my - hh * .5), (mx + w * 1.1, my - hh * .5), (mx + w * 1.2, my + hh * .5),
                   (mx - w * 1.2, my + hh * .5)]
            self.hpoly(pts, TOOTH, 3)
            self.hline([(mx - w * 1.15, my), (mx + w * 1.15, my)], 2)
            for i in range(-3, 4):
                self.hline([(mx + i * w * .3, my - hh * .45), (mx + i * w * .3, my + hh * .45)], 1.6)
            return
        if k == "wavy":
            pts = [(mx - w + i * w / 4, my + (2.5 if i % 2 else -2.5)) for i in range(9)]
            self.hline(pts, 3.2)
            return
        if k == "smirk":
            self.hline([(mx - w * .8, my + 2), (mx + w * .2, my + 1), (mx + w * .9, my - 6)], 3.4)
            return
        if k in ("line",) or op < 0.06:
            pts = [(mx - w, my - sm * w * .32), (mx - w * .5, my + sm * w * .14), (mx, my + sm * w * .2),
                   (mx + w * .5, my + sm * w * .14), (mx + w, my - sm * w * .32)]
            self.hline(pts, 3.4)
            if k == "line" and sm < -0.2:
                pass
            return
        # open shapes: talk / shout / scream / grin
        if k == "scream":
            ww, h = w * (0.75 + .2 * op), w * (0.9 + 1.4 * op)
            pts = ellipse_pts(mx, my + h * .3, ww, h * .65, 0, 26)
            self.hpolyn(pts, MOUTH_IN)
            self.hpolyn(ellipse_pts(mx, my + h * .62, ww * .6, h * .26, 0, 16), TONGUE)
            self.hpolyn([(mx - ww * .7, my - h * .2), (mx + ww * .7, my - h * .2), (mx + ww * .55, my - h * .05),
                         (mx - ww * .55, my - h * .05)], TOOTH)
            self.hpoly(pts, None, 3.2)
            return
        ww = w * (1.25 if k == "grin" else 1.0 + .15 * op)
        h = (w * (0.55 + 0.6 * op) if k == "grin" else w * (0.15 + 1.15 * op)) * (1.25 if k == "shout" else 1)
        up = [(mx - ww, my - sm * ww * .3), (mx - ww * .5, my - h * .12 + sm * ww * .06),
              (mx, my - h * .16 + sm * ww * .08), (mx + ww * .5, my - h * .12 + sm * ww * .06), (mx + ww, my - sm * ww * .3)]
        lo = [(mx + ww * .78, my + h * .52 - sm * ww * .08), (mx, my + h + sm * ww * .12), (mx - ww * .78, my + h * .52 - sm * ww * .08)]
        pts = up + lo
        self.hpolyn(pts, MOUTH_IN)
        if h > w * .35:
            self.hpolyn(ellipse_pts(mx, my + h * .78 + sm * ww * .1, ww * .5, h * .22, 0, 16), TONGUE)
        th = min(h * .3, w * .32)
        if self.teeth_top and th > 1.5:
            tpts = [(x, y + 1) for x, y in up] + [(x, y + th) for x, y in reversed(up[1:-1])]
            self.hpolyn(tpts, TOOTH)
        self.extra_teeth(mx, my, ww, h, sm)
        self.hpoly(pts, None, 3.2)

    teeth_top = True

    def extra_teeth(self, mx, my, ww, h, sm):
        pass

    def face_extras(self, F):
        t = self.t
        if F["blush"] > 0.01:
            for side in (-1, 1):
                cx, cy = self.feat(side * (self.eye_x + 6), self.eye_y + 20)
                self.hpolyn(ellipse_pts(cx, cy, 11, 6, 0, 16), (255, 120, 120, int(110 * F["blush"])))
        if F["bags"] > 0.01:
            for side in (-1, 1):
                cx, cy = self.feat(side * self.eye_x, self.eye_y + self.eye_ry + 4)
                a = int(255 * min(1, F["bags"]))
                self.hline([(cx - 9, cy), (cx, cy + 3), (cx + 9, cy)], 2.2, (90, 60, 70, a))
                self.hline([(cx - 6, cy + 6), (cx, cy + 8), (cx + 6, cy + 6)], 1.8, (90, 60, 70, a))
        if F["sweat"] > 0.01:
            for i, (sx, ph) in enumerate(((1, 0.0), (-1, 0.55))):
                if i == 1 and F["sweat"] < 0.6: continue
                k = ((t * 0.9 + ph) % 1.0)
                cx, cy = self.feat(sx * (self.eye_x + 24), -30 + k * 30)
                sz = 7 * F["sweat"]
                pts = [(cx, cy - sz * 1.8)] + ellipse_pts(cx, cy, sz, sz, 0, 14, -0.3, math.pi + 0.3)
                self.hpoly(pts, SWEAT, 2.2)
        if F["tear"] > 0.01:
            for side in (-1, 1):
                cx, cy = self.feat(side * self.eye_x, self.eye_y + self.eye_ry * .6)
                L = 30 * F["tear"]
                self.hpoly([(cx - 4, cy), (cx + 4, cy), (cx + 5, cy + L), (cx - 5, cy + L)], (140, 200, 255), 2)
        if F["vein"] > 0.01:
            cx, cy = self.feat(30, -42)
            k = 1 + 0.15 * math.sin(t * 30)
            for a in (45, 135, 225, 315):
                p = rotp((7 * k, 0), a)
                q = rotp((12 * k, 0), a)
                self.hline([(cx + p[0], cy + p[1]), (cx + q[0], cy + q[1])], 3.2, (220, 30, 40))


# ===================================================================== scared friend
class Scared(Puppet):
    pants = ((46, 66, 112), (32, 46, 82))
    shoes = ((236, 236, 240), (196, 198, 210))
    sole = (206, 50, 54)
    sleeve = ((206, 44, 50), (150, 24, 34))
    cuff = (150, 24, 34)
    hood = (206, 44, 50); hood_sh = (150, 24, 34); hood_dk = (118, 16, 26)
    hair = (54, 36, 30)

    def draw_back(self, U, yn):
        pts = [(-48, yn + 14), (-46, yn - 26), (-24, yn - 42), (24, yn - 42), (46, yn - 26), (48, yn + 14)]
        self.poly([U(p) for p in pts], self.hood_dk, 3.5)

    def draw_torso(self, U, yn):
        yh = -self.hip_h; sx = self.sh_x
        body = [(-sx + 2, yn + 2), (sx - 2, yn + 2), (sx + 14, yn + 30), (sx + 10, yn + 110), (54, yh + 4),
                (56, yh + 34), (-56, yh + 34), (-54, yh + 4), (-sx - 10, yn + 110), (-sx - 14, yn + 30)]
        self.poly([U(p) for p in body], self.hood, 4)
        sh = [(16, yn + 4), (sx - 2, yn + 4), (sx + 14, yn + 30), (sx + 10, yn + 110), (54, yh + 4), (56, yh + 32), (24, yh + 32)]
        self.polyn([U(p) for p in sh], self.hood_sh)
        self.poly([U(p) for p in [(-56, yh + 14), (56, yh + 14), (56, yh + 34), (-56, yh + 34)]], self.hood_sh, 3)
        self.poly([U(p) for p in [(-38, yh - 58), (38, yh - 58), (48, yh + 8), (-48, yh + 8)]], None, 2.6)
        self.line([U(p) for p in [(-30, yn + 2), (0, yn + 30), (30, yn + 2)]], 3.2)
        for x in (-11, 11):
            self.line([U(p) for p in [(x, yn + 22), (x * 1.2, yn + 78)]], 2.6, (240, 240, 240))

    def draw_head(self, F):
        sk, sks = self.skin_cols()
        for side in (-1, 1):
            ex, ey = side * 52 + self.P["hx"] * -4, 4
            self.hell((ex, ey), 9, 15, sk if side < 0 else sks, 3)
        head = [(-50, -48), (50, -48), (51, 8), (38, 46), (14, 62), (-14, 62), (-38, 46), (-51, 8)]
        self.hpoly(head, sk, 3.6)
        self.hpolyn([(28, -46), (50, -46), (51, 8), (38, 46), (14, 62), (6, 62)], sks)
        self.face_extras_under(F)
        for side in (-1, 1):
            self.eye(side, F)
        self.brows(F)
        nx, ny = self.feat(0, 0)
        nx += self.P["hx"] * 5
        self.hline([(nx + 3, ny + 2), (nx - 3, ny + 20), (nx + 6, ny + 22)], 2.6)
        self.mouth(F)
        self.draw_hair(F)
        self.face_extras(F)

    def face_extras_under(self, F):
        pass

    def draw_hair(self, F):
        up = self.P["hair_up"]
        hx = self.P["hx"]
        def spk(x, y, k=1.0):
            return (x - hx * 4, y - up * k * 26)
        hair = [spk(-56, -6, 0), spk(-60, -48, .3), spk(-50, -72, .6), spk(-44, -98, 1), spk(-28, -86, .7),
                spk(-10, -108, 1.1), spk(4, -94, .8), spk(22, -112, 1.1), spk(30, -90, .8), spk(52, -96, 1),
                spk(50, -74, .6), spk(62, -50, .3), spk(58, -8, 0), spk(50, -30, 0), spk(44, -44, 0), spk(28, -50, 0),
                spk(16, -40, 0), spk(4, -52, 0), spk(-10, -42, 0), spk(-26, -52, 0), spk(-42, -40, 0), spk(-50, -26, 0)]
        self.hpoly(hair, self.hair, 3.6)
        self.hpolyn([spk(-30, -80, .7), spk(-14, -92, .9), spk(-4, -78, .7), spk(-20, -70, .5)], (92, 66, 54))


# ===================================================================== idiot friend
class Idiot(Puppet):
    thigh = 132; shin = 130; hip_x = 34; stance = 38
    thigh_w = (27, 24); shin_w = (15, 13)
    torso_h = 228; sh_x = 70; sh_dy = 18
    upper = 108; fore = 104; up_w = (18, 15); fo_w = (14, 12); hand_r = 18
    neck_h = 14; neck_w = 18; head_c = 66
    eye_x = 22; eye_y = -2; eye_rx = 11; eye_ry = 12.5; pupil_r = 4.6
    brow_y = -30; brow_len = 20; brow_w = 4.6; mouth_y = 40; mouth_w = 17
    def_lid = 0.42
    shirt = ((252, 196, 34), (214, 150, 14))
    shorts = ((150, 136, 92), (118, 104, 66))
    shoes = ((210, 44, 50), (160, 24, 32))
    sole = (240, 240, 240)
    cap = ((38, 92, 214), (20, 52, 150))
    hairc = (214, 120, 48)
    pants = shorts
    cuff = (214, 150, 14)

    def draw_leg(self, side, hipj, knee, ank):
        sk, sks = self.skin_cols()
        self.poly(quad(knee, ank, *self.shin_w), sk)
        self.polyn(shade_quad(knee, ank, *self.shin_w), sks)
        d = (ank[0] - knee[0], ank[1] - knee[1]); L = math.hypot(*d) or 1
        sock_top = (ank[0] - d[0] / L * 52, ank[1] - d[1] / L * 52)
        self.poly(quad(sock_top, ank, self.shin_w[1] + 2, self.shin_w[1] + 1), (245, 245, 245), 3)
        self.line([(sock_top[0] - 10, sock_top[1] + 8), (sock_top[0] + 10, sock_top[1] + 8)], 2, (200, 60, 60))
        # shorts end at the knee
        k2 = (knee[0] + d[0] / L * 14, knee[1] + d[1] / L * 14)
        self.poly(quad(hipj, k2, *self.thigh_w), self.shorts[0])
        self.polyn(shade_quad(hipj, k2, *self.thigh_w), self.shorts[1])

    def draw_upper(self, side, S, el):
        sk, sks = self.skin_cols()
        self.poly(quad(S, el, *self.up_w), sk)
        self.polyn(shade_quad(S, el, *self.up_w), sks)
        d = (el[0] - S[0], el[1] - S[1]); L = math.hypot(*d) or 1
        m = (S[0] + d[0] / L * 58, S[1] + d[1] / L * 58)
        self.poly(quad(S, m, self.up_w[0] + 6, self.up_w[0] + 4), self.shirt[0])
        self.polyn(shade_quad(S, m, self.up_w[0] + 6, self.up_w[0] + 4), self.shirt[1])

    def draw_fore(self, side, el, wr):
        sk, sks = self.skin_cols()
        self.poly(quad(el, wr, *self.fo_w), sk)
        self.polyn(shade_quad(el, wr, *self.fo_w), sks)

    def draw_torso(self, U, yn):
        yh = -self.hip_h; sx = self.sh_x
        c, cs = self.shirt
        # shorts waist under the shirt
        self.poly([U(p) for p in [(-70, yh - 10), (70, yh - 10), (72, yh + 34), (-72, yh + 34)]], self.shorts[0], 3.5)
        body = [(-sx + 4, yn + 2), (sx - 4, yn + 2), (sx + 16, yn + 34), (sx + 12, yn + 84), (76, yh - 70),
                (82, yh - 22), (72, yh + 18), (-72, yh + 18), (-82, yh - 22), (-76, yh - 70), (-sx - 12, yn + 84),
                (-sx - 16, yn + 34)]
        self.poly([U(p) for p in body], c, 4)
        self.polyn([U(p) for p in [(22, yn + 4), (sx - 4, yn + 4), (sx + 16, yn + 34), (sx + 12, yn + 84), (76, yh - 70),
                                   (82, yh - 22), (72, yh + 16), (30, yh + 16)]], cs)
        self.line([U(p) for p in [(-26, yn + 2), (-14, yn + 16), (0, yn + 20), (14, yn + 16), (26, yn + 2)]], 3.2)
        # pizza slice print
        px, py = -6, yn + 96
        self.poly([U(p) for p in [(px - 30, py - 26), (px + 30, py - 26), (px, py + 34)]], (250, 170, 60), 3)
        self.poly([U(p) for p in [(px - 33, py - 34), (px + 33, py - 34), (px + 30, py - 24), (px - 30, py - 24)]],
                  (196, 120, 50), 2.6)
        for qx, qy in ((-10, -12), (10, -8), (0, 10)):
            self.ell(U((px + qx, py + qy)), 5.5, 5.5, (206, 50, 50), 2)
        # belly fold line
        self.line([U(p) for p in [(-40, yh - 6), (0, yh + 2), (40, yh - 6)]], 2.4)

    def draw_head(self, F):
        sk, sks = self.skin_cols()
        hx = self.P["hx"]
        # backwards cap visor behind the head
        self.hpoly(ellipse_pts(36 - hx * 6, -78, 46, 13, -18, 24), self.cap[1], 3)
        for side in (-1, 1):
            self.hell((side * 63 - hx * 4, 8), 9, 15, sk if side < 0 else sks, 3)
        head = [(-58, -44), (58, -44), (64, 0), (58, 34), (40, 56), (14, 66), (-14, 66), (-40, 56), (-58, 34), (-64, 0)]
        self.hpoly(head, sk, 3.6)
        self.hpolyn([(34, -42), (58, -42), (64, 0), (58, 34), (40, 56), (14, 66), (8, 66)], sks)
        self.hline([(-22, 74), (0, 79), (22, 74)], 2.2)
        # freckles
        for side in (-1, 1):
            cx, cy = self.feat(side * 34, 18)
            for dx, dy in ((-4, 0), (3, -3), (4, 4)):
                self.hdot((cx + dx, cy + dy), 1.7, SKIN_SH)
        for side in (-1, 1):
            self.eye(side, F)
        self.brows(F)
        nx, ny = self.feat(0, 14)
        nx += hx * 6
        self.hell((nx, ny), 9.5, 7.5, sks, 2.6)
        self.mouth(F)
        # ginger tufts
        for side in (-1, 1):
            b = side * 58 - hx * 4
            self.hpoly([(b, -6), (b + side * 12, -20), (b + side * 4, -24), (b + side * 14, -36), (b - side * 2, -34)],
                       self.hairc, 3)
        cap = [(-62, -14), (-64, -46), (-50, -74), (-22, -90), (22, -90), (50, -74), (64, -46), (62, -14), (40, -30),
               (0, -34), (-40, -30)]
        cap = [(x - hx * 4, y) for x, y in cap]
        self.hpoly(cap, self.cap[0], 3.6)
        self.hpolyn([(x - hx * 4, y) for x, y in [(30, -86), (50, -74), (64, -46), (62, -14), (40, -30), (24, -32)]], self.cap[1])
        # strap opening of the backwards cap
        ox = -hx * 4
        self.hpoly(ellipse_pts(ox, -33, 13, 11, 0, 18, math.pi, 2 * math.pi) + [(ox + 13, -33)], self.hairc, 2.6)
        self.hline([(ox - 16, -30), (ox + 16, -30)], 3)
        self.hline([(ox - 4, -88), (ox - 2, -60)], 2)
        self.face_extras(F)

    def extra_teeth(self, mx, my, ww, h, sm):
        # buck teeth
        y0 = my - h * .16 + sm * ww * .08
        tw = ww * .22
        for side in (-1, 1):
            x0 = mx + side * tw * .02
            pts = [(x0, y0 - 1), (x0 + side * tw, y0 - 1), (x0 + side * tw, y0 + tw * 1.15), (x0, y0 + tw * 1.2)]
            self.hpoly(pts, TOOTH, 2)


# ===================================================================== the slasher
class Slasher(Puppet):
    foot_h = 30; shoe_w = 36; stance = 50
    thigh = 222; shin = 215; hip_x = 46
    thigh_w = (33, 28); shin_w = (28, 24)
    torso_h = 330; sh_x = 104; sh_dy = 28
    upper = 170; fore = 158; up_w = (28, 23); fo_w = (23, 20); hand_r = 26
    neck_h = 4; neck_w = 38; head_c = 70
    pants = ((42, 44, 52), (28, 30, 36))
    shoes = ((36, 30, 28), (22, 18, 16))
    sole = (24, 20, 18)
    sleeve = ((74, 80, 66), (52, 56, 46))
    cuff = (52, 56, 46)
    jacket = ((74, 80, 66), (52, 56, 46), (40, 44, 36))
    mask = ((238, 234, 218), (198, 194, 178))
    red = (196, 30, 38)

    def skin_cols(self):
        return (168, 150, 140), (130, 116, 108)

    def draw_torso(self, U, yn):
        yh = -self.hip_h; sx = self.sh_x
        c, cs, cd = self.jacket
        body = [(-sx + 6, yn + 4), (sx - 6, yn + 4), (sx + 22, yn + 40), (sx + 16, yn + 150), (88, yh + 10),
                (94, yh + 46), (62, yh + 58), (40, yh + 42), (12, yh + 62), (-22, yh + 44), (-50, yh + 60),
                (-94, yh + 46), (-88, yh + 10), (-sx - 16, yn + 150), (-sx - 22, yn + 40)]
        self.poly([U(p) for p in body], c, 4.5)
        self.polyn([U(p) for p in [(24, yn + 6), (sx - 6, yn + 6), (sx + 22, yn + 40), (sx + 16, yn + 150), (88, yh + 10),
                                   (94, yh + 46), (62, yh + 56), (40, yh + 40), (24, yh + 50)]], cs)
        self.poly([U(p) for p in [(-28, yn + 10), (28, yn + 10), (36, yh + 36), (-36, yh + 36)]], (50, 48, 46), 3)
        for side in (-1, 1):
            self.poly([U(p) for p in [(side * 58, yn + 2), (side * 16, yn + 8), (side * 34, yn + 96)]], cd, 3)
        for (x0, y0, x1, y1) in ((-70, yn + 120, -52, yn + 150), (58, yn + 190, 74, yn + 214), (-40, yh - 40, -30, yh - 20)):
            self.line([U((x0, y0)), U((x1, y1))], 3, (24, 24, 22))

    def draw_head(self, F):
        sk, sks = self.skin_cols()
        hx = self.P["hx"]
        skull = [(-60, -66), (-36, -96), (0, -104), (36, -96), (60, -66), (70, -16), (64, 28), (44, 52), (-44, 52),
                 (-64, 28), (-70, -16)]
        self.hpoly(skull, sk, 4)
        self.hpolyn([(30, -96), (60, -66), (70, -16), (64, 28), (44, 52), (38, 52)], sks)
        for y in (-34, 26):
            self.hline([(-66, y), (66, y)], 4.5, (30, 26, 24))
        ox = hx * 14
        if self.P.get("maskL") is not None:
            self.L = self.P["maskL"]
        m = [(-54, -74), (-30, -90), (0, -94), (30, -90), (54, -74), (62, -34), (60, 14), (48, 50), (26, 72),
             (0, 80), (-26, 72), (-48, 50), (-60, 14), (-62, -34)]
        m = [(x * (1 - abs(hx) * .08) + ox, y) for x, y in m]
        mc, ms = self.mask
        self.hpoly(m, mc, 4)
        self.hpolyn([(x * (1 - abs(hx) * .08) + ox, y) for x, y in
                     [(28, -90), (54, -74), (62, -34), (60, 14), (48, 50), (26, 72), (14, 76), (24, 20), (30, -40)]], ms)
        def F_(x, y):
            return (x * (1 - abs(hx) * .08) + ox + (hx * 4 if abs(x) < 40 else 0), y)
        # vent holes
        for (x, y) in ((-26, -52), (26, -52), (-40, -40), (40, -40), (-12, -44), (12, -44),
                       (-34, 34), (-24, 46), (-40, 46), (34, 34), (24, 46), (40, 46), (-8, 60), (8, 60), (0, 69),
                       (-6, 28), (6, 28)):
            self.hpolyn(ellipse_pts(*F_(x, y), 3.4, 4.2, 0, 10), (40, 34, 34))
        # red chevrons
        self.hpoly([F_(-17, -78), F_(0, -63), F_(17, -78), F_(17, -67), F_(0, -52), F_(-17, -67)], self.red, 2.6)
        for side in (-1, 1):
            self.hpoly([F_(side * 52, 10), F_(side * 30, 16), F_(side * 50, 28)], self.red, 2.6)
            self.hpoly([F_(side * 54, -12), F_(side * 36, -6), F_(side * 52, 4)], self.red, 2.4)
        # brow ridge shadow + eye holes
        for side in (-1, 1):
            hole = [F_(side * 44, -26), F_(side * 12, -18), F_(side * 9, -6), F_(side * 22, 3), F_(side * 42, -6)]
            self.hpolyn([F_(side * 48, -32), F_(side * 8, -24), F_(side * 10, -16), F_(side * 46, -24)], ms)
            self.hpoly(hole, (8, 6, 10), 3)
            if F["glint"] > 0.01:
                gx, gy = F_(side * 24 + F["look"][0] * 5, -10 + F["look"][1] * 3)
                self.hdot((gx, gy), 3.2 * F["glint"], F["glint_col"])
        self.hline([F_(0, -14), F_(-3, 20), F_(4, 24)], 2.2, (150, 146, 132))

    def draw_machete(self, side, wr, ang):
        r = self.hand_r
        sk, sks = self.skin_cols()
        L = 230
        hp = lambda pts: self.hand_pts(wr, ang, pts)
        self.poly(hp([(-7, -10), (7, -10), (7, r * 1.4), (-7, r * 1.4)]), (66, 42, 32), 3)
        blade = [(-11, r * 1.6), (12, r * 1.6), (17, r * 1.6 + L * .55), (20, r * 1.6 + L * .9), (2, r * 1.6 + L),
                 (-11, r * 1.6 + L * .82)]
        self.poly(hp(blade), (184, 190, 198), 3.5)
        self.polyn(hp([(4, r * 1.6), (12, r * 1.6), (17, r * 1.6 + L * .55), (20, r * 1.6 + L * .9), (6, r * 1.6 + L * .96)]),
                   (140, 146, 156))
        self.line(hp([(-8, r * 1.8), (-8, r * 1.6 + L * .8)]), 2, (240, 244, 250))
        self.poly(hp([(-16, r * 1.45), (16, r * 1.45), (16, r * 1.75), (-16, r * 1.75)]), (60, 60, 64), 2.6)
        self.poly(self.hand_pts(wr, ang, ellipse_pts(0, r * .85, r * .95, r * .98, 0, 24)), sk, 3)
        self.polyn(self.hand_pts(wr, ang, ellipse_pts(r * .35, r * .85, r * .5, r * .85, 0, 16)), sks)
        self.line(self.hand_pts(wr, ang, [(-r * .55, r * 1.2), (r * .55, r * 1.2)]), 2.4)


SCARED = Scared()
IDIOT = Idiot()
JASON = Slasher()
