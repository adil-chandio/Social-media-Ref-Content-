"""v6c/v8 asset extraction: exact-number frames + all 9 RGBA sprites (final recipes)."""
import subprocess, os
from PIL import Image, ImageFilter, ImageChops, ImageDraw

FF = open('/tmp/ffpath').read().strip()
E = 'refs/extract/'
os.makedirs(E, exist_ok=True)
W, H = 720, 1280

for n in (9, 15, 33, 47, 70, 84, 92, 100, 126, 216, 240):
    out = E + f'n{n}.png'
    if not os.path.exists(out):
        subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', 'refs/ref-reels-tutorial.mp4',
                        '-vf', f'select=eq(n\\,{n})', '-frames:v', '1', out], check=True)
print('frames ok')


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


# bag
im = Image.open(E + 'n47.png').convert('RGB')
px = im.load(); hv = im.convert('HSV').load()
m, mk = newmask()
for y in range(400, 880):
    for x in range(140, 600):
        if x < 215 and y < 580: continue
        r, g, b = px[x, y]; h, s, v = hv[x, y]
        if abs(r - 226) + abs(g - 226) + abs(b - 226) <= 100: continue
        if v < 90 and s < 60 and y < 700: continue
        mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
m = fill_q(m).filter(ImageFilter.MinFilter(3))
sprite(im, m, ablu=1).save(E + 'sp_bag.png')
# stool
m, mk = newmask()
for y in range(1010, 1180):
    for x in range(160, 560):
        r, g, b = px[x, y]; h, s, v = hv[x, y]
        if v < 140 or (10 < h < 32 and s > 60): mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
sprite(im, m, ablu=1).save(E + 'sp_stool.png')
# smoke (diff-based soft puffs)
a70 = Image.open(E + 'n70.png').convert('RGB')
diff = ImageChops.difference(a70, im).convert('L').point(lambda p: 255 if p > 16 else 0)
for name, (x0, y0, x1, y1) in (('sp_smoke_l', (0, 300, 250, 700)), ('sp_smoke_r', (460, 350, 720, 760))):
    box = Image.new('L', (W, H), 0); box.paste(255, (x0, y0, x1, y1))
    mm = ImageChops.darker(diff, box).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
    sprite(a70, mm, ablu=4).save(E + f'{name}.png')
# glove / logo / cash from n126
im = Image.open(E + 'n126.png').convert('RGB')
hv = im.convert('HSV').load()
m, mk = newmask()
for y in range(690, 1030):
    for x in range(0, 300):
        h, s, v = hv[x, y]
        if v < 75 or (s < 45 and 85 < v < 180): mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
m = fill_q(m)
sprite(im, m, ablu=1).save(E + 'sp_glove.png')
m, mk = newmask()
for y in range(584, 690):
    for x in range(86, 244):
        h, s, v = hv[x, y]
        if 40 < h < 120 and s > 100 and v > 40: mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
m = fill_q(m)
sprite(im, m).save(E + 'sp_logo.png')
m, mk = newmask()
for y in range(400, 900):
    for x in range(380, 700):
        h, s, v = hv[x, y]
        if v > 15 and not (s > 110 and (h < 14 or h > 242)): mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
sprite(im, m).save(E + 'sp_cash.png')
# jensen from n216
im = Image.open(E + 'n216.png').convert('RGB')
hv = im.convert('HSV').load()
m, mk = newmask()
for y in range(290, 1250):
    for x in range(110, 630):
        h, s, v = hv[x, y]
        darkred = s > 100 and (h < 12 or h > 240)
        if (v < 75 and not darkred) or (5 < h < 32 and 40 < s < 160 and 80 < v < 235) or (s < 45 and 85 < v < 210 and not darkred):
            mk[x, y] = 255
m = m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
m = fill_q(m)
sprite(im, m, ablu=1).save(E + 'sp_jensen.png')
# plate from n240 (contiguous yellow run)
im0 = Image.open(E + 'n240.png').convert('RGB')
hv = im0.convert('HSV').load()
def isy(x, y):
    h, s, v = hv[x, y]
    return 20 < h < 45 and s > 110 and v > 110
y = 855
if not isy(360, y):
    for yy in range(840, 990):
        if isy(360, yy): y = yy; break
x = 360
while isy(x - 1, y): x -= 1
x0 = x
x = 360
while isy(x + 1, y): x += 1
x1 = x
ys = [yy for yy in range(700, 1100) if sum(1 for xx in range(x0, x1, 6) if isy(xx, yy)) > 3]
y0, y1 = min(ys), max(ys)
m, mk = newmask()
for yy in range(y0 - 3, y1 + 4):
    for xx in range(x0 - 3, x1 + 4):
        if isy(xx, yy): mk[xx, yy] = 255
m = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(5))
m = fill_q(m, 120)
sprite(im0, m).save(E + 'sp_plate.png')
print('ALL SPRITES v6c DONE', [Image.open(E + f'sp_{n}.png').size for n in ('bag', 'stool', 'smoke_l', 'glove', 'logo', 'cash', 'jensen', 'plate')])
