#!/usr/bin/env python3
"""v11b asset pass: 2x-supersampled keying + soft matting + edge decontamination.
Kills the jagged 'cutout' look of v11 sprites."""
import cv2, numpy as np, os

A = '/tmp/v11b'
os.makedirs(A, exist_ok=True)
UP = 2

def F(n):
    f = cv2.imread('/tmp/rf/%04d.png' % n)
    return cv2.resize(f, None, fx=UP, fy=UP, interpolation=cv2.INTER_LANCZOS4)

def hsv(f):
    return cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2HSV))

def feather_matte(m, soft=3):
    """soft matte: blur in matte-space then smoothstep -> anti-aliased alpha"""
    m = m.astype(np.float32) / 255.0
    m = cv2.GaussianBlur(m, (0, 0), soft)
    m = np.clip((m - 0.25) / 0.5, 0, 1)          # smoothstep band
    m = m * m * (3 - 2 * m)
    return m

def decontaminate(bgr, alpha, bgc):
    """un-mix background colour from semi-transparent edge pixels"""
    a = alpha[..., None]
    bg = np.array(bgc, np.float32).reshape(1, 1, 3)
    safe = np.clip(a, 0.12, 1.0)
    rgb = (bgr.astype(np.float32) - bg * (1 - a)) / safe
    rgb = np.clip(rgb, 0, 255)
    return np.where(a > 0.02, rgb, bgr.astype(np.float32)).astype(np.uint8)

