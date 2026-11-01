#!/usr/bin/env python3
"""S01 v4 — frame-exact grammar rebuild from REAL reference video
(refs/ref-reels-tutorial.mp4, 23.35s @720x1280, forensics 2026-11-01).
Systems decoded per-second and re-implemented with MONARCH swap:
  F1 flat color-field pops per micro-beat (paper/ink/gold/crimson-chevron)
  F2 chevron arrow pattern fields (darker tone zigzag columns)
  F3 3D EXTRUDED condensed type (depth sides + face, slide-in)
  F4 gravity drop w/ vertical motion-blur ghosts + bounce settle
  F5 selective desaturation grade lerp (color -> grayscale scene)
  F6 cartoon smoke puff clusters drifting at type height
  F7 prop fly-ins w/ thin white wireframe polygon outlines
  F8 digit-by-digit year type-in (last digit alpha fade)
  F9 subject cutout rise-from-bottom + slow push-in
  F10 caption plate stamp (gold MONARCH plate)
  F11 eye-glow red flare + full-frame desat/darken grade shift
  F12 white flash at hard cuts, shake on SFX hits
Audio muxed from v1 master (VO+bed+SFX).
"""
import math, os, subprocess, random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = ROOT + '/docs/shorts/s01'
FF = open('/tmp/ffpath').read().strip()
W, H, FPS = 1080, 1920, 30
DURS = [5, 5, 5, 4, 4, 4, 4, 4.16]
STARTS = []
_a = 0.0
for d in DURS:
    STARTS.append(_a); _a += d
NF = int(_a * FPS)
CX, CY = W // 2, H // 2

PAPER = (243, 241, 236)
INK = (17, 16, 16)
GOLD = (212, 175, 55)
GOLD_D = (146, 118, 32)
CRIM = (178, 16, 42)
CRIM_D = (128, 10, 30)
CRIM_F = (162, 14, 38)
WHITE = (248, 246, 242)

ANTON = ROOT + '/assets/fonts/Anton-Regular.ttf'
MONO = ROOT + '/assets/fonts/IBMPlexMono-400.ttf'
MANR = ROOT + '/assets/fonts/Manrope-700.ttf'
def anton(sz): return ImageFont.truetype(ANTON, int(sz))
def mono(sz): return ImageFont.truetype(MONO, int(sz))
def manr(sz): return ImageFont.truetype(MANR, int(sz))

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def eoc(t): t = clamp(t); return 1 - (1 - t) ** 3
def eob(t):
    t = clamp(t); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def eoi(t): t = clamp(t); return t * t

def load(p): return Image.open(p).convert('RGB')
sc1 = load(SC + '/sc1_moneybag.png'); sc3 = load(SC + '/sc3_refuse.png')
sc4 = load(SC + '/sc4_chip.png'); sc5 = load(SC + '/sc5_split.png')
PERS = load(ROOT + '/docs/lookdev/char.jpg')

def cropc(im, x0, y0, x1, y1):
    w, h = im.size
    return im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
def gray(im):
    return ImageOps.grayscale(im).convert('RGB')
def sil(im, bg, tol=26):
    from PIL import ImageChops
    im = im.convert('RGB')
    diff = ImageChops.difference(im, Image.new('RGB', im.size, bg)).convert('L')
    mask = diff.point(lambda q: 255 if q > tol else 0)
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    rgba = im.convert('RGBA'); rgba.putalpha(mask)
    return rgba

BAG_C = sil(load(SC + '/cut_bag.png'), (255, 255, 255), 24)
_g = ImageOps.grayscale(BAG_C.convert('RGB')).convert('RGBA'); _g.putalpha(BAG_C.getchannel('A')); BAG_G = _g
CASH = sil(load(SC + '/cut_cash.png'), (255, 255, 255), 24)
HAND_G = gray(cropc(sc3, 0.22, 0.12, 0.82, 0.88))
CHIP_C = sil(cropc(load(SC + '/cut_chip.png'), 0.30, 0.04, 0.70, 0.96), (0, 0, 0), 24)
CROWD_G = gray(cropc(sc5, 0.0, 0.30, 0.50, 0.62))
PERS_C = sil(load(SC + '/cut_perso.png'), (255, 255, 255), 24)


