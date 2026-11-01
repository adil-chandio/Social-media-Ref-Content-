"""v6b sprite re-extraction: fixes bg leaks, holes, fringes, hard smoke edges."""
from PIL import Image, ImageFilter, ImageChops, ImageDraw

E = 'refs/extract/'
W, H = 720, 1280


def fill_q(mask, iters=200):
    q = mask.resize((W // 4, H // 4), Image.NEAREST)
    inv = q.point(lambda p: 255 - p)
    seed = Image.new('L', q.size, 0)
    d = ImageDraw.Draw(seed)
    d.rectangle([0, 0, q.width - 1, 0], fill=255)
    d.rectangle([0, q.height - 1, q.width - 1, q.height - 1], fill=255)
    d.rectangle([0, 0, 0, q.height - 1], fill=255)
    d.rectangle([q.width - 1, 0, q.width - 1, q.height - 1], fill=255)
    seed = ImageChops.darker(seed, inv)
    for _ in range(iters):
        new = ImageChops.darker(seed.filter(ImageFilter.MaxFilter(3)), inv)
        if new.tobytes() == seed.tobytes():
            break
        seed = new
    return ImageChops.lighter(mask, ImageChops.subtract(inv, seed).resize(mask.size, Image.NEAREST))


def sprite(im, m, pad=2, ablu=0):
    bb = m.getbbox()
    b = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(W, bb[2] + pad), min(H, bb[3] + pad))
    r = im.crop(b).convert('RGBA')
    a = m.crop(b)
    if ablu:
        a = a.filter(ImageFilter.GaussianBlur(ablu))
    r.putalpha(a)
    return r


def newmask():
    m = Image.new('L', (W, H), 0)
    return m, m.load()


# ---------- bag (n47, white field): distance-from-white, exclude dark tag, fill bill holes
im = Image.open(E + 'n47.png').convert('RGB')
px = im.load()
hsv = im.convert('HSV')
hv = hsv.load()
m, mk = newmask()
for y in range(400, 880):
    for x in range(140, 600):
        r, g, b = px[x, y]
        hh, ss, vv = hv[x, y]
        if abs(r - 226) + abs(g - 226) + abs(b - 226) <= 100:
            continue
        if vv < 90 and ss < 60 and y < 700:      # rotated TWENTY tag fragment
            continue
        mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
m = fill_q(m)
m = m.filter(ImageFilter.MinFilter(3))           # kill white fringe
sprite(im, m, ablu=1).save(E + 'sp_bag.png')
print('bag', sprite(im, m).size)

# ---------- stool: stricter distance
m, mk = newmask()
for y in range(900, 1180):
    for x in range(160, 560):
        r, g, b = px[x, y]
        if abs(r - 226) + abs(g - 226) + abs(b - 226) > 140:
            mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
sprite(im, m, ablu=1).save(E + 'sp_stool.png')
print('stool', sprite(im, m).size)

# ---------- smoke (n70): soft alpha
im = Image.open(E + 'n70.png').convert('RGB')
hv = im.convert('HSV').load()
for name, (x0, y0, x1, y1) in (('sp_smoke_l', (0, 400, 240, 640)), ('sp_smoke_r', (470, 430, 720, 680))):
    m, mk = newmask()
    for y in range(y0, y1):
        for x in range(x0, x1):
            hh, ss, vv = hv[x, y]
            if ss < 40 and 110 < vv < 165:
                mk[x, y] = 255
    m = m.filter(ImageFilter.MaxFilter(5))
    sprite(im, m, ablu=5).save(E + f'{name}.png')
print('smoke ok')

# ---------- glove (n126): colour-only (black leather), no baked wireframe
im = Image.open(E + 'n126.png').convert('RGB')
hv = im.convert('HSV').load()
m, mk = newmask()
for y in range(640, 1030):
    for x in range(0, 300):
        hh, ss, vv = hv[x, y]
        if vv < 75 or (ss < 45 and 85 < vv < 180):
            mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
m = fill_q(m)
sprite(im, m, ablu=1).save(E + 'sp_glove.png')
print('glove', sprite(im, m).size)

# ---------- logo (n126): green square, fill holes (keeps ref wireframe bake)
m, mk = newmask()
for y in range(584, 690):
    for x in range(86, 244):
        hh, ss, vv = hv[x, y]
        if 40 < hh < 120 and ss > 110 and vv > 70:
            mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
m = fill_q(m)
sprite(im, m).save(E + 'sp_logo.png')
print('logo', sprite(im, m).size)

# ---------- jensen (n216): colour-only mask (no chevron bg leak)
im = Image.open(E + 'n216.png').convert('RGB')
hv = im.convert('HSV').load()
m, mk = newmask()
for y in range(290, 1250):
    for x in range(110, 630):
        hh, ss, vv = hv[x, y]
        darkred = ss > 100 and (hh < 12 or hh > 240)
        if (vv < 75 and not darkred) or (5 < hh < 32 and 40 < ss < 160 and 80 < vv < 235) or (ss < 45 and 85 < vv < 210 and not darkred):
            mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
m = fill_q(m)
sprite(im, m, ablu=1).save(E + 'sp_jensen.png')
print('jensen', sprite(im, m).size)
print('ALL SPRITES v6b DONE')
