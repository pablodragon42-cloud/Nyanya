# Core 2D vector drawing for the Jason short: world-space camera + supersampled PIL canvas.
# Same look as video_src (flat fills, dark ink outlines, one-side cel shade), but every
# shape goes through a camera so shots can push in, rotate and shake without resampling.
import math, os, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SS = 2                      # supersampling factor
INK = (14, 12, 20)
YEL = (255, 214, 0)
WHITE = (255, 255, 255)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)

def eout(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ein(x):
    x = clamp(x); return x ** 3

def eback(x, s=1.9):
    x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1

def eelastic(x):
    x = clamp(x)
    if x in (0.0, 1.0): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1

def mix(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))

def seg(t, a, b):
    """0..1 progress of t through [a, b]"""
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def kf(t, keys, fn=ease):
    """keyframes [(time, value), ...]; value may be a number or a tuple"""
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            k = fn(seg(t, t0, t1))
            if isinstance(v0, tuple): return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return keys[-1][1]

def noise1(t, seed=0):
    """smooth pseudo-noise in [-1, 1]"""
    return (math.sin(t * 1.7 + seed * 1.3) * 0.5 + math.sin(t * 2.9 + seed * 2.7) * 0.3
            + math.sin(t * 5.3 + seed * 0.7) * 0.2)

def shake(t, amp, freq=13.0, seed=0):
    return (amp * (math.sin(t * freq * 2.1 + seed) + .5 * math.sin(t * freq * 3.7 + seed * 2)),
            amp * (math.cos(t * freq * 1.7 + seed * 3) + .5 * math.sin(t * freq * 4.3 + seed)))


@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(os.path.join(HERE, "fonts", name), size)


class Cam:
    """world -> screen. (cx, cy) world point at the screen centre, zoom, rotation (deg), screen offset."""
    __slots__ = ("cx", "cy", "zoom", "rot", "ox", "oy")

    def __init__(self, cx=W / 2, cy=H / 2, zoom=1.0, rot=0.0, ox=0.0, oy=0.0):
        self.cx, self.cy, self.zoom, self.rot, self.ox, self.oy = cx, cy, zoom, rot, ox, oy

    def matrix(self):
        c, s = math.cos(math.radians(self.rot)), math.sin(math.radians(self.rot))
        z = self.zoom * SS
        a, b, d, e = c * z, -s * z, s * z, c * z
        tx = (W / 2 + self.ox) * SS - (a * self.cx + b * self.cy)
        ty = (H / 2 + self.oy) * SS - (d * self.cx + e * self.cy)
        return (a, b, tx, d, e, ty)

    def par(self, p, ref):
        """parallax copy: p=1 follows this camera, p=0 stays at the reference camera"""
        return Cam(lerp(ref.cx, self.cx, p), lerp(ref.cy, self.cy, p),
                   ref.zoom * (self.zoom / ref.zoom) ** p, self.rot, self.ox, self.oy)

    def shaken(self, dx, dy, drot=0.0):
        return Cam(self.cx, self.cy, self.zoom, self.rot + drot, self.ox + dx, self.oy + dy)


def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=40, a0=0.0, a1=2 * math.pi):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    pts = []
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    m = n if full else n + 1
    for i in range(m):
        a = a0 + (a1 - a0) * i / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


class Frame:
    def __init__(self, bg=(0, 0, 0)):
        self.im = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.lw = 1.0
        self.set_cam(Cam())

    # ---- camera
    def set_cam(self, cam):
        self.cam = cam
        self.M = cam.matrix()
        self.z = cam.zoom * SS

    def T(self, pts):
        a, b, tx, d, e, ty = self.M
        return [(a * x + b * y + tx, d * x + e * y + ty) for x, y in pts]

    def Tp(self, x, y):
        a, b, tx, d, e, ty = self.M
        return (a * x + b * y + tx, d * x + e * y + ty)

    def _lw(self, w):
        return max(1, int(round(w * self.z * self.lw)))

    # ---- primitives (world space)
    def poly(self, pts, fill=None, w=4.0, ol=INK):
        if len(pts) < 3: return
        P = self.T(pts)
        if fill is not None:
            self.d.polygon(P, fill=fill)
        if w and ol is not None:
            self.d.line(P + [P[0], P[1]], fill=ol, width=self._lw(w), joint="curve")

    def polyn(self, pts, fill):
        if len(pts) >= 3:
            self.d.polygon(self.T(pts), fill=fill)

    def line(self, pts, w=4.0, col=INK, caps=True):
        P = self.T(pts)
        lw = self._lw(w)
        self.d.line(P, fill=col, width=lw, joint="curve")
        if caps and lw > 2:
            r = lw / 2
            for x, y in (P[0], P[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def ell(self, cx, cy, rx, ry, fill=None, w=4.0, ol=INK, rot=0.0, n=None):
        if n is None:
            n = int(clamp((rx + ry) * self.z * 0.35, 14, 90))
        self.poly(ellipse_pts(cx, cy, rx, ry, rot, n), fill, w, ol)

    def circ(self, cx, cy, r, fill=None, w=4.0, ol=INK):
        self.ell(cx, cy, r, r, fill, w, ol)

    def dot(self, cx, cy, r, fill):
        """fast filled circle (no outline), radius in world units"""
        x, y = self.Tp(cx, cy)
        rr = r * self.z
        self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill)

    def rect(self, x0, y0, x1, y1, fill=None, w=4.0, ol=INK):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, w, ol)

    # ---- screen-space helpers
    def fill_screen(self, col):
        self.d.rectangle([0, 0, W * SS, H * SS], fill=col)

    def vgrad(self, stops, y0=0, y1=H):
        """vertical gradient in screen space; stops = [(pos 0..1, rgb), ...]"""
        key = (tuple(stops), y0, y1)
        g = _grad_cache(key)
        self.im.paste(g, (0, int(y0 * SS)))

    def paste(self, sprite, wx, wy, scale=1.0, alpha=1.0, anchor=(0.5, 0.5)):
        """paste an RGBA sprite at world point (scaled with the camera, no rotation)"""
        z = self.z * scale          # canvas pixels per sprite pixel (1 sprite px = 1 world unit)
        sw, sh = max(1, int(sprite.width * z)), max(1, int(sprite.height * z))
        sp = sprite.resize((sw, sh), Image.BILINEAR)
        if alpha < 1:
            a = sp.getchannel("A").point(lambda v: int(v * alpha))
            sp.putalpha(a)
        x, y = self.Tp(wx, wy)
        self.im.paste(sp, (int(x - sw * anchor[0]), int(y - sh * anchor[1])), sp)

    def glow(self, wx, wy, r, col, strength=1.0):
        """soft radial light (normal blend), radius in world units"""
        rr = r * self.z
        if rr < 2: return
        sp = glow_sprite(col, int(clamp(strength, 0, 1) * 255))
        size = int(rr * 2)
        if size > 6000: return
        g = sp.resize((size, size), Image.BILINEAR)
        x, y = self.Tp(wx, wy)
        self.im.paste(g, (int(x - rr), int(y - rr)), g)

    def finish(self):
        return self.im.reduce(SS)


