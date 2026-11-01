#!/usr/bin/env python3
"""S01 v9c - robust per-frame camera transforms.
red scene: translation via matchTemplate of a textured plate patch (bars).
jen scene: similarity (zoom+shift) from the static '2008' digit track (push-in camera).
other scenes: identity (smooth gradient fields carry no visible shake).
Writes /tmp/v9/aff2.npz  (n, 2x3 matrix flattened).
"""
import numpy as np, cv2

OUT = '/tmp/v9'
def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))
def G(n):
    return cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY)

# ---- red plate rebuild with matchTemplate alignment ----
base = G(98)
P0 = base[300:556, 60:316]  # textured bars patch
acc = []
for n in range(98, 177, 3):
    g = G(n)
    r = cv2.matchTemplate(g, P0, cv2.TM_CCOEFF_NORMED)
    _, _, _, mx = cv2.minMaxLoc(r)
    acc.append(cv2.warpAffine(F(n), np.float32([[1, 0, -mx[0]], [0, 1, -mx[1]]]), (720, 1280)))
red_plate = np.median(np.stack(acc), 0).astype(np.uint8)
cv2.imwrite(f'{OUT}/plates/red.png', red_plate)
print('red plate rebuilt')

aff = {}
for n in range(0, 698):
    aff[n] = np.eye(2, 3, dtype=np.float32)

# red translations
rp = cv2.cvtColor(red_plate, cv2.COLOR_BGR2GRAY)
P1 = rp[300:556, 60:316]
for n in range(98, 177):
    g = G(n)
    r = cv2.matchTemplate(g, P1, cv2.TM_CCOEFF_NORMED)
    _, _, _, mx = cv2.minMaxLoc(r)
    aff[n] = np.float32([[1, 0, mx[0] - 60], [0, 1, mx[1] - 300]])

# ---- jen: track 2008 digits ----
def eoc(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

rows = []
for n in range(177, 270):
    f = F(n)
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    m = ((g > 90)).astype(np.uint8)
    W = np.zeros_like(m); W[60:320, 60:660] = 1
    m *= W
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(m)
    if len(xs) < 200:
        rows.append((n, 0, 0, 0, 0, 0)); continue
    rows.append((n, 1, xs.mean(), ys.mean(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
rows = np.array(rows, np.float32)
vis = rows[rows[:, 1] == 1]
refrow = vis[-1]  # settled at end of jen scene
z_smooth = 1.0
for r in rows:
    n = int(r[0])
    if r[1] == 1:
        z = r[5] / refrow[5]
        z = min(1.6, max(0.6, z))
        cx, cy = r[2], r[3]
        rcx, rcy = refrow[2], refrow[3]
        # scale z about settled center then shift by center delta
        tx = cx - z * rcx
        ty = cy - z * rcy
        aff[n] = np.float32([[z, 0, tx], [0, z, ty]])
    else:
        aff[n] = aff[n - 1] if n > 177 else np.eye(2, 3, dtype=np.float32)
# smooth jen transforms
ks = np.array([aff[n] for n in range(177, 270)])
kf = np.copy(ks)
for i in range(2, len(ks) - 2):
    kf[i] = ks[i - 2:i + 3].mean(0)
for i, n in enumerate(range(177, 270)):
    aff[n] = kf[i]
# make jen transforms RELATIVE to plate frame 178
z0, tx0, ty0 = aff[178][0, 0], aff[178][0, 2], aff[178][1, 2]
for n in range(177, 270):
    z, tx, ty = aff[n][0, 0], aff[n][0, 2], aff[n][1, 2]
    zr = z / z0
    aff[n] = np.float32([[zr, 0, tx - zr * tx0], [0, zr, ty - zr * ty0]])
print('jen similarity from 2008 track, visible', len(vis))

ns = np.array(sorted(aff))
np.savez(f'{OUT}/aff2.npz', n=ns, a=np.stack([aff[n] for n in ns]).reshape(len(ns), 6))
print('aff2 done')
