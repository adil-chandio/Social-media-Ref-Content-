#!/usr/bin/env python3
"""S01 v3 — reference-grammar motion engine (forensics-matched, 2026-11-01).
Layer stack decoded from source frames (Ld5LkPkQodQ vision stills):
  L0 bg: charcoal field OR maroon field (per scene)
  L1 giant display type bleeding off-canvas, slow parallax drift/scale
  L2 smoke wisps drifting (grey, semi-transparent)
  L3 center vertical paper strip (full-height band) w/ soft side shadows
  L4 on-strip: red condensed type stacks (stamp-in on VO beats)
  L5 grayscale photo cutouts w/ soft drop shadows / maroon scenes: white year type BEHIND cutout + jacket collage + caption plate
  L6 global: push-in per beat, screen-shake on hits, white flash at cuts, grain, vignette
Audio muxed from v1 master (VO + bed + SFX).
"""
import math, os, subprocess, random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = ROOT + '/docs/shorts/s01'
FF = open('/tmp/ffpath').read().strip()
W, H, FPS = 1080, 1920, 30
DURS = [5, 5, 5, 5, 4, 4, 4, 4.6]
STARTS = []
_a = 0.0
for d in DURS:
    STARTS.append(_a); _a += d
NF = int(_a * FPS)
CX, CY = W // 2, H // 2

CHAR = (26, 24, 24)          # charcoal field
PAPER = (242, 240, 235)      # paper strip
RED = (196, 18, 46)          # MONARCH crimson (shifted from source pure red)
DRED = (120, 10, 24)
MAROON = (72, 12, 18)        # maroon scene field
GOLD = (212, 175, 55)
INK = (16, 14, 14)

ANTON = ROOT + '/assets/fonts/Anton-Regular.ttf'
MONO = ROOT + '/portfolio-site/assets/fonts/IBMPlexMono-400.ttf'
MANR = ROOT + '/portfolio-site/assets/fonts/Manrope-700.ttf'

def anton(sz): return ImageFont.truetype(ANTON, int(sz))
def mono(sz): return ImageFont.truetype(MONO, int(sz))
def manr(sz): return ImageFont.truetype(MANR, int(sz))

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def eoc(t): t = clamp(t); return 1 - (1 - t) ** 3
def eob(t):
    t = clamp(t); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def eoi(t): t = clamp(t); return t * t * t

# ---------- assets ----------
def load(p): return Image.open(p).convert('RGB')
sc1 = load(SC + '/sc1_moneybag.png'); sc3 = load(SC + '/sc3_refuse.png')
sc4 = load(SC + '/sc4_chip.png'); sc5 = load(SC + '/sc5_split.png')
sc6 = load(SC + '/sc6_empire.png'); perso = load(ROOT + '/docs/lookdev/char.jpg')

def gray(im, contrast=1.25):
    g = ImageOps.grayscale(im)
    return ImageOps.autocontrast(g, cutoff=1).convert('RGB') if contrast <= 1 else ImageEnhance.Contrast(g.convert('RGB')).enhance(contrast)

def cropc(im, fx0, fy0, fx1, fy1):
    w, h = im.size
    return im.crop((int(w * fx0), int(h * fy0), int(w * fx1), int(h * fy1)))

BAG = gray(cropc(sc1, 0.33, 0.36, 0.68, 0.70))          # money bag on stool
HAND = gray(cropc(sc3, 0.30, 0.18, 0.74, 0.80))         # refusing figure
CHIP = gray(cropc(sc4, 0.26, 0.24, 0.74, 0.76))         # chip
CROWD = gray(cropc(sc5, 0.0, 0.30, 0.50, 0.62))        # crowd half
EMP = gray(cropc(sc6, 0.20, 0.15, 0.80, 0.80))          # skyline/empire
PERS = perso                                             # our masked persona (color)

# ---------- procedural sprites ----------
random.seed(7)
def smoke_sprite(sz=520, seed=3):
    rnd = random.Random(seed)
    im = Image.new('L', (sz, sz), 0); d = ImageDraw.Draw(im)
    for _ in range(26):
        x = rnd.uniform(sz * .2, sz * .8); y = rnd.uniform(sz * .25, sz * .75)
        r = rnd.uniform(sz * .06, sz * .2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randint(70, 150))
    im = im.filter(ImageFilter.GaussianBlur(sz * .07))
    return im
SMOKE = [smoke_sprite(780, s) for s in (3, 11, 23)]

def noise_tile(sz=270, amp=14):
    im = Image.effect_noise((sz, sz), amp).convert('L')
    return im
GRAIN = [noise_tile(270, 13) for _ in range(4)]
PAPNOISE = noise_tile(270, 7)

