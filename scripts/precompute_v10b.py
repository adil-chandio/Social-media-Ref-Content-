#!/usr/bin/env python3
"""S01 v10b - clean fields (median mosaic + static-rect inpaint) and masks/tracks
recomputed against those clean fields, so patch alphas never leak text/bg."""
import numpy as np, cv2, os

OUT = '/tmp/v9'
V10 = '/tmp/v10'
def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))
def G(n):
    return cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY)
W, H = 720, 1280

RECTS = {
    'stamp': [(80, 120, 640, 470)],
    'green': [(140, 240, 660, 420), (100, 120, 280, 400), (120, 300, 600, 950)],
    'white': [(140, 240, 660, 420), (100, 120, 280, 400), (0, 300, 350, 700), (450, 350, 720, 760)],
    'desat': [(40, 240, 660, 500), (100, 440, 620, 1080), (60, 880, 660, 1240)],
    'teal': [],
}
RANGES = {'stamp': (0, 13), 'green': (26, 41), 'white': (47, 57), 'desat': (70, 90), 'teal': (90, 98)}
for name, (n0, n1) in RANGES.items():
    acc = [F(n) for n in range(n0, n1, 2)]
    med = np.median(np.stack(acc), 0).astype(np.uint8)
    m = np.zeros((H, W), np.uint8)
    for x0, y0, x1, y1 in RECTS[name]:
        m[y0:y1, x0:x1] = 255
    if m.any():
        keep = (m == 0)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        xn, yn = xx / W, yy / H
        rr = np.sqrt((xn - .5) ** 2 + (yn - .5) ** 2)
        terms = [np.ones_like(xn), xn, yn, xn * xn, xn * yn, yn * yn, xn ** 3, yn ** 3,
                 xn * xn * yn, xn * yn * yn, rr, rr * rr, rr ** 3, rr ** 4]
        TM = np.stack([t.ravel() for t in terms], 1)
        A = TM[keep.ravel()]
        fld = np.zeros((H, W, 3), np.uint8)
        for c in range(3):
            b = med[..., c].ravel()[keep.ravel()].astype(np.float64)
            coef, *_ = np.linalg.lstsq(A, b, rcond=None)
            fld[..., c] = (TM @ coef).reshape(H, W).clip(0, 255).astype(np.uint8)
    else:
        fld = med
    cv2.imwrite(f'{OUT}/plates/field_{name}.png', fld)
    print('field', name)

# red + jen fields already good (v10 median / inpaint) - ensure exist
if not os.path.exists(f'{OUT}/plates/field_red.png'):
    raise SystemExit('field_red missing')

# ---------------- masks + tracks vs clean fields ----------------
def field_of(sc):
    p = f'{OUT}/plates/field_{sc}.png'
    if not os.path.exists(p):
        p = f'{OUT}/plates/{sc}.png'
    return cv2.imread(p)

SC = {'stamp': (0, 13), 'black': (13, 18), 'green': (18, 41), 'white': (41, 57),
      'desat': (57, 90), 'teal': (90, 98), 'red': (98, 177), 'jen': (177, 270)}