# ---------- primitives ----------
def paste(fr, im, x, y, scale=1.0, rot=0.0, alpha=1.0):
    if alpha <= 0 or scale <= 0.01: return
    w = max(1, int(im.width * scale)); h = max(1, int(im.height * scale))
    im2 = im.resize((w, h))
    if rot: im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
    im2 = im2.convert('RGBA')
    if alpha < 1: im2.putalpha(im2.getchannel('A').point(lambda p: int(p * alpha)))
    fr.paste(im2, (int(x - im2.width / 2), int(y - im2.height / 2)), im2)

def text_im(txt, font, fill):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    bb = d.textbbox((0, 0), txt, font=font)
    im = Image.new('RGBA', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=font, fill=fill)
    return im

def extrude(fr, txt, sz, x, y, face, side, tl, t0, depth=14, rot=0.0, dur=0.34, dx0=-520, fontf=anton):
    """F3 3D extruded type slide-in"""
    if tl < t0: return
    k = eoc((tl - t0) / dur)
    xx = x + dx0 * (1 - k)
    im = text_im(txt, fontf(sz), face + (255,))
    lay = Image.new('RGBA', (im.width + depth * 2 + 4, im.height + depth * 2 + 4), (0, 0, 0, 0))
    for d in range(depth, 0, -1):
        lay.paste(Image.new('RGBA', im.size, side + (255,)), (2 + depth - d, 2 + d), im)
    lay.paste(im, (2 + depth, 2), im)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    paste(fr, lay, xx, y, alpha=clamp((tl - t0) / .12))

def field(fr, color):
    fr.paste(Image.new('RGB', (W, H), color), (0, 0))

def chevron(fr, base, dark, t, drift=0.0):
    """F2 chevron arrow pattern field"""
    field(fr, base)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    step = 260; th = 110
    for ci, cxr in enumerate((0.22, 0.5, 0.78)):
        x = int(W * cxr); al = 70 if ci == 1 else 110
        y = -260 + int(drift * 40) % 260 - 260
        while y < H + 200:
            d.polygon([(x - 190, y + th), (x, y), (x + 190, y + th), (x + 190, y + th + 90),
                       (x, y + 90), (x - 190, y + th + 90)], fill=dark + (al,))
            y += step
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), ov).convert('RGB'), (0, 0))