VIG = Image.new('L', (W, H), 255); _vd = ImageDraw.Draw(VIG)
_vd.rectangle([0, 0, W, H], outline=0, width=1)
VIG = Image.new('L', (W, H), 255); _vd = ImageDraw.Draw(VIG)
_vd.ellipse([-W * .3, -H * .25, W * 1.3, H * 1.25], fill=255)
VIG = VIG.filter(ImageFilter.GaussianBlur(150))
VIG = ImageEnhance.Brightness(VIG).enhance(0.82)

# ---------- helpers ----------
def paste(fr, im, x, y, scale=1.0, rot=0.0, alpha=1.0):
    if alpha <= 0 or scale <= 0.01: return
    w = max(1, int(im.width * scale)); h = max(1, int(im.height * scale))
    im2 = im.resize((w, h))
    if rot: im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        im2 = im2.convert('RGBA'); im2.putalpha(im2.getchannel('A').point(lambda p: int(p * alpha)))
    fr.paste(im2, (int(x - im2.width / 2), int(y - im2.height / 2)), im2)

def cutw(im, w, blur=22):
    r = w / im.width
    return shadowed(im.resize((w, int(im.height * r))), blur=blur)

def shadowed(im, blur=26, off=(10, 22), dark=150):
    """photo cutout with soft drop shadow, returns RGBA"""
    rgba = im.convert('RGBA')
    sh = Image.new('RGBA', (im.width + 160, im.height + 160), (0, 0, 0, 0))
    m = Image.new('L', im.size, 255)
    sh.paste(Image.new('L', im.size, dark), (80 + off[0], 80 + off[1]), m)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.paste(rgba, (80, 80), rgba)
    return sh

def text_im(txt, font, fill, stroke=0, stroke_fill=None):
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    bb = d.textbbox((0, 0), txt, font=font, stroke_width=stroke)
    im = Image.new('RGBA', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=font, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def stamp(fr, txt, sz, x, y, tl, t0, fill=RED, rot=0.0, fontf=anton, dur=0.28, maxw=0):
    if maxw:
        tw0 = text_im(txt, fontf(sz), fill + (255,)).width
        if tw0 > maxw: sz = int(sz * maxw / tw0)
    """condensed type stamp-in: scale 1.7->1 overshoot + alpha, at local time tl>=t0"""
    if tl < t0: return
    k = (tl - t0) / dur
    paste(fr, text_im(txt, fontf(sz), fill), x, y, scale=1.7 - 0.7 * eob(k),
          rot=rot * (1 - eoc(k)), alpha=clamp(k * 1.6))

def giant(fr, txt, color, y, t, spd=26, sz=820, alpha=255, xoff=0):
    """L1 giant bleeding type w/ slow drift"""
    col = color if len(color) == 4 else color + (alpha,)
    im = text_im(txt, anton(sz), col)
    x = CX + xoff + math.sin(t * 0.35) * spd - spd
    fr.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)

def smoke_layer(fr, t, alpha=125):
    for i, sp in enumerate(SMOKE):
        sw = sp.width
        x = ((t * (34 + i * 17) + i * 640) % (W + sw * 1.6)) - sw * .8
        y = 200 + i * 520 + math.sin(t * .8 + i) * 34
        a = Image.new('RGBA', (sw, sw), (190, 188, 186, 0))
        a.putalpha(sp.point(lambda p: int(p * alpha / 255)))
        fr.paste(a, (int(x), int(y)), a)

def strip(fr, w=430, t=0.0):
    """L3 center paper strip full-height + soft side shadows"""
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.rectangle([CX - w / 2 - 26, 0, CX + w / 2 + 26, H], fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), sh).convert('RGB'), (0, 0))
    band = Image.new('RGB', (w, H), PAPER)
    pn = PAPNOISE.resize((w, H)).convert('L')
    band = Image.composite(band, Image.new('RGB', (w, H), (228, 225, 218)), pn.point(lambda p: 255 if p > 128 else 0))
    fr.paste(band, (int(CX - w / 2), 0))

def maroon_field(fr, t):
    fr.paste(Image.new('RGB', (W, H), MAROON), (0, 0))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([CX - 620, CY - 780, CX + 620, CY + 620], fill=(120, 26, 30, 150))
    g = g.filter(ImageFilter.GaussianBlur(180))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

def char_field(fr, t):
    fr.paste(Image.new('RGB', (W, H), CHAR), (0, 0))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([CX - 700, CY - 900, CX + 700, CY + 700], fill=(52, 48, 47, 160))
    g = g.filter(ImageFilter.GaussianBlur(200))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))