def save(name, bgr, matte, bgc, pad=2):
    a8 = (matte * 255).astype(np.uint8)
    # downscale alpha 2x -> 1x (anti-aliased)
    a1 = cv2.resize(a8, (a8.shape[1] // UP, a8.shape[0] // UP), interpolation=cv2.INTER_AREA)
    b1 = cv2.resize(bgr, (bgr.shape[1] // UP, bgr.shape[0] // UP), interpolation=cv2.INTER_AREA)
    b1 = decontaminate(b1, a1.astype(np.float32) / 255.0, bgc)
    ys, xs = np.nonzero(a1 > 6)
    if len(xs) == 0:
        print('EMPTY', name); return
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + 1 + pad, b1.shape[1])
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + 1 + pad, b1.shape[0])
    rgba = np.dstack([b1[y0:y1, x0:x1], a1[y0:y1, x0:x1][..., None]])
    cv2.imwrite(f'{A}/{name}.png', rgba)
    print('sprite', name, rgba.shape)

def win(shape, y0, y1, x0, x1):
    w = np.zeros(shape[:2], np.uint8); w[y0*UP:y1*UP, x0*UP:x1*UP] = 1; return w

def close_open(m, c=9, o=5):
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((c*UP, c*UP), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((o*UP, o*UP), np.uint8))
    return m

def hole_fill(m):
    b = (m > 127).astype(np.uint8)
    ff = b.copy()
    cv2.floodFill(ff, None, (0, 0), 1)
    return np.maximum(b, (ff == 0).astype(np.uint8)) * 255

def largest_cc(m):
    nn, lab, stats, _ = cv2.connectedComponentsWithStats((m > 127).astype(np.uint8))
    if nn > 1:
        big = 1 + int(np.argmax(stats[1:, 4]))
        return ((lab == big) * 255).astype(np.uint8)
    return m

# ---------------- money bag (green scene, frame 30) ----------------
f = F(30); h, s, v = hsv(f)
h = h.astype(np.int16); s = s.astype(np.int16); v = v.astype(np.int16)
green = (h > 30) & (h < 90) & (s > 80) & (v > 110)
bills = (s < 60) & (v > 120)
m = ((green | bills).astype(np.uint8)) * 255
m *= win(f.shape, 430, 1010, 150, 620)
m = close_open(m, 11, 5)
m = hole_fill(m); m = largest_cc(m)
save('bag', f, feather_matte(m, 2.2), (26, 48, 22))

# ---------------- cash bundle (red scene, frame 126) ----------------
f = F(126); h, s, v = hsv(f)
h = h.astype(np.int16); s = s.astype(np.int16); v = v.astype(np.int16)
grey = (s < 70) & (v > 60)
m = (grey.astype(np.uint8)) * 255
m *= win(f.shape, 400, 800, 340, 575)
m = close_open(m, 7, 3)
m = hole_fill(m); m = largest_cc(m)
save('cash', f, feather_matte(m, 1.8), (45, 22, 150))

# ---------------- black glove / open hand (frame 126) ----------------
blk = (v < 70)
m = (blk.astype(np.uint8)) * 255
m *= win(f.shape, 700, 1000, 60, 340)
m = close_open(m, 9, 5)
m = hole_fill(m); m = largest_cc(m)
save('glove', f, feather_matte(m, 1.8), (96, 85, 255))

# ---------------- fist holding cash (frame 170, wire faded) ----------------
f = F(126); h, s, v = hsv(f)
h = h.astype(np.int16); s = s.astype(np.int16); v = v.astype(np.int16)
m = ((v < 110) & ~((v > 140) & (s < 40)) & ~(((h < 10) | (h > 170)) & (s > 80)) & ~((h > 30) & (h < 90))).astype(np.uint8) * 255
m *= win(f.shape, 420, 840, 555, 720)
m = close_open(m, 7, 3)
m = hole_fill(m); m = largest_cc(m)
save('hand2', f, feather_matte(m, 1.8), (96, 85, 255))

# ---------------- nvidia logo (frame 126) ----------------
m = ((s > 40) & (h > 25) & (h < 95) & (v > 60)).astype(np.uint8) * 255
m *= win(f.shape, 560, 900, 90, 300)
m = close_open(m, 15, 3)
m = largest_cc(m)
save('logo', f, feather_matte(m, 1.5), (45, 22, 150))

# ---------------- jensen (frame 210): bg-poly difference at 2x ----------------
f = F(210)
ff = f.astype(np.float64); HH, WW = f.shape[:2]
yy, xx = np.mgrid[0:HH, 0:WW].astype(np.float64)
ring = (xx < 70*UP) | (xx > 650*UP) | (yy < 130*UP)
xn = xx / WW * 2 - 1; yn = yy / HH * 2 - 1
AM = np.stack([np.ones_like(xn), xn, yn, xn*yn, xn*xn, yn*yn,
               xn**3, yn**3, xn*xn*yn, xn*yn*yn], -1)
Ar = AM[ring]; fit = np.zeros_like(ff)
for c in range(3):
    coef, *_ = np.linalg.lstsq(Ar, ff[..., c][ring], rcond=None)
    fit[..., c] = AM @ coef
resid = np.abs(ff - fit).max(-1)
hs, ss, vs = cv2.split(cv2.cvtColor(f, cv2.COLOR_BGR2HSV))
hs = hs.astype(np.int16); ss = ss.astype(np.int16); vs = vs.astype(np.int16)
side = (xx < 210*UP) | (xx > 510*UP)
maroon = (((hs < 12) | (hs > 168)) & (ss > 100) & (vs < 130)) & side
darklow = (ss < 60) & (vs < 90)
m = (((resid > 28) & ~maroon) | (darklow & (resid > 16))).astype(np.uint8) * 255
m *= win(f.shape, 180, 1280, 40, 680)
m[130*UP:360*UP, 110*UP:252*UP] = 0
m[140*UP:360*UP, 460*UP:610*UP] = 0
m[640*UP:1280*UP, 240*UP:520*UP] |= (vs[640*UP:1280*UP, 240*UP:520*UP] < 120).astype(np.uint8) * 255
m = close_open(m, 13, 5)
m = hole_fill(m); m = largest_cc(m)
# edge refine: shave fringe then soft matte
m = cv2.medianBlur(m, 9)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
m = cv2.erode(m, np.ones((5, 5), np.uint8), iterations=2)
save('jen', f, feather_matte(m, 2.6), (30, 22, 80))

# ---------------- smoke alpha sequence (frames 47..72) ----------------
os.makedirs(f'{A}/smoke', exist_ok=True)
for n in range(47, 73):
    f = F(n)
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    a = np.clip((232 - g) / 55.0, 0, 1)
    wb = win(f.shape, 300, 640, 60, 700).astype(bool)
    wb[430*UP:1010*UP, 150*UP:620*UP] = False
    a *= wb
    a8 = (a * 255).astype(np.uint8)
    a1 = cv2.resize(a8, (a8.shape[1] // UP, a8.shape[0] // UP), interpolation=cv2.INTER_AREA)
    cv2.imwrite(f'{A}/smoke/{n:04d}.png', a1)
print('ASSETS v11b DONE')
