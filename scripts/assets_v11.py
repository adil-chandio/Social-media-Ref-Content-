#!/usr/bin/env python3
"""S01 v11 stage 1 - clean asset extraction (proper matting).
Each sprite: source frame -> color/luma key -> morphology -> hole fill -> edge feather.
Verified via contact sheet before use in the composition engine.
"""
import numpy as np, cv2, os

A = '/tmp/v11'
os.makedirs(A, exist_ok=True)
def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))

def hole_fill(m):
    b = (m > 127).astype(np.uint8)
    ff = b.copy()
    cv2.floodFill(ff, None, (0, 0), 1)
    return np.maximum(b, (ff == 0).astype(np.uint8)) * 255

def feather(m, k=3):
    return cv2.GaussianBlur(m, (k, k), 0)

def save(name, bgr, alpha):
    a = feather(alpha.astype(np.uint8))
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        print('EMPTY', name); return
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rgba = np.dstack([bgr[y0:y1, x0:x1], a[y0:y1, x0:x1][..., None]])
    cv2.imwrite(f'{A}/{name}.png', rgba)
    print('sprite', name, rgba.shape)

def hsv(f):
    return cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.int16)

# ---- bag + stool from n55 (settled on white) ----
f = F(55)
h, s, v = cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2HSV))
h = h.astype(np.int16); s = s.astype(np.int16); v = v.astype(np.int16)
alpha = (((s > 30) | (v < 150)).astype(np.uint8)) * 255
wb_ = np.zeros_like(alpha); wb_[440:1010, 150:620] = 255
alpha = cv2.bitwise_and(alpha, wb_)
alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
alpha = hole_fill(alpha)
# split bag (upper) / stool (lower) by y
bag_a = alpha.copy(); bag_a[1000:, :] = 0
alpha2 = ((((v > 85) & (s > 60) & (h < 32)) | ((v > 100) & (s > 50) & (h < 35))).astype(np.uint8)) * 255
wb2 = np.zeros_like(alpha2); wb2[940:1280, 100:620] = 255
st_a = cv2.bitwise_and(alpha2, wb2)
st_a = cv2.morphologyEx(st_a, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
st_a = hole_fill(st_a)
save('bag', f, bag_a)
save('stool', f, st_a)

# ---- smoke sequence n47..n72 ----
os.makedirs(A + '/smoke', exist_ok=True)
for n in range(47, 73):
    f = F(n)
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    s2 = cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2HSV))[1].astype(np.int16)
    a = np.clip((235 - g) * 3, 0, 255).astype(np.uint8)
    a[s2 > 45] = 0                      # keep only gray smoke (not bag/stool/text)
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cv2.imwrite(f'{A}/smoke/{n:04d}.png', a)
print('smoke seq done')

# ---- cash / glove / logo / wire from n126 ----
f = F(126)
h, s, v = cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2HSV)).map if False else cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2HSV))
h = h.astype(np.int16); s = s.astype(np.int16); v = v.astype(np.int16)
red = ((h < 10) | (h > 170)) & (s > 90)
box = np.zeros_like(red); box[400:800, 340:575] = True
cash_m = (~red) & box
cash_m = cv2.morphologyEx(cash_m.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cash_m = hole_fill(cash_m)
# remove wire lines from cash (thin): keep big component
nn, lab, stats, _ = cv2.connectedComponentsWithStats((cash_m > 127).astype(np.uint8))
if nn > 1:
    big = 1 + np.argmax(stats[1:, 4])
    cash_m = ((lab == big) * 255).astype(np.uint8)
save('cash', f, cash_m)

glove_m = ((v < 95) & ~red).astype(np.uint8) * 255
gb = np.zeros_like(glove_m); gb[700:1000, 60:340] = 1
glove_m *= gb
glove_m = cv2.morphologyEx(glove_m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
glove_m = hole_fill(glove_m)
save('glove', f, glove_m)

logo_m = ((h > 30) & (h < 90) & (s > 55)).astype(np.uint8) * 255
logo_m = cv2.morphologyEx(logo_m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
logo_m = hole_fill(logo_m)
nn2, lab2, st2, _ = cv2.connectedComponentsWithStats((logo_m > 127).astype(np.uint8))
if nn2 > 1:
    bg2 = 1 + np.argmax(st2[1:, 4])
    logo_m = ((lab2 == bg2) * 255).astype(np.uint8)
save('logo', f, logo_m)



hand2_m = ((v < 110) & ~((h > 30) & (h < 90)) & ~(((h < 10) | (h > 170)) & (s > 80))).astype(np.uint8) * 255
hb = np.zeros_like(hand2_m); hb[420:840, 555:720] = 1
hand2_m *= hb
hand2_m = cv2.morphologyEx(hand2_m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
hand2_m = hole_fill(hand2_m)
save('hand2', f, hand2_m)

# ---- jensen from n210: background-polynomial difference key ----
f = F(210)
ff = f.astype(np.float64)
HH, WW = f.shape[:2]
yy, xx = np.mgrid[0:HH, 0:WW].astype(np.float64)
ring = (xx < 70) | (xx > 650) | (yy < 130)
xn = xx / WW * 2 - 1
yn = yy / HH * 2 - 1
AM = np.stack([np.ones_like(xn), xn, yn, xn * yn, xn * xn, yn * yn,
                   xn ** 3, yn ** 3, xn * xn * yn, xn * yn * yn], -1)
Ar = AM[ring]
fit = np.zeros_like(ff)
for c in range(3):
    coef, *_ = np.linalg.lstsq(Ar, ff[..., c][ring], rcond=None)
    fit[..., c] = AM @ coef
resid = np.abs(ff - fit).max(-1)
jen_m = (resid > 24).astype(np.uint8) * 255
jb = np.zeros_like(jen_m); jb[180:1280, 40:680] = 1
jen_m *= jb
jen_m = cv2.morphologyEx(jen_m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
jen_m = cv2.morphologyEx(jen_m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
jen_m = hole_fill(jen_m)
nn, lab, stats, _ = cv2.connectedComponentsWithStats((jen_m > 127).astype(np.uint8))
if nn > 1:
    big = 1 + int(np.argmax(stats[1:, 4]))
    jen_m = ((lab == big) * 255).astype(np.uint8)
save('jen', f, jen_m)

# ---- contact sheet ----
names = ['bag', 'stool', 'cash', 'glove', 'logo', 'hand2', 'jen']
cw, ch = 240, 300
sheet = np.full((ch * 2, cw * 4, 3), 45, np.uint8)
for i, nm in enumerate(names):
    im = cv2.imread(f'{A}/{nm}.png', cv2.IMREAD_UNCHANGED)
    if im is None:
        continue
    al = im[:, :, 3:4] / 255.0
    chk = np.indices((im.shape[0], im.shape[1])).sum(0) // 12 % 2
    bgc = np.dstack([chk * 30 + 40] * 3).astype(np.float32)
    vis = (im[:, :, :3] * al + bgc * (1 - al)).astype(np.uint8)
    sc = min((cw - 12) / vis.shape[1], (ch - 12) / vis.shape[0])
    r = cv2.resize(vis, (int(vis.shape[1] * sc), int(vis.shape[0] * sc)))
    x, y = (i % 4) * cw + 6, (i // 4) * ch + 6
    sheet[y:y + r.shape[0], x:x + r.shape[1]] = r
    cv2.putText(sheet, nm, (x, y + ch - 10), 0, .5, (0, 255, 255), 1)
cv2.imwrite('/tmp/v11_sheet.png', sheet)
print('ASSETS v11 DONE')
