# Dev tool: character model sheet (python sheet.py out.png)
import sys
from gfx import *
from chars import SCARED, IDIOT, JASON

fr = Frame((70, 80, 100))
fr.vgrad([(0, (60, 70, 96)), (1, (120, 130, 150))])
fr.set_cam(Cam(cx=540, cy=600, zoom=0.82))
fr.line([(-400, 1050), (1500, 1050)], 3)
SCARED.draw(fr, dict(x=170, y=1050, s=1.0), dict())
IDIOT.draw(fr, dict(x=430, y=1050, s=1.0, rh="phone", la=(-60, -330), lh="can"), dict(mouth="grin", mo=0.3, smile=0.6))
JASON.draw(fr, dict(x=820, y=1050, s=1.0, rh="machete", hy=0.1), dict(glint=1.0))

# expression rows (heads only, big)
exprs = [
    (SCARED, dict(eyes="wide", mouth="scream", mo=0.8, brow=8, browa=-6, sweat=1.0, pale=0.4), dict(hair_up=1)),
    (SCARED, dict(mouth="teeth", browa=10, vein=1.0, look=(0.6, 0)), dict()),
    (SCARED, dict(lid=0.5, bags=1.0, mouth="line", smile=-0.3, browa=-3), dict()),
    (SCARED, dict(mouth="talk", mo=0.6, browa=-5, brow=5, look=(-0.5, 0)), dict(hx=-0.5, ra=(10, -600), rh="shush", rlayer=2)),
    (IDIOT, dict(mouth="grin", mo=0.5, smile=0.7, eyes="happy"), dict()),
    (IDIOT, dict(eyes="squeeze", mouth="o", mo=0.6), dict(ht=-8)),
    (IDIOT, dict(lid=0.55, mouth="talk", mo=0.5, smile=0.1, browa=4, look=(0.3, 0)), dict()),
    (IDIOT, dict(mouth="shout", mo=0.9, smile=0.4, eo=1.0, lid=0.1, brow=6), dict()),
]
fr.set_cam(Cam(cx=540, cy=1500, zoom=1.0))
for i, (ch, f, extra) in enumerate(exprs):
    x = 90 + (i % 4) * 300
    y = 1330 + (i // 4) * 330
    hc = -ch.hip_h - ch.torso_h - ch.neck_h - ch.head_c
    ch.draw(fr, dict(x=x, y=y - hc * 1.6, s=1.6, **extra), f, t=0.3)
out = fr.finish()
out.save(sys.argv[1] if len(sys.argv) > 1 else "sheet.png")
print("ok")
