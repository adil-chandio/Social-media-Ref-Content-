#!/usr/bin/env python3
"""S01 v5 — EXACT replica of reference edit (refs/ref-reels-tutorial.mp4, 23.35s).
Event timeline measured at 4fps forensic (see docs/shorts/s01/forensics-v3.md):
 pass = 11.67s loop, played twice (pass2 offset 11.67).
 0.00 white field + radial glow, TWENTY stamp
 0.43 cut black field: TWENTY-extruded + BILLION slide-in
 0.60 cut gold field (dark->bright ramp): BILLION black top + rotated TWENTY tag,
      bag rises from bottom w/ motion blur
 1.35 field -> white; stool rises in; bag lands w/ bounce; smoke puffs in
 1.90 desat ramp -> grayscale; 2.05 HE; 2.20 SAID pink->red; 2.45 NO pink->red+scale
 3.00 cut teal chevron field (0.25s)
 3.25 cut crimson chevron: cash fly-in rot + wireframe; glove hand slide; logo pop + wireframe
 4.75 digit-by-digit 2008 (per-digit fade)
 6.00 persona cutout rise + push-in; 7.50 plate stamp; 9.00 grade shift
      (desat+darken+eye-glow ramp .4s); hold slow push to 11.67
Audio = reference original track verbatim (SFX+music).
MONARCH swaps: lime->gold, red->crimson, yellow plate->gold, Jensen->masked persona,
nvidia logo->crown plate. Everything else 1:1.
"""
import math, os, subprocess, random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageOps, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = ROOT + '/docs/shorts/s01'
FF = open('/tmp/ffpath').read().strip()
W, H, FPS = 1080, 1920, 30
PASS = 11.67
NF = int(23.35 * FPS)
CX, CY = W // 2, H // 2

WHITE = (246, 244, 240)
BLACK = (14, 13, 13)
GOLD = (172, 142, 34)
GOLD_B = (206, 172, 44)
GOLD_D = (120, 98, 22)
CRIM = (186, 14, 40)
CRIM_D = (126, 8, 26)
CRIM_F = (168, 12, 34)
TEAL = (38, 178, 178)
TEAL_L = (86, 205, 202)
INK = (12, 11, 11)

ANTON = ROOT + '/assets/fonts/Anton-Regular.ttf'
MONO = ROOT + '/assets/fonts/IBMPlexMono-400.ttf'
def anton(sz): return ImageFont.truetype(ANTON, int(sz))
def mono(sz): return ImageFont.truetype(MONO, int(sz))

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def eoc(t): t = clamp(t); return 1 - (1 - t) ** 3
def eob(t):
    t = clamp(t); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def eoi(t): t = clamp(t); return t * t
def lerp(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

def load(p): return Image.open(p).convert('RGB')
def sil(im, bg, tol=26):
    im = im.convert('RGB')
    diff = ImageChops.difference(im, Image.new('RGB', im.size, bg)).convert('L')
    mask = diff.point(lambda q: 255 if q > tol else 0)
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    rgba = im.convert('RGBA'); rgba.putalpha(mask)
    return rgba
def cropc(im, x0, y0, x1, y1):
    w, h = im.size
    return im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))

