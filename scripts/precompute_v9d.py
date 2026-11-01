#!/usr/bin/env python3
"""S01 v9d - pure-field plates + robust transforms.
1. union of all element masks per scene -> inpaint over median plate => field-only plate
   (no static element baked in => zero double-draw ghosts).
2. red: median rebuilt with matchTemplate alignment on a cash-free bars patch;
   per-frame translation from same patch on the clean field plate.
3. jen: '2008' digits tracked (generous window) -> similarity zoom of dark field plate.
4. aff3.npz: identity | red translation | jen similarity.
"""
import numpy as np, cv2, glob, os
from collections import defaultdict

OUT = '/tmp/v9'
def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))
def G(n):
    return cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY)

SCENES = [('stamp', 0, 13), ('black', 13, 18), ('green', 18, 41), ('white', 41, 57),
          ('desat', 57, 90), ('teal', 90, 98), ('red', 98, 177), ('jen', 177, 270),
          ('graded', 270, 698)]

per_frame = defaultdict(list)
for mp in glob.glob(OUT + '/masks/*_????.png'):
    base = os.path.basename(mp)[:-4]
    key, n = base.rsplit('_', 1)
    per_frame[int(n)].append(key)

# ---------- 1. union masks per scene, inpaint -> field plates ----------
scene_of = {}
for name, n0, n1 in SCENES:
    for n in range(n0, n1):
        scene_of[n] = name
union = {name: np.zeros((1280, 720), np.uint8) for name, _, _ in SCENES}
for n, keys in per_frame.items():
    sc = scene_of.get(n)
    if not sc:
        continue
    for k in keys:
        m = cv2.imread(f'{OUT}/masks/{k}_{n:04d}.png', 0)
        union[sc] = np.maximum(union[sc], m)
for name, _, _ in SCENES:
    union[name] = (union[name] > 40).astype(np.uint8)
    union[name] = cv2.dilate(union[name], np.ones((11, 11), np.uint8))

for name in ('stamp', 'green', 'white', 'desat', 'teal'):
    pl = cv2.imread(f'{OUT}/plates/{name}.png')
    fld = cv2.inpaint(pl, union[name] * 255, 12, cv2.INPAINT_TELEA)
    cv2.imwrite(f'{OUT}/plates/field_{name}.png', fld)
    print('field', name)

# ---------- 2. red field + translations ----------
x0, y0, x1, y1 = 40, 100, 296, 340
base = G(98)
P0 = base[y0:y1, x0:x1]
acc = []
for n in range(98, 177, 2):
    r = cv2.matchTemplate(G(n), P0, cv2.TM_CCOEFF_NORMED)
    _, _, _, mx = cv2.minMaxLoc(r)
    acc.append(cv2.warpAffine(F(n), np.float32([[1, 0, -mx[0]], [0, 1, -mx[1]]]), (720, 1280)))
redmed = np.median(np.stack(acc), 0).astype(np.uint8)
redfield = cv2.inpaint(redmed, union['red'] * 255, 12, cv2.INPAINT_TELEA)
cv2.imwrite(f'{OUT}/plates/field_red.png', redfield)
print('field red')

aff = {n: np.eye(2, 3, dtype=np.float32) for n in range(698)}
P1 = cv2.cvtColor(redfield, cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1]
for n in range(98, 177):
    r = cv2.matchTemplate(G(n), P1, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, mx = cv2.minMaxLoc(r)
    if maxv > 0.4:
        aff[n] = np.float32([[1, 0, mx[0] - x0], [0, 1, mx[1] - y0]])
    else:
        aff[n] = aff[n - 1]
red_tr = [(int(n), float(aff[n][0, 2]), float(aff[n][1, 2])) for n in range(98, 177, 10)]
print('red translations sample', red_tr[:6])

# ---------- 3. jen 2008 track + masks + similarity ----------
K3 = np.ones((3, 3), np.uint8)
rows = []
for n in range(177, 270):
    f = F(n)
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    m = (g > 90).astype(np.uint8)
    W = np.zeros_like(m); W[20:400, 40:680] = 1
    m *= W
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, K3)
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    ys, xs = np.nonzero(m)
    if len(xs) < 300:
        rows.append((n, 0, 0, 0, 0, 0)); continue
    mf = cv2.GaussianBlur((m * 255).astype(np.uint8), (9, 9), 0)
    cv2.imwrite(f'{OUT}/masks/y2008@jen_{n:04d}.png', mf)
    rows.append((n, 1, xs.mean(), ys.mean(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
rows = np.array(rows, np.float32)
vis = rows[rows[:, 1] == 1]
ref = vis[-1]
for r in rows:
    n = int(r[0])
    if r[1] == 1:
        z = min(1.5, max(0.6, r[5] / ref[5]))
        tx = r[2] - z * ref[2]
        ty = r[3] - z * ref[3]
        aff[n] = np.float32([[z, 0, tx], [0, z, ty]])
    else:
        aff[n] = aff[n - 1]
ks = np.stack([aff[n] for n in range(177, 270)])
kf = np.copy(ks)
for i in range(2, len(ks) - 2):
    kf[i] = ks[i - 2:i + 3].mean(0)
z0, tx0, ty0 = kf[178 - 177][0, 0], kf[178 - 177][0, 2], kf[178 - 177][1, 2]
for i, n in enumerate(range(177, 270)):
    z, tx, ty = kf[i][0, 0], kf[i][0, 2], kf[i][1, 2]
    zr = z / z0
    aff[n] = np.float32([[zr, 0, tx - zr * tx0], [0, zr, ty - zr * ty0]])
# jen field plate: inpaint 2008+jen+sub from f178
pl = F(178)
u = union['jen'].copy()
m178 = cv2.imread(f'{OUT}/masks/y2008@jen_0178.png', 0)
if m178 is not None:
    u = np.maximum(u, (m178 > 40).astype(np.uint8))
u = cv2.dilate(u, np.ones((11, 11), np.uint8))
cv2.imwrite(f'{OUT}/plates/field_jen.png', cv2.inpaint(pl, u * 255, 12, cv2.INPAINT_TELEA))
print('field jen, 2008 visible frames', len(vis))

ns = np.array(sorted(aff))
np.savez(f'{OUT}/aff3.npz', n=ns, a=np.stack([aff[n] for n in ns]).reshape(len(ns), 6))
print('PRECOMPUTE v9d DONE')
