#!/usr/bin/env python3
"""S01 v10 - MONARCH themed reconstruction (fixed).
- pass-aware: video loops at 11.675s; effective frame e = n % 350 for scenes/masks/tracks
- PIL RGB color tuples (no BGR mixup)
- tight element alpha inside patches (color-distance vs old field) => no halo on recolored fields
- red field plate = frame 101 + small cash inpaint (perfect bars)
- y2008 track computed inline (bright digits)
Motion/animation identical to reference tracks; audio byte-identical copy.
"""
import numpy as np, cv2, subprocess, os, glob
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

OUT = '/tmp/v9'
V10 = '/tmp/v10'
os.makedirs(V10, exist_ok=True)
FF = open('/tmp/ffpath').read().strip()
REF = 'refs/ref-reels-tutorial.mp4'
W, H = 720, 1280
PASS = 350  # frames per loop (11.675s * 30)

# MONARCH tokens - RGB for PIL, BGR for cv2
INK, CARBON, BONE, RED, GOLD, BLOOD = (10, 10, 11), (38, 38, 42), (244, 241, 234), (255, 85, 96), (212, 175, 55), (160, 16, 32)
def bgr(c): return (c[2], c[1], c[0])

SCENES = [('stamp', 0.0, 0.43), ('black', 0.43, 0.60), ('green', 0.60, 1.35),
          ('white', 1.35, 1.90), ('desat', 1.90, 3.00), ('teal', 3.00, 3.25),
          ('red', 3.25, 5.90), ('jen', 5.90, 9.00), ('graded', 9.00, 11.675)]
def scene_of(n):
    t = (n / 30.0) % 11.675
    for name, a, b in SCENES:
        if a <= t < b:
            return name, t
    return 'graded', t
def eff(n):
    return n % PASS

# ---------- field plates (recolored) ----------
TARGET = {'stamp': (INK, 0.5), 'green': ((24, 44, 20), 0.55), 'white': (BONE, 0.5),
          'desat': ((216, 211, 200), 0.5), 'teal': (BLOOD, 0.7), 'red': (BLOOD, 1.15),
          'jen': (None, 1.0), 'black': (INK, 1.0)}
OLD = {}
fields = {}
FR = {}
for name, _, _ in SCENES:
    if name == 'red':
        acc = [cv2.imread('/tmp/rf/%04d.png' % (nn + 1)) for nn in range(112, 177, 4)]
        pl = np.median(np.stack(acc), 0).astype(np.uint8)
        m = np.zeros((H, W), np.uint8)
        m[430:800, 380:720] = 255   # settled cash+wires
        m[640:960, 0:300] = 255    # glove
        m[560:760, 80:300] = 255   # logo
        pl = cv2.inpaint(pl, m, 12, cv2.INPAINT_TELEA)
    else:
        pp = f'{OUT}/plates/field_{name}.png'
        if not os.path.exists(pp):
            pp = f'{OUT}/plates/{name}.png'
        pl = cv2.imread(pp)
        if pl is None:
            pl = np.full((H, W, 3), 10, np.uint8)
    OLD[name] = pl.astype(np.float32)
    tgt, sc = TARGET.get(name, (None, 1.0))
    if tgt is None:
        fields[name] = pl
        FR[name] = None
    else:
        mf = pl.astype(np.float32).mean((0, 1)); sf = pl.astype(np.float32).std((0, 1)) + 1e-3
        k = sf * sc / sf
        new = ((pl.astype(np.float32) - mf) * k + np.array(bgr(tgt), np.float32)).clip(0, 255)
        fields[name] = new.astype(np.uint8)
        FR[name] = (mf, k, np.array(bgr(tgt), np.float32))
    cv2.imwrite(f'{V10}/field_{name}.png', fields[name])
print('fields ok')

A = np.load(f'{OUT}/aff3.npz')
AFF = {int(n): w.reshape(2, 3) for n, w in zip(A['n'], A['a'])}
_RP = None
def red_shift(n):
    global _RP
    if _RP is None:
        _RP = cv2.cvtColor(fields['red'], cv2.COLOR_BGR2GRAY)[88:352, 28:308]
    g = cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY)
    roi = g[76:364, 16:320]
    r = cv2.matchTemplate(roi, _RP, cv2.TM_CCOEFF_NORMED)
    _, mv, _, mx = cv2.minMaxLoc(r)
    if mv < 0.5:
        return 0, 0
    return mx[0] - 12, mx[1] - 12