PUFF = None
def smoke_puffs(fr, t, alpha=150, ybase=520, tint=(150, 148, 146)):
    """F6 cartoon puff clusters both sides"""
    global PUFF
    if PUFF is None:
        rnd = random.Random(5)
        PUFF = Image.new('RGBA', (420, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(PUFF)
        for i in range(9):
            x = 60 + i * 36 + rnd.uniform(-14, 14); y = 150 - math.sin(i / 8 * math.pi) * 90 + rnd.uniform(-10, 10)
            r = rnd.uniform(38, 66)
            d.ellipse([x - r, y - r, x + r, y + r], fill=tint + (255,))
        PUFF = PUFF.filter(ImageFilter.GaussianBlur(6))
    for sx, ph in ((-1, 0), (1, 2.1)):
        x = CX + sx * (430 + 26 * math.sin(t * .7 + ph))
        y = ybase + 18 * math.sin(t * .9 + ph)
        paste(fr, PUFF, x, y, alpha=alpha / 255, rot=sx * 4)

def wireframe(fr, x, y, w, h, rot=0.0, alpha=210):
    """F7 thin white wireframe polygon around prop"""
    rnd = random.Random(int(w + h))
    pts = []
    for i in range(9):
        ang = i / 9 * 2 * math.pi
        rr = 0.5 + rnd.uniform(-0.10, 0.14)
        pts.append((int(round(x + math.cos(ang) * w * rr)), int(round(y + math.sin(ang) * h * rr))))
    d = ImageDraw.Draw(fr)
    d.line(pts + [pts[0]], fill=WHITE + (alpha,) if len(WHITE) == 3 else WHITE, width=3)
    for i in (1, 4, 7):
        d.line([pts[i], pts[(i + 4) % 9]], fill=WHITE, width=2)

def digits_typein(fr, txt, sz, x, y, tl, t0, fill, per=0.22, fontf=anton):
    """F8 digit-by-digit type-in, last digit fades"""
    if tl < t0: return
    n = int((tl - t0) / per) + 1
    show = txt[:min(n, len(txt))]
    im = text_im(show, fontf(sz), fill + (255,))
    paste(fr, im, x - (len(txt) - len(show)) * sz * 0.28, y)
    if n <= len(txt):
        k = clamp(((tl - t0) % per) / per)
        im2 = text_im(txt[min(n - 1, len(txt) - 1):n], fontf(sz), fill + (255,))
        paste(fr, im2, x - (len(txt) - n) * sz * 0.28 + sz * 0.28, y, alpha=k)

def drop_blur(fr, im, x, y, vy, scale=1.0):
    """F4 gravity drop w/ motion-blur ghosts"""
    if vy > 900:
        for g, al in ((0.05, .35), (0.10, .22), (0.16, .12)):
            paste(fr, im, x, y - vy * g, scale=scale, alpha=al)
    paste(fr, im, x, y, scale=scale)

def desat(fr, k, dark=1.0):
    """F5/F11 grade lerp"""
    if k <= 0: return fr
    g = ImageOps.grayscale(fr).convert('RGB')
    out = Image.blend(fr, g, clamp(k))
    if dark < 1: out = ImageEnhance.Brightness(out).enhance(dark)
    return out

def stool(fr, x, y, w=340):
    d = ImageDraw.Draw(fr)
    br = (122, 84, 52)
    d.ellipse([x - w / 2, y - 26, x + w / 2, y + 26], fill=br)
    d.ellipse([x - w / 2, y - 34, x + w / 2, y + 18], fill=(146, 102, 64))
    for lx in (-w * 0.36, 0, w * 0.36):
        d.polygon([(x + lx - 12, y + 16), (x + lx + 12, y + 16), (x + lx * 1.25 + 8, y + 250), (x + lx * 1.25 - 8, y + 250)], fill=(96, 66, 40))

def plate(fr, txt, x, y, tl, t0, w=320, hgt=76):
    if tl < t0: return
    k = eob((tl - t0) / .3)
    im = Image.new('RGBA', (w, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, hgt - 1], 10, fill=GOLD + (255,))
    tw = text_im(txt, mono(34), INK + (255,))
    im.paste(tw, ((w - tw.width) // 2, (hgt - tw.height) // 2), tw)
    paste(fr, im, x, y, scale=.55 + .45 * k, rot=-3 + 3 * eoc((tl - t0) / .3), alpha=clamp((tl - t0) / .12))

def eyeglow(fr, x, y, spread, k):
    """F11 red eye flare"""
    if k <= 0: return
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for ex in (-spread / 2, spread / 2):
        d.ellipse([int(x + ex - 90), int(y - 60), int(x + ex + 90), int(y + 60)], fill=(255, 40, 40, int(150 * k)))
    g = g.filter(ImageFilter.GaussianBlur(46))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

HITS = [0.45, 0.95, 1.45, 2.1, 2.7, 5.0, 6.0, 6.8, 8.2, 10.0, 11.3, 15.0, 19.0, 20.4, 23.0, 27.0, 31.0, 31.9]
def shake_amt(t):
    for h in HITS:
        dt = t - h
        if 0 <= dt < .3: return (1 - dt / .3) * 13
    return 0
FLASHES = [0.45, 0.95, 1.45, 5.0, 11.3, 15.0, 19.0, 23.0, 27.0, 31.0]

# ---------- timeline ----------
def render_frame(fno):
    t = fno / FPS
    fr = Image.new('RGB', (W, H), INK)
    push = 1.0
    # ---- b0 0-5 : word pops -> bag drop -> desat -> NAHI stack
    if t < 5:
        if t < 0.45:
            field(fr, PAPER)
            extrude(fr, '20 BILLION', 150, CX, 620, CRIM, CRIM_D, t, 0.02, dx0=-620)
        elif t < 0.95:
            field(fr, INK)
            extrude(fr, '20 BILLION', 150, CX, 620, GOLD, GOLD_D, t, 0.0, dur=0.01, dx0=0)
        elif t < 1.45:
            field(fr, GOLD)
            extrude(fr, 'BILLION', 190, CX, 430, INK, (60, 48, 14), t, 0.0, dur=0.01, dx0=0)
            tag = text_im('TWENTY', anton(64), INK + (255,))
            paste(fr, tag, CX - 190, 640, rot=78)
            k = eob(clamp((t - 0.95) / .4))
            paste(fr, BAG_C, CX, 1150, scale=.9 * (.7 + .3 * k), rot=-4 + 4 * k)
        else:
            tl = t - 1.45
            field(fr, PAPER)
            # bag gravity drop onto stool
            fall = 0.38
            if tl < fall:
                p = eoi(tl / fall); y = 500 + (1150 - 500) * p
                drop_blur(fr, BAG_C, CX, y, vy=2400 * (tl / fall), scale=.92)
                stool(fr, CX, 1420, alpha=None) if False else stool(fr, CX, 1420)
            else:
                b = 1 + .12 * math.sin((tl - fall) * 14) * math.exp(-(tl - fall) * 5)
                stool(fr, CX, 1420)
                paste(fr, BAG_G, CX, 1150, scale=.92 * b)
            dk = clamp((tl - 0.65) / .3)
            if dk > 0:
                fr = desat(fr, dk)
                smoke_puffs(fr, t, alpha=170, ybase=560)
                extrude(fr, 'US NE KAHA', 84, CX, 430, CRIM, CRIM_D, tl, 0.65, depth=8, dx0=0, dur=0.2)
            if tl > 1.25:
                k = clamp((tl - 1.25) / .3)
                im = text_im('NAHI.', anton(300), (int(178 + 70 * (1 - k)), int(16 + 60 * (1 - k)), int(42 + 60 * (1 - k)), 255))
                paste(fr, im, CX, 700, scale=1.25 - .25 * eob(k))
            push = 1 + .05 * eoi(tl / 3.5)
    # ---- b1 5-10 : crimson chevron + props fly + 2008 + persona rise + plate
    elif t < 10:
        tl = t - 5
        chevron(fr, CRIM_F, CRIM_D, t, drift=t * .3)
        if tl > 0.15:
            k = eoc((tl - .15) / .45)
            px = W + 300 - (W + 300 - 760) * k
            paste(fr, CASH, px, 1080, scale=0.55, rot=-24 + 24 * k)
            if k >= 1: wireframe(fr, 760, 1080, 250, 120)
        if tl > 0.35:
            k = eoc((tl - .35) / .45)
            lx = -300 + 600 * k
            cr = Image.new('RGBA', (200, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(cr)
            d.rounded_rectangle([0, 0, 199, 139], 18, fill=GOLD + (255,))
            d.polygon([(40, 100), (40, 48), (70, 74), (100, 34), (130, 74), (160, 48), (160, 100)], fill=CRIM)
            paste(fr, cr, lx, 980, scale=1.25, rot=18 - 18 * k)
            if k >= 1: wireframe(fr, 300, 980, 160, 120)
        digits_typein(fr, '2008', 210, CX, 420, tl, 1.0, WHITE)
        if tl > 1.8:
            k = eoc((tl - 1.8) / .7)
            paste(fr, PERS_C, CX, 1240 + (1 - k) * 900, scale=1.0 + .10 * eoi((tl - 1.8) / 3.2))
        plate(fr, 'CEO — NVIDIA', CX, 1640, tl, 3.2)
        push = 1 + .04 * eoi(tl / 5)
    # ---- b2 10-15 : eye-glow grade shift hold -> paper field MANA stack
    elif t < 15:
        tl = t - 10
        if tl < 1.3:
            chevron(fr, CRIM_F, CRIM_D, t, drift=t * .3)
            digits_typein(fr, '2008', 210, CX, 420, 99, 0.0, WHITE)
            paste(fr, PERS_C, CX, 1240, scale=1.10 + .03 * eoi(tl / 1.3))
            plate(fr, 'CEO — NVIDIA', CX, 1640, 99, 0.0)
            gk = clamp(tl / .3)
            fr = desat(fr, .65 * gk, dark=1 - .18 * gk)
            eyeglow(fr, CX, 1010, 210, gk)
            push = 1 + .02 * eoi(tl / 1.3)
        else:
            tl2 = tl - 1.3
            field(fr, PAPER)
            smoke_puffs(fr, t, alpha=160, ybase=520)
            extrude(fr, 'OFFER', 110, CX, 430, CRIM, CRIM_D, tl2, 0.05, depth=10, dx0=0, dur=0.22)
            extrude(fr, 'MANA.', 260, CX, 680, CRIM, CRIM_D, tl2, 0.3, dx0=0)
            if tl2 > 0.5:
                k = eoc((tl2 - .5) / .7)
                bx = CX + 760 * k; by = 1260 - 620 * k
                paste(fr, BAG_C, bx, by, scale=.6, rot=-34 * k)
                if k < 1: wireframe(fr, bx, by, 210, 210)
            if tl2 > 2.0:
                d = ImageDraw.Draw(fr); p = eoc((tl2 - 2.0) / .4)
                d.line([CX - 260, 1000, int(CX - 260 + 520 * p), int(950 + 60 * p)], fill=CRIM, width=16)
            push = 1 + .04 * eoi(tl2 / 3.7)
    # ---- b3 15-19 : gold chevron + chip fly + YAQEEN
    elif t < 19:
        tl = t - 15
        chevron(fr, GOLD, GOLD_D, t, drift=t * .25)
        if tl > 0.2:
            k = eoc((tl - .2) / .5)
            cxx = W + 300 - (W + 300 - CX) * k
            paste(fr, CHIP_C, cxx, 1250, scale=0.62, rot=30 - 30 * k)
            if k >= 1: wireframe(fr, CX, 1250, 260, 260)
        extrude(fr, 'APNE CHIP PAR', 76, CX, 430, INK, (60, 48, 14), tl, 0.35, depth=8, dx0=0, dur=0.22)
        extrude(fr, 'YAQEEN.', 220, CX, 660, INK, (60, 48, 14), tl, 0.6, dx0=0)
        if tl > 2.2:
            d = ImageDraw.Draw(fr)
            for i in range(6):
                tt = tl - 2.2 - i * .16
                if tt > 0:
                    r = 13 + 6 * math.sin(t * 5 + i)
                    d.ellipse([int(CX - 160 + i * 64 - r), int(1660 - r), int(CX - 160 + i * 64 + r), int(1660 + r)], fill=CRIM)
        push = 1 + .05 * eoi(tl / 4)
    # ---- b4 19-23 : ink field $20B cross + EMPIRE + crowd rise
    elif t < 23:
        tl = t - 19
        field(fr, INK)
        extrude(fr, '$20B', 200, CX - 40, 560, WHITE, (120, 118, 114), tl, 0.1, dx0=0)
        if tl > 0.7:
            d = ImageDraw.Draw(fr); p = eoc((tl - .7) / .35)
            d.line([CX - 260, 460, int(CX - 260 + 420 * p), int(460 + 200 * p)], fill=CRIM, width=18)
            d.line([CX + 160, 460, int(CX + 160 - 420 * p), int(460 + 200 * p)], fill=CRIM, width=18)
        extrude(fr, 'EMPIRE.', 230, CX, 900, CRIM, CRIM_D, tl, 1.4, dx0=0)
        if tl > 2.2:
            k = eoc((tl - 2.2) / .7)
            paste(fr, CROWD_G, CX, 1620 + (1 - k) * 700, scale=1.0)
        push = 1 + .04 * eoi(tl / 4)
    # ---- b5 23-27 : crimson chevron + $ type-in + graph
    elif t < 27:
        tl = t - 23
        chevron(fr, CRIM_F, CRIM_D, t, drift=t * .3)
        digits_typein(fr, '$3.00T', 240, CX, 480, tl, 0.25, GOLD, per=0.2)
        d = ImageDraw.Draw(fr)
        pts = [(int(CX - 360 + i * 120), int(1560 - (i ** 2.1) * 28)) for i in range(7)]
        n = int(7 * clamp((tl - 1.6) / 1.6))
        for i in range(max(1, n)):
            if i: d.line([pts[i - 1], pts[i]], fill=GOLD, width=10)
            d.ellipse([pts[i][0] - 12, pts[i][1] - 12, pts[i][0] + 12, pts[i][1] + 12], fill=WHITE)
        if tl > 3.2:
            tw = text_im('NASDAQ: NVDA', mono(44), WHITE + (255,))
            paste(fr, tw, CX, 1800, alpha=clamp((tl - 3.2) / .3))
        push = 1 + .04 * eoi(tl / 4)
    # ---- b6 27-31 : paper field footnote
    elif t < 31:
        tl = t - 27
        field(fr, PAPER)
        smoke_puffs(fr, t, alpha=150, ybase=500)
        extrude(fr, 'AB YEHI SIRF', 84, CX, 430, CRIM, CRIM_D, tl, 0.1, depth=8, dx0=0, dur=0.22)
        extrude(fr, 'FOOTNOTE.', 200, CX, 660, CRIM, CRIM_D, tl, 0.35, dx0=0)
        if tl > 1.2:
            tw = text_im('$20,000,000,000', mono(46), INK + (255,))
            paste(fr, tw, CX, 1150, alpha=clamp((tl - 1.2) / .3))
        if tl > 2.0:
            d = ImageDraw.Draw(fr); p = clamp((tl - 2.0) / .8)
            d.arc([CX - 300, 1080, CX + 300, 1220], start=-40, end=-40 + 360 * p, fill=CRIM, width=10)
        if tl > 3.0:
            tw = text_im('footnote 7, page 3', mono(40), (96, 92, 88, 255))
            paste(fr, tw, CX, 1310, alpha=clamp((tl - 3.0) / .3))
        push = 1 + .03 * eoi(tl / 4)
    # ---- b7 31-34.16 : end card
    else:
        tl = t - 31
        field(fr, INK)
        if tl > 0.1:
            k = eob((tl - .1) / .5)
            paste(fr, PERS_C, CX, 950 + (1 - k) * 700, scale=.62)
        if tl > 0.5:
            d = ImageDraw.Draw(fr); k = eob((tl - .5) / .35)
            cw = int(130 * k); ch = int(95 * k)
            d.polygon([(CX - cw, 500), (CX - cw, 500 - int(ch * .7)), (CX - cw // 2, 500 - int(ch * .35)),
                       (CX - cw // 6, 500 - ch), (CX, 500 - int(ch * .4)), (CX + cw // 6, 500 - ch),
                       (CX + cw // 2, 500 - int(ch * .35)), (CX + cw, 500 - int(ch * .7)), (CX + cw, 500)], fill=CRIM)
        extrude(fr, 'MONARCH RULE:', 100, CX, 1420, GOLD, GOLD_D, tl, 0.9, depth=10, dx0=0, dur=0.3)
        if tl > 1.5:
            tw = text_im('Vision chhota ho toh', manr(46), WHITE + (255,))
            paste(fr, tw, CX, 1560, alpha=clamp((tl - 1.5) / .25))
        if tl > 1.9:
            tw = text_im('deal badi lagti hai.', manr(46), CRIM + (255,))
            paste(fr, tw, CX, 1640, alpha=clamp((tl - 1.9) / .25))
        push = 1 + .03 * eoi(tl / 3.1)
    # ---- global: push, shake, flash
    if push != 1.0:
        w2, h2 = int(W * push), int(H * push)
        im2 = fr.resize((w2, h2))
        fr = im2.crop(((w2 - W) // 2, (h2 - H) // 2, (w2 + W) // 2, (h2 + H) // 2))
    sh = shake_amt(t)
    if sh:
        dx = math.sin(t * 71) * sh; dy = math.cos(t * 63) * sh
        fr = fr.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=INK)
    for f in FLASHES:
        dt = t - f
        if 0 <= dt < 0.09:
            fr = Image.blend(fr, Image.new('RGB', (W, H), WHITE), 0.5 * (1 - dt / 0.09))
    return fr

OUT = ROOT + '/deliverables/shorts/S01_monarch_20billion_v4.mp4'
WEB = ROOT + '/deliverables/shorts/S01_monarch_20billion_v4_web.mp4'
proc = subprocess.Popen([FF, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                         '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
                         '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for fno in range(NF):
    proc.stdin.write(render_frame(fno).tobytes())
proc.stdin.close(); proc.wait()
subprocess.run([FF, '-y', '-i', OUT, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-preset', 'slow', '-crf', '27',
                '-pix_fmt', 'yuv420p', '-an', WEB], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
V1 = ROOT + '/deliverables/shorts/S01_monarch_20billion.mp4'
for src, dst in ((OUT, OUT), (WEB, WEB)):
    tmp = dst + '.mux.mp4'
    subprocess.run([FF, '-y', '-i', src, '-i', V1, '-map', '0:v', '-map', '1:a', '-c', 'copy', '-shortest', tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, dst)
print('DONE v4', os.path.getsize(WEB))
