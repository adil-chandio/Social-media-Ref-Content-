#!/usr/bin/env python3
"""S01 v11 - from-scratch composition engine (mini After-Effects).
Everything is a LAYER with KEYFRAMES + EASING, rendered at 60fps:
  bg generators (procedural MONARCH fields) | sprite layers (clean alpha assets)
  | native type layers (Anton/Manrope) | footage clips (smoke seq, graded talk head)
  | analytic-velocity directional motion blur | soft shadows | additive glow | grade+grain
Motion design matches the reference event sheet; theme/fonts/colors are MONARCH.
"""
import numpy as np, cv2, subprocess, math, os
from PIL import Image, ImageDraw, ImageFont

FF = open('/tmp/ffpath').read().strip()
REF = 'refs/ref-reels-tutorial.mp4'
A = '/tmp/v11b'
W, H = 720, 1280
FPS = 60
PASS = 11.675
NF = int(23.35 * FPS)

# ---------------- MONARCH palette ----------------
INK = (10, 10, 11); BLOOD = (160, 16, 32); BONE = (244, 241, 234)
GOLD = (212, 175, 55); RED = (255, 85, 96); FOREST = (26, 48, 22)
def bgr(c): return (c[2], c[1], c[0])

# ---------------- easing ----------------
def clamp01(x): return min(1.0, max(0.0, x))
def lin(x): return clamp01(x)
def eoC(x):  # cubic out
    x = clamp01(x); return 1 - (1 - x) ** 3
def eoQ(x):  # quint out
    x = clamp01(x); return 1 - (1 - x) ** 5