def aff_of(n):
    e = eff(n)
    M = AFF.get(e, np.eye(2, 3, dtype=np.float32)).copy()
    if 98 <= e < 177:
        dx, dy = red_shift(e)
        M[0, 2] += dx; M[1, 2] += dy
    return M

FA = 'assets/fonts/Anton-Regular.ttf'
FM = 'assets/fonts/Manrope-800.ttf'
_fc = {}
def font(p, sz):
    k = (p, int(sz))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(p, max(8, int(sz)))
    return _fc[k]

def text_layer(txt, sz, face, side=None, depth=0, fpath=FA, spacing=0):
    f = font(fpath, sz)
    lines = txt.split('\n')
    hs = []
    ws = []
    for ln in lines:
        b = f.getbbox(ln)
        ws.append(b[2] - b[0]); hs.append(b[3] - b[1])
    w = max(ws) + depth * 2 + 10
    h = sum(hs) + spacing * (len(lines) - 1) + depth * 2 + 10
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = depth + 5
    for ln, hh in zip(lines, hs):
        if side and depth:
            for kk in range(depth, 0, -1):
                d.text((depth + 5 - kk * 0.7, y + kk * 0.9), ln, font=f, fill=side + (255,))
        d.text((depth + 5, y), ln, font=f, fill=face + (255,))
        y += hh + spacing
    return im

def paste_center(fr, im, cx, cy, rot=0.0):
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    fr.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im.split()[3])

TR = np.load(f'{OUT}/tracks9.npz')
def bbox(key, n):
    e = eff(n)
    if key not in TR:
        return None
    a = TR[key]
    r = a[a[:, 0] == e]
    if len(r) == 0 or r[0, 1] != 1:
        return None
    return r[0, 2:6]

# y2008 track inline (jen scene both passes)
_y = {}
def bbox2008(n):
    e = eff(n)
    if e in _y:
        return _y[e]
    if not (177 <= e < 270):
        _y[e] = None
        return None
    f = cv2.imread('/tmp/rf/%04d.png' % (e + 1))
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    m = (g > 90).astype(np.uint8)
    Wm = np.zeros_like(m); Wm[20:400, 40:680] = 1
    m *= Wm
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(m)
    _y[e] = (xs.mean(), ys.mean(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) if len(xs) > 300 else None
    return _y[e]

def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))

per_frame = defaultdict(list)
for mp in glob.glob(OUT + '/masks/*_????.png'):
    base = os.path.basename(mp)[:-4]
    key, nn = base.rsplit('_', 1)
    per_frame[int(nn)].append(key)
PHOTO = {'bag', 'bagw', 'stool', 'smoke', 'smoked', 'cash', 'glove', 'logo', 'jen', 'glow'}
FULLMASK = {'red', 'jen'}
_mc = {}
def mask_of(key, e):
    k = (key, e)
    if k not in _mc:
        m = cv2.imread(f'{OUT}/masks/{key}_{e:04d}.png', 0)
        if m is not None and key.split('@')[0] in PHOTO:
            b = (m > 60).astype(np.uint8)
            ff = b.copy()
            cv2.floodFill(ff, None, (0, 0), 1)
            holes = (ff == 0).astype(np.uint8)
            b = np.maximum(b, holes)
            m = cv2.GaussianBlur((b * 255).astype(np.uint8), (7, 7), 0)
        _mc[k] = m
        if len(_mc) > 300:
            _mc.pop(next(iter(_mc)))
    return _mc[k]

def win_bill(n):
    t = (n / 30.0) % 11.675
    k = min(1, max(0, (t - .75) / .25)); k = k * k * (3 - 2 * k)
    return (400, 330 + 160 * (1 - k), 240, 80)
def win_tag(n):
    t = (n / 30.0) % 11.675
    return (185, 260, 80, 140) if t < 1.35 else (288, 166, 80, 140)
