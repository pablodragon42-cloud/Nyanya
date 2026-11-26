# The 18 scenes of "За нами пришёл Джейсон, а мой друг — идиот", timed to the narration.
import json, math, os, random
from gfx import *
from sets import *
from chars import SCARED as F1, IDIOT as F2, JASON as JS

TL = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
WORDS, ENV, QUOTES, DUR = TL["words"], TL["env"], TL["quotes"], TL["duration"]


def ws(sc, i):
    return next(w["s"] for w in WORDS if w["scene"] == sc and w["i"] == i)


def we(sc, i):
    return next(w["e"] for w in WORDS if w["scene"] == sc and w["i"] == i)


def env(t):
    i = int(t * FPS)
    return ENV[i] if 0 <= i < len(ENV) else 0.0


def quote(t, who):
    for q in QUOTES:
        if q["who"] == who and q["s"] - 0.04 <= t <= q["e"] + 0.06:
            return q
    return None


def talk(F, t, who, gain=1.0):
    q = quote(t, who)
    if not q:
        return F
    e = env(t) * gain
    m = q["mode"]
    if m == "shout":
        F.update(mouth="shout", mo=clamp(0.3 + e * 0.9))
    elif m == "whisper":
        F.update(mouth="talk", mo=clamp(e * 0.85))
    elif m == "hiss":
        F.update(mouth="teeth" if e < 0.45 else "talk", mo=clamp(e * .8))
    else:
        F.update(mouth="talk", mo=clamp(e * 0.95))
    return F


def hcam(t, cx, cy, z, rot=0.0, amp=4.0, seed=0, shk=0.0, rot_amp=0.25):
    dx, dy = noise1(t * 1.1, seed) * amp, noise1(t * 0.9, seed + 7) * amp
    dr = noise1(t * 0.6, seed + 3) * rot_amp
    if shk:
        sx, sy = shake(t, shk)
        dx += sx; dy += sy
    return Cam(cx, cy, z, rot + dr, dx, dy)


def cy_for(head_wy, z, sy=780):
    """camera centre y that puts a world point at screen height sy"""
    return head_wy - (sy - H / 2) / z


def blink(t, period=3.1, ph=0.0, dur=0.13):
    k = ((t + ph) % period) / dur
    return 1.0 - math.sin(min(1.0, k) * math.pi) if k < 1 else 1.0


def vx(cam, pad=500):
    return (cam.cx - (W / 2) / cam.zoom - pad, cam.cx + (W / 2) / cam.zoom + pad)


def hang(ch, side, dx=0.0, dy=0.0):
    a = ch.anchor("hang", side)
    return (a[0] + dx, a[1] + dy)


def at(ch, name, dx=0.0, dy=0.0, side=1):
    a = ch.anchor(name, side)
    return (a[0] + dx, a[1] + dy)


def head_y(ch, y, s=1.0, hip=0.0):
    return y + s * (ch.anchor("head")[1] + hip)


def walk(ch, t, speed=1.0, amp=1.0, ph=0.0):
    p = (t * speed + ph) * 2 * math.pi
    a = math.sin(p)
    return dict(bob=abs(math.cos(p)) * 7 * amp, lf=(0, -max(0, a) * 34 * amp), rf=(0, -max(0, -a) * 34 * amp),
                la=hang(ch, -1, a * 8 * amp, -abs(a) * 14 * amp), ra=hang(ch, 1, a * 8 * amp, -abs(a) * 14 * amp),
                ht=a * 1.5 * amp, sway=a * 3 * amp)


def run(ch, t, speed=2.4, ph=0.0, amp=1.0):
    p = (t * speed + ph) * 2 * math.pi
    a = math.sin(p)
    sh = ch.anchor("shoulder", 1)
    up = lambda s: (s * 16, sh[1] + 92)            # fist swings up in front of the chest
    dn = lambda s: (s * (ch.sh_x + 12), sh[1] + 178)  # and back down by the hip
    k = (a + 1) / 2
    la = (lerp(dn(-1)[0], up(-1)[0], k), lerp(dn(-1)[1], up(-1)[1], k))
    ra = (lerp(up(1)[0], dn(1)[0], k), lerp(up(1)[1], dn(1)[1], k))
    return dict(bob=abs(math.cos(p)) * 18 * amp, lf=(-4, -max(0, a) * 80 * amp), rf=(4, -max(0, -a) * 80 * amp),
                la=la, ra=ra, ht=a * 3, sway=a * 5, lel=True, rel=True)


def flail(ch, t, speed=2.2):
    """the idiot's goofy windmill run"""
    d = run(ch, t, speed, amp=0.9)
    sh = ch.anchor("shoulder", 1)
    for side, key in ((-1, "la"), (1, "ra")):
        ang = t * speed * 2 * math.pi + (0 if side < 0 else math.pi)
        d[key] = (side * (ch.sh_x + 60 + math.cos(ang) * 90), sh[1] - 40 + math.sin(ang) * 130)
    d["lh"] = d["rh"] = "open"
    return d


