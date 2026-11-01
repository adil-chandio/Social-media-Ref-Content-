#!/usr/bin/env python3
"""S01 v9 - layer decomposition precompute.
Decomposes the reference into: per-scene clean background plates, per-frame global
camera transform (ECC affine), per-element per-frame tracks (bbox center/size/rot),
alpha sprites (sharp, from settled frames) and per-frame feather masks for patch layers.
Outputs: /tmp/v9/plates/*.png, /tmp/v9/sprites/*.png, /tmp/v9/masks/*.png, /tmp/v9/tracks.npz
"""
import numpy as np, cv2, os, json
from PIL import Image

RF = '/tmp/rf/%04d.png'
OUT = '/tmp/v9'
os.makedirs(OUT + '/plates', exist_ok=True)
os.makedirs(OUT + '/sprites', exist_ok=True)
os.makedirs(OUT + '/masks', exist_ok=True)

def F(n):  # frame n (0-based) as BGR uint8
    return cv2.imread(RF % (n + 1))

GRAY = {}
def G(n):
    if n not in GRAY:
        GRAY[n] = cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY)
    return GRAY[n]

# ---------------- scenes: (name, n0, n1, plate_frame) ----------------
SCENES = [
    ('stamp', 0, 13, 6),
    ('black', 13, 18, 13),
    ('green', 18, 41, 19),
    ('white', 41, 57, 42),
    ('desat', 57, 90, 60),
    ('teal', 90, 98, 90),
    ('red', 98, 177, 98),
    ('jen', 177, 270, 178),
    ('graded', 270, 698, 400),
]

def inpaint_plate(n, mask):
    f = F(n)
    m = (mask * 255).astype(np.uint8)
    m = cv2.dilate(m, np.ones((15, 15), np.uint8))
    pl = cv2.inpaint(f, m, 9, cv2.INPAINT_TELEA)
    return pl

def median_plate(name, n0, n1, pn):
    idx = list(range(n0, n1, 3))
    base = G(n0)
    acc = []
    for n in idx:
        W = np.eye(2, 3, dtype=np.float32)
        try:
            cv2.findTransformECC(base, G(n), W, cv2.MOTION_TRANSLATION,
                                 (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 1e-4))
        except cv2.error:
            W = np.eye(2, 3, dtype=np.float32)
        acc.append(cv2.warpAffine(F(n), W, (720, 1280)))
    acc = np.stack(acc)
    return np.median(acc, 0).astype(np.uint8)

plates = {}
for name, n0, n1, pn in SCENES:
    if name == 'black':
        plates[name] = np.full((1280, 720, 3), 8, np.uint8)
    elif name == 'graded':
        plates[name] = F(pn)
    elif name == 'jen':
        plates[name] = F(178)
    else:
        plates[name] = median_plate(name, n0, n1, pn)
    cv2.imwrite(f'{OUT}/plates/{name}.png', plates[name])
    print('plate', name, plates[name].shape)

# ---------------- per-frame global transform (ECC affine vs plate) ----------------
tracks = {'scene': [], 'n': []}
aff = {}
for name, n0, n1, pn in SCENES:
    plate = plates[name]
    pg = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    for n in range(n0, n1):
        g = G(n)
        W = np.eye(2, 3, dtype=np.float32)
        try:
            if name == 'jen':
                cc, W = cv2.findTransformECC(pg, g, W, cv2.MOTION_AFFINE,
                                             (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 1e-4))
            else:
                cc, W = cv2.findTransformECC(pg, g, W, cv2.MOTION_TRANSLATION,
                                             (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 1e-4))
        except cv2.error:
            W = np.eye(2, 3, dtype=np.float32)
        aff[n] = W
A = np.stack([aff[n] for n in sorted(aff)]).reshape(-1)
ns = np.array(sorted(aff))
np.savez(f'{OUT}/aff.npz', n=ns, a=A.reshape(len(ns), 6))

def warp_plate(name, n):
    return cv2.warpAffine(plates[name], aff[n], (720, 1280))

