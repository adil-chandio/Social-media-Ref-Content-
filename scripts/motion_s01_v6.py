#!/usr/bin/env python3
"""S01 v6 — PIXEL-FAITHFUL replica of refs/ref-reels-tutorial.mp4 (23.35s).
Assets extracted FROM the reference frames themselves (HSV/diff keying):
sp_bag, sp_stool, sp_smoke_l/r, sp_logo, sp_glove, sp_cash, sp_jensen, sp_plate.
Colors sampled from reference pixels. Timeline measured at 4fps (forensics doc).
Pass = 11.67s played twice. Audio = reference original track verbatim.
Render 1080x1920 (1.5x ref 720x1280 coords) = sharper 'next level' master.
"""
import math, os, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = ROOT + '/refs/extract/'
FF = open('/tmp/ffpath').read().strip()
W, H, FPS = 1080, 1920, 30
S = 1.5
PASS = 11.67
NF = int(23.35 * FPS)
CX, CY = W // 2, H // 2
def P(x, y): return (x * S, y * S)

WHITE_F = (228, 228, 228)
BLACK_F = (26, 26, 26)
GREEN_F = (79, 126, 4)
RED_B = (118, 8, 8)
RED_C = (152, 16, 16)
RED_S = (92, 6, 6)
TEAL_B = (40, 174, 175)
TEAL_C = (70, 216, 216)
TEAL_S = (30, 148, 150)
LIME = (123, 193, 2)
LIME_D = (74, 118, 1)
REDT = (186, 2, 2)
PINK = (236, 168, 166)
WHT = (238, 238, 238)
BLK = (12, 12, 12)

ANTON = ROOT + '/assets/fonts/Anton-Regular.ttf'
def anton(sz): return ImageFont.truetype(ANTON, int(sz * S))

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def eoc(t): t = clamp(t); return 1 - (1 - t) ** 3
def eob(t):
    t = clamp(t); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def eoi(t): t = clamp(t); return t * t
def lerp(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

def loadA(n): return Image.open(E + n).convert('RGBA')
BAG = loadA('sp_bag.png'); STOOL = loadA('sp_stool.png')
SMKL = loadA('sp_smoke_l.png'); SMKR = loadA('sp_smoke_r.png')
LOGO = loadA('sp_logo.png'); GLOVE = loadA('sp_glove.png')
CASH = loadA('sp_cash.png'); JEN = loadA('sp_jensen.png'); PLATE = loadA('sp_plate.png')

def paste(fr, im, x, y, tw=None, scale=1.0, rot=0.0, alpha=1.0):
    if alpha <= 0: return
    if tw: scale = tw / im.width
    w = max(1, int(im.width * scale)); h = max(1, int(im.height * scale))
    im2 = im.resize((w, h))
    if rot: im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        im2 = im2.copy(); im2.putalpha(im2.getchannel('A').point(lambda p: int(p * alpha)))
    fr.paste(im2, (int(x - im2.width / 2), int(y - im2.height / 2)), im2)

def text_im(txt, font, fill):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    bb = d.textbbox((0, 0), txt, font=font)
    im = Image.new('RGBA', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=font, fill=fill)
    return im

def extrude(fr, txt, sz, x, y, face, side, depth=9, rot=0.0, alpha=1.0):
    im = text_im(txt, anton(sz), face + (255,))
    dpx = int(depth * S)
    lay = Image.new('RGBA', (im.width + dpx * 2 + 4, im.height + dpx * 2 + 4), (0, 0, 0, 0))
    for d in range(dpx, 0, -1):
        lay.paste(Image.new('RGBA', im.size, side + (255,)), (2 + dpx - d, 2 + d), im)
    lay.paste(im, (2 + dpx, 2), im)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    paste(fr, lay, x, y, alpha=alpha)

EDGE = None
def edge_vig(fr, strength=170):
    global EDGE
    if EDGE is None:
        EDGE = Image.new('L', (W, H), 255); d = ImageDraw.Draw(EDGE)
        d.rectangle([0, 0, int(W * .10), H], fill=40); d.rectangle([int(W * .90), 0, W, H], fill=40)
        d.rectangle([0, 0, W, int(H * .04)], fill=120); d.rectangle([0, int(H * .96), W, H], fill=120)
        EDGE = EDGE.filter(ImageFilter.GaussianBlur(140))
    dark = Image.new('RGB', (W, H), (6, 5, 5))
    fr.paste(Image.composite(fr, dark, EDGE), (0, 0))

def glow(fr, lift=34, size=620):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([CX - size, CY - size, CX + size, CY + size], fill=(255, 255, 255, lift))
    g = g.filter(ImageFilter.GaussianBlur(200))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

def chevron(fr, base, tone, sidec, drift):
    fr.paste(Image.new('RGB', (W, H), base), (0, 0))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    step = int(340 * S); th = int(150 * S)
    for cxr, col, al in ((0.0, sidec, 150), (0.45, tone, 165), (0.95, sidec, 150)):
        x = int(W * cxr)
        y = -step * 2 + int(drift * 26) % step
        while y < H + step:
            d.polygon([(x - int(260 * S), y + th), (x, y), (x + int(260 * S), y + th),
                       (x + int(260 * S), y + th + int(90 * S)), (x, y + int(90 * S)),
                       (x - int(260 * S), y + th + int(90 * S))], fill=col + (al,))
            y += step
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), ov).convert('RGB'), (0, 0))
    edge_vig(fr)