def merge(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


INT_GRADE = ((1.0, .96, .9), (0, 0, 0))


# ============================================================= shared backgrounds
def night_bg(fr, t, cam, base, gy=1500, seed=1, moon=(800, 330), moon_r=80, Lf=NIGHT, fogA=55, stars=True,
             stops=SKY_NIGHT, far=(FAR1, FAR2)):
    fr.set_cam(Cam())
    sky(fr, stops, t, stars=stars, moon=moon, moon_r=moon_r)
    c1 = cam.par(0.3, base); fr.set_cam(c1)
    forest_row(fr, gy - 150, *vx(c1), 520, 820, TREE_DK, far[0], seed, lw=2.5, ol=False)
    c2 = cam.par(0.6, base); fr.set_cam(c2)
    forest_row(fr, gy - 90, *vx(c2), 600, 900, TREE_DK, far[1], seed + 1, lw=3)
    fr.set_cam(cam)
    ground(fr, gy - 60, Lf)
    forest_row(fr, gy - 50, *vx(cam), 700, 1050, TREE, Lf, seed + 2)
    fog(fr, gy - 30, 220, fogA, t=t)


def cabin_at(fr, ox, oy, s, Lf, t, **kw):
    sub = Sub(fr, ox, oy, s)
    cabin_ext(sub, 0, 0, Lf, t=t, **kw)
    return sub


def closeup_bg(fr, t, cam, Lf=NIGHT, seed=31):
    """dark forest behind a close-up"""
    base = Cam(cam.cx, cam.cy, cam.zoom)
    night_bg(fr, t, cam, base, gy=cam.cy + 380 / cam.zoom, seed=seed, moon=None, fogA=25, Lf=Lf)
    fr.set_cam(cam)


def interior_closeup_bg(fr, t, cam, win=(-700, 300, -150, 900)):
    fr.set_cam(cam)
    interior(fr, INTERIOR, win=win, outside=lambda f, r: night_view(f, r, t), t=t, calendar=False, lantern=(1300, 1300))


# ============================================================= SCENE 1
def s01(fr, t):
    """Мы с другом приехали отдохнуть в лес. (dusk establishing tilt-down)"""
    k = ease(seg(t, 0.0, 1.6))
    z = lerp(0.60, 0.75, ease(seg(t, 0.6, 2.4)))
    cam = hcam(t, lerp(520, 560, k), lerp(450, 1476, k), z, amp=3)
    base = Cam(560, 1476, 0.75)
    fr.set_cam(Cam())
    sky(fr, SKY_DUSK, t, stars=False, moon=None)
    fr.set_cam(cam)
    for i in range(5):
        bx = -300 + (t * 260 + i * 90) % 1600 + i * 30
        by = 260 + i * 34 + math.sin(t * 3 + i) * 10
        fl = math.sin(t * 16 + i)
        fr.poly([(bx - 22, by - fl * 10), (bx, by + 4), (bx + 22, by - fl * 10), (bx, by - 2)], (40, 30, 50), 0)
    c1 = cam.par(0.3, base); fr.set_cam(c1)
    forest_row(fr, 1330, *vx(c1), 520, 820, TREE_DK, DFAR1, 3, lw=2.5, ol=False)
    c2 = cam.par(0.6, base); fr.set_cam(c2)
    forest_row(fr, 1400, *vx(c2), 600, 900, TREE_DK, DFAR2, 4, lw=3)
    fr.set_cam(cam)
    ground(fr, 1440, DUSK)
    cabin_at(fr, 150, 1470, 1.45, DUSK, t)
    car(fr, -330, 1640, 0.95, DUSK)
    # camp
    camp_chair(fr, 860, 1880, DUSK, .95)
    sip = seg(t, 1.25, 1.55) - seg(t, 1.95, 2.25)
    F2.draw(fr, dict(x=860, y=1880, s=0.95, hip=140, lf=(-34, 0), rf=(34, 0), lfore=False, rfore=False,
                     la=hang(F2, -1, 20, -70), ra=(lerp(110, 16, ease(sip)), lerp(-370, -585, ease(sip))), rh="can",
                     ht=-4), dict(lid=.55, smile=.6, eo=blink(t, 2.7)), DUSK, t)
    camp_chair(fr, 860, 1880, DUSK, .95, front=True)
    hx = kf(t, [(0.6, -0.7), (1.3, -0.7), (1.7, 0.6), (2.35, 0.6)])
    F1.draw(fr, dict(x=260, y=1900, s=0.95, hx=hx, la=(-30, -350), ra=(30, -350)),
            dict(look=(hx, -.1), smile=.25, eo=blink(t, 3.0, .7)), DUSK, t)
    campfire(fr, 560, 1930, t, DUSK, 1.0)
    fr.glow(560, 1860, 520, (255, 160, 60), .35)
    return dict()


# ============================================================= SCENE 2
def s02(fr, t):
    t_poka, t_jas, t_vur = ws(2, 4), ws(2, 10), ws(2, 11)
    if t < t_poka + 0.2:
        # 2a: everything was normal (dusk -> night at "пока")
        k = ease(seg(t, t_poka - 0.05, t_poka + 0.2))
        Lf = light_mix(DUSK, NIGHT, k)
        z = lerp(1.0, 1.04, seg(t, 2.35, 4))
        cam = hcam(t, 560, cy_for(head_y(F1, 1880, 1, 130), z, 800), z, amp=3, seed=2)
        fr.set_cam(Cam())
        fr.vgrad(SKY_DUSK)
        if k > 0:
            fr.d.rectangle([0, 0, W * SS, H * SS], fill=(6, 10, 28, int(235 * k)))
        fr.set_cam(cam)
        forest_row(fr, 1250, *vx(cam), 600, 900, TREE_DK, light_mix(DFAR2, FAR2, k), 4, lw=3)
        ground(fr, 1330, Lf)
        cabin_at(fr, -420, 1390, 1.45, Lf, t, win_light=1.0)
        log_seat(fr, 300, 1770, Lf, 1.0)
        F1.draw(fr, dict(x=300, y=1880, s=1.0, hip=130, lf=(-34, 0), rf=(34, 0), lfore=False, rfore=False,
                         ra=(150, -470), la=hang(F1, -1, 40, -160)),
                dict(smile=lerp(.6, -.2, k), lid=lerp(.3, 0, k), eo=blink(t, 2.4, .3), look=(.4, .3)), Lf, t)
        hx_, hy_ = 300 + 150, 1880 - 470 + 130
        fr.line([(hx_, hy_), (hx_ + 160, hy_ + 170)], 5, Lf((120, 86, 52)))
        fr.ell(hx_ + 168, hy_ + 180, 17, 13, Lf(mix((250, 246, 236), (120, 70, 40), seg(t, 2.4, 3.7))), 3)
        camp_chair(fr, 830, 1880, Lf)
        sip = seg(t, 2.6, 2.9) - seg(t, 3.3, 3.6)
        F2.draw(fr, dict(x=830, y=1880, s=1.0, hip=140, lf=(-34, 0), rf=(34, 0), lfore=False, rfore=False,
                         ra=(lerp(110, 16, ease(sip)), lerp(-370, -585, ease(sip))), rh="can", la=hang(F2, -1, 20, -70)),
                dict(lid=.55, smile=lerp(.6, 0, k), eo=blink(t, 2.9)), Lf, t)
        camp_chair(fr, 830, 1880, Lf, front=True)
        campfire(fr, 600, 1930, t, Lf, lerp(1.0, 0.55, k))
        fr.glow(600, 1860, 560, (255, 160, 60), .35 * (1 - .6 * k))
        return dict()
    if t < t_jas:
        # 2b: the silhouette between the trees
        k = seg(t, t_poka + 0.2, t_jas)
        z = lerp(0.95, 1.12, ease(k))
        cam = hcam(t, 520, cy_for(head_y(JS, 1520, .65), z, 760), z, amp=2.5, seed=3)
        base = Cam(520, 1150, 0.95)
        night_bg(fr, t, cam, base, gy=1500, seed=21, moon=(860, 260), moon_r=70, fogA=40, Lf=NIGHT_DK)
        fr.set_cam(cam)
        JS.draw(fr, dict(x=520, y=1520, s=0.62 + 0.06 * k, rh="machete", hy=.15, breath=math.sin(t * 2) * 3, maskL=MASK_SIL),
                dict(glint=.8 * seg(t, t_poka + .6, t_poka + .9)), SIL, t)
        for x in (180, 860):
            pine(fr, x, 1640, 1500, 640, TREE, NIGHT_DK, 4)
        fog(fr, 1540, 260, 70, t=t)
        return dict(vig=1.3)
    if t < t_vur:
        # 2c: lightning reveal
        k = seg(t, t_jas, t_vur)
        fl = 1 - seg(t, t_jas, t_jas + 0.25)
        z = lerp(1.25, 1.36, eout(k))
        cam = hcam(t, 520, cy_for(head_y(JS, 1540, .7), z, 700), z, amp=3, seed=4, shk=6 * fl)
        base = Cam(520, 980, 1.25)
        Lf = light_mix(NIGHT, LIGHTNING, fl)
        night_bg(fr, t, cam, base, gy=1500, seed=21, moon=(860, 260), moon_r=70, fogA=40, Lf=Lf)
        fr.set_cam(cam)
        JS.draw(fr, dict(x=520, y=1540, s=0.7, rh="machete", hy=-.05, breath=math.sin(t * 2) * 3),
                dict(glint=1.0), Lf, t)
        fog(fr, 1560, 240, 70, t=t)
        return dict(flash=fl * 0.7)
    # 2d: scared face close-up
    k = seg(t, t_vur, t_vur + 0.25)
    z = lerp(3.0, 3.35, eout(k))
    cam = hcam(t, 540, cy_for(head_y(F1, 1500), z, 760), z, amp=3, seed=5, shk=5 * (1 - k))
    closeup_bg(fr, t, cam)
    F1.draw(fr, dict(x=540, y=1500, s=1.0, hair_up=eout(k), hdy=-6 * k),
            dict(eyes="wide", mouth="o", mo=.4, brow=8, browa=-6, sweat=1.0, pale=.5 * k, look=(0, 0)), NIGHT, t)
    return dict(vig=1.2)


# ============================================================= SCENE 3
def s03(fr, t):
    t_my = ws(3, 3)
    if t < t_my:
        # 3a: same close-up, eyes slide to the idiot ("сука")
        cam = hcam(t, 540, cy_for(head_y(F1, 1500), 3.35, 760), 3.35, amp=2.5, seed=5)
        closeup_bg(fr, t, cam)
        k = ease(seg(t, ws(3, 2), ws(3, 2) + .25))
        F1.draw(fr, dict(x=540, y=1500, s=1.0, hair_up=1 - k, hx=.25 * k),
                dict(eyes="normal", eo=1.0, lid=.35 * k, mouth="wavy" if k > .5 else "o", mo=.3, brow=lerp(8, -2, k),
                     browa=lerp(-6, 6, k), sweat=1.0 - k * .5, pale=.4 * (1 - k), look=(lerp(0, 1, k), 0)), NIGHT, t)
        return dict(vig=1.2)
    # 3b: the idiot waves at Jason and steps toward him; the scared one grabs him
    t_reshil, t_pozn = ws(3, 5), ws(3, 8)
    z = lerp(0.92, 1.0, ease(seg(t, t_my, 9.6)))
    cam = hcam(t, lerp(600, 560, seg(t, t_my, 9.6)), cy_for(head_y(F2, 1900), z, 760), z, amp=4, seed=6)
    base = Cam(600, 1480, 0.92)
    night_bg(fr, t, cam, base, gy=1560, seed=41, moon=(860, 300), moon_r=70)
    fr.set_cam(cam)
    cabin_at(fr, 1120, 1520, 1.45, NIGHT, t)
    JS.draw(fr, dict(x=140, y=1540, s=0.46, rh="machete", breath=math.sin(t * 2) * 3, hy=.1),
            dict(glint=1.0), NIGHT, t)
    fog(fr, 1550, 180, 50, t=t)
    camp_chair(fr, 700, 1900, NIGHT)
    campfire(fr, 330, 1985, t, NIGHT, .5)
    step = ease(seg(t, t_reshil, t_reshil + .7))
    pull = ease(seg(t, t_pozn - .25, t_pozn + .25))
    x2 = lerp(700, 560, step) + 60 * pull
    w2 = walk(F2, t, 1.6, amp=.7 * (1 - abs(step - .5) * 2 if step < 1 else 0))
    wave = math.sin(t * 14) * 18
    F2.draw(fr, merge(w2, dict(x=x2, y=1900, s=1.0, la=(-175 + wave * .3, -700 + wave), lh="wave",
                               ra=hang(F2, 1, 0, -40), rh="can", hx=-.5, lean=-3 + 4 * pull)),
            dict(eyes="happy", mouth="grin", mo=.5, smile=.8, brow=6), NIGHT, t)
    x1 = lerp(960, 900, step)
    reach = ease(seg(t, t_pozn - .5, t_pozn - .1))
    grab = F2.wpt(x2, 1900, 1.0, "shoulder", 1)
    F1.draw(fr, dict(x=x1 - 60 * reach, y=1910, s=1.0, lean=-6 * reach, hx=-.6,
                     law=(lerp(x1 - 120, grab[0] + 10, reach), lerp(1500, grab[1] + 10, reach)) if reach > 0 else None,
                     lh="grab" if reach > .5 else "fist", llayer=1, ra=hang(F1, 1, 10, -60)),
            dict(eyes="wide", mouth="scream" if reach > .3 else "o", mo=.6, brow=7, browa=-6, sweat=1, pale=.3,
                 look=(-1, 0)), NIGHT, t)
    return dict()


# ============================================================= SCENE 4 (interior by the window)
WIN4 = (40, 560, 500, 1100)


def jason_in_window(fr, rect, hz, t, s=0.34, x=None, glint=1.0, Lf=NIGHT, flash=0.0):
    x0, y0, x1, y1 = rect
    jx = x if x is not None else (x0 + x1) / 2 + 20
    JS.draw(fr, dict(x=jx, y=hz + 50, s=s, rh="machete", breath=math.sin(t * 2) * 3),
            dict(glint=glint), light_mix(Lf, FLASH, flash) if flash else Lf, t)


def s04(fr, t):
    t_tiho, t_eto, t_ne = ws(4, 3), ws(4, 4), ws(4, 6)
    push = .06 * ease(seg(t, t_tiho, t_tiho + .2)) + .06 * ease(seg(t, t_eto, t_eto + .2)) + .1 * ease(seg(t, t_ne, t_ne + .2))
    z = 0.9 + push
    cam = hcam(t, lerp(520, 600, push * 3), cy_for(head_y(F1, 1660, 1.06), z, 760), z, amp=3.5, seed=8)
    fr.set_cam(cam)
    interior(fr, INTERIOR, win=WIN4, outside=lambda f, r: night_view(f, r, t, jason=lambda f2, r2, hz: jason_in_window(f2, r2, hz, t)),
             t=t, lantern=(1180, 1180))
    sip = seg(t, 9.9, 10.2) - seg(t, 10.5, 10.8)
    curious = seg(t, 12.6, 12.9)
    F2.draw(fr, dict(x=930, y=1720, s=1.12, ra=(lerp(110, 16, ease(sip)), lerp(-370, -585, ease(sip))), rh="can",
                     la=hang(F2, -1, 0, -10), hx=lerp(-.3, -.6, curious)),
            dict(lid=lerp(.5, .3, curious), smile=.15, eo=blink(t, 2.6, .4), look=(lerp(-.8, -1, curious), 0)), INTERIOR, t)
    F = dict(eyes="wide", brow=6, browa=-6, sweat=1.0, look=(-1, 0))
    P = dict(x=620, y=1660, s=1.06)
    if t < t_tiho:
        P.update(lean=-10, hx=-.8, la=(-150, -560), ra=(90, -470))
        F.update(look=(-1, 0), mouth="o", mo=.2, eyes="normal")
    elif t < t_eto:
        P.update(hx=.6, ra=at(F1, "mouth", 12, 28), rh="shush", rhr=180, rlayer=2, rel=False, la=hang(F1, -1, 0, -20))
        F.update(look=(1, 0))
    elif t < t_ne:
        P.update(hx=.3, la=(-290, -690), lh="point", ra=hang(F1, 1, 0, -20), lean=-4)
        F.update(look=(1, -.1))
    else:
        P.update(hx=.5, la=(-110, -560), ra=(110, -560), lh="open", rh="open", lhr=180, rhr=180)
        F.update(look=(1, 0), brow=9)
    talk(F, t, 1)
    F1.draw(fr, P, F, INTERIOR, t)
    return dict(grade=INT_GRADE)


# ============================================================= SCENE 5
WS_S, WS_OX, WS_OY = 2.2, -637, 1407     # cabin scale/offset for the window shots (window centred on screen)


def window_shot(fr, t, cam, shutters=1.0, f2=None, f1=None, flash=0.0, Lf=NIGHT):
    """exterior: camera outside, the cabin window with the idiot leaning out"""
    Lx = light_mix(Lf, FLASH, flash) if flash else Lf
    fr.set_cam(Cam())
    sky(fr, SKY_NIGHT, t, moon=(940, 160), moon_r=50)
    base = Cam(540, 1000, 1.0)
    c2 = cam.par(0.6, base); fr.set_cam(c2)
    forest_row(fr, 900, *vx(c2), 500, 800, TREE_DK, FAR2, 52, lw=3)
    fr.set_cam(cam)

    def inside(sub, rect):
        x0, y0, x1, y1 = rect
        a, b = sub.W(x0, y0), sub.W(x1, y1)
        fr.poly([a, (b[0], a[1]), b, (a[0], b[1])], Lx((150, 100, 64)), 0)
        for i in range(8):
            yy = a[1] + i * (b[1] - a[1]) / 8
            fr.line([(a[0], yy), (b[0], yy)], 2.5, Lx((110, 70, 40)))
        fr.glow((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 520, (255, 200, 110), .45)
        if f1: f1(fr, a, b)
    sub = Sub(fr, WS_OX, WS_OY, WS_S)
    cabin_ext(sub, 0, 0, Lx, t=t, shutters=shutters, inside=inside, smoke=False)
    x0, y0, x1, y1 = window_rect(0, 0)
    a, b = sub.W(x0, y0), sub.W(x1, y1)
    fr.glow((a[0] + b[0]) / 2, b[1], 700, (255, 190, 100), .25)
    if f2: f2(fr, sub, (a[0] + b[0]) / 2, b[1])
    cabin_lower(sub, 0, 0, Lx)
    ground(fr, WS_OY + 2, Lx)
    fog(fr, WS_OY + 40, 120, 40, t=t)
    return sub


def s05(fr, t):
    t_genius, t_rasp, t_oret, t_jas, t_a, t_mine = ws(5, 3), ws(5, 4), ws(5, 7), ws(5, 8), ws(5, 10), ws(5, 13)
    t_end = we(5, 14)
    if t < t_rasp - 0.08:
        k = ease(seg(t, t_genius, t_genius + .5))
        z = lerp(3.0, 3.3, seg(t, 13.3, t_rasp))
        cam = hcam(t, 540, cy_for(head_y(F2, 1520), z, 740), z, amp=2.5, seed=10)
        interior_closeup_bg(fr, t, cam)
        F2.draw(fr, dict(x=540, y=1520, s=1.0, hx=.25 * k, ht=-4 * k),
                dict(lid=lerp(.45, .25, k), smile=lerp(0, .9, k), mouth="smirk" if k > .3 else "line",
                     brow=lerp(0, 9, k), browa=lerp(0, -3, k), eo=blink(t, 2.2), look=(lerp(0, .5, k), 0)), INTERIOR, t)
        return dict(grade=INT_GRADE)
    if t < t_a:
        # exterior: window bursts open, the idiot leans out and yells
        kopen = eout(seg(t, t_rasp, t_rasp + .18))
        lean_out = eback(seg(t, t_rasp + .05, t_rasp + .4))
        push = ease(seg(t, t_oret, t_end))
        shk = 7 * env(t) if quote(t, 2) else 0
        z = lerp(1.42, 1.62, push)
        cam = hcam(t, 540, lerp(1000, 960, push), z, amp=3, seed=11, shk=shk)

        def f1(fr_, a, b):
            cx = lerp(a[0], b[0], .78)
            F1.draw(fr_, dict(x=cx, y=b[1] + 330, s=.62, la=at(F1, "head", -52, -20), ra=at(F1, "head", 52, -20),
                              lh="open", rh="open", lhr=150, rhr=-150, llayer=2, rlayer=2),
                    dict(eyes="wide", mouth="scream", mo=.7, brow=8, sweat=1, pale=.2), INTERIOR, t)

        def f2(fr_, sub, wx, wy):
            cup = ease(seg(t, t_oret, t_oret + .2))
            spread = 1 - cup
            s = lerp(1.1, 1.3, lean_out)
            P = dict(x=wx - 20, y=wy + 40 + s * 284 + lerp(260, 0, lean_out), s=s,
                     la=(lerp(-60, -250, spread), lerp(-500, -660, spread)), ra=(lerp(60, 250, spread), lerp(-500, -660, spread)),
                     lh="open", rh="open")
            if cup > 0:
                P.update(la=at(F2, "mouth", -46 * cup - 30 * spread, 6), ra=at(F2, "mouth", 46 * cup + 30 * spread, 6),
                         lhr=-120, rhr=120, llayer=2, rlayer=2)
            F = dict(eyes="normal", lid=.15, mouth="grin", mo=.5, smile=.8, brow=6)
            talk(F, t, 2, 1.1)
            F2.draw(fr_, P, F, NIGHT, t)
        window_shot(fr, t, cam, shutters=kopen, f2=f2 if kopen > .3 else None, f1=f1)
        return dict()
    if t < t_end + 0.12:
        # Jason just stares; tilts his head at "Майнкрафт"
        k = seg(t, t_a, t_end)
        z = lerp(1.25, 1.45, ease(k))
        cam = hcam(t, 540, cy_for(head_y(JS, 1560, .72), z, 740), z, amp=2, seed=12)
        base = Cam(540, 1060, 1.25)
        night_bg(fr, t, cam, base, gy=1460, seed=61, moon=(200, 240), moon_r=60, fogA=50)
        fr.set_cam(cam)
        tilt = 9 * ease(seg(t, t_mine, t_mine + .5))
        JS.draw(fr, dict(x=540, y=1560, s=.72, rh="machete", ht=tilt, breath=math.sin(t * 2) * 3),
                dict(glint=1.0), NIGHT, t)
        fog(fr, 1560, 240, 60, t=t)
        return dict(vig=1.2)
    # facepalm during the pause
    k = seg(t, t_end + .12, 20.05)
    z = lerp(3.0, 3.15, k)
    cam = hcam(t, 540, cy_for(head_y(F1, 1510), z, 740), z, amp=2, seed=13)
    interior_closeup_bg(fr, t, cam, win=(-760, 300, -200, 900))
    slide = ease(seg(t, t_end + .2, 20.0))
    F1.draw(fr, dict(x=540, y=1510, s=1.0, ra=at(F1, "head", 12, lerp(-30, 20, slide)), rh="open", rhr=180, rlayer=2,
                     rel=False, ht=-4),
            dict(eyes="closed" if slide < .6 else "normal", lid=.6, mouth="line", smile=-.4, browa=-4,
                 look=(0, .3)), INTERIOR, t)
    return dict(grade=INT_GRADE)


# ============================================================= SCENE 6
def s06(fr, t):
    t_no, t_etot, t_foto, t_vsp = ws(6, 5), ws(6, 7), ws(6, 10), ws(6, 13)
    flashes = [22.85, 23.2, 23.45, 24.05, 24.35, 24.62, t_vsp + 0.05]
    fl = max([max(0.0, 1 - (t - f) / 0.16) if t >= f else 0.0 for f in flashes] + [0.0])
    if t < t_no - .05:
        z = lerp(2.75, 2.95, seg(t, 20.05, t_no))
        cam = hcam(t, 560, cy_for(head_y(F1, 1580), z, 740), z, amp=2.5, seed=14)
        fr.set_cam(cam)
        interior(fr, INTERIOR, win=(-260, 420, 260, 960), outside=lambda f, r: night_view(f, r, t), t=t, calendar=False,
                 shutters=1.0, wind=.4, lantern=(1300, 1300))
        chuckle = math.sin(t * 18) * 4 * seg(t, ws(6, 3), ws(6, 4) + .3)
        F1.draw(fr, dict(x=560, y=1580, s=1.0, bob=chuckle, hx=.3, ra=hang(F1, 1, -30, -80), la=hang(F1, -1, 30, -80)),
                dict(mouth="grin", mo=.25, smile=.6, brow=5, browa=-5, sweat=1, look=(.8, 0), eo=blink(t, 1.6)), INTERIOR, t)
        return dict(grade=INT_GRADE)
    if t < t_etot:
        cam = hcam(t, 540, 950, 1.6, amp=2.5, seed=15)

        def f2(fr_, sub, wx, wy):
            up = eback(seg(t, t_no - .05, t_no + .3))
            F2.draw(fr_, dict(x=wx - 20, y=wy + 40 + 1.3 * 284, s=1.3, ra=(lerp(60, 130, up), lerp(-420, -770, up)),
                              rh="phoneb", flash=1.0 if t > t_no + .35 else 0, la=hang(F2, -1, 0, -40)),
                    dict(lid=.2, mouth="grin", mo=.3, smile=.9, eo=1, look=(.6, -.6), brow=5), NIGHT, t)
        window_shot(fr, t, cam, shutters=1.0, f2=f2)
        return dict()
    seq = [(t_etot, "win"), (23.35, "jas1"), (23.85, "win2"), (24.55, "jas2"), (t_vsp, "photo")]
    shot = "win"
    for st, nm in seq:
        if t >= st: shot = nm
    if shot in ("win", "win2"):
        cam = hcam(t, 540, 960, 1.55 if shot == "win" else 1.45, amp=3, seed=16, shk=4 * fl)

        def f1(fr_, a, b):
            if shot == "win":
                F1.draw(fr_, dict(x=lerp(a[0], b[0], .8), y=b[1] + 330, s=.62, la=at(F1, "head", -52, -20),
                                  ra=at(F1, "head", 52, -20), lh="open", rh="open", lhr=150, rhr=-150, llayer=2, rlayer=2),
                        dict(eyes="wide", mouth="scream", mo=.6, sweat=1), light_mix(INTERIOR, FLASH, fl), t)

        def f2(fr_, sub, wx, wy):
            Lx = light_mix(NIGHT, FLASH, fl)
            snap = math.sin(t * 20) * 6
            x2 = wx - (90 if shot == "win2" else 20)
            s2 = 1.3 if shot == "win" else 1.22
            y2 = wy + 40 + s2 * 284
            if shot == "win2":
                x1, s1 = wx + 150, 1.08
                y1 = wy + 40 + s1 * 322
                F1.draw(fr_, dict(x=x1, y=y1, s=s1, lean=-8, law=F2.wpt(x2, y2, s2, "shoulder", 1), lh="grab", llayer=2,
                                  raw=(x2 + 90, y2 + s2 * (-760) + 40), rh="grab", rlayer=2, hx=-.5),
                        dict(eyes="wide", mouth="teeth", brow=6, browa=4, sweat=1, look=(-1, -.3)), Lx, t)
            F2.draw(fr_, dict(x=x2, y=y2, s=s2, ra=(130, -770 + snap), rh="phoneb", flash=fl, la=hang(F2, -1, 0, -40),
                              lean=4 if shot == "win2" else 0),
                    dict(lid=.1 if fl > .2 else .25, eyes="happy" if fl > .5 else "normal", mouth="grin", mo=.4, smile=1,
                         look=(.6, -.6), brow=6), Lx, t)
        window_shot(fr, t, cam, shutters=1.0, f2=f2, f1=f1, flash=fl)
        return dict(flash=fl * .55)
    if shot in ("jas1", "jas2"):
        z = 1.35 if shot == "jas1" else 2.6
        cam = hcam(t, 540, cy_for(head_y(JS, 1560, .78), z, 760), z, amp=2, seed=17)
        base = Cam(540, 1000, 1.3)
        Lx = light_mix(NIGHT_DK, FLASH, max(fl, .15))
        night_bg(fr, t, cam, base, gy=1460, seed=61, moon=(200, 240), moon_r=60, fogA=40, Lf=Lx)
        fr.set_cam(cam)
        JS.draw(fr, dict(x=540, y=1560, s=.78, rh="machete", breath=math.sin(t * 2) * 3), dict(glint=1.0), Lx, t)
        return dict(flash=fl * .6, vig=1.3)
    # photo freeze-frame in a camera UI
    k = seg(t, t_vsp, t_vsp + .25)
    z = lerp(2.9, 2.75, eout(k))
    cam = hcam(t, 540, cy_for(head_y(JS, 1640, .95), z, 730), z, rot=-4 * eout(k), amp=1, seed=18)
    fr.set_cam(cam)
    fr.fill_screen(FLASH((20, 30, 60)))
    JS.draw(fr, dict(x=540, y=1640, s=.95, hy=-.05), dict(glint=1.0, glint_col=(255, 255, 255)), FLASH, t)
    fr.set_cam(Cam())
    for (x, y, sx, sy) in ((120, 260, 1, 1), (960, 260, -1, 1), (120, 1640, 1, -1), (960, 1640, -1, -1)):
        fr.line([(x, y + sy * 90), (x, y), (x + sx * 90, y)], 6, (255, 255, 255))
    fr.poly([(360, 520), (720, 520), (720, 940), (360, 940)], None, 4, (255, 214, 0))
    fr.circ(540, 1790, 70, (255, 255, 255), 6, (200, 200, 200))
    fr.circ(540, 1790, 56, None, 4, (40, 40, 40))
    return dict(flash=fl * .8 if t < t_vsp + .3 else 0, vig=.7)


# ============================================================= SCENE 7
def s07(fr, t):
    t_vyb, t_ponesl = ws(7, 2), ws(7, 6)
    if t < t_ponesl - .1:
        k = seg(t, 25.9, t_ponesl)
        cam = hcam(t, lerp(700, 420, ease(k)), 1340, 0.8, amp=4, seed=19)
        base = Cam(560, 1340, 0.8)
        night_bg(fr, t, cam, base, gy=1560, seed=71, moon=(880, 260), moon_r=70)
        fr.set_cam(cam)
        door = eout(seg(t, t_vyb - .1, t_vyb + .05))
        cabin_at(fr, 140, 1640, 1.75, NIGHT, t, door_open=door, shutters=1.0)
        dx0 = 140 + CAB["door_x"] * 1.75
        dx1 = dx0 + CAB["door_w"] * 1.75
        JS.draw(fr, dict(x=1300, y=1760, s=.95, rh="machete", hx=-lerp(0, .7, seg(t, t_vyb + .3, t_vyb + .8)),
                         breath=math.sin(t * 2) * 3), dict(glint=1), NIGHT, t)
        r1 = seg(t, t_vyb, t_vyb + 1.0)
        if r1 > 0:
            x1 = lerp((dx0 + dx1) / 2, -80, eout(r1))
            F1.draw(fr, merge(run(F1, t, 2.6), dict(x=x1, y=lerp(1660, 1900, r1), s=lerp(.9, 1.05, r1), hx=-.3)),
                    dict(eyes="wide", mouth="scream", mo=.6, brow=7, sweat=1, pale=.2, look=(-1, 0)), NIGHT, t)
        r2 = seg(t, t_vyb + .45, t_vyb + 1.5)
        if r2 > 0:
            x2 = lerp((dx0 + dx1) / 2, 60, ease(r2))
            F2.draw(fr, merge(flail(F2, t, 2.2), dict(x=x2, y=lerp(1660, 1880, r2), s=lerp(.9, 1.05, r2), hx=-.2)),
                    dict(lid=.35, mouth="grin", mo=.4, smile=.8, eyes="happy"), NIGHT, t)
        return dict()
    return path_chase(fr, t)


def path_bg(fr, t, cam, chars, camz):
    pz = Persp(horizon=840, f=900, cam_h=420)
    fr.set_cam(Cam())
    sky(fr, SKY_NIGHT, t, moon=(820, 250), moon_r=62)
    fr.set_cam(cam)
    path_scene(fr, t, NIGHT, pz, camz, chars=chars)
    fr.set_cam(Cam())
    fog_screen(fr, 640, 1000, 50)
    fr.set_cam(cam)
    return pz


PZ = Persp(horizon=840, f=900, cam_h=420)


def path_chase(fr, t):
    cam = hcam(t, 540, 960, 1.0, amp=6, seed=20, shk=3)

    def dj(fr_, Z):
        x, y = PZ.p(-40, Z)
        JS.draw(fr_, merge(walk(JS, t, .9, .9), dict(x=x, y=y, s=PZ.s(Z), rh="machete")), dict(glint=1), FAR2, t)

    def d2(fr_, Z):
        x, y = PZ.p(120, Z)
        F2.draw(fr_, merge(flail(F2, t, 2.2), dict(x=x, y=y, s=PZ.s(Z))),
                dict(lid=.3, mouth="grin", mo=.4, smile=.8, eyes="happy"), NIGHT, t)

    def d1(fr_, Z):
        x, y = PZ.p(-110, Z)
        lookback = math.sin(t * 5) > .3
        F1.draw(fr_, merge(run(F1, t, 2.6), dict(x=x, y=y, s=PZ.s(Z), hx=-.9 if lookback else -.1)),
                dict(eyes="wide", mouth="scream", mo=.6, brow=7, sweat=1, look=(-1, 0) if lookback else (0, 0)), NIGHT, t)
    path_bg(fr, t, cam, [(3200, dj), (1150, d2), (780, d1)], t * 900)
    return dict()


# ============================================================= SCENE 8
def s08(fr, t):
    cam = hcam(t, 540, 960, 1.0, amp=8, seed=21, shk=4 + 6 * (env(t) if quote(t, 1) else 0))

    def dj(fr_, Z):
        x, y = PZ.p(60, Z)
        JS.draw(fr_, merge(walk(JS, t, .9, .9), dict(x=x, y=y, s=PZ.s(Z), rh="machete")), dict(glint=1), FAR2, t)
    path_bg(fr, t, cam, [(2900, dj)], t * 900)
    r = run(F1, t, 2.8)
    F = dict(eyes="wide", mouth="scream", mo=.5, brow=8, browa=-4, sweat=1, look=(0, 0))
    talk(F, t, 1, 1.2)
    point = ease(seg(t, ws(8, 3) - .1, ws(8, 3) + .15))
    yy = 680 - 2.6 * F1.anchor("head")[1]
    P = merge(r, dict(x=500, y=yy, s=2.6))
    if point > 0:
        P.update(ra=(lerp(r["ra"][0], 300, point), lerp(r["ra"][1], -720, point)), rh="point", rhr=lerp(0, -115, point))
    F1.draw(fr, P, F, NIGHT, t)
    return dict()


# ============================================================= SCENE 9
def s09(fr, t):
    t_ost, t_shn = ws(9, 3), ws(9, 4)
    stop = ease(seg(t, t_ost, t_ost + .25))
    camz = (min(t, t_ost) * 900) + (max(0, t - t_ost) * 900 * (1 - stop) * .3)
    if t < t_shn:
        cam = hcam(t, 540, 960, lerp(1.0, 1.12, stop), amp=5, seed=22, shk=3 * (1 - stop))

        def d2(fr_, Z):
            x, y = PZ.p(0, Z)
            if stop < 1:
                P = merge(flail(F2, t, 2.2), dict(x=x, y=y, s=PZ.s(Z)))
                F = dict(lid=.3, mouth="grin", mo=.4, smile=.8, eyes="happy")
            else:
                P = dict(x=x, y=y, s=PZ.s(Z), hy=.8, ht=4)
                F = dict(lid=.3, mouth="o", mo=.2, look=(0, 1))
            F2.draw(fr_, P, F, NIGHT, t)

        def dj(fr_, Z):
            x, y = PZ.p(80, Z)
            JS.draw(fr_, merge(walk(JS, t, .9, .9), dict(x=x, y=y, s=PZ.s(Z), rh="machete")), dict(glint=1), FAR2, t)
        path_bg(fr, t, cam, [(3600, dj), (900, d2)], camz)
        if t_ost < t < t_ost + .6:
            k = seg(t, t_ost, t_ost + .6)
            x, y = PZ.p(0, 900)
            for i in range(4):
                fr.dot(x + (i - 1.5) * 70 * (1 + 1.5 * k), y - 4 - k * 24, 18 * (1 + 2 * k), (140, 132, 124, int(70 * (1 - k))))
        return dict()
    # 9b-i: calmly tying the laces in the middle of the path, Jason coming up behind
    t_zav = ws(9, 5)
    loop = math.sin(t * 7)

    def squat(fr_, x, y, s):
        F2.draw(fr_, dict(x=x, y=y, s=s, hip=158, lf=(-62, 0), rf=(44, 0), lfore=False, rfore=False,
                          la=(28 + loop * 10, -150), ra=(62 - loop * 10, -156), hy=.75, ht=5),
                dict(lid=.3, mouth="o", mo=.12, look=(.3, 1), eo=1), NIGHT, t)
        ax, ay = x + s * 44, y - s * 24
        fr_.line([(ax, ay), (ax - 26 * s + loop * 9 * s, ay - 24 * s), (ax - 8 * s, ay - 36 * s)], 3 * s, (240, 240, 240))
        fr_.line([(ax, ay), (ax + 22 * s - loop * 9 * s, ay - 22 * s), (ax + 6 * s, ay - 34 * s)], 3 * s, (240, 240, 240))
    if t < t_zav:
        k = seg(t, t_shn, t_zav)
        cam = hcam(t, 540, 1150, lerp(1.0, 1.06, k), amp=3, seed=23)

        def d2(fr_, Z):
            x, y = PZ.p(-20, Z)
            squat(fr_, x, y, PZ.s(Z))

        def dj(fr_, Z):
            x, y = PZ.p(120, Z)
            JS.draw(fr_, merge(walk(JS, t, .9, .9), dict(x=x, y=y, s=PZ.s(Z), rh="machete")), dict(glint=1), NIGHT, t)
        path_bg(fr, t, cam, [(lerp(2300, 2050, k), dj), (560, d2)], camz)
        return dict()
    # 9b-ii: the scared friend turns back in total disbelief
    k = seg(t, t_zav, 33.35)
    cam = hcam(t, 540, 960, lerp(1.0, 1.05, k), amp=4, seed=23)

    def d2(fr_, Z):
        x, y = PZ.p(-120, Z)
        squat(fr_, x, y, PZ.s(Z))

    def dj(fr_, Z):
        x, y = PZ.p(40, Z)
        JS.draw(fr_, merge(walk(JS, t, .9, .9), dict(x=x, y=y, s=PZ.s(Z), rh="machete")), dict(glint=1), NIGHT, t)
    path_bg(fr, t, cam, [(lerp(2000, 1800, k), dj), (1250, d2)], camz)
    spread = eback(seg(t, t_zav, t_zav + .35))
    yy = 820 - 1.9 * F1.anchor("head")[1]
    F1.draw(fr, dict(x=850, y=yy, s=1.9, hx=-.85, la=(lerp(-80, -240, spread), lerp(-380, -640, spread)),
                     ra=(lerp(80, 250, spread), lerp(-380, -640, spread)), lh="open", rh="open",
                     lhr=lerp(0, 120, spread), rhr=lerp(0, -120, spread)),
            dict(eyes="normal", eo=1.15, mouth="o", mo=.5, brow=10, browa=-5, sweat=1, look=(-1, 0)), NIGHT, t)
    return dict()


# ============================================================= SCENES 10-14 (the big tree)
def tree_bg(fr, t, cam, base, Lf=NIGHT, moon=(240, 230), gy=1300):
    night_bg(fr, t, cam, base, gy=gy, seed=81, moon=moon, moon_r=58, fogA=35, Lf=Lf)
    fr.set_cam(cam)


def s10(fr, t):
    k = seg(t, 33.35, 35.05)
    z = lerp(1.08, 1.15, k)
    cam = hcam(t, lerp(640, 560, ease(k)), cy_for(head_y(F1, 1780), z, 820), z, amp=3, seed=24)
    base = Cam(560, 1300, 1.08)
    tree_bg(fr, t, cam, base)
    big_tree(fr, 560, 1760, NIGHT, w=560)
    peek = ease(seg(t, 33.9, 34.3)) * (1 - ease(seg(t, 34.7, 34.95)))
    F1.draw(fr, dict(x=440, y=1780, s=1.0, la=(-150, -470), ra=(150, -470), lh="open", rh="open", lhr=90, rhr=-90,
                     lean=-9 * peek, hx=-.9 * peek, hdx=-10 * peek),
            dict(eyes="wide", mouth="line", smile=-.3, sweat=1, look=(-1, 0) if peek > .3 else (0, 0), brow=5), NIGHT, t)
    F2.draw(fr, dict(x=700, y=1790, s=1.0, ra=at(F2, "chest", 40, 30), rh="phone", screen=.6, la=hang(F2, -1, 0, -10),
                     hy=.5, lean=3),
            dict(lid=.45, smile=.2, look=(.1, 1), eo=blink(t, 2.5)), NIGHT, t)
    fr.glow(*F2.wpt(700, 1790, 1.0, "chest", 1), 160, (150, 190, 255), .35)
    return dict()


def s11(fr, t):
    k = seg(t, 35.05, 36.65)
    z = lerp(1.12, 1.2, ease(k))
    cam = hcam(t, 560, cy_for(head_y(F1, 1780), z, 860), z, rot=lerp(0, -2.5, k), amp=2.5, seed=25)
    base = Cam(560, 1300, 1.08)
    tree_bg(fr, t, cam, base)
    jx = lerp(-160, 1260, k)
    JS.draw(fr, merge(walk(JS, t, .85, 1.0), dict(x=jx, y=1590, s=1.0, rh="machete", hx=.5, breath=math.sin(t * 2) * 4)),
            dict(glint=1), NIGHT, t)
    big_tree(fr, 560, 1760, NIGHT, w=560)
    F1.draw(fr, dict(x=440, y=1780, s=1.0, la=(-150, -470), ra=(150, -470), lh="open", rh="open", lhr=90, rhr=-90),
            dict(eyes="squeeze", puff=1.0, sweat=1, brow=4), NIGHT, t)
    F2.draw(fr, dict(x=700, y=1790, s=1.0, ra=at(F2, "chest", 40, 30), rh="phone", screen=.6, la=hang(F2, -1, 0, -10),
                     hy=.5), dict(lid=.45, smile=.2, look=(.1, 1), eo=blink(t, 2.5)), NIGHT, t)
    return dict(vig=1.15)


TS_Y1, TS_Y2, TS_S = 2200, 2210, 1.55     # two-shot at the tree


def two_cam(t, z, seed, shk=0.0, cx=560):
    return hcam(t, cx, cy_for(head_y(F1, TS_Y1, TS_S), z, 760), z, amp=2.5, seed=seed, shk=shk)


def two_bg(fr, t, cam, birds_t0=None):
    base = Cam(560, 1390, 1.05)
    tree_bg(fr, t, cam, base, moon=(160, 200), gy=1500)
    if birds_t0:
        birds(fr, t, birds_t0, 600, 1000)
    big_tree(fr, 560, 2300, NIGHT, w=1000, h=3000)


def s12(fr, t):
    t_gromko = ws(12, 5)
    t_choo = we(12, 6) + 0.30
    build = seg(t, ws(12, 3), t_choo - .05)
    after = seg(t, t_choo, t_choo + .5)
    snap = eout(seg(t, t_choo, t_choo + .08)) * (1 - ease(seg(t, t_choo + .25, t_choo + .7)))
    shk = 22 * (1 - seg(t, t_choo, t_choo + .5)) if t > t_choo else 0
    cam = two_cam(t, lerp(1.02, 1.1, seg(t, 36.65, t_choo)), 26, shk)
    if t < t_choo:
        f2f = dict(eyes="squeeze" if build > .55 else "normal", eo=lerp(1, .5, build), lid=lerp(.45, .7, build),
                   mouth="o", mo=build * .9, brow=lerp(0, 10, build), browa=lerp(0, -4, build))
        f2p = dict(ht=lerp(0, -10, build), hdy=lerp(0, -12, build), hy=-.3 * build, bob=math.sin(t * 30) * 2 * build)
    else:
        f2f = dict(eyes="squeeze", mouth="scream", mo=.9, brow=4)
        f2p = dict(ht=10 * snap, hdy=22 * snap, hy=.4 * snap)
    react = ease(seg(t, t_gromko - .1, t_gromko + .3))
    no = math.sin(t * 16) * .35 * react * (1 - after)
    f1f = dict(eyes="wide", mouth="o" if t < t_choo else "scream", mo=.5, brow=8, browa=-6, sweat=1, look=(1, 0),
               pale=.3 * react)
    f1p = dict(hx=.5 * react + no, la=hang(F1, -1, 0, -10), ra=(lerp(80, 170, react), lerp(-300, -560, react)),
               rh="open", rhr=lerp(0, -150, react), lean=-6 * after)
    fr.set_cam(cam)
    two_bg(fr, t, cam, birds_t0=t_choo)
    F1.draw(fr, merge(dict(x=360, y=TS_Y1, s=TS_S), f1p), f1f, NIGHT, t)
    F2.draw(fr, merge(dict(x=760, y=TS_Y2, s=TS_S), f2p), f2f, NIGHT, t)
    if t > t_choo:
        k = seg(t, t_choo, t_choo + .45)
        mx, my = F2.wpt(760, TS_Y2, TS_S, "mouth")
        rnd = random.Random(3)
        for i in range(26):
            a = rnd.uniform(-1.2, 1.2)
            sp = rnd.uniform(200, 520)
            fr.dot(mx + math.sin(a) * sp * k, my + 30 + math.cos(a) * sp * k * .35 - 40 * k,
                   rnd.uniform(4, 9) * (1 - k * .6), (200, 230, 255, int(220 * (1 - k))))
    return dict()


def s13(fr, t):
    t_zatk = ws(13, 3)
    if t < 40.95:
        clamp_ = eout(seg(t, 39.75, 39.95))
        punch = eout(seg(t, t_zatk, t_zatk + .15))
        cam = two_cam(t, 1.1 + .1 * punch, 27, 4 * punch * (1 - seg(t, t_zatk + .2, t_zatk + .5)))
        mouth = F2.wpt(760, TS_Y2, TS_S, "mouth")
        f1f = dict(mouth="teeth", browa=10, brow=-2, vein=1.0, look=(1, 0), eyes="normal", lid=.15)
        talk(f1f, t, 1)
        f1p = dict(hx=.6, raw=(lerp(560, mouth[0] + 10, clamp_), lerp(1750, mouth[1] + 40, clamp_)), rh="open",
                   rhr=-100, rlayer=2, la=hang(F1, -1, 0, -10), lean=4 * clamp_)
        f2f = dict(lid=.25, mouth="line", look=(-.6, 0), brow=4, eo=blink(t, 1.3))
        fr.set_cam(cam)
        two_bg(fr, t, cam)
        F2.draw(fr, dict(x=760, y=TS_Y2, s=TS_S), f2f, NIGHT, t)
        F1.draw(fr, merge(dict(x=360, y=TS_Y1, s=TS_S), f1p), f1f, NIGHT, t)
        return dict()
    k = seg(t, 40.95, 41.45)
    z = lerp(2.0, 2.15, k)
    cam = hcam(t, 520, cy_for(head_y(JS, 1560, .85), z, 760), z, amp=2, seed=28)
    base = Cam(520, 900, 1.6)
    night_bg(fr, t, cam, base, gy=1300, seed=91, moon=None, fogA=40)
    fr.set_cam(cam)
    JS.draw(fr, dict(x=540, y=1560, s=.85, rh="machete", hx=lerp(.8, -.1, ease(k)), breath=math.sin(t * 2) * 3),
            dict(glint=lerp(.4, 1.3, k), look=(lerp(1, -.4, k), 0)), NIGHT, t)
    return dict(vig=1.3)


def s14(fr, t):
    t_brat = ws(14, 4)
    k = seg(t, 41.45, 46.0)
    cam = two_cam(t, lerp(1.1, 1.22, ease(k)), 29)
    finger = eback(seg(t, t_brat - .2, t_brat + .2))
    f2f = dict(lid=.55, brow=-3, browa=6, mouth="line", look=(-.7, 0), eyes="normal")
    talk(f2f, t, 2, .9)
    f2p = dict(la=(lerp(-60, -40, finger), lerp(-420, -780, finger)), lh="point", lhr=180, llayer=2, hx=-.3, ht=-3)
    sink = ease(seg(t, 43.0, 45.4))
    twitch = 1.0 if (45.15 < t < 45.25 or 45.45 < t < 45.52) else 0.0
    f1f = dict(lid=lerp(.3, .62, sink) + twitch * .25, mouth="line", smile=-.2, browa=-2, look=(1, 0), bags=sink)
    f1p = dict(hx=.45, hip=60 * sink, la=hang(F1, -1, 0, -10), ra=hang(F1, 1, 0, -10))
    fr.set_cam(cam)
    two_bg(fr, t, cam)
    F1.draw(fr, merge(dict(x=360, y=TS_Y1, s=TS_S), f1p), f1f, NIGHT, t)
    F2.draw(fr, merge(dict(x=760, y=TS_Y2, s=TS_S), f2p), f2f, NIGHT, t)
    return dict()


# ============================================================= SCENE 15
J3 = (170, 1880, 1.08)      # Jason in the trio shots
F1X, F2X, TY1, TY2 = 580, 880, 1760, 1770


def s15(fr, t):
    t_i = ws(15, 1)
    if t < t_i + 0.62:
        k = seg(t, t_i, t_i + .62)
        z = lerp(5.2, 4.6, eout(k))
        cam = hcam(t, 540, cy_for(head_y(JS, 1640, .95), z, 820), z, amp=2, seed=30, shk=22 * (1 - k))
        fr.set_cam(Cam())
        fr.fill_screen((40, 6, 10))
        fr.set_cam(cam)
        JS.draw(fr, dict(x=540, y=1640, s=.95), dict(glint=1.4, glint_col=(255, 60, 50)), light((0.9, 0.62, 0.6), (40, 0, 0)), t)
        return dict(flash=.6 * (1 - seg(t, t_i, t_i + .12)), vig=1.5)
    k = seg(t, t_i + .62, 48.85)
    z = lerp(.98, 1.04, ease(k))
    cam = hcam(t, 560, cy_for(head_y(F1, TY1), z, 800), z, rot=-2.5, amp=3, seed=31)
    base = Cam(560, 1280, .98)
    tree_bg(fr, t, cam, base)
    big_tree(fr, 840, 1700, NIGHT, w=520)
    tremble = math.sin(t * 60) * 2.5
    F1.draw(fr, dict(x=F1X + tremble, y=TY1, s=1.0, hair_up=1, la=hang(F1, -1, 6, -4), ra=hang(F1, 1, -6, -4)),
            dict(eyes="wide", mouth="wavy", ps=.6, brow=10, browa=-4, sweat=1, pale=.7, look=(-1, -.3)), NIGHT, t)
    F2.draw(fr, dict(x=F2X, y=TY2, s=1.0, ra=hang(F2, 1, 0, -10), la=hang(F2, -1, 0, -10), hy=-.3),
            dict(lid=.45, smile=.3, look=(-1, -.6), eo=blink(t, 2.3)), NIGHT, t)
    JS.draw(fr, dict(x=J3[0], y=J3[1], s=J3[2], rh="machete", hx=.45, hy=.25, breath=math.sin(t * 2) * 4),
            dict(glint=1.0, look=(1, .5)), NIGHT, t)
    return dict()


# ============================================================= SCENES 16-17 (the photo request)
def frozen_f1(t, extra=None):
    tremble = math.sin(t * 60) * 2
    P = dict(x=F1X + tremble, y=TY1, s=1.0, hair_up=.8, la=hang(F1, -1, 6, -4), ra=hang(F1, 1, -6, -4))
    F = dict(eyes="wide", mouth="wavy", ps=.6, brow=9, browa=-4, sweat=1, pale=.6, look=(-1, -.3))
    if extra: F.update(extra)
    return P, F


def trio_bg(fr, t, cam):
    base = Cam(560, 1280, .98)
    tree_bg(fr, t, cam, base)
    big_tree(fr, 860, 1700, NIGHT, w=520)


def s16(fr, t):
    t_prot, t_tel, t_brat, t_tolko = ws(16, 4), ws(16, 6), ws(16, 7), ws(16, 10)
    if t < t_brat - .05:
        # the idiot strolls over to Jason, hands him the phone, strolls back
        k = seg(t, 48.85, t_brat)
        z = lerp(.98, 1.04, ease(k))
        cam = hcam(t, lerp(560, 500, k), cy_for(head_y(F1, TY1), z, 800), z, amp=3, seed=32)
        trio_bg(fr, t, cam)
        go = ease(seg(t, 48.95, t_prot - .1))
        back = ease(seg(t, t_tel + .45, t_brat - .1))
        x2 = lerp(F2X, 420, go) + (F2X - 420) * back
        y2 = TY2 + 40 * math.sin(math.pi * min(1, go + back))
        moving = (0 < go < 1) or (0 < back < 1)
        reach = ease(seg(t, t_prot - .1, t_prot + .35)) * (1 - ease(seg(t, t_tel + .3, t_tel + .5)))
        jchest = JS.wpt(*J3, "chest")
        handed = t > t_tel + .3
        p1, f1 = frozen_f1(t)
        f1["look"] = (lerp(-1, 1, back) if back > 0 else -1, -.3)
        F1.draw(fr, p1, f1, NIGHT, t)
        look_down = ease(seg(t, t_prot + .2, t_prot + .8))
        JS.draw(fr, dict(x=J3[0], y=J3[1], s=J3[2], rh="machete", breath=math.sin(t * 2) * 4,
                         hx=.45 + .1 * look_down, hy=.25 + .35 * look_down,
                         la=(-20, -560) if handed else None, lh="phoneb" if handed else "fist"),
                dict(glint=1, look=(1, .8)), NIGHT, t)
        P2 = merge(walk(F2, t, 1.5, .8) if moving else {}, dict(x=x2, y=y2, s=1.0, hx=-.4 if back == 0 else .3))
        if reach > .02:
            P2.update(law=(lerp(x2 - 60, jchest[0] + 150, reach), lerp(1400, jchest[1] + 40, reach)), lh="phone", llayer=1)
        elif not handed:
            P2.update(la=hang(F2, -1, 0, -60), lh="phone")
        F2.draw(fr, P2, dict(lid=.45, smile=.45, look=(-1 if back == 0 else 1, -.4), eo=blink(t, 2.3)), NIGHT, t)
        return dict()
    # Jason holds the phone; the idiot poses with his friend
    z = lerp(1.04, 1.1, seg(t, t_brat, 54.75))
    cam = hcam(t, 520, cy_for(head_y(F1, TY1), z, 800), z, amp=3, seed=33)
    trio_bg(fr, t, cam)
    gest = ease(seg(t, t_tolko, t_tolko + .3))
    jp = dict(x=J3[0], y=J3[1], s=J3[2], rh="machete", breath=math.sin(t * 2) * 4, hx=.15, hy=.3,
              la=(-20, -560), lh="phoneb", ht=lerp(0, 6, seg(t, t_tolko, 54.5)))
    JS.draw(fr, jp, dict(glint=1, look=(.6, .5)), NIGHT, t)
    p1, f1 = frozen_f1(t, dict(mouth="teeth", look=(-1, 0)))
    F1.draw(fr, p1, f1, NIGHT, t)
    f1_sh = F1.wpt(F1X, TY1, 1.0, "shoulder", -1)
    x2 = F2X - 70
    P2 = dict(x=x2, y=TY2, s=1.0, hx=-.25)
    if gest < .5:
        P2.update(law=(f1_sh[0] + 6, f1_sh[1] + 4), lh="open", llayer=2, ra=at(F2, "head", 95, -10), rh="peace", rhr=180)
    else:
        P2.update(la=(-110, -440), ra=(110, -440), lh="point", rh="point", lhr=-90, rhr=90)
    f2f = dict(eyes="happy" if gest < .5 else "normal", lid=.2, mouth="grin", mo=.35, smile=.9, look=(-.8, -.2))
    talk(f2f, t, 2)
    F2.draw(fr, P2, f2f, NIGHT, t)
    if t > t_tolko:
        rot_icon(fr, F2.wpt(x2, TY2, 1.0, "head")[0] + 40, F2.wpt(x2, TY2, 1.0, "head")[1] - 230,
                 seg(t, t_tolko + .05, t_tolko + .2), ease(seg(t, ws(16, 11), ws(16, 11) + .5)))
    return dict()


def rot_icon(fr, cx, cy, appear, turn):
    """the familiar 'rotate your phone' pictogram"""
    if appear <= 0: return
    s = eback(appear) * 1.0
    ang = -90 * turn
    def R(pts):
        c, si = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        return [(cx + (x * c - y * si) * s, cy + (x * si + y * c) * s) for x, y in pts]
    fr.poly(R([(-40, -70), (40, -70), (40, 70), (-40, 70)]), (245, 245, 245), 6)
    fr.poly(R([(-30, -54), (30, -54), (30, 50), (-30, 50)]), (120, 170, 230), 3)
    fr.dot(*R([(0, 61)])[0], 5 * s, INK)
    arc = [(cx + math.cos(math.radians(a)) * 105 * s, cy + math.sin(math.radians(a)) * 105 * s) for a in range(-150, -40, 8)]
    fr.line(arc, 14, INK)
    fr.line(arc, 7, YEL)
    ex, ey = arc[-1]
    fr.poly([(ex + 18 * s, ey - 4 * s), (ex - 10 * s, ey - 22 * s), (ex - 4 * s, ey + 16 * s)], YEL, 4)


def s17(fr, t):
    t_i = ws(17, 4)
    t_end = we(17, 9)
    if t < t_end + .1:
        k = seg(t, 54.75, t_end)
        z = lerp(1.12, 1.3, ease(k))
        cam = hcam(t, lerp(560, 600, k), cy_for(head_y(F1, TY1), z, 820), z, amp=2.5, seed=34)
        trio_bg(fr, t, cam)
        tilt = ease(seg(t, ws(17, 2), ws(17, 3) + .3))
        JS.draw(fr, dict(x=J3[0], y=J3[1], s=J3[2], rh="machete", breath=math.sin(t * 2) * 4, hx=.3, hy=.2,
                         la=(-20, -560), lh="phoneb"), dict(glint=1, look=(1, .5)), NIGHT, t)
        gaze = ease(seg(t, t_i - .3, t_end - .3))
        p1, f1 = frozen_f1(t, dict(look=(lerp(-1, 1, gaze), 0), mouth="line", smile=-.2, lid=.25, eyes="normal", pale=.4,
                                   brow=2))
        p1["hx"] = lerp(-.4, .45, gaze)
        F1.draw(fr, p1, f1, NIGHT, t)
        f2f = dict(lid=.05, brow=7, browa=-7, mouth="line", smile=-.1, look=(-1, -.5), eo=1.05)
        talk(f2f, t, 2)
        F2.draw(fr, dict(x=F2X, y=TY2, s=1.0, ht=13 * tilt, hx=-.35, ra=at(F2, "chest", 20, 10), rh="open", rhr=160,
                         la=hang(F2, -1, 0, -10)), f2f, NIGHT, t)
        return dict()
    k = seg(t, t_end + .1, 59.5)
    z = lerp(3.0, 3.5, ease(k))
    cam = hcam(t, 540, cy_for(head_y(JS, 1640, .95), z, 760), z, amp=1.2, seed=35)
    closeup_bg(fr, t, cam, seed=95)
    JS.draw(fr, dict(x=540, y=1640, s=.95, hy=.05, breath=math.sin(t * 2) * 3),
            dict(glint=.8 + .4 * math.sin(t * 3)), NIGHT, t)
    return dict(vig=1.35)


# ============================================================= SCENE 18
def s18(fr, t):
    k = seg(t, 59.5, DUR)
    z = lerp(1.04, 1.22, ease(k))
    cam = hcam(t, lerp(540, 470, ease(k)), lerp(940, 860, ease(k)), z, amp=1.5, seed=36)
    base = Cam(540, 960, 1.0)
    flashes = [61.3, 65.25]          # 2nd selfie flash closes the film (keeps the punchline clean)
    fl = max([max(0.0, 1 - (t - f) / 0.2) if t >= f else 0.0 for f in flashes] + [0.0])
    Lx = light_mix(NIGHT, FLASH, fl * .6)
    night_bg(fr, t, cam, base, gy=1150, seed=97, moon=(860, 210), moon_r=50, fogA=30, Lf=Lx)
    fr.set_cam(cam)
    # background: the idiot takes a selfie with Jason
    JS.draw(fr, dict(x=840, y=1230, s=.62, rh="machete", hx=-.1, breath=math.sin(t * 2) * 2), dict(glint=1), Lx, t)
    F2.draw(fr, dict(x=660, y=1240, s=.62, ra=(130, -800), rh="phoneb", flash=fl, la=at(F2, "head", -80, -30), lh="peace",
                     lhr=180, llayer=2, ht=10, hx=.3),
            dict(eyes="happy", mouth="grin", mo=.4, smile=1), Lx, t)
    fog(fr, 1240, 140, 50, t=t)
    # foreground: the doomed stare into the camera
    tw = 1.0 if (62.0 < t < 62.08) else 0.0
    yy = 640 - 2.0 * F1.anchor("head")[1]
    F1.draw(fr, dict(x=320, y=yy, s=2.0, ht=-2),
            dict(lid=.55 + tw * .3, bags=1.0, mouth="line", smile=-.25, browa=-3, brow=-1, look=(.05, 0),
                 eo=blink(t, 3.4, 1.0)), Lx, t)
    return dict(title=True)


SCENES = [(0.0, s01), (2.35, s02), (6.62, s03), (9.6, s04), (13.3, s05), (20.05, s06), (25.9, s07), (28.85, s08),
          (30.9, s09), (33.35, s10), (35.05, s11), (36.65, s12), (39.7, s13), (41.45, s14), (46.0, s15), (48.85, s16),
          (54.75, s17), (59.5, s18)]