class Sub:
    """Draw into a Frame through an extra local transform p' = (ox + s*x, oy + s*y).
    Outline widths are NOT scaled, so a scaled-up set keeps the same line weight as the characters."""
    def __init__(self, fr, ox, oy, s):
        self.fr, self.ox, self.oy, self.s = fr, ox, oy, s
        self.d = fr.d
        self.im = fr.im

    @property
    def z(self):
        return self.fr.z * self.s

    def _p(self, pts):
        return [(self.ox + self.s * x, self.oy + self.s * y) for x, y in pts]

    def poly(self, pts, fill=None, w=4.0, ol=INK):
        self.fr.poly(self._p(pts), fill, w, ol)

    def polyn(self, pts, fill):
        self.fr.polyn(self._p(pts), fill)

    def line(self, pts, w=4.0, col=INK, caps=True):
        self.fr.line(self._p(pts), w, col, caps)

    def ell(self, cx, cy, rx, ry, fill=None, w=4.0, ol=INK, rot=0.0, n=None):
        self.fr.ell(self.ox + self.s * cx, self.oy + self.s * cy, rx * self.s, ry * self.s, fill, w, ol, rot, n)

    def circ(self, cx, cy, r, fill=None, w=4.0, ol=INK):
        self.ell(cx, cy, r, r, fill, w, ol)

    def dot(self, cx, cy, r, fill):
        self.fr.dot(self.ox + self.s * cx, self.oy + self.s * cy, r * self.s, fill)

    def glow(self, wx, wy, r, col, strength=1.0):
        self.fr.glow(self.ox + self.s * wx, self.oy + self.s * wy, r * self.s, col, strength)

    def Tp(self, x, y):
        return self.fr.Tp(self.ox + self.s * x, self.oy + self.s * y)

    def W(self, x, y):
        """local -> world"""
        return (self.ox + self.s * x, self.oy + self.s * y)


@lru_cache(maxsize=32)
def _grad_cache(key):
    stops, y0, y1 = key
    hh = int((y1 - y0) * SS)
    ys = np.linspace(0, 1, hh)
    pos = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], np.float32)
    rgb = np.stack([np.interp(ys, pos, cols[:, i]) for i in range(3)], 1)
    arr = np.repeat(rgb[:, None, :], W * SS, 1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


@lru_cache(maxsize=64)
def glow_sprite(col, a):
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - n / 2 + .5) ** 2 + (yy - n / 2 + .5) ** 2) / (n / 2)
    al = np.clip(1 - r, 0, 1) ** 2.2 * a
    im = np.zeros((n, n, 4), np.uint8)
    im[..., 0], im[..., 1], im[..., 2] = col
    im[..., 3] = al.astype(np.uint8)
    return Image.fromarray(im, "RGBA")


# ---------------------------------------------------------------- post (final 1080x1920)
_rng = np.random.default_rng(1)
GRAIN = [(_rng.normal(0, 7, (H // 2, W // 2))).astype(np.float32) for _ in range(6)]
_yy, _xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.38 * (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 1.6)) ** 2)).clip(0.45, 1).astype(np.float32)[..., None]
del _yy, _xx


def grain_vignette(im, fi, vig=1.0, grade=None):
    a = np.asarray(im).astype(np.float32)
    if grade is not None:
        mul, add = grade
        a = a * np.array(mul, np.float32) + np.array(add, np.float32)
    g = GRAIN[fi % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    v = VIG if vig == 1.0 else (1 - (1 - VIG) * vig)
    a = a * v + g
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def text_img(txt, f, fill, stroke=8, sfill=INK, spacing=0):
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