def wireframe(fr, x, y, w, h, seed=3, al=1.0):
    import random
    rnd = random.Random(seed)
    pts = []
    for i in range(9):
        ang = i / 9 * 2 * math.pi
        rr = 0.5 + rnd.uniform(-0.10, 0.14)
        pts.append((int(x + math.cos(ang) * w * rr), int(y + math.sin(ang) * h * rr)))
    d = ImageDraw.Draw(fr)
    d.line(pts + [pts[0]], fill=(255, 255, 255, int(150 * al)), width=3)
    for i in (1, 4, 7):
        d.line([pts[i], pts[(i + 4) % 9]], fill=(255, 255, 255, int(110 * al)), width=2)

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
        d.ellipse([int(x + ex - 62), int(y - 34), int(x + ex + 62), int(y + 34)], fill=(255, 40, 40, int(170 * k)))
    g = g.filter(ImageFilter.GaussianBlur(30))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

SHAKES = [0.43, 0.60, 3.00, 3.25, 11.67, 12.10, 12.27, 14.67, 14.92]
def shake_amt(t):
    for h in SHAKES:
        dt = t - h
        if 0 <= dt < .22: return (1 - dt / .22) * 6
    return 0

def scene(fr, tl):
    push = 1.0
    if tl < 0.43:
        fr.paste(Image.new('RGB', (W, H), WHITE_F), (0, 0)); glow(fr, 40); edge_vig(fr)
        if tl > 0.10:
            k = eob((tl - .10) / .22)
            paste(fr, text_im('TWENTY', anton(86), LIME + (255,)), CX, 640 * S, scale=1.45 - .45 * k, alpha=clamp((tl - .10) / .08))
    elif tl < 0.60:
        fr.paste(Image.new('RGB', (W, H), BLACK_F), (0, 0)); glow(fr, 16); edge_vig(fr)
        k = eoc((tl - .43) / .17)
        xx = CX - 180 * S * (1 - k)
        extrude(fr, 'TWENTY', 42, xx - 150 * S, 640 * S, LIME, LIME_D, depth=7)
        extrude(fr, 'BILLION', 94, xx + 95 * S, 640 * S, LIME, LIME_D)
    elif tl < 1.35:
        kk = clamp((tl - .60) / .30)
        fr.paste(Image.new('RGB', (W, H), lerp((46, 74, 2), GREEN_F, kk)), (0, 0)); edge_vig(fr)
        k = eoc((tl - .60) / .18)
        extrude(fr, 'BILLION', 100, CX + 40 * S + 160 * S * (1 - k), 230 * S, BLK, (40, 40, 8))
        extrude(fr, 'TWENTY', 36, CX - 128 * S, 300 * S, BLK, (40, 40, 8), depth=6, rot=78)
        ry = H + 400 - (H + 400 - 660 * S) * eoc((tl - .60) / .40)
        vk = 1 - clamp((tl - .60) / .40)
        if vk > 0.25:
            for g_, al in ((.06, .3), (.12, .16)):
                paste(fr, BAG, CX, ry + 900 * vk * g_, tw=470 * S, alpha=al)
        paste(fr, BAG, CX, ry, tw=470 * S)
    elif tl < 1.90:
        fr.paste(Image.new('RGB', (W, H), WHITE_F), (0, 0)); glow(fr, 36); edge_vig(fr)
        sk = eoc((tl - 1.35) / .25)
        paste(fr, STOOL, CX, 1000 * S + (1 - sk) * 80 * S, tw=390 * S, alpha=sk)
        b = 1 + .09 * math.sin((tl - 1.55) * 16) * math.exp(-(tl - 1.55) * 6) if tl > 1.55 else 1
        by = 700 * S + (760 - 700) * S * eoc((tl - 1.35) / .2)
        paste(fr, BAG, CX, by, tw=470 * S * b)
        pk = clamp((tl - 1.60) / .3)
        if pk > 0:
            paste(fr, SMKL, 95 * S, 520 * S, tw=SMKL.width * S * .95, alpha=pk)
            paste(fr, SMKR, 625 * S, 560 * S, tw=SMKR.width * S * .95, alpha=pk)
    elif tl < 3.00:
        fr.paste(Image.new('RGB', (W, H), WHITE_F), (0, 0)); glow(fr, 32); edge_vig(fr)
        paste(fr, STOOL, CX, 1000 * S, tw=390 * S)
        b = 1 + .04 * math.sin((tl - 1.55) * 16) * math.exp(-(tl - 1.55) * 6)
        paste(fr, BAG, CX, 760 * S, tw=470 * S * b)
        paste(fr, SMKL, 95 * S, 520 * S, tw=SMKL.width * S * .95)
        paste(fr, SMKR, 625 * S, 560 * S, tw=SMKR.width * S * .95)
        desat(fr, clamp((tl - 1.90) / .25))
        if tl > 2.05:
            paste(fr, text_im('HE', anton(90), REDT + (255,)), 262 * S, 300 * S, alpha=clamp((tl - 2.05) / .1))
        if tl > 2.20:
            fk = clamp((tl - 2.20) / .25)
            paste(fr, text_im('SAID', anton(90), lerp(PINK, REDT, fk) + (255,)), 400 * S, 300 * S, alpha=clamp((tl - 2.20) / .1))
        if tl > 2.45:
            fk = clamp((tl - 2.45) / .3)
            paste(fr, text_im('NO', anton(170), lerp(PINK, REDT, fk) + (255,)), CX, 450 * S, scale=1.2 - .2 * eob(fk))
    elif tl < 3.25:
        chevron(fr, TEAL_B, TEAL_C, TEAL_S, tl)
    else:
        tl2 = tl - 3.25
        chevron(fr, RED_B, RED_C, RED_S, tl)
        ck = eoc(tl2 / .40)
        pf = 1 - clamp((tl2 - 2.15) / .45)
        bx = 288 * S
        by = 755 * S
        cxp = W + 320 - (W + 320 - bx) * ck
        cyp = by + 5 * math.sin(tl * 1.8)
        if pf > 0:
            if tl2 < .40:
                for g_, al in ((.06, .3), (.12, .16)):
                    paste(fr, CASH, cxp + 240 * g_, cyp, tw=360 * S, rot=-24 + 16 * ck, alpha=al * pf)
            paste(fr, CASH, cxp, cyp, tw=360 * S, rot=-24 + 16 * ck, alpha=pf)
            wireframe(fr, cxp, cyp, 200 * S, 90 * S, seed=7, al=pf)
        hk = eoc((tl2 - .15) / .35)
        if tl2 > .15 and pf > 0:
            paste(fr, GLOVE, -260 + (145 * S + 260) * hk, 770 * S, tw=340 * S, alpha=pf)
        if tl2 > .35 and pf > 0:
            lk = eob((tl2 - .35) / .3)
            paste(fr, LOGO, 164 * S, 636 * S + 6 * math.sin(tl * 1.6), tw=158 * S * (.5 + .5 * lk), rot=-6 + 6 * lk, alpha=pf)
            if lk >= 1: wireframe(fr, 164 * S, 636 * S, 110 * S, 80 * S, seed=11, al=pf)
        if tl2 > 1.50:
            n = int((tl2 - 1.40) / .15) + 1
            txt = '2008'
            show = txt[:min(n, 4)]
            part = text_im(show, anton(135), WHT + (255,))
            paste(fr, part, CX - (4 - len(show)) * 42 * S, 260 * S)
            if n <= 4:
                fk = clamp(((tl2 - 1.40) % .15) / .15)
                dgt = text_im(txt[n - 1:n], anton(135), WHT + (255,))
                paste(fr, dgt, CX - (4 - n) * 42 * S + 42 * S, 260 * S, alpha=fk)
        if tl2 > 0.95:
            rk = eoc((tl2 - 2.75) / .8) if tl2 > 2.75 else 0.0
            u_ = clamp((tl2 - 1.95) / 1.45); sk = u_ * u_ * (3 - 2 * u_)
            psc_tw = 760 * S * (.85 + .15 * rk)
            jx = -0.44 * W + (CX + 0.44 * W) * sk
            paste(fr, JEN, jx, 800 * S + (1 - rk) * 120 * S, tw=psc_tw)
            push = 1 + .05 * eoi((tl2 - 3.55) / 8.1)
        if tl2 > 4.25:
            pk2 = eob((tl2 - 4.25) / .3)
            paste(fr, PLATE, CX, 911 * S, tw=390 * S * (.5 + .5 * pk2), rot=-5 + 5 * eoc((tl2 - 4.25) / .3), alpha=clamp((tl2 - 4.25) / .1))
        if tl2 > 5.75:
            gk = clamp((tl2 - 5.75) / .4)
            desat(fr, .80 * gk, dark=1 - .30 * gk)
            eyeglow(fr, CX, 610 * S, 90 * S, gk)
    return push

def render_frame(fno):
    t = fno / FPS
    tl = t % PASS if t < 2 * PASS else PASS - 0.001
    if t >= 2 * PASS: tl = PASS - 0.001
    fr = Image.new('RGB', (W, H), (10, 10, 10))
    push = scene(fr, tl)
    if push != 1.0:
        w2, h2 = int(W * push), int(H * push)
        im2 = fr.resize((w2, h2))
        fr = im2.crop(((w2 - W) // 2, (h2 - H) // 2, (w2 + W) // 2, (h2 + H) // 2))
    sh = shake_amt(t)
    if sh:
        dx = math.sin(t * 71) * sh; dy = math.cos(t * 63) * sh
        fr = fr.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=(10, 10, 10))
    return fr

OUT = ROOT + '/deliverables/shorts/S01_monarch_20billion_v6.mp4'
WEB = ROOT + '/deliverables/shorts/S01_monarch_20billion_v6_web.mp4'
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
print('DONE v6', os.path.getsize(WEB))