# ---------------- element tracks: per-frame mask inside predicted window ----------------
# windows from v8 curves (ref px); each element: scene, key predicate on (frame, bg) diff
def bbox_of(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) < 12:
        return None
    return (xs.mean(), ys.mean(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)

def track_element(name, scene, pred, win, margin=60, morph=3):
    """win(n) -> (cx, cy, hw, hh) predicted window in ref px; pred(f, bg) -> bool mask full-frame."""
    n0, n1 = [s[1] for s in SCENES if s[0] == scene][0], [s[2] for s in SCENES if s[0] == scene][0]
    res = {}
    for n in range(n0, n1):
        f = F(n); bg = warp_plate(scene, n)
        m = pred(f, bg).astype(np.uint8)
        cx, cy, hw, hh = win(n)
        w = np.zeros_like(m)
        x0, x1 = max(0, int(cx - hw - margin)), min(720, int(cx + hw + margin))
        y0, y1 = max(0, int(cy - hh - margin)), min(1280, int(cy + hh + margin))
        w[y0:y1, x0:x1] = 1
        m = m * w
        if morph:
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((morph, morph), np.uint8))
        bb = bbox_of(m)
        res[n] = (bb, m)
    return res

def diffpred(tau=26):
    def p(f, bg):
        return (np.abs(f.astype(np.int16) - bg.astype(np.int16)).max(2) > tau)
    return p

def lumpred(tau, mode='dark'):
    def p(f, bg):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
        gb = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY).astype(np.int16)
        d = g - gb
        return (d < -tau) if mode == 'dark' else (d > tau)
    return p

S = 1.0  # ref px here
CX = 360
def win_at(cx, cy, hw, hh):
    return lambda n: (cx, cy, hw, hh)

# motion windows (follow v8 curves, ref px)
def win_bag(n):
    t = n / 30.0
    tl = t % 11.67
    if tl < 1.35:
        ry = 1280 + 400 - (1280 + 400 - 360) * min(1, max(0, (tl - .9) / .5)) ** 2
        return (CX, ry, 200, 240)
    by = 360 + 400 * min(1, max(0, (tl - 1.35) / .25)) ** 2 + 60 * (1 - min(1, max(0, (tl - 1.55) / .18)) ** 2)
    return (CX, by, 200, 240)

def win_bill(n):
    t = (n / 30.0) % 11.67
    k = min(1, max(0, (t - .75) / .25))
    y = 330 + 160 * (1 - k)
    return (CX + 40, y, 200, 60)

def win_tag(n):
    t = (n / 30.0) % 11.67
    if t < 1.35:
        return (185, 260, 60, 120)
    return (288, 166, 60, 120)

def win_stool(n):
    return (CX, 1030, 240, 100)

def win_he(n):
    return (158, 295, 90, 50)
def win_said(n):
    return (245, 295, 90, 50)
def win_no(n):
    return (209, 410, 120, 60)

def win_cash(n):
    t = (n / 30.0) % 11.67
    tl2 = t - 3.25
    ck = min(1, max(0, tl2 / .40)) ** 2
    cx = 1080 - (1080 - 432) * ck
    cy = 500 + 255 * ck
    return (cx / 1.5, cy / 1.5 * 1.0, 130, 90) if False else (cx * S / 1.5, cy / 1.5, 130, 90)

def win_glove(n):
    t = (n / 30.0) % 11.67
    tl2 = t - 3.25
    hk = min(1, max(0, (tl2 - .15) / .35)) ** 2
    x = -260 + (145 * 1.5 + 260) * hk
    return (x / 1.5, 770, 130, 120)

def win_logo(n):
    return (164, 636, 90, 60)

def win_jen(n):
    t = n / 30.0
    rk = min(1, max(0, (t - 6.0) / .5)) ** 2
    return (CX, 830 + (1 - rk) * 120, 260, 330)

def win_sub(n):
    return (CX, 1030, 160, 60)