def plate(fr, txt, x, y, tl, t0, w=330):
    if tl < t0: return
    k = eob((tl - t0) / .3)
    im = Image.new('RGBA', (w, 74), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 73], 8, fill=GOLD + (255,))
    tw = text_im(txt, mono(34), INK + (255,))
    im.paste(tw, ((w - tw.width) // 2, (74 - tw.height) // 2), tw)
    paste(fr, im, x, y, scale=.6 + .4 * k, alpha=clamp((tl - t0) / .15))

HITS = [1.8, 5.0, 6.2, 10.6, 13.2, 20.4, 21.4, 24.6, 31.2, 32.4]
def shake_amt(t):
    for h in HITS:
        dt = t - h
        if 0 <= dt < .34: return (1 - dt / .34) * 15
    return 0

# ---------- beats ----------
def beat(fr, bi, tl, t):
    push = 1.0
    if bi == 0:  # hook: giant NO bleed + smoke + strip + red stack + bag cutout
        char_field(fr, t)
        giant(fr, 'NO', RED, 420, t, sz=900, xoff=-30)
        giant(fr, 'NO', DRED, 1500, t + 2.1, sz=760, xoff=40, alpha=200)
        strip(fr, 470)
        smoke_layer(fr, t, alpha=140)
        stamp(fr, 'US NE KAHA', 74, CX, 470, tl, .25)
        stamp(fr, 'NAHI.', 250, CX, 700, tl, .55)
        if tl > 1.1:
            k = eob((tl - 1.1) / .5)
            paste(fr, cutw(BAG, 350), CX, 1240 + (1 - k) * 260, scale=.8 + .2 * k)
        if tl > 2.4:
            d = ImageDraw.Draw(fr)
            ww = int(300 * eoc((tl - 2.4) / .4))
            d.rectangle([CX - ww, 852, CX + ww, 866], fill=RED)
        return 1 + .07 * eoi(tl / 5)
    if bi == 1:  # 2008 maroon: enlarged darkened photo bleed + sharp band + year behind head + plate
        bl = cropc(PERS, .05, .30, .95, 1.0)
        bl = ImageEnhance.Brightness(bl).enhance(.38).filter(ImageFilter.GaussianBlur(7))
        bl = bl.resize((int(W * 2.6), int(bl.height * 2.6 * W / bl.width)))
        if bl.height < H: bl = bl.resize((int(bl.width * H / bl.height), H))
        fr.paste(bl, ((bl.width - W) // 2 - 0, (bl.height - H) // 2 * -1 + 120))
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d0 = ImageDraw.Draw(g)
        d0.rectangle([0, 0, W, H], fill=MAROON + (150,)); g = g.filter(ImageFilter.GaussianBlur(2))
        fr.paste(Image.alpha_composite(fr.convert('RGBA'), g).convert('RGB'), (0, 0))
        bw = 470
        band = Image.new('RGB', (bw, H), MAROON)
        fr.paste(band, (CX - bw // 2, 0))
        giant(fr, '2008', (238, 232, 226, 255), 430, t, sz=300, spd=10)
        if tl > .15:
            k = eob((tl - .15) / .55)
            paste(fr, cutw(cropc(PERS, .26, .02, .74, .88), 465, blur=16), CX, 1230 + (1 - k) * 150)
        plate(fr, 'CEO — NVIDIA', CX, 1600, tl, 1.2, w=300)
        if tl > 1.9:
            tw = text_im('$20,000,000,000', mono(46), GOLD + (255,))
            paste(fr, tw, CX, 1760, alpha=clamp((tl - 1.9) / .25))
        return 1 + .05 * eoi(tl / 5)
    if bi == 2:  # mana kar diya: strip + red stack + refusing cutout + slash
        char_field(fr, t)
        giant(fr, 'MANA', RED, 380, t, sz=780, xoff=-40)
        strip(fr, 470)
        smoke_layer(fr, t + 1.3, alpha=95)
        stamp(fr, 'OFFER', 96, CX, 430, tl, .2)
        stamp(fr, 'MANA.', 230, CX, 660, tl, .5)
        if tl > .9:
            k = eob((tl - .9) / .5)
            paste(fr, cutw(HAND, 340), CX, 1270 + (1 - k) * 220, scale=.85 + .15 * k, rot=-2 + 2 * eoc((tl - .9) / .5))
        if tl > 2.2:
            d = ImageDraw.Draw(fr)
            p = eoc((tl - 2.2) / .45)
            d.line([CX - 260, 1010, CX - 260 + 520 * p, 950 + 60 * p], fill=RED, width=16)
        return 1 + .06 * eoi(tl / 5)
    if bi == 3:  # chip yaqeen: strip + chip cutout + red stack + dot pulse
        char_field(fr, t)
        giant(fr, 'YAQEEN', DRED, 1560, t, sz=640, xoff=30, alpha=220)
        strip(fr, 470)
        smoke_layer(fr, t + 2.7, alpha=90)
        stamp(fr, 'APNE CHIP PAR', 70, CX, 430, tl, .2)
        stamp(fr, 'YAQEEN.', 200, CX, 640, tl, .5, maxw=380)
        if tl > .8:
            k = eob((tl - .8) / .5)
            paste(fr, cutw(CHIP, 330), CX, 1200 + (1 - k) * 200, scale=.85 + .15 * k, rot=3 - 3 * eoc((tl - .8) / .6))
        if tl > 2.0:
            d = ImageDraw.Draw(fr)
            for i in range(6):
                tt = tl - 2.0 - i * .18
                if tt > 0:
                    r = 14 + 7 * math.sin(t * 5 + i)
                    d.ellipse([CX - 160 + i * 64 - r, 1610 - r, CX - 160 + i * 64 + r, 1610 + r], fill=RED)
        return 1 + .07 * eoi(tl / 4)
    if bi == 4:  # empire not deal: maroon, $20B crossed, EMPIRE type, crowd cutout
        maroon_field(fr, t)
        giant(fr, 'EMPIRE', (238, 232, 226, 255), 430, t, sz=430, spd=18)
        stamp(fr, '$20B', 190, CX - 140, 800, tl, .2, fill=(242, 238, 232))
        if tl > .7:
            d = ImageDraw.Draw(fr)
            p = eoc((tl - .7) / .35)
            d.line([CX - 330, 700, CX - 330 + 420 * p, 700 + 200 * p], fill=RED, width=18)
            d.line([CX + 90, 700, CX + 90 - 420 * p, 700 + 200 * p], fill=RED, width=18)
        stamp(fr, 'EMPIRE.', 210, CX, 1080, tl, 1.1, fill=RED)
        if tl > 1.5:
            k = eoc((tl - 1.5) / .6)
            paste(fr, cutw(CROWD, 700, blur=30), CX, 1600 + (1 - k) * 120, alpha=clamp((tl - 1.5) / .3))
        return 1 + .06 * eoi(tl / 4)
    if bi == 5:  # 3 trillion: maroon + graph gold draw + counters
        maroon_field(fr, t)
        giant(fr, '3T', GOLD + (255,), 500, t, sz=620, spd=16)
        stamp(fr, 'AAJ KI QEEMAT:', 62, CX, 270, tl, .2, fill=(242, 238, 232))
        val = 3.0 * clamp((tl - .6) / 1.6)
        stamp(fr, f'${val:.2f}T', 150, CX, 450, tl, .6, fill=GOLD, maxw=600)
        d = ImageDraw.Draw(fr)
        pts = [(CX - 360 + i * 120, 1500 - (i ** 2.1) * 26) for i in range(7)]
        n = int(7 * clamp((tl - 1.0) / 1.6))
        for i in range(max(1, n)):
            if i: d.line([pts[i - 1], pts[i]], fill=GOLD, width=10)
            r = 12 if i < n else 0
            if r: d.ellipse([pts[i][0] - r, pts[i][1] - r, pts[i][0] + r, pts[i][1] + r], fill=(242, 238, 232))
        if tl > 2.6:
            tw = text_im('NASDAQ: NVDA', mono(44), (242, 238, 232, 255))
            paste(fr, tw, CX, 1780, alpha=clamp((tl - 2.6) / .3))
        return 1 + .06 * eoi(tl / 4)
    if bi == 6:  # footnote: strip + mono footnote + red circle scribble
        char_field(fr, t)
        giant(fr, 'FOOTNOTE', DRED, 400, t, sz=520, xoff=-20, alpha=210)
        strip(fr, 470)
        smoke_layer(fr, t + 4.1, alpha=85)
        stamp(fr, 'AB YEH SIRF', 78, CX, 450, tl, .2)
        stamp(fr, 'FOOTNOTE.', 190, CX, 660, tl, .5)
        if tl > 1.0:
            tw = text_im('$20,000,000,000', mono(44), INK + (255,))
            paste(fr, tw, CX, 1150, alpha=clamp((tl - 1.0) / .3))
        if tl > 1.8:
            d = ImageDraw.Draw(fr)
            p = clamp((tl - 1.8) / .8)
            d.arc([CX - 300, 1080, CX + 300, 1220], start=-40, end=-40 + 360 * p, fill=RED, width=10)
        if tl > 2.8:
            tw = text_im('footnote 7, page 3', mono(40), (90, 86, 82, 255))
            paste(fr, tw, CX, 1300, alpha=clamp((tl - 2.8) / .3))
        return 1 + .05 * eoi(tl / 4)
    if bi == 7:  # end: monarch rule card
        char_field(fr, t)
        giant(fr, 'MONARCH', RED, 360, t, sz=560, xoff=-20, alpha=230)
        strip(fr, 470)
        smoke_layer(fr, t + 5.2, alpha=110)
        if tl > .1:
            k = eob((tl - .1) / .5)
            paste(fr, cutw(cropc(PERS, .28, .02, .72, .72), 500, blur=18), CX, 880 + (1 - k) * 200)
        # crown
        if tl > .5:
            d = ImageDraw.Draw(fr)
            k = eob((tl - .5) / .35)
            cw = int(130 * k); ch = int(95 * k)
            d.polygon([(CX - cw, 500), (CX - cw, 500 - int(ch * .7)), (CX - cw // 2, 500 - int(ch * .35)),
                       (CX - cw // 6, 500 - ch), (CX, 500 - int(ch * .4)), (CX + cw // 6, 500 - ch),
                       (CX + cw // 2, 500 - int(ch * .35)), (CX + cw, 500 - int(ch * .7)), (CX + cw, 500)], fill=RED)
        stamp(fr, 'MONARCH RULE:', 92, CX, 1420, tl, .8, fill=GOLD)
        if tl > 1.4:
            tw = text_im('Vision chhota ho toh', manr(46), INK + (255,))
            paste(fr, tw, CX, 1540, alpha=clamp((tl - 1.4) / .25))
        if tl > 1.8:
            tw = text_im('deal badi lagti hai.', manr(46), RED + (255,))
            paste(fr, tw, CX, 1615, alpha=clamp((tl - 1.8) / .25))
        return 1 + .04 * eoi(tl / 4.6)
    return push

# ---------- render ----------
OUT = ROOT + '/deliverables/shorts/S01_monarch_20billion_v3.mp4'
WEB = ROOT + '/deliverables/shorts/S01_monarch_20billion_v3_web.mp4'
proc = subprocess.Popen([FF, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                         '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21',
                         '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
grains = [Image.merge('RGBA', [g, g, g, g.point(lambda p: 20)]) for g in GRAIN]
for fno in range(NF):
    t = fno / FPS
    bi = 0; tl = t
    for i, st in enumerate(STARTS):
        if t >= st: bi = i; tl = t - st
    fr = Image.new('RGB', (W, H), INK)
    push = beat(fr, bi, tl, t)
    if push != 1.0:
        w2, h2 = int(W * push), int(H * push)
        r = max(w2 / W, h2 / H)
        im2 = fr.resize((int(W * r), int(H * r)))
        fr = im2.crop(((im2.width - w2) // 2, (im2.height - h2) // 2, (im2.width + w2) // 2, (im2.height + h2) // 2)).resize((W, H))
    sh = shake_amt(t)
    if sh:
        dx = math.sin(t * 71) * sh; dy = math.cos(t * 63) * sh
        fr = fr.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=CHAR)
    for st in STARTS[1:]:
        dt = t - st
        if 0 <= dt < 0.10:
            fl = Image.new('RGB', (W, H), (255, 244, 240)); fr = Image.blend(fr, fl, 0.45 * (1 - dt / 0.10))
    gr = grains[fno % 4].resize((W, H)); fr.paste(Image.alpha_composite(fr.convert('RGBA'), gr).convert('RGB'), (0, 0))
    fr.paste(Image.composite(fr, Image.new('RGB', (W, H), INK), VIG), (0, 0))
    proc.stdin.write(fr.tobytes())
proc.stdin.close(); proc.wait()
subprocess.run([FF, '-y', '-i', OUT, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-preset', 'slow', '-crf', '27',
                '-pix_fmt', 'yuv420p', '-an', WEB], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
# mux audio from v1 master
V1 = ROOT + '/deliverables/shorts/S01_monarch_20billion.mp4'
tmp = OUT + '.mux.mp4'
subprocess.run([FF, '-y', '-i', OUT, '-i', V1, '-map', '0:v', '-map', '1:a', '-c', 'copy', '-shortest', tmp],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.replace(tmp, OUT)
tmpw = WEB + '.mux.mp4'
subprocess.run([FF, '-y', '-i', WEB, '-i', V1, '-map', '0:v', '-map', '1:a', '-c', 'copy', '-shortest', tmpw],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.replace(tmpw, WEB)
print('DONE v3', os.path.getsize(WEB))
