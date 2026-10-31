from PIL import Image, ImageDraw, ImageFont
import math, io, os

W, H = 1200, 600
SS = 3
PAPER = (236, 233, 226, 255)
RED = (210, 31, 43, 255)
BG = (10, 10, 11, 255)

def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
            u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1])

def sample(segs, n=90):
    pts = []
    for s in segs:
        for i in range(n + 1):
            pts.append(cubic(s[0], s[1], s[2], s[3], i / n))
    return pts

def width_at(t, wmin, wmax):
    return wmin + (wmax - wmin) * (0.14 + 0.86 * math.sin(math.pi * min(max(t, 0.001), 0.999)) ** 0.65)

def draw_stroke(d, segs, color, wmin, wmax):
    pts = sample(segs)
    N = len(pts)
    for i, (x, y) in enumerate(pts):
        w = width_at(i / (N - 1), wmin, wmax) * SS
        d.ellipse([x*SS - w/2, y*SS - w/2, x*SS + w/2, y*SS + w/2], fill=color)

def draw_dot(d, x, y, r, color):
    d.ellipse([x*SS - r*SS, y*SS - r*SS, x*SS + r*SS, y*SS + r*SS], fill=color)

# ── legible stylised "Adil" ──
A1 = [((95,415),(120,340),(170,220),(215,160))]                      # A left diagonal
A2 = [((215,160),(240,220),(270,330),(300,415))]                    # A right diagonal
A3 = [((148,332),(190,322),(240,322),(272,332))]                    # crossbar
CN = [((300,415),(312,398),(318,372),(330,352))]                    # connector to d
DB = [((395,315),(360,300),(330,320),(330,360)), ((330,360),(330,400),(360,425),(390,415)),
      ((390,415),(410,408),(415,380),(415,350))]                    # d bowl (round)
DA = [((415,350),(425,330),(432,255),(438,195)), ((438,195),(446,250),(440,330),(442,390)),
      ((442,390),(444,412),(452,418),(462,410))]                    # d ascender + exit
IS = [((462,410),(470,395),(474,370),(478,345)), ((478,345),(480,370),(478,395),(482,408)),
      ((482,408),(490,418),(498,414),(504,402))]                    # i stroke + exit
LL = [((504,402),(512,340),(520,240),(536,192)), ((536,192),(546,250),(538,340),(542,388)),
      ((542,388),(546,416),(562,420),(576,404)), ((576,404),(610,380),(660,368),(710,368))]  # l + swash
CORE = [A1, A2, A3, CN, DB, DA, IS, LL]
IDOT = (492, 288)

UNDER = [((640,470),(480,505),(260,505),(150,470)), ((150,470),(240,492),(480,492),(600,462))]
SLASH1 = [((140,470),(260,462),(400,458),(520,455))]
SLASH2 = [((170,492),(260,486),(380,482),(470,480))]
CROWN = [((188,128),(196,110),(204,98),(212,98)), ((212,98),(220,98),(228,110),(236,128)),
         ((236,128),(244,110),(252,98),(260,98)), ((260,98),(268,98),(276,110),(284,128))]
ORBIT = [((710,368),(800,352),(820,292),(740,262)), ((740,262),(580,212),(240,206),(140,258)),
         ((140,258),(80,300),(110,470),(300,492)), ((300,492),(430,505),(560,492),(650,468))]
SWOOSH = [((150,468),(320,500),(520,498),(660,462))]

STYLES = {
 1: dict(name='THE FLOURISH', strokes=[(s, PAPER, 5, 15) for s in CORE] + [(UNDER, RED, 4, 10)], dot=(IDOT, RED, 11)),
 2: dict(name='THE MONARCH', strokes=[(s, PAPER, 5, 15) for s in CORE] + [(CROWN, RED, 5, 11), (SLASH1, PAPER, 4, 8), (SLASH2, PAPER, 3, 6)], dot=(IDOT, PAPER, 10)),
 3: dict(name='THE ORBIT', strokes=[(s, PAPER, 5, 15) for s in CORE] + [(ORBIT, RED, 3, 9)], dot=(IDOT, RED, 11)),
 4: dict(name='THE BOLD BRUSH', strokes=[(s, PAPER, 9, 27) for s in CORE] + [(SWOOSH, RED, 6, 14)], dot=(IDOT, RED, 14)),
}

def render_panel(idx):
    st = STYLES[idx]
    img = Image.new('RGBA', (W*SS, H*SS), BG)
    d = ImageDraw.Draw(img)
    for segs, color, wmin, wmax in st['strokes']:
        draw_stroke(d, segs, color, wmin, wmax)
    if st.get('dot'):
        (x, y), c, r = st['dot']
        draw_dot(d, x, y, r, c)
    return img.resize((W, H), Image.LANCZOS)

os.makedirs('signatures', exist_ok=True)
panels = {}
for i in range(1, 5):
    panels[i] = render_panel(i)
    panels[i].save('signatures/sig-%d.png' % i)

try:
    font = ImageFont.load_default(size=34)
except Exception:
    font = ImageFont.load_default()
sheet = Image.new('RGBA', (W*2 + 60, (H + 70)*2 + 30), (5, 5, 6, 255))
sd = ImageDraw.Draw(sheet)
pos = {1: (10, 10), 2: (W + 50, 10), 3: (10, H + 110), 4: (W + 50, H + 110)}
for i in range(1, 5):
    x, y = pos[i]
    sheet.paste(panels[i], (x, y))
    sd.text((x + 8, y + H + 12), '%d - %s' % (i, STYLES[i]['name']), fill=PAPER, font=font)
sheet.save('signatures/sheet.png')

def svg_for(idx):
    st = STYLES[idx]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600" fill="none">']
    for segs, color, wmin, wmax in st['strokes']:
        col = '#ece9e2' if color == PAPER else '#d21f2b'
        dpath = 'M%d,%d ' % segs[0][0] + ' '.join('C%d,%d %d,%d %d,%d' % (s[1][0], s[1][1], s[2][0], s[2][1], s[3][0], s[3][1]) for s in segs)
        out.append('<path d="%s" stroke="%s" stroke-width="%d" stroke-linecap="round" stroke-linejoin="round"/>' % (dpath, col, 9 if wmax < 20 else 18))
    if st.get('dot'):
        (x, y), c, r = st['dot']
        col = '#ece9e2' if c == PAPER else '#d21f2b'
        out.append('<circle cx="%d" cy="%d" r="%d" fill="%s"/>' % (x, y, r, col))
    out.append('</svg>')
    return '\n'.join(out)
for i in range(1, 5):
    io.open('signatures/sig-%d.svg' % i, 'w').write(svg_for(i))
print('rendered v2')