ELEMS = [
    ('bag', 'green', diffpred(30), win_bag),
    ('bill', 'green', lumpred(60, 'dark'), win_bill),
    ('tag', 'green', lumpred(60, 'dark'), win_tag),
    ('bagw', 'white', diffpred(30), win_bag),
    ('stool', 'white', lumpred(40, 'dark'), win_stool),
    ('stoold', 'desat', lumpred(40, 'dark'), win_stool),
    ('bagd', 'desat', diffpred(30), win_bag),
    ('he', 'desat', lumpred(30, 'dark'), win_he),
    ('said', 'desat', diffpred(30), win_said),
    ('no', 'desat', diffpred(30), win_no),
    ('cash', 'red', diffpred(34), win_cash),
    ('glove', 'red', lumpred(50, 'dark'), win_glove),
    ('logo', 'red', diffpred(34), win_logo),
    ('jen', 'jen', diffpred(30), win_jen),
    ('sub', 'jen', diffpred(30), win_sub),
]

TR = {}
for name, scene, pred, win in ELEMS:
    res = track_element(name, scene, pred, win)
    arr = []
    for n in sorted(res):
        bb, m = res[n]
        if bb is None:
            arr.append((n, 0, 0, 0, 0, 0))
        else:
            cx, cy, w, h = bb
            ys, xs = np.nonzero(m)
            ang = 0.0
            if len(xs) > 50 and name in ('cash', 'tag'):
                pts = np.stack([xs, ys], 1).astype(np.float32)
                rect = cv2.minAreaRect(pts)
                ang = rect[2]
            arr.append((n, 1, cx, cy, w, h))
        # save feather mask for patch use
        if bb is not None and name in ('cash',):
            mf = cv2.GaussianBlur((m * 255).astype(np.uint8), (5, 5), 0)
            cv2.imwrite(f'{OUT}/masks/{name}_{n:04d}.png', mf)
    TR[name] = np.array(arr, np.float32)
    vis = TR[name][TR[name][:, 1] == 1]
    print('track', name, 'frames', len(TR[name]), 'visible', len(vis))

np.savez(f'{OUT}/tracks.npz', **TR)

# ---------------- sprites (sharp, settled frames, alpha via same keying) ----------------
def sprite(name, n, pred, win, margin=40, feather=1.5):
    f = F(n); bg = warp_plate([s[0] for s in SCENES if s[1] <= n < s[2]][0], n)
    m = pred(f, bg).astype(np.uint8)
    cx, cy, hw, hh = win(n)
    w = np.zeros_like(m)
    x0, x1 = max(0, int(cx - hw - margin)), min(720, int(cx + hw + margin))
    y0, y1 = max(0, int(cy - hh - margin)), min(1280, int(cy + hh + margin))
    w[y0:y1, x0:x1] = 1
    m = m * w
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    nn, lab, stats, cent = cv2.connectedComponentsWithStats(m)
    if nn > 1:
        big = 1 + np.argmax(stats[1:, 4])
        m = (lab == big).astype(np.uint8)
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    alpha = cv2.GaussianBlur((m * 255).astype(np.uint8), (3, 3), 0)
    rgba = np.dstack([f[y0:y1 + 1, x0:x1 + 1], alpha[y0:y1 + 1, x0:x1 + 1]])
    cv2.imwrite(f'{OUT}/sprites/{name}.png', rgba)
    print('sprite', name, rgba.shape)

sprite('bag', 55, diffpred(30), win_bag, 50)
sprite('stool', 55, lumpred(40, 'dark'), win_stool, 50)
sprite('bill', 40, lumpred(60, 'dark'), win_bill, 40)
sprite('tag', 40, lumpred(60, 'dark'), win_tag, 40)
sprite('he', 75, lumpred(30, 'dark'), win_he, 40)
sprite('said', 75, diffpred(30), win_said, 40)
sprite('no', 75, diffpred(30), win_no, 40)
sprite('cash', 126, diffpred(34), win_cash, 50)
sprite('glove', 126, lumpred(50, 'dark'), win_glove, 50)
sprite('logo', 126, diffpred(34), win_logo, 40)
sprite('jen', 250, diffpred(30), win_jen, 60)
sprite('sub', 250, diffpred(30), win_sub, 40)
sprite('stamp', 6, lumpred(30, 'dark'), win_at(CX, 300, 220, 90), 60)
print('PRECOMPUTE v9 DONE')