BAG = sil(load(SC + '/cut_bag2.png'), (255, 255, 255), 24)
BAG_G = ImageOps.grayscale(BAG.convert('RGB')).convert('RGBA'); BAG_G.putalpha(BAG.getchannel('A'))
CASH = sil(load(SC + '/cut_cash.png'), (255, 255, 255), 24)
GLOVE = sil(load(SC + '/cut_glove.png'), (255, 255, 255), 24)
PERS = sil(load(SC + '/cut_perso.png'), (255, 255, 255), 24)
LOGO = None
def logo_im():
    global LOGO
    if LOGO is None:
        LOGO = Image.new('RGBA', (220, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(LOGO)
        d.rounded_rectangle([0, 0, 219, 159], 20, fill=GOLD_B + (255,))
        d.polygon([(45, 115), (45, 55), (78, 85), (110, 40), (142, 85), (175, 55), (175, 115)], fill=CRIM)
    return LOGO

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

def extrude(fr, txt, sz, x, y, face, side, k, depth=12, rot=0.0, alpha=1.0):
    im = text_im(txt, anton(sz), face + (255,))
    lay = Image.new('RGBA', (im.width + depth * 2 + 4, im.height + depth * 2 + 4), (0, 0, 0, 0))
    for d in range(depth, 0, -1):
        lay.paste(Image.new('RGBA', im.size, side + (255,)), (2 + depth - d, 2 + d), im)
    lay.paste(im, (2 + depth, 2), im)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    paste(fr, lay, x, y, alpha=alpha)

def glow_field(fr, base, lift=26):
    fr.paste(Image.new('RGB', (W, H), base), (0, 0))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([CX - 620, CY - 620, CX + 620, CY + 620], fill=(255, 255, 255, lift))
    g = g.filter(ImageFilter.GaussianBlur(220))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

EDGE = None
def edge_vig(fr, k=110):
    global EDGE
    if EDGE is None:
        EDGE = Image.new('L', (W, H), 255); d = ImageDraw.Draw(EDGE)
        d.rectangle([0, 0, 150, H], fill=90); d.rectangle([W - 150, 0, W, H], fill=90)
        EDGE = EDGE.filter(ImageFilter.GaussianBlur(160))
    fr.paste(Image.composite(fr, Image.new('RGB', (W, H), (8, 6, 6)), EDGE.point(lambda q: q if q < 255 else 255)), (0, 0)) if k else None
def chevron_field(fr, base, tone, drift):
    fr.paste(Image.new('RGB', (W, H), base), (0, 0))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    step = 430; th = 200
    for ci, cxr in enumerate((0.18, 0.5, 0.82)):
        x = int(W * cxr); al = 40 if ci == 1 else 74
        col = tone if ci == 1 else (0, 0, 0)
        y = -320 + int(drift * 30) % step
        while y < H + 200:
            d.polygon([(x - 320, y + th), (x, y), (x + 320, y + th), (x + 320, y + th + 150),
                       (x, y + 150), (x - 320, y + th + 150)],
                      fill=(col + (al,) if col != (0, 0, 0) else (60, 0, 6, al)))
            y += step
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), ov).convert('RGB'), (0, 0))
    edge_vig(fr)

PUFF = None
def puff_im():
    global PUFF
    if PUFF is None:
        rnd = random.Random(5)
        PUFF = Image.new('RGBA', (460, 280), (0, 0, 0, 0)); d = ImageDraw.Draw(PUFF)
        for i in range(10):
            x = 60 + i * 38 + rnd.uniform(-14, 14); y = 170 - math.sin(i / 9 * math.pi) * 100 + rnd.uniform(-10, 10)
            r = rnd.uniform(40, 70)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(148, 146, 144, 255))
        PUFF = PUFF.filter(ImageFilter.GaussianBlur(9)).resize((640, 300))
    return PUFF

def wireframe(fr, x, y, w, h, seed=3):
    rnd = random.Random(seed)
    pts = []
    for i in range(9):
        ang = i / 9 * 2 * math.pi
        rr = 0.5 + rnd.uniform(-0.10, 0.14)
        pts.append((int(x + math.cos(ang) * w * rr), int(y + math.sin(ang) * h * rr)))
    d = ImageDraw.Draw(fr)
    d.line(pts + [pts[0]], fill=(255, 255, 255, 200), width=3)
    for i in (1, 4, 7):
        d.line([pts[i], pts[(i + 4) % 9]], fill=(255, 255, 255, 150), width=2)

