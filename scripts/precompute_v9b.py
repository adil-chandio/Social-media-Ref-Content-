#!/usr/bin/env python3
"""S01 v9b - layered decomposition precompute (patch-layer variant).
For every (element, scene) pair: per-frame feathered alpha mask (diff vs median plate
inside a generous window) saved as PNG, plus bbox track. Renderer composites
plate(ECC-warped) + patch pixels of ref frame n => reconstruction == reference at 30fps,
built from independent layers (foundation for S02+ persona swaps).
"""
import numpy as np, cv2, os

RF = '/tmp/rf/%04d.png'
OUT = '/tmp/v9'
os.makedirs(OUT + '/masks', exist_ok=True)

def F(n):
    return cv2.imread(RF % (n + 1))

def G(n):
    return cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY)

SCENES = [
    ('stamp', 0, 13, 6), ('black', 13, 18, 13), ('green', 18, 41, 19),
    ('white', 41, 57, 42), ('desat', 57, 90, 60), ('teal', 90, 98, 90),
    ('red', 98, 177, 98), ('jen', 177, 270, 178), ('graded', 270, 698, 400),
]
SC = {s[0]: s for s in SCENES}

# ---------- plates (reuse from v9 run if present, else median) ----------
def median_plate(n0, n1, pn):
    idx = list(range(n0, n1, 3))
    base = G(n0)
    acc = []
    for n in idx:
        W = np.eye(2, 3, dtype=np.float32)
        try:
            cv2.findTransformECC(base, G(n), W, cv2.MOTION_TRANSLATION,
                                 (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 1e-4))
        except cv2.error:
            pass
        acc.append(cv2.warpAffine(F(n), W, (720, 1280)))
    return np.median(np.stack(acc), 0).astype(np.uint8)

plates = {}
for name, n0, n1, pn in SCENES:
    pf = f'{OUT}/plates/{name}.png'
    if os.path.exists(pf):
        plates[name] = cv2.imread(pf)
    elif name == 'black':
        plates[name] = np.full((1280, 720, 3), 8, np.uint8)
    elif name == 'jen':
        plates[name] = F(178)
    elif name == 'graded':
        plates[name] = F(400)
    else:
        plates[name] = median_plate(n0, n1, pn)
        cv2.imwrite(pf, plates[name])
    print('plate', name)

# ---------- per-frame affine vs plate ----------
aff = {}
for name, n0, n1, pn in SCENES:
    pg = cv2.cvtColor(plates[name], cv2.COLOR_BGR2GRAY)
    for n in range(n0, n1):
        W = np.eye(2, 3, dtype=np.float32)
        try:
            mode = cv2.MOTION_AFFINE if name == 'jen' else cv2.MOTION_TRANSLATION
            cv2.findTransformECC(pg, G(n), W, mode,
                                 (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 1e-4))
        except cv2.error:
            pass
        aff[n] = W
ns = np.array(sorted(aff))
np.savez(f'{OUT}/aff.npz', n=ns, a=np.stack([aff[n] for n in ns]).reshape(len(ns), 6))
print('aff done', len(ns))

# ---------- element windows (ref px): name -> (scene, window fn, tau, mode) ----------
CX = 360
def clamp01(x):
    return min(1.0, max(0.0, x))
def eoc(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)

def w_stamp(n):  return (CX, 300, 260, 110)
def w_black(n):  return (CX, 420, 320, 260)
def w_bill(n):
    t = (n / 30.0) % 11.67
    k = eoc((t - .75) / .25)
    return (CX + 40, 330 + 160 * (1 - k), 240, 70)
def w_tag(n):
    t = (n / 30.0) % 11.67
    if t < 1.35:
        return (185, 260, 70, 130)
    return (288, 166, 70, 130)
def w_bag(n):
    t = (n / 30.0) % 11.67
    if t < 1.35:
        ry = 1680 - (1680 - 360) * eoc((t - .9) / .5)
        return (CX, ry, 220, 260)
    by = 360 + 400 * eoc((t - 1.35) / .25) + 60 * (1 - eoc((t - 1.55) / .18))
    return (CX, by, 220, 260)