TEXTW = {'green': (win_bill, win_tag), 'white': (win_bill, win_tag),
         'desat': (lambda n: (158, 295, 110, 60), lambda n: (245, 295, 110, 60), lambda n: (209, 410, 140, 80))}
def text_mask(sc, e, f, oldg):
    if sc not in TEXTW:
        return None
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    m = np.zeros((H, W), np.float32)
    for wn in TEXTW[sc]:
        cx, cy, hw, hh = wn(e)
        x0, x1 = max(0, int(cx - hw - 30)), min(W, int(cx + hw + 30))
        y0, y1 = max(0, int(cy - hh - 30)), min(H, int(cy + hh + 30))
        sub = (oldg[y0:y1, x0:x1] - g[y0:y1, x0:x1]) > 50
        m[y0:y1, x0:x1] = np.maximum(m[y0:y1, x0:x1], sub)
    return cv2.GaussianBlur(m, (5, 5), 0)

CAP = 0.72
SZ = {'stamp': (94, 139), 'btext': (94, 139), 'bill': 103, 'tag': 62, 'he': 80, 'said': 64,
      'no': 170, 'y2008': 260, 'sub': (420, 260)}
def popscale(key, n, default=1.0):
    e = eff(n)
    if key not in TR:
        return default
    a = TR[key]; v = a[a[:, 1] == 1]
    if len(v) < 6:
        return default
    sh = float(np.median(v[-5:, 5]))
    r = a[a[:, 0] == e]
    if len(r) == 0 or r[0, 1] != 1:
        return default
    return 1.0 if 'sub' not in key else min(1.15, max(0.15, float(r[0, 5]) / sh))