def back(x):  # overshoot
    x = clamp01(x); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def seg(t, t0, d, fn=eoC):
    return fn((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)

# ---------------- assets ----------------
SPR = {}
def spr(name):
    if name not in SPR:
        if name == 'bagv':
            SPR[name] = _vec_bag()
        elif name == 'stoolv':
            SPR[name] = _vec_stool()
        elif name == 'bagvg':
            SPR[name] = _grey(_vec_bag())
        elif name == 'stoolvg':
            SPR[name] = _grey(_vec_stool())
        else:
            SPR[name] = cv2.imread(f'{A}/{name}.png', cv2.IMREAD_UNCHANGED)
    return SPR[name]
SMOKE = {}
def smoke(n):
    if n not in SMOKE:
        SMOKE[n] = cv2.imread(f'{A}/smoke/{n:04d}.png', 0)
    return SMOKE[n]

def _vec_bag():
    S = 2
    W2, H2 = 476 * S, 470 * S
    cvx = np.zeros((H2, W2, 3), np.uint8)
    # bill fan
    for i, ang in enumerate((-30, -18, -6, 6, 18, 30)):
        bw, bh = 240 * S, 92 * S
        bill = np.full((bh, bw, 3), (234, 241, 244), np.uint8)
        cv2.rectangle(bill, (4 * S, 4 * S), (bw - 4 * S, bh - 4 * S), (30, 30, 32), 3 * S)
        cv2.ellipse(bill, (bw // 2, bh // 2), (17 * S, 24 * S), 0, 0, 360, (168, 166, 160), -1)
        cv2.ellipse(bill, (bw // 2, bh // 2), (17 * S, 24 * S), 0, 0, 360, (120, 118, 112), 2 * S)
        M = cv2.getRotationMatrix2D((bw / 2, bh / 2), ang, 1.0)
        rot = cv2.warpAffine(bill, M, (bw, bh), borderMode=cv2.BORDER_TRANSPARENT,
                             flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
        msk = (rot.sum(2) > 0).astype(np.float32)
        x0 = int(238 * S - bw / 2 + ang * 3.0 * S); y0 = int((150 - 48 + abs(i - 2.5) * 14) * S - bh * 0.55)
        M2 = cv2.getRotationMatrix2D((bw / 2, bh / 2), ang, 1.0)
        canvas = np.zeros((H2, W2), np.float32)
        tmp = np.zeros((H2, W2, 3), np.uint8)
        ys, ye = max(y0, 0), min(y0 + bh, H2); xs, xe = max(x0, 0), min(x0 + bw, W2)
        tmp[ys:ye, xs:xe] = rot[ys - y0:ye - y0, xs - x0:xe - x0]
        canvas[ys:ye, xs:xe] = msk[ys - y0:ye - y0, xs - x0:xe - x0]
        cvx = (cvx.astype(np.float32) * (1 - canvas[..., None]) + tmp.astype(np.float32) * canvas[..., None]).astype(np.uint8)
    # envelope body with vertical gradient
    env = np.zeros((H2, W2, 3), np.float32)
    y0, y1 = int(150 * S), int(440 * S)
    grad = np.linspace(1.0, 0.80, y1 - y0)[:, None]
    col = np.array((48, 140, 84), np.float32)
    env[y0:y1, 28 * S:448 * S] = col * grad[..., None]
    msk = np.zeros((H2, W2), np.float32); msk[y0:y1, 28 * S:448 * S] = 1
    cvx = (cvx.astype(np.float32) * (1 - msk[..., None]) + env * msk[..., None]).astype(np.uint8)
    # flap
    tri = np.array([[28 * S, y0], [238 * S, int(300 * S)], [448 * S, y0]], np.int32)
    cv2.fillPoly(cvx, [tri], (36, 110, 62))
    cv2.polylines(cvx, [tri], True, (150, 200, 150), 2 * S)
    a = (cvx.sum(2) > 0).astype(np.uint8) * 255
    out = np.dstack([cv2.resize(cvx, (476, 470), interpolation=cv2.INTER_AREA),
                     cv2.resize(a, (476, 470), interpolation=cv2.INTER_AREA)[..., None]])
    return out

def _vec_stool():
    S = 2
    W2, H2 = 300 * S, 260 * S
    cvx = np.zeros((H2, W2, 3), np.uint8)
    cv2.fillPoly(cvx, [np.array([[130*S,68*S],[145*S,68*S],[120*S,215*S],[108*S,215*S]])], (48, 62, 80))
    cv2.fillPoly(cvx, [np.array([[155*S,68*S],[170*S,68*S],[192*S,215*S],[180*S,215*S]])], (48, 62, 80))
    cv2.fillPoly(cvx, [np.array([[95*S,70*S],[115*S,70*S],[75*S,255*S],[58*S,255*S]])], (66, 88, 110))
    cv2.fillPoly(cvx, [np.array([[185*S,70*S],[205*S,70*S],[242*S,255*S],[225*S,255*S]])], (66, 88, 110))
    for fx, fy in ((66, 255), (234, 255)):
        cv2.ellipse(cvx, (fx * S, fy * S), (12 * S, 5 * S), 0, 0, 360, (24, 30, 40), -1)
    cv2.ellipse(cvx, (150 * S, 55 * S), (140 * S, 30 * S), 0, 0, 360, (80, 100, 120), -1)
    cv2.ellipse(cvx, (150 * S, 45 * S), (140 * S, 30 * S), 0, 0, 360, (95, 120, 140), -1)
    cv2.ellipse(cvx, (150 * S, 45 * S), (116 * S, 23 * S), 0, 0, 360, (110, 138, 158), -1)
    a = (cvx.sum(2) > 0).astype(np.uint8) * 255
    return np.dstack([cv2.resize(cvx, (300, 260), interpolation=cv2.INTER_AREA),
                      cv2.resize(a, (300, 260), interpolation=cv2.INTER_AREA)[..., None]])

def _grey(im):
    g = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)[..., None].repeat(3, 2)
    return np.dstack([g, im[..., 3:4]])

FA = 'assets/fonts/Anton-Regular.ttf'
FM = 'assets/fonts/Manrope-800.ttf'
_fc = {}
def font(p, sz):
    k = (p, int(sz))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(p, max(8, int(sz)))
    return _fc[k]

def text_img(txt, sz, face, side=None, depth=0, fpath=FA, spacing=0):
    f = font(fpath, sz)
    lines = txt.split('\n')
    ws, hs = [], []
    for ln in lines:
        b = f.getbbox(ln); ws.append(b[2] - b[0]); hs.append(b[3] - b[1])
    w = max(ws) + depth * 2 + 10
    h = sum(hs) + spacing * (len(lines) - 1) + depth * 2 + 10
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = depth + 5
    for ln, hh in zip(lines, hs):
        if side and depth:
            for k in range(depth, 0, -1):
                d.text((depth + 5 - k * 0.7, y + k * 0.9), ln, font=f, fill=side + (255,))
        d.text((depth + 5, y), ln, font=f, fill=face + (255,))
        y += hh + spacing
    return im

# ---------------- backgrounds ----------------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx / W - .5) ** 2) + ((_yy / H - .5) ** 2)) / 0.75
def radial(c0, c1, p=1.6):
    t = (_r ** p)[..., None]
    a = np.array(bgr(c0), np.float32); b = np.array(bgr(c1), np.float32)
    return (a * (1 - t) + b * t).clip(0, 255).astype(np.uint8)

def bg_bars():
    base = radial((150, 20, 35), (96, 10, 22))
    ov = Image.fromarray(np.zeros((H, W, 4), np.uint8))
    d = ImageDraw.Draw(ov)
    step, th, tilt, hw = 180, 95, 76, 200
    for cxr, al in ((0.32, 46), (0.86, 30)):
        cx = int(cxr * W); y = -step
        while y < H + step:
            d.polygon([(cx - hw, y - tilt), (cx + hw, y + tilt),
                       (cx + hw, y + tilt + th), (cx - hw, y - tilt + th)],
                      fill=(255, 90, 90, al))
            y += step
    return cv2.cvtColor(np.array(ov), cv2.COLOR_RGBA2BGRA)[:, :, :3] * 0 + \
        cv2.addWeighted(base, 1.0, cv2.cvtColor(np.array(ov)[:, :, :3], cv2.COLOR_RGB2BGR), 0.0, 0) if False else \
        np.clip(base.astype(np.float32) * (1 - np.array(ov)[:, :, 3:4] / 255.0 * 0.5) +
                np.array(ov)[:, :, :3][..., ::-1] * (np.array(ov)[:, :, 3:4] / 255.0 * 0.5), 0, 255).astype(np.uint8)

BG = {}
def bg(name):
    if name in BG:
        return BG[name]
    if name == 'stamp':
        v = radial((250, 247, 240), (214, 208, 196))
    elif name == 'black':
        v = radial((24, 24, 27), INK)
    elif name == 'green':
        v = radial((130, 195, 10), (60, 95, 0))
    elif name == 'white':
        v = radial((236, 236, 234), (196, 196, 194))
    elif name == 'desat':
        v = radial((206, 206, 204), (166, 166, 164))
    elif name == 'teal':
        v = radial((185, 10, 8), (140, 6, 4))
    elif name == 'red':
        v = bg_bars()
    elif name == 'jen':
        v = radial((70, 20, 24), (10, 6, 8), 1.2)
    else:
        v = radial((24, 24, 27), INK)
    BG[name] = v
    return v

# ---------------- layer helpers ----------------
def dirblur(im, vx, vy, scale=0.5):
    L = min(45, max(0, int(math.hypot(vx, vy) * scale)))
    if L < 3:
        return im
    ang = math.atan2(vy, vx)
    k = np.zeros((L, L), np.float32)
    c = L // 2
    for i in range(L):
        x = int(round(c + (i - c) * math.cos(ang)))
        y = int(round(c + (i - c) * math.sin(ang)))
        if 0 <= x < L and 0 <= y < L:
            k[y, x] = 1
    k /= k.sum()
    out = im.astype(np.float32)
    for cch in range(im.shape[2]):
        out[..., cch] = cv2.filter2D(im[..., cch], -1, k)
    if im.shape[2] == 4:
        out[..., 3] = cv2.filter2D(im[..., 3], -1, k)
    return out.clip(0, 255).astype(np.uint8)

_prev = {}
def place(fr, im, x, y, scale=1.0, rot=0.0, alpha=1.0, key=None, blur=True, shadow=None):
    """sub-pixel composite of RGBA sprite; velocity blur from key track"""
    if im is None or alpha <= 0:
        return
    vx = vy = 0.0
    if key:
        px, py = _prev.get(key, (x, y))
        vx, vy = (x - px) * FPS / 30.0, (y - py) * FPS / 30.0
        _prev[key] = (x, y)
    if scale != 1.0:
        im = cv2.resize(im, (max(2, int(im.shape[1] * scale)), max(2, int(im.shape[0] * scale))), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    if rot:
        M = cv2.getRotationMatrix2D((im.shape[1] / 2, im.shape[0] / 2), rot, 1.0)
        im = cv2.warpAffine(im, M, (im.shape[1], im.shape[0]))
    if blur:
        im = dirblur(im, vx, vy)
    ix, iy = int(math.floor(x - im.shape[1] / 2)), int(math.floor(y - im.shape[0] / 2))
    sx, sy = (x - im.shape[1] / 2) - ix, (y - im.shape[0] / 2) - iy
    if sx > 1e-3 or sy > 1e-3:
        im = cv2.warpAffine(im, np.float32([[1, 0, sx], [0, 1, sy]]), (im.shape[1] + 2, im.shape[0] + 2))
    else:
        im = cv2.copyMakeBorder(im, 0, 0, 0, 2, 0, 2, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0)) if False else im
    a = (im[..., 3:4].astype(np.float32) / 255.0) * alpha
    x0, y0 = ix, iy
    x1, y1 = x0 + im.shape[1], y0 + im.shape[0]
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(W, x1), min(H, y1)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    if shadow:
        sw, sa = shadow
        sh = np.zeros((H, W), np.float32)
        cv2.ellipse(sh, (int(x), int(y + im.shape[0] * 0.44)), (int(im.shape[1] * sw), int(im.shape[1] * sw * 0.16)), 0, 0, 360, sa, -1)
        sh = cv2.GaussianBlur(sh, (61, 61), 0)
        fr[:] = (fr * (1 - sh[..., None] * 0.45)).astype(np.uint8)
    sl = im[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    al = a[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    fr[cy0:cy1, cx0:cx1] = (sl[..., :3] * al + fr[cy0:cy1, cx0:cx1] * (1 - al)).astype(np.uint8)

def place_pil(fr, pil_im, x, y, rot=0.0, alpha=1.0, scale=1.0):
    if scale != 1.0:
        pil_im = pil_im.resize((max(2, int(pil_im.width * scale)), max(2, int(pil_im.height * scale))), Image.LANCZOS)
    if rot:
        pil_im = pil_im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        r, g, b, a = pil_im.split()
        pil_im = Image.merge('RGBA', (r, g, b, a.point(lambda v: int(v * alpha))))
    fr.paste(pil_im, (int(x - pil_im.width / 2), int(y - pil_im.height / 2)), pil_im.split()[3])

# ---------------- scene timeline (local seconds) ----------------
def scene_at(t):
    t = t % PASS
    for nm, a0, a1 in [('stamp', 0, .43), ('black', .43, .60), ('green', .60, 1.35),
                       ('white', 1.35, 1.90), ('desat', 1.90, 3.00), ('teal', 3.00, 3.25),
                       ('red', 3.25, 5.90), ('jen', 5.90, 9.00), ('graded', 9.00, PASS)]:
        if a0 <= t < a1:
            return nm, t
    return 'graded', t

GREY = False
def render_frame(n):
    t = n / FPS
    sc, tl = scene_at(t)
    fr = bg(sc).copy()
    pil = None
    if sc == 'stamp':
        k = back(seg(tl, 0.02, .28))
        im = text_img('TWENTY\nBILLION', 74 * (0.35 + 0.65 * k), INK, RED, 4, spacing=8)
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        place_pil(pil, im, 360, 300, -6, min(1, seg(tl, 0.02, .12, lin) * 2))
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'black':
        k = seg(tl, .43 - .43, .17)
        fr = bg('black').copy()
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        im = text_img('TWENTY\nBILLION', 139, BONE, RED, 9, spacing=8)
        place_pil(pil, im, 360 - 180 * (1 - eoC(k)) * 0 + 0, 420, 0, 1, 0.5 + 0.5 * eoC(k))
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'green':
        kk = seg(tl, .60 - .60, .18, lin)
        fr = (bg('green').astype(np.float32) * kk).clip(0, 255).astype(np.uint8) if False else bg('green').copy()
        bk = eoC(seg(tl, .75, .25))
        ry = 1680 - (1680 - 360) * eoQ(seg(tl, .85, .45))
        place(fr, spr('bagv'), 260, 1500 - 900 * eoC(seg(tl, .60, .55)), 1.0, 0, 1, 'bag')
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        place_pil(pil, text_img('BILLION', 62, INK, (120, 118, 112), 6), 250, 120, -8, bk)
        place_pil(pil, text_img('TWENTY', 36, RED, INK, 3), 150, 110, -78, seg(tl, .90, .15, lin))
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'white':
        fr = bg('white').copy()
        sk = eoC(seg(tl, 1.35, .20))
        sx = 760 - 400 * sk
        by = 360 + 400 * eoC(seg(tl, 1.35, .20)) - 25 * math.sin(clamp01((tl - 1.55) / .18) * math.pi)
        place(fr, spr('bagv'), 352, 749 - 25 * math.sin(clamp01((tl - 1.55) / .18) * math.pi), 0.72, 0, 1, 'bagw')
        place(fr, spr('stoolv'), sx, 877, 0.94, 0, 1, 'stool', shadow=(0.45, 0.3))
        sn = int(47 + (tl - 1.35) / .55 * 25)
        sm = smoke(min(72, max(47, sn)))
        if sm is not None and tl > 1.58:
            sa = min(1, (tl - 1.58) / .12) * 0.85
            scl = 0.85 + 0.3 * seg(tl, 1.6, .3, lin)
            smi = cv2.resize(sm, (int(sm.shape[1] * scl), int(sm.shape[0] * scl)))
            rgba = np.dstack([np.full((smi.shape[0], smi.shape[1], 3), 150, np.uint8), np.clip(smi.astype(np.float32) * 3.0, 0, 255).astype(np.uint8)])
            place(fr, rgba, 108, 410, 0, 0, sa, key=None, blur=False)
            place(fr, rgba, 634, 512, 0, 0, sa * .9, key=None, blur=False)
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        tx = 150 + 60 * eoC(seg(tl, 1.35, .2))
        ty = 150 - 60 * eoC(seg(tl, 1.35, .2))
        place_pil(pil, text_img('TWENTY', 36, RED, INK, 3), tx, ty, -78, 1)
        place_pil(pil, text_img('BILLION', 62, INK, (120, 118, 112), 6), 300, 120, -8, 1)
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'desat':
        fr = bg('desat').copy()
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        place_pil(pil, text_img('NO', 150, (240, 170, 170), (200, 130, 130), 8), 360, 700, 0, back(seg(tl, 2.45, .25)), min(1, seg(tl, 2.45, .18, lin) * 1.2) * 0.75)
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        place(fr, spr('bagvg'), 352, 749, 0.72, 0, 1)
        place(fr, spr('stoolvg'), 360, 877, 0.94, 0, 1, shadow=(0.45, 0.3))
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        place_pil(pil, text_img('HE SAID', 60, (200, 30, 40), INK, 5), 360, 420, 0, back(seg(tl, 2.05, .22)))
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'teal':
        fr = bg('teal').copy()
    elif sc == 'red':
        fr = bg('red').copy()
        ck = eoC(seg(tl, 3.25, .40))
        cx = 1080 - 648 * ck
        cy = 333 + 170 * ck
        rot = -35 + 27 * ck
        place(fr, spr('glove'), -160 + 310 * eoC(seg(tl, 3.40, .35)), 740, 1.0, 0, 1, 'glove')
        place(fr, spr('hand2'), 1080 - 560 * ck + 70, 400 + 370 * ck + 25, 0.9, rot, min(1, seg(tl, 3.55, .15, lin)), 'hand2')
        place(fr, spr('cash'), 1080 - 560 * ck, 400 + 370 * ck, 0.85, rot, 1, 'cash', shadow=(0.3, 0.22))
        lk = back(seg(tl, 3.55, .30))
        place(fr, spr('logo'), 160, 640, 0.4 + 0.5 * lk, 0, min(1, lk * 1.5), 'logo')
        gp = lk * (1 - lk) * 4
        if gp > 0.03:
            gg = np.zeros((H, W), np.float32)
            cv2.circle(gg, (160, 640), 90, 1.0, -1)
            gg = cv2.GaussianBlur(gg, (81, 81), 0) * gp * 0.5
            fr = np.clip(fr.astype(np.float32) + gg[..., None] * np.array((60, 200, 80), np.float32), 0, 255).astype(np.uint8)
        # native wireframe
        wa = 0.75 * min(1, seg(tl, 3.5, .2, lin))
        if wa > 0:
            ov = np.zeros((H, W), np.float32)
            cxy = (1080 - 560 * ck + 40, 400 + 370 * ck + 20)
            rr = 130 + 10 * math.sin(tl * 6)
            ay, ax = tl * 0.0, 0.0
            pts = []
            for i in range(6):
                an = tl * 0.9 + i * math.pi / 3
                pts.append((cxy[0] + rr * math.cos(an), cxy[1] + rr * 0.8 * math.sin(an)))
            cv2.polylines(ov, [np.array(pts, np.int32)], True, 1.0, 2)
            ov = cv2.GaussianBlur(ov, (3, 3), 0) * wa
            fr = np.clip(fr.astype(np.float32) + ov[..., None] * np.array((190, 180, 240), np.float32) * 0.8, 0, 255).astype(np.uint8)
        yk = seg(tl, 4.75, .85, lin)
        ndig = int(4 * yk + 0.999)
        if ndig > 0:
            pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
            place_pil(pil, text_img('2008'[:ndig], 95, BONE, (120, 118, 112), 5), 140 + ndig * 48, 80, 0, 1)
            fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'jen':
        fr = bg('jen').copy()
        zk = 1.0 + 0.12 * eoC(seg(tl, 6.0, 1.5))
        fr = cv2.resize(fr, (int(W * zk), int(H * zk)))[int((zk - 1) * H * .45):int((zk - 1) * H * .45) + H, int((zk - 1) * W / 2):int((zk - 1) * W / 2) + W]
        pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        place_pil(pil, text_img('2008', 100, (205, 202, 196), (120, 118, 112), 5), 400, 240, 0, 0.45)
        fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        jy = 1400 - 677 * eoC(seg(tl, 6.0, .5))
        js = spr('jen')
        js = js.copy()
        js[-30:, :, 3] = 255
        if js.shape[0] < 1000:
            pad = np.repeat(js[-1:, :, :], 320, 0)
            js = np.vstack([js, pad])
            SPR['jen'] = js
        place(fr, js, 360, jy, 0.95 * zk, 0, 1, 'jen')
        sk2 = back(seg(tl, 7.5, .28))
        if sk2 > 0:
            pw, ph = 420, 250
            plate = Image.new('RGBA', (pw + 26, ph + 26), (0, 0, 0, 0))
            d0 = ImageDraw.Draw(plate)
            d0.rounded_rectangle([0, 0, pw + 25, ph + 25], 16, fill=GOLD + (255,))
            f1 = font(FM, int(ph * 0.36)); f2 = font(FM, int(ph * 0.28))
            d0.text((16, 14), 'subscribe', font=f1, fill=INK + (255,))
            d0.text((16 + int(pw * 0.2), 14 + int(ph * 0.48)), '& like', font=f2, fill=INK + (230,))
            pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
            place_pil(pil, plate, 360, 1000, 0, min(1, sk2 * 1.4), 0.4 + 0.6 * sk2)
            fr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    elif sc == 'graded':
        e = min(int(t * 30), 696)
        f = cv2.imread('/tmp/rf/%04d.png' % (e + 1))
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.int16)
        hch, sch, vch = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        out = f.astype(np.float32)
        reg = np.zeros_like(hch, bool); reg[940:1130, 150:570] = True
        digreg = np.zeros_like(hch, bool); digreg[150:340, 40:680] = True
        digreg[200:340, 230:490] = False  # head occludes digits
        gl = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
        yel = reg & (((hch > 18) & (hch < 40) & (sch > 90)) | (gl > 130))
        w = cv2.GaussianBlur(yel.astype(np.float32), (7, 7), 0)[..., None]
        gold = np.array(bgr(GOLD), np.float32)
        out = out * (1 - w) + (out * 0.35 + gold * 0.65) * w
        txtm = reg & (gl > 185)
        wt = cv2.GaussianBlur(txtm.astype(np.float32), (5, 5), 0)[..., None] * 0.9
        out = out * (1 - wt) + np.array(bgr(INK), np.float32) * wt
        reg2 = np.zeros_like(gl, bool); reg2[150:330, 40:680] = True
        reg2[330:400, 40:240] = True; reg2[330:400, 480:680] = True
        reg2[150:340, 210:510] = False  # Jensen's head occludes the digits
        dig = reg2 & (gl > 100)
        wd = cv2.GaussianBlur(dig.astype(np.float32), (5, 5), 0)[..., None]
        wd = np.clip(wd * 1.2, 0, 1)
        out = out * (1 - wd) + np.array(bgr(INK), np.float32) * wd
        fr = out.clip(0, 255).astype(np.uint8)
        gk = min(1, seg(tl, 9.0, .6, lin) if tl < 11 else 1)
        if gk > 0:
            g = np.zeros((H, W), np.float32)
            for ex in (-60, 60):
                cv2.ellipse(g, (360 + ex, 392), (30, 16), 0, 0, 360, 1.0, -1)
            g = cv2.GaussianBlur(g, (21, 21), 0) * gk
            fr = np.clip(fr.astype(np.float32) + g[..., None] * np.array((30, 30, 255), np.float32) * 0.85, 0, 255).astype(np.uint8)
    # ---- grade: vignette + grain ----
    vig = (1 - 0.13 * (_r ** 2.2))[..., None]
    fr = (fr.astype(np.float32) * vig).clip(0, 255)
    grain = np.random.default_rng(n).normal(0, 1.1, (H, W, 1))
    fr = np.clip(fr + grain, 0, 255).astype(np.uint8)
    return fr

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'stills':
        for n in [int(x) for x in sys.argv[2].split(',')]:
            fr = render_frame(n * 2)
            cv2.imwrite(f'/tmp/v11_still_{n}.png', fr)
        print('stills ok')
        raise SystemExit
    cmd = [FF, '-y', '-hide_banner', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '60', '-i', '-',
           '-i', REF, '-map', '0:v', '-map', '1:a',
           '-vf', 'tmix=frames=2,fps=30',
           '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
           '-c:a', 'copy', '-movflags', '+faststart', 'deliverables/shorts/S01_monarch_20billion_v11.mp4']
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(NF):
        fr = render_frame(n)
        p.stdin.write(cv2.resize(fr, (1080, 1920), interpolation=cv2.INTER_LANCZOS4).tobytes())
        if n % 200 == 0:
            print('frame', n, flush=True)
    p.stdin.close(); p.wait()
    print('v11 master done')