def w_stool(n):  return (CX, 1060, 260, 120)
def w_smoke(n):  return (CX, 560, 360, 300)
def w_he(n):     return (158, 295, 110, 60)
def w_said(n):   return (245, 295, 110, 60)
def w_no(n):     return (209, 410, 140, 70)
def w_cash(n):
    t = (n / 30.0) % 11.67
    ck = eoc((t - 3.25) / .40)
    return ((1080 - (1080 - 432) * ck) / 1.5, (500 + 255 * ck) / 1.5, 190, 120)
def w_glove(n):
    t = (n / 30.0) % 11.67
    hk = eoc((t - 3.40) / .35)
    return ((-260 + (145 * 1.5 + 260) * hk) / 1.5, 770, 150, 140)
def w_logo(n):   return (164, 636, 110, 80)
def w_jen(n):
    t = n / 30.0
    rk = eoc((t - 6.0) / .5)
    return (CX, 830 + (1 - rk) * 120, 300, 400)
def w_sub(n):    return (CX, 1030, 190, 80)
def w_glow(n):   return (CX, 330, 150, 60)

ELEMS = [
    ('stamp', 'stamp', w_stamp, 12),
    ('btext', 'black', w_black, 18),
    ('bill',  'green', w_bill, 40),
    ('tag',   'green', w_tag, 40),
    ('bag',   'green', w_bag, 18),
    ('smoke', 'white', w_smoke, 10),
    ('stool', 'white', w_stool, 26),
    ('bagw',  'white', w_bag, 22),
    ('tagw',  'white', w_tag, 40),
    ('billw', 'white', w_bill, 40),
    ('smoked', 'desat', w_smoke, 8),
    ('stool', 'desat', w_stool, 26),
    ('bag',   'desat', w_bag, 22),
    ('he',    'desat', w_he, 22),
    ('said',  'desat', w_said, 22),
    ('no',    'desat', w_no, 22),
    ('logo',  'red', w_logo, 26),
    ('glove', 'red', w_glove, 26),
    ('cash',  'red', w_cash, 26),
    ('jen',   'jen', w_jen, 22),
    ('sub',   'jen', w_sub, 26),
    ('glow',  'graded', w_glow, 14),
]

K = np.ones((3, 3), np.uint8)
tracks = {}
for name, scene, win, tau in ELEMS:
    key = f'{name}@{scene}'
    n0, n1 = SC[scene][1], SC[scene][2]
    plate = plates[scene]
    rows = []
    for n in range(n0, n1):
        f = F(n)
        bg = cv2.warpAffine(plate, aff[n], (720, 1280))
        d = np.abs(f.astype(np.int16) - bg.astype(np.int16)).max(2)
        m = (d > tau).astype(np.uint8)
        cx, cy, hw, hh = win(n)
        W = np.zeros_like(m)
        x0, x1 = max(0, int(cx - hw - 60)), min(720, int(cx + hw + 60))
        y0, y1 = max(0, int(cy - hh - 60)), min(1280, int(cy + hh + 60))
        W[y0:y1, x0:x1] = 1
        m *= W
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, K)
        dk = 15 if name in ('smoke', 'smoked', 'stamp', 'glow') else 9
        m = cv2.dilate(m, np.ones((dk, dk), np.uint8))
        ys, xs = np.nonzero(m)
        if len(xs) < 30:
            rows.append((n, 0, 0, 0, 0, 0))
            continue
        mf = cv2.GaussianBlur((m * 255).astype(np.uint8), (9, 9), 0)
        cv2.imwrite(f'{OUT}/masks/{key}_{n:04d}.png', mf)
        rows.append((n, 1, xs.mean(), ys.mean(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
    tracks[key] = np.array(rows, np.float32)
    v = sum(1 for r in rows if r[1])
    print('track', key, v, '/', len(rows))

np.savez(f'{OUT}/tracks9.npz', **tracks)
print('PRECOMPUTE v9b DONE')