def draw_text(fr, n, sc):
    def put(key, txt, face, side, depth, rot=0.0, fpath=FA, spacing=0):
        bb = bbox(key, n)
        if bb is None:
            return
        cx, cy, w, h = bb
        probe = text_layer(txt, 100, face, side, 0, fpath, spacing)
        w0, h0 = probe.width, probe.height
        tgt = h if abs(rot) > 45 else w
        base = w0 if abs(rot) > 45 or '\n' not in txt else w0
        sz = 100.0 * tgt / (h0 if abs(rot) > 45 and '\n' in txt else (w0 if abs(rot) <= 45 else h0)) if False else 100.0 * tgt / (w0 if abs(rot) <= 45 else h0)
        sz = min(sz, 100.0 * (h * 1.35) / h0)
        im = text_layer(txt, sz, face, side, depth, fpath, spacing)
        paste_center(fr, im, cx, cy, rot)
    def fixed(key, txt, face, side, depth, szs, rot=0.0, spacing=0, pos=None):
        bb = pos or bbox(key, n)
        if bb is None:
            return
        cx, cy = bb[0], bb[1]
        if isinstance(szs, tuple):
            lines = txt.split('\n')
            im = None
            layers = []
            for ln, sz in zip(lines, szs):
                layers.append(text_layer(ln, sz * popscale(key, n), face, side, depth, FA, 0))
            wmax = max(l.width for l in layers)
            htot = sum(l.height for l in layers) + 8 * (len(layers) - 1)
            im = Image.new('RGBA', (wmax, htot), (0, 0, 0, 0))
            y = 0
            for l in layers:
                im.paste(l, ((wmax - l.width) // 2, y), l)
                y += l.height + 8
        else:
            im = text_layer(txt, szs * popscale(key, n), face, side, depth, FA, spacing)
        paste_center(fr, im, cx, cy, rot)
    if sc == 'stamp':
        t = (n / 30.0) % 11.675
        k = min(1.0, max(0.0, t / .30)); k = k * k * (3 - 2 * k)
        bb = bbox('stamp@stamp', n)
        pos = (bb[0], bb[1]) if bb is not None else (360, 300)
        fixed('stamp@stamp', 'TWENTY\nBILLION', GOLD, INK, 6, (54 * (0.4 + 0.6 * k), 74 * (0.4 + 0.6 * k)), -6, 8, pos)
    elif sc == 'black':
        fixed('btext@black', 'TWENTY\nBILLION', BONE, RED, 8, SZ['btext'], 0, 8, (360, 420))
    elif sc == 'green':
        fixed('bill@green', 'BILLION', BONE, INK, 7, SZ['bill'], -6)
        fixed('tag@green', 'TWENTY', RED, INK, 5, SZ['tag'], -78)
    elif sc == 'white':
        fixed('billw@white', 'BILLION', BONE, INK, 7, SZ['bill'], -6)
        fixed('tagw@white', 'TWENTY', RED, INK, 5, SZ['tag'], -78)
    elif sc == 'desat':
        fixed('he@desat', 'HE', GOLD, INK, 5, SZ['he'])
        fixed('said@desat', 'SAID', GOLD, INK, 5, SZ['said'])
        fixed('no@desat', 'NO', RED, INK, 8, SZ['no'])
    elif sc == 'jen':
        bb = bbox('sub@jen', n)
        if bb is not None:
            cx, cy, w, h = bb
            pw, ph = SZ['sub']
            plate = Image.new('RGBA', (pw + 26, ph + 26), (0, 0, 0, 0))
            d = ImageDraw.Draw(plate)
            d.rounded_rectangle([0, 0, pw + 25, ph + 25], 14, fill=GOLD + (255,))
            f1 = font(FM, int(ph * 0.40)); f2 = font(FM, int(ph * 0.32))
            d.text((13, 9), 'subscribe', font=f1, fill=INK + (255,))
            d.text((13 + int(pw * 0.20), 9 + int(ph * 0.50)), '& like', font=f2, fill=INK + (230,))
            paste_center(fr, plate, cx, cy)

def graded_recolor(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.int16)
    hch, sch, vch = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    out = f.astype(np.float32)
    reg = np.zeros_like(hch, bool); reg[940:1130, 150:570] = True
    gl = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16)
    yel = reg & (((hch > 18) & (hch < 40) & (sch > 90)) | (gl > 130))
    w = cv2.GaussianBlur(yel.astype(np.float32), (7, 7), 0)[..., None]
    gold = np.array(bgr(GOLD), np.float32)
    tgt = out * 0.35 + gold * 0.65
    out = out * (1 - w) + tgt * w
    txtm = reg & (cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16) > 185)
    wt = cv2.GaussianBlur(txtm.astype(np.float32), (5, 5), 0)[..., None] * 0.9
    out = out * (1 - wt) + np.array(bgr(INK), np.float32) * wt
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
    reg2 = np.zeros_like(g, bool); reg2[20:400, 40:680] = True
    dig = reg2 & (g > 90)
    w2 = cv2.GaussianBlur(dig.astype(np.float32), (5, 5), 0)[..., None] * 0.85
    tgt2 = out * 0.3 + gold * 0.7
    out = out * (1 - w2) + tgt2 * w2
    return out.clip(0, 255).astype(np.uint8)

