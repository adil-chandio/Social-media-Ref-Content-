#!/usr/bin/env python3
"""S01 v9e - perfect background fields without inpaint smear.
smooth scenes (stamp/green/white/desat/teal/jen): per-channel deg-3 polynomial surface
  fitted over pixels OUTSIDE the union element mask  => clean gradient field.
red scene: clean mosaic - per pixel take first unmasked frame (scene static after hit).
black: constant. graded: unused (footage layer).
"""
import numpy as np, cv2, glob, os
from collections import defaultdict

OUT = '/tmp/v9'
def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))

SCENES = [('stamp', 0, 13), ('black', 13, 18), ('green', 18, 41), ('white', 41, 57),
          ('desat', 57, 90), ('teal', 90, 98), ('red', 98, 177), ('jen', 177, 270),
          ('graded', 270, 698)]
scene_of = {}
for name, n0, n1 in SCENES:
    for n in range(n0, n1):
        scene_of[n] = name

per_frame = defaultdict(list)
for mp in glob.glob(OUT + '/masks/*_????.png'):
    base = os.path.basename(mp)[:-4]
    key, n = base.rsplit('_', 1)
    per_frame[int(n)].append(key)

union = {name: np.zeros((1280, 720), np.uint8) for name, _, _ in SCENES}
for n, keys in per_frame.items():
    sc = scene_of.get(n)
    if not sc:
        continue
    for k in keys:
        m = cv2.imread(f'{OUT}/masks/{k}_{n:04d}.png', 0)
        union[sc] = np.maximum(union[sc], m)
for name in union:
    union[name] = cv2.dilate((union[name] > 40).astype(np.uint8), np.ones((15, 15), np.uint8))

yy, xx = np.mgrid[0:1280, 0:720].astype(np.float32)
xn, yn = xx / 720.0, yy / 1280.0
terms = [np.ones_like(xn), xn, yn, xn * xn, xn * yn, yn * yn, xn ** 3, yn ** 3, xn * xn * yn, xn * yn * yn]
TM = np.stack([t.ravel() for t in terms], 1)

def poly_field(scene):
    keep = (union[scene] == 0).ravel()
    f = F(SCENES[[s[0] for s in SCENES].index(scene)][1] + 2)
    out = np.zeros((1280, 720, 3), np.uint8)
    A = TM[keep]
    for c in range(3):
        b = f[..., c].ravel()[keep].astype(np.float64)
        coef, *_ = np.linalg.lstsq(A, b, rcond=None)
        out[..., c] = (TM @ coef).reshape(1280, 720).clip(0, 255).astype(np.uint8)
    return out

for sc in ('stamp', 'green', 'white', 'desat', 'teal', 'jen'):
    fld = poly_field(sc)
    cv2.imwrite(f'{OUT}/plates/field_{sc}.png', fld)
    print('poly field', sc)

# red mosaic
red = np.zeros((1280, 720, 3), np.uint8)
done = np.zeros((1280, 720), bool)
for n in list(range(107, 177, 1)):
    f = F(n)
    m = union['red']
    for k in per_frame.get(n, []):
        mk = cv2.imread(f'{OUT}/masks/{k}_{n:04d}.png', 0)
        m = np.maximum(m, cv2.dilate((mk > 30).astype(np.uint8), np.ones((13, 13), np.uint8)))
    sel = (m == 0) & ~done
    red[sel] = f[sel]
    done |= sel
    if done.all():
        break
if not done.all():
    red = cv2.inpaint(red, (~done).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
    print('red mosaic holes filled', int((~done).sum()))
cv2.imwrite(f'{OUT}/plates/field_red.png', red)
print('red mosaic done, coverage', round(float(done.mean()), 4))
print('PRECOMPUTE v9e DONE')