def stool_draw(fr, x, y, alpha=1.0, dy=0):
    im = Image.new('RGBA', (520, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([20, 40, 500, 130], fill=(150, 106, 66, 255))
    d.ellipse([20, 24, 500, 114], fill=(172, 124, 80, 255))
    for lx, sx in ((110, -46), (260, 0), (410, 46)):
        d.polygon([(lx - 14, 96), (lx + 14, 96), (lx + sx + 10, 400), (lx + sx - 10, 400)], fill=(104, 70, 42, 255))
    if alpha < 1: im.putalpha(im.getchannel('A').point(lambda p: int(p * alpha)))
    fr.paste(im, (int(x - 260), int(y - 60 + dy)), im)

def desat(fr, k, dark=1.0):
    if k <= 0: return
    g = ImageOps.grayscale(fr).convert('RGB')
    out = Image.blend(fr, g, clamp(k))
    if dark < 1: out = ImageEnhance.Brightness(out).enhance(dark)
    fr.paste(out, (0, 0))

def eyeglow(fr, x, y, spread, k):
    if k <= 0: return
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for ex in (-spread / 2, spread / 2):
        d.ellipse([int(x + ex - 80), int(y - 46), int(x + ex + 80), int(y + 46)], fill=(255, 46, 46, int(165 * k)))
    g = g.filter(ImageFilter.GaussianBlur(38))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

SHAKES = [0.43, 0.60, 3.00, 3.25, 11.67, 12.10, 12.27, 14.67, 14.92]
def shake_amt(t):
    for h in SHAKES:
        dt = t - h
        if 0 <= dt < .22: return (1 - dt / .22) * 7
    return 0

def scene(fr, tl):
    """one 11.67s pass; tl in [0,11.67)"""
    push = 1.0
    if tl < 0.43:
        glow_field(fr, WHITE, 26)
        if tl > 0.10:
            k = eob((tl - .10) / .22)
            paste(fr, text_im('TWENTY', anton(120), GOLD_B + (255,)), CX, 780, scale=1.5 - .5 * k, alpha=clamp((tl - .10) / .08))
    elif tl < 0.60:
        fr.paste(Image.new('RGB', (W, H), BLACK), (0, 0))
        k = eoc((tl - .43) / .17)
        xx = CX - 260 * (1 - k)
        extrude(fr, 'TWENTY', 58, xx - 165, 742, GOLD_B, GOLD_D, 1, depth=8)
        extrude(fr, 'BILLION', 150, xx + 90, 742, GOLD_B, GOLD_D, 1)
    elif tl < 1.35:
        kk = clamp((tl - .60) / .35)
        field_c = lerp(GOLD_D, GOLD_B, kk)
        fr.paste(Image.new('RGB', (W, H), field_c), (0, 0))
        k = eoc((tl - .60) / .18)
        extrude(fr, 'BILLION', 170, CX + 60 + 240 * (1 - k), 350, INK, (52, 42, 10), 1)
        extrude(fr, 'TWENTY', 56, CX - 175, 420, INK, (52, 42, 10), 1, depth=7, rot=78)
        ry = H + 420 - (H + 420 - 1060) * eoc((tl - .60) / .45)
        vy = 2600 * (1 - clamp((tl - .60) / .45))
        if vy > 700:
            for g_, al in ((.05, .3), (.1, .18)):
                paste(fr, BAG, CX, ry + vy * g_, scale=.78, alpha=al)
        paste(fr, BAG, CX, ry, scale=.78)
    elif tl < 1.90:
        glow_field(fr, WHITE, 22)
        sk = eoc((tl - 1.35) / .25)
        stool_draw(fr, CX, 1345, alpha=sk, dy=(1 - sk) * 90)
        b = 1 + .10 * math.sin((tl - 1.55) * 16) * math.exp(-(tl - 1.55) * 6) if tl > 1.55 else 1
        by = 1060 + (1120 - 1060) * eoc((tl - 1.35) / .2)
        paste(fr, BAG, CX, by, scale=.78 * b)
        pk = clamp((tl - 1.60) / .3)
        if pk > 0:
            paste(fr, puff_im(), 170 + 10 * math.sin(tl), 700, scale=1.5, alpha=.45 * pk)
            paste(fr, puff_im(), 910 - 10 * math.sin(tl * .9), 780, scale=1.45, alpha=.42 * pk, rot=6)
    elif tl < 3.00:
        glow_field(fr, WHITE, 18)
        stool_draw(fr, CX, 1345)
        b = 1 + .05 * math.sin((tl - 1.55) * 16) * math.exp(-(tl - 1.55) * 6)
        paste(fr, BAG, CX, 1120, scale=.78 * b)
        paste(fr, puff_im(), 170 + 10 * math.sin(tl), 700, scale=1.5, alpha=.45)
        paste(fr, puff_im(), 910 - 10 * math.sin(tl * .9), 780, scale=1.45, alpha=.42, rot=6)
        dk = clamp((tl - 1.90) / .25)
        desat(fr, dk)
        if tl > 2.05:
            paste(fr, text_im('HE', anton(96), CRIM + (255,)), CX - 130, 420, alpha=clamp((tl - 2.05) / .1))
        if tl > 2.20:
            fk = clamp((tl - 2.20) / .25)
            paste(fr, text_im('SAID', anton(96), lerp((238, 168, 168), CRIM, fk) + (255,)), CX + 92, 420, alpha=clamp((tl - 2.20) / .1))
        if tl > 2.45:
            fk = clamp((tl - 2.45) / .3)
            paste(fr, text_im('NO', anton(340), lerp((238, 168, 168), CRIM, fk) + (255,)), CX, 660, scale=1.22 - .22 * eob(fk))
    elif tl < 3.25:
        chevron_field(fr, TEAL, TEAL_L, tl)
    else:
        tl2 = tl - 3.25
        chevron_field(fr, CRIM_F, (206, 60, 66), tl)
        # cash fly-in
        ck = eoc(tl2 / .40)
        cxp = W + 320 - (W + 320 - 780) * ck
        if tl2 < .40:
            for g_, al in ((.05, .3), (.1, .18)):
                paste(fr, CASH, cxp + 260 * g_ * 8, 1060, scale=.5, rot=-30 + 22 * ck, alpha=al)
        paste(fr, CASH, cxp, 1060 + 6 * math.sin(tl * 1.8), scale=.5, rot=-30 + 22 * ck)
        wireframe(fr, cxp, 1060, 240, 110, seed=7)
        # glove hand slide
        hk = eoc((tl2 - .15) / .35)
        if tl2 > .15:
            paste(fr, GLOVE, -260 + 430 * hk, 1150, scale=.46, rot=-84)
        # logo pop
        if tl2 > .35:
            lk = eob((tl2 - .35) / .3)
            paste(fr, logo_im(), 165, 945 + 8 * math.sin(tl * 1.6), scale=.5 + .5 * lk, rot=-8 + 8 * lk)
            if lk >= 1: wireframe(fr, 165, 945, 150, 110, seed=11)
        # 2008 digits
        if tl2 > 1.50:
            n = int((tl2 - 1.50) / .22) + 1
            txt = '2008'
            base_x = CX
            full = text_im(txt, anton(200), WHITE + (255,))
            show = txt[:min(n, 4)]
            part = text_im(show, anton(200), WHITE + (255,))
            paste(fr, part, base_x - (4 - len(show)) * 62, 240)
            if n <= 4:
                fk = clamp(((tl2 - 1.50) % .22) / .22)
                dgt = text_im(txt[n - 1:n], anton(200), WHITE + (255,))
                paste(fr, dgt, base_x - (4 - n) * 62 + 62, 240, alpha=fk)
        # persona rise + push
        if tl2 > 2.75:
            rk = eoc((tl2 - 2.75) / .8)
            psc = 1.28 + .22 * rk + .08 * eoi((tl2 - 3.55) / 5.0)
            paste(fr, PERS, CX, H + 700 - (H + 700 - 1250) * rk, scale=psc)
            push = 1 + .05 * eoi((tl2 - 3.55) / 8.1)
        # plate
        if tl2 > 4.25:
            pk2 = eob((tl2 - 4.25) / .3)
            pim = Image.new('RGBA', (330, 84), (0, 0, 0, 0)); d = ImageDraw.Draw(pim)
            d.rounded_rectangle([0, 0, 329, 83], 10, fill=GOLD_B + (255,))
            t1 = text_im('MONARCH', mono(30), INK + (255,))
            t2 = text_im('& like', mono(26), INK + (180,))
            pim.paste(t1, ((330 - t1.width) // 2, 8), t1)
            pim.paste(t2, ((330 - t2.width) // 2, 44), t2)
            paste(fr, pim, CX, 1620, scale=.5 + .5 * pk2, rot=-6 + 6 * eoc((tl2 - 4.25) / .3), alpha=clamp((tl2 - 4.25) / .1))
        # grade shift
        if tl2 > 5.75:
            gk = clamp((tl2 - 5.75) / .4)
            desat(fr, .72 * gk, dark=1 - .26 * gk)
            eyeglow(fr, CX, 985, 175, gk)
    return push

def render_frame(fno):
    t = fno / FPS
    tl = t % PASS if t < 2 * PASS else PASS - 0.001
    if t >= 2 * PASS: tl = PASS - 0.001
    fr = Image.new('RGB', (W, H), INK)
    push = scene(fr, tl)
    if push != 1.0:
        w2, h2 = int(W * push), int(H * push)
        im2 = fr.resize((w2, h2))
        fr = im2.crop(((w2 - W) // 2, (h2 - H) // 2, (w2 + W) // 2, (h2 + H) // 2))
    sh = shake_amt(t)
    if sh:
        dx = math.sin(t * 71) * sh; dy = math.cos(t * 63) * sh
        fr = fr.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=INK)
    return fr

OUT = ROOT + '/deliverables/shorts/S01_monarch_20billion_v5.mp4'
WEB = ROOT + '/deliverables/shorts/S01_monarch_20billion_v5_web.mp4'
proc = subprocess.Popen([FF, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                         '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                         '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for fno in range(NF):
    proc.stdin.write(render_frame(fno).tobytes())
proc.stdin.close(); proc.wait()
subprocess.run([FF, '-y', '-i', OUT, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-preset', 'slow', '-crf', '26',
                '-pix_fmt', 'yuv420p', '-an', WEB], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
AUD = ROOT + '/refs/ref-audio.m4a'
for dst in (OUT, WEB):
    tmp = dst + '.mux.mp4'
    subprocess.run([FF, '-y', '-i', dst, '-i', AUD, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '160k', '-shortest', tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, dst)
print('DONE v5', os.path.getsize(WEB))