NF = 698
cmd = [FF, '-y', '-hide_banner', '-loglevel', 'error',
       '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '30', '-i', '-',
       '-i', REF, '-map', '0:v', '-map', '1:a',
       '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
       '-c:a', 'copy', '-movflags', '+faststart', 'deliverables/shorts/S01_monarch_20billion_v10.mp4']
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for n in range(NF):
    sc, t = scene_of(n)
    e = eff(n)
    if sc == 'graded':
        comp = graded_recolor(F(n))
    elif sc == 'red':
        comp = F(n)
    elif sc == 'jen':
        comp = F(n)
        g = cv2.cvtColor(comp, cv2.COLOR_BGR2GRAY).astype(np.float32)
        reg = np.zeros_like(g, bool)
        reg[150:330, 40:680] = True
        reg[330:400, 40:240] = True
        reg[330:400, 480:680] = True
        dig = reg & (g > 100)
        wd = cv2.GaussianBlur(dig.astype(np.float32), (5, 5), 0)[..., None]
        wd = np.clip(wd * 1.2, 0, 1)
        comp = (comp.astype(np.float32) * (1 - wd) + np.array(bgr(INK), np.float32) * wd).clip(0, 255).astype(np.uint8)
        pil0 = Image.fromarray(cv2.cvtColor(comp, cv2.COLOR_BGR2RGB))
        bb = bbox2008(n)
        if bb:
            im = text_layer('2008', SZ['y2008'], GOLD, INK, 6)
            paste_center(pil0, im, bb[0], bb[1])
        bb = bbox('sub@jen', n)
        if bb is not None:
            cx, cy = 360, 990
            pw, ph = SZ['sub']
            plate = Image.new('RGBA', (pw + 26, ph + 26), (0, 0, 0, 0))
            d0 = ImageDraw.Draw(plate)
            d0.rounded_rectangle([0, 0, pw + 25, ph + 25], 14, fill=GOLD + (255,))
            f1 = font(FM, int(ph * 0.40)); f2 = font(FM, int(ph * 0.32))
            d0.text((13, 9), 'subscribe', font=f1, fill=INK + (255,))
            d0.text((13 + int(pw * 0.20), 9 + int(ph * 0.50)), '& like', font=f2, fill=INK + (230,))
            paste_center(pil0, plate, cx, cy)
        comp = cv2.cvtColor(np.array(pil0), cv2.COLOR_RGB2BGR)
    else:
        comp = cv2.warpAffine(fields[sc], aff_of(n), (W, H))
        f = F(n)
        oldf = OLD[sc]
        PATCH_SC = sc in ('green', 'white', 'desat')
        tmask = text_mask(sc, e, f, cv2.cvtColor(oldf, cv2.COLOR_BGR2GRAY).astype(np.int16))
        M = aff_of(n)
        oldcur = cv2.warpAffine(oldf, M, (W, H)) if sc == 'red' else oldf
        for key in sorted(per_frame.get(e, [])):
            nm = key.split('@')[0]
            if nm not in PHOTO or not PATCH_SC:
                continue
            m = mask_of(key, e)
            if m is None:
                continue
            ys, xs = np.nonzero(m)
            if len(xs) == 0:
                continue
            x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            mf = m[y0:y1, x0:x1].astype(np.float32) / 255.0
            if tmask is not None:
                mf = mf * (1 - tmask[y0:y1, x0:x1])
            px = f[y0:y1, x0:x1].astype(np.float32)
            of = oldcur[y0:y1, x0:x1]
            dist = np.abs(px - of).max(2)
            wr = np.clip(1.0 - (dist / 45.0) ** 2, 0, 1)
            wr = cv2.GaussianBlur(wr, (5, 5), 0)
            bgc = comp[y0:y1, x0:x1].astype(np.float32)
            inner = px * (1 - wr[..., None]) + bgc * wr[..., None]
            comp[y0:y1, x0:x1] = (inner * mf[..., None] + bgc * (1 - mf[..., None])).astype(np.uint8)
        pil = Image.fromarray(cv2.cvtColor(comp, cv2.COLOR_BGR2RGB))
        if sc == 'jen':
            bb = bbox2008(n)
            if bb:
                im = text_layer('2008', SZ['y2008'], GOLD, INK, 6)
                paste_center(pil, im, bb[0], bb[1])
            comp = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            for key in sorted(per_frame.get(e, [])):
                nm = key.split('@')[0]
                if nm not in PHOTO:
                    continue
                m = mask_of(key, e)
                if m is None:
                    continue
                ys, xs = np.nonzero(m)
                if len(xs) == 0:
                    continue
                x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
                mf2 = m[y0:y1, x0:x1].astype(np.float32) / 255.0
                px = f[y0:y1, x0:x1].astype(np.float32)
                dist = np.abs(px - oldf[y0:y1, x0:x1]).max(2)
                ael = np.clip((dist - 10.0) / 18.0, 0, 1)
                ael = cv2.GaussianBlur(ael, (3, 3), 0)
                a = (mf2 * ael)[..., None]
                bgc = comp[y0:y1, x0:x1].astype(np.float32)
                comp[y0:y1, x0:x1] = (px * a + bgc * (1 - a)).astype(np.uint8)
            pil = Image.fromarray(cv2.cvtColor(comp, cv2.COLOR_BGR2RGB))
        draw_text(pil, n, sc)
        comp = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    p.stdin.write(cv2.resize(comp, (1080, 1920), interpolation=cv2.INTER_LANCZOS4).tobytes())
p.stdin.close(); p.wait()
print('v10 master done')