def eoc(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
CX = 360
def w_stamp(n): return (CX, 300, 260, 110)
def w_black(n): return (CX, 420, 320, 260)
def w_bill(n):
    t = (n / 30.0) % 11.675
    return (CX + 40, 330 + 160 * (1 - eoc((t - .75) / .25)), 240, 80)
def w_tag(n):
    t = (n / 30.0) % 11.675
    return (185, 260, 80, 140) if t < 1.35 else (288, 166, 80, 140)
def w_bag(n):
    t = (n / 30.0) % 11.675
    if t < 1.35:
        ry = 1680 - (1680 - 360) * eoc((t - .9) / .5)
        return (CX, ry, 220, 260)
    by = 360 + 400 * eoc((t - 1.35) / .25) + 60 * (1 - eoc((t - 1.55) / .18))
    return (CX, by, 220, 260)
def w_stool(n): return (CX, 1060, 260, 120)
def w_smoke(n): return (CX, 470, 280, 230)
def w_he(n): return (150, 295, 75, 55)
def w_said(n): return (250, 295, 75, 55)
def w_no(n): return (209, 410, 140, 80)
def w_cash(n):
    t = (n / 30.0) % 11.675
    ck = eoc((t - 3.25) / .40)
    return ((1080 - (1080 - 432) * ck) / 1.5, (500 + 255 * ck) / 1.5, 190, 120)
def w_glove(n):
    t = (n / 30.0) % 11.675
    hk = eoc((t - 3.40) / .35)
    return ((-260 + (145 * 1.5 + 260) * hk) / 1.5, 770, 150, 140)
def w_logo(n): return (164, 636, 110, 80)
def w_jen(n):
    t = (n / 30.0) % 11.675
    rk = eoc((t - 6.0) / .5)
    return (CX, 830 + (1 - rk) * 120, 300, 400)
def w_sub(n): return (CX, 1030, 190, 80)
def w_2008(n): return (CX, 300, 300, 120)
def w_glow(n): return (CX, 330, 150, 60)

def pred_dark(tau):
    def p(f, of, g, og):
        return (og - g) > tau
    return p
def pred_bright(tau):
    def p(f, of, g, og):
        return (g - og) > tau
    return p
def pred_diff(tau):
    def p(f, of, g, og):
        return np.abs(f.astype(np.int16) - of.astype(np.int16)).max(2) > tau
    return p
def pred_band(lo, hi):
    def p(f, of, g, og):
        d = og - g
        return (d > lo) & (d < hi)
    return p

ELEMS = [
    ('stamp', 'stamp', w_stamp, pred_dark(40), 40),
    ('btext', 'black', w_black, pred_bright(40), 40),
    ('bill', 'green', w_bill, pred_dark(50), 30),
    ('tag', 'green', w_tag, pred_dark(50), 30),
    ('bag', 'green', w_bag, pred_diff(30), 30),
    ('smoke', 'white', w_smoke, pred_band(15, 90), 30),
    ('stool', 'white', w_stool, pred_dark(40), 30),
    ('bagw', 'white', w_bag, pred_diff(30), 30),
    ('tagw', 'white', w_tag, pred_dark(50), 30),
    ('billw', 'white', w_bill, pred_dark(50), 30),
    ('smoked', 'desat', w_smoke, pred_band(15, 90), 30),
    ('stool', 'desat', w_stool, pred_dark(40), 30),
    ('bag', 'desat', w_bag, pred_diff(30), 30),
    ('he', 'desat', w_he, pred_dark(40), 30),
    ('said', 'desat', w_said, pred_dark(40), 30),
    ('no', 'desat', w_no, pred_diff(40), 30),
    ('cash', 'red', w_cash, pred_diff(26), 30),
    ('glove', 'red', w_glove, pred_diff(26), 30),
    ('logo', 'red', w_logo, pred_diff(26), 30),
    ('jen', 'jen', w_jen, pred_diff(22), 40),
    ('sub', 'jen', w_sub, pred_diff(26), 30),
    ('y2008', 'jen', w_2008, pred_bright(60), 30),
]
TEXTWIN = {'smoke': (w_bill, w_tag), 'smoked': (w_he, w_said, w_no)}
K3 = np.ones((3, 3), np.uint8)
tracks = {}
for name, sc, win, pred, marg in ELEMS:
    n0, n1 = SC[sc]
    of_img = field_of(sc)
    og = cv2.cvtColor(of_img, cv2.COLOR_BGR2GRAY).astype(np.int16)
    rows = []
    for n in range(n0, n1):
        f = F(n)
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
        m = pred(f, of_img, g, og).astype(np.uint8)
        cx, cy, hw, hh = win(n)
        Wm = np.zeros_like(m)
        x0, x1 = max(0, int(cx - hw - marg)), min(W, int(cx + hw + marg))
        y0, y1 = max(0, int(cy - hh - marg)), min(H, int(cy + hh + marg))
        Wm[y0:y1, x0:x1] = 1
        for tw in TEXTWIN.get(name, ()):
            tcx, tcy, thw, thh = tw(n)
            Wm[max(0, int(tcy - thh - 60)):min(H, int(tcy + thh + 60)), max(0, int(tcx - thw - 60)):min(W, int(tcx + thw + 60))] = 0
        m *= Wm
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, K3)
        m = cv2.dilate(m, np.ones((7, 7), np.uint8))
        ys, xs = np.nonzero(m)
        if len(xs) < 30:
            rows.append((n, 0, 0, 0, 0, 0))
            p = f'{OUT}/masks/{name}@{sc}_{n:04d}.png'
            if os.path.exists(p):
                os.remove(p)
            continue
        mf = cv2.GaussianBlur((m * 255).astype(np.uint8), (7, 7), 0)
        cv2.imwrite(f'{OUT}/masks/{name}@{sc}_{n:04d}.png', mf)
        rows.append((n, 1, xs.mean(), ys.mean(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
    tracks[f'{name}@{sc}'] = np.array(rows, np.float32)
    print('track', name, sc, sum(r[1] for r in rows), '/', len(rows))
np.savez(f'{OUT}/tracks9.npz', **tracks)
print('PRECOMPUTE v10b DONE')
