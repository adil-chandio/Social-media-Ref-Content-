import base64, io, os
from PIL import Image

KIT = '/home/user/Social-media-Ref-Content-/profile-kit'
SITE = '/home/user/Social-media-Ref-Content-/portfolio-site'
os.makedirs(KIT + '/assets', exist_ok=True)

INK, INK2, PAPER, RED, MUT, LINE = '#0a0a0b', '#111113', '#ece9e2', '#d21f2b', '#8a8781', '#2a2a2e'
SANS = "Manrope,'Segoe UI',system-ui,sans-serif"
MONO = "'IBM Plex Mono',ui-monospace,SFMono-Regular,monospace"

# ── embeds ──
p = Image.open(SITE + '/assets/portrait-masked.png').convert('RGBA')
p = p.resize((260, int(p.height * 260 / p.width)), Image.LANCZOS)
buf = io.BytesIO(); p.save(buf, format='PNG', optimize=True)
PORTRAIT_B64 = base64.b64encode(buf.getvalue()).decode()
print('portrait b64 KB', len(PORTRAIT_B64) // 1024)
l = Image.open(SITE + '/assets/logo-64.png').convert('RGBA')
buf = io.BytesIO(); l.save(buf, format='PNG', optimize=True)
LOGO_B64 = base64.b64encode(buf.getvalue()).decode()

DOTS = '<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="#1c1c20"/></pattern>'

def card(w, h, uid):
    return ('<rect x="1" y="1" width="%d" height="%d" rx="22" fill="%s"/>'
            '<rect x="1" y="1" width="%d" height="%d" rx="22" fill="url(#dots%d)"/>'
            '<rect x="1" y="1" width="%d" height="%d" rx="22" fill="none" stroke="%s" stroke-width="2"/>'
            ) % (w - 2, h - 2, INK, w - 2, h - 2, uid, w - 2, h - 2, LINE)

def head(w, h, uid):
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 %d %d" width="%d" height="%d" font-family="%s">'
            '<defs>%s</defs>' % (w, h, w, h, SANS, DOTS.replace('id="dots"', 'id="dots%d"' % uid)))

# ═══ 1. HERO ═══
W, H = 1200, 640
roles = ['AI CONTENT CREATOR', 'YOUTUBE AUTOMATION', 'AI LEARNER', 'DEVELOPER']
role_txt = ''
vals = ['0;0;0;0', '']
for i, r in enumerate(roles):
    v = ['0'] * 5
    v[i] = '1'; v[4] = '1' if i == 0 else '0'
    # discrete slots of 3s in 12s
    vals_i = ['0', '0', '0', '0', '0']
    vals_i[i] = '1'
    if i == 0:
        seq = '1;0;0;0;1'
    else:
        seq = '0;' + ';'.join('1' if j == i else '0' for j in range(1, 4)) + ';0'
    role_txt += ('<text x="70" y="418" font-family="%s" font-size="26" letter-spacing="6" fill="%s" opacity="%s">%s'
                 '<animate attributeName="opacity" values="%s" keyTimes="0;0.25;0.5;0.75;1" calcMode="discrete" dur="12s" repeatCount="indefinite"/></text>'
                 ) % (MONO, RED, '1' if i == 0 else '0', r, seq)
hero = head(W, H, 1) + card(W, H, 1) + '''
<image x="880" y="96" width="260" height="373" xlink:href="data:image/png;base64,%s"/>
<ellipse cx="1010" cy="290" rx="150" ry="210" fill="none" stroke="%s" stroke-opacity=".35" stroke-width="1.5"/>
<image x="64" y="60" width="52" height="52" xlink:href="data:image/png;base64,%s"/>
<text x="130" y="95" font-family="%s" font-size="26" letter-spacing="4" fill="%s">MONARCH<tspan fill="%s">&#174;</tspan></text>
<text x="1136" y="95" text-anchor="end" font-family="%s" font-size="15" letter-spacing="3" fill="%s">AI FILMS &#8226; YT AUTOMATION &#8226; SYSTEMS</text>
<line x1="64" y1="130" x2="1136" y2="130" stroke="%s" stroke-width="1"/>
<g clip-path="url(#typewrap1)">
<text x="70" y="212" font-family="%s" font-size="24" letter-spacing="2" fill="%s">I&#8217;m Adil.<rect x="212" y="188" width="14" height="30" fill="%s"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect></text>
</g>
<clipPath id="typewrap1"><rect x="60" y="170" width="0" height="60"><animate attributeName="width" values="0;240" dur="0.9s" begin="0.2s" fill="freeze"/></rect></clipPath>
<g clip-path="url="namemask1">
<text x="64" y="330" font-size="118" font-weight="800" letter-spacing="-3" fill="%s">ADIL CHANDIO</text>
</g>
<clipPath id="namemask1"><rect x="0" y="352" width="1200" height="220"><animate attributeName="y" values="352;180" dur="1s" begin="0.5s" fill="freeze" calcMode="spline" keySplines=".16 1 .3 1"/></rect></clipPath>
%s
<text x="70" y="470" font-size="24" fill="%s">I turn AI into films, films into channels, and channels into systems that run themselves.</text>
<text x="70" y="560" font-family="%s" font-size="15" letter-spacing="4" fill="%s">21 &#8226; SELF-MADE &#8226; STILL HUNGRY</text>
<circle cx="1108" cy="552" r="5" fill="%s"><animate attributeName="opacity" values="1;.2;1" dur="2.2s" repeatCount="indefinite"/></circle>
<text x="1092" y="558" text-anchor="end" font-family="%s" font-size="15" letter-spacing="3" fill="%s">EST. THE $400 DELL ERA</text>
</svg>''' % (PORTRAIT_B64, RED, LOGO_B64, MONO, PAPER, RED, MONO, MUT, LINE, MONO, PAPER, RED, PAPER, role_txt, MUT, MONO, MUT, RED, MONO, MUT)
io.open(KIT + '/assets/hero.svg', 'w').write(hero)

# ═══ 2. ABOUT-LIFE ═══
W, H = 1200, 560
caps = [('01', 'Reference-matched films', 'style-matched frame for frame, rebuilt clean'),
        ('02', 'YouTube automation systems', 'channels that plan, script and schedule themselves'),
        ('03', 'AI-folded content', 'shorts, films, voice, motion — new tools every day')]
cap_txt = ''
y = 190
for n, t, s in caps:
    cap_txt += ('<text x="70" y="%d" font-family="%s" font-size="20" fill="%s">%s</text>'
                '<text x="130" y="%d" font-size="34" font-weight="800" fill="%s">%s</text>'
                '<text x="130" y="%d" font-size="19" fill="%s">%s</text>'
                '<rect x="70" y="%d" width="46" height="3" fill="%s"/>') % (y, MONO, RED, n, y + 4, PAPER, t, y + 36, MUT, s, y + 16, RED)
    y += 108
slides = [('FILMS &amp; EDITS', 'cuts locked to the beat, composites, clean finish'),
          ('AI TOOLS DAILY', 'learning new tools every day, folding them into content'),
          ('CREATIVITY FIRST', 'I love creativity — it&#8217;s the whole reason I start')]
sl_txt = ''
for i, (t, s) in enumerate(slides):
    seq = '1;0;0;0' if i == 0 else ('0;' + ';'.join('1' if j == i else '0' for j in range(1, 3)) + ';0')
    kt = '0;0.3333;0.6666;1'
    sl_txt += ('<g opacity="%s"><animate attributeName="opacity" values="%s" keyTimes="%s" calcMode="discrete" dur="12s" repeatCount="indefinite"/>'
               '<text x="700" y="250" font-family="%s" font-size="26" letter-spacing="3" fill="%s">%s</text>'
               '<text x="700" y="292" font-size="20" fill="%s">%s</text></g>') % ('1' if i == 0 else '0', seq, kt, MONO, RED, t, MUT, s)
bars = ''
bw = [ ('0;108;108;108;0', '0;0.3332;0.3333;0.9999;1'),
       ('0;0;108;108;0', '0;0.3333;0.6665;0.9999;1'),
       ('0;0;0;108;108', '0;0.3333;0.6666;0.9999;1') ]
for i, (v, kt) in enumerate(bw):
    bars += ('<rect x="%d" y="352" width="0" height="4" rx="2" fill="%s"><animate attributeName="width" values="%s" keyTimes="%s" dur="12s" repeatCount="indefinite"/></rect>'
             ) % (700 + i * 124, RED if True else PAPER, v, kt)
    bars += '<rect x="%d" y="352" width="108" height="4" rx="2" fill="#222226"/>' % (700 + i * 124)
about = head(W, H, 2) + card(W, H, 2) + '''
<text x="70" y="92" font-family="%s" font-size="16" letter-spacing="4" fill="%s">01 &#8212; WHAT I ACTUALLY DO</text>
<rect x="640" y="150" width="496" height="260" rx="18" fill="%s" stroke="%s"/>
%s%s%s
<text x="700" y="204" font-family="%s" font-size="15" letter-spacing="3" fill="%s">OFF THE CLOCK</text>
</svg>''' % (MONO, MUT, INK2, LINE, cap_txt, sl_txt, bars, MONO, MUT)
# bars drawn over track: reorder -> put tracks first (rebuild bars properly)
bars2 = ''
for i, (v, kt) in enumerate(bw):
    bars2 += '<rect x="%d" y="352" width="108" height="4" rx="2" fill="#222226"/>' % (700 + i * 124)
    bars2 += ('<rect x="%d" y="352" width="0" height="4" rx="2" fill="%s"><animate attributeName="width" values="%s" keyTimes="%s" dur="12s" repeatCount="indefinite"/></rect>'
              ) % (700 + i * 124, RED, v, kt)
about = about.replace(bars, bars2)
io.open(KIT + '/assets/about-life.svg', 'w').write(about)

# ═══ 3. STACK ═══
W, H = 1200, 560
orbits = ''
for i, (rx, ry, rot, dur) in enumerate([(430, 150, -10, 26), (330, 110, -10, 20), (230, 74, -10, 15)]):
    orbits += ('<ellipse cx="600" cy="300" rx="%d" ry="%d" transform="rotate(%d 600 300)" fill="none" stroke="%s" stroke-width="1.4" stroke-dasharray="7 9">'
               '<animate attributeName="stroke-dashoffset" from="0" to="-160" dur="%ss" repeatCount="indefinite"/></ellipse>') % (rx, ry, rot, LINE, dur)
chips = [('AI CONTENT', 250, 180), ('YT AUTOMATION', 760, 168), ('VIDEO EDITING', 168, 330),
         ('WEB DESIGN', 872, 330), ('PYTHON', 372, 452), ('FFMPEG', 600, 470), ('GITHUB ACTIONS', 806, 440),
         ('WORKFLOW SYSTEMS', 470, 128)]
chips_txt = ''
for i, (t, x, y) in enumerate(chips):
    wch = 14 * len(t) + 34
    chips_txt += ('<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -6;0 0" dur="%ss" begin="%ss" repeatCount="indefinite"/>'
                  '<rect x="%d" y="%d" width="%d" height="44" rx="22" fill="%s" stroke="%s"/>'
                  '<circle cx="%d" cy="%d" r="4" fill="%s"/>'
                  '<text x="%d" y="%d" font-family="%s" font-size="16" letter-spacing="2" fill="%s">%s</text></g>'
                  ) % (3 + i * 0.3, i * 0.4, x, y, wch, INK2, LINE, x + 22, y + 22, RED, x + 38, y + 28, MONO, PAPER, t)
stack = head(W, H, 3) + card(W, H, 3) + '''
<text x="70" y="86" font-family="%s" font-size="16" letter-spacing="4" fill="%s">02 &#8212; THE STACK IN ORBIT</text>
%s<circle cx="600" cy="300" r="34" fill="%s"/><circle cx="600" cy="300" r="46" fill="none" stroke="%s" stroke-opacity=".5"/>
<image x="576" y="276" width="48" height="48" xlink:href="data:image/png;base64,%s"/>
%s
<text x="600" y="540" text-anchor="middle" font-family="%s" font-size="14" letter-spacing="4" fill="%s">TOOLS I TRUST &#8212; DISCIPLINE OVER MOOD</text>
</svg>''' % (MONO, MUT, orbits, INK2, RED, LOGO_B64, chips_txt, MONO, MUT)
io.open(KIT + '/assets/stack.svg', 'w').write(stack)

# ═══ 4. ID-DASHBOARD ═══
W, H = 1200, 640
CX, CY = 600, 40
metrics = [('583K+', 'VIEWS'), ('+1.6K', 'SUBS'), ('74%', 'RETENTION')]
m_txt = ''
for i, (v, lb) in enumerate(metrics):
    x = 470 + i * 118
    m_txt += ('<text x="%d" y="472" font-size="30" font-weight="800" fill="%s">%s</text>'
              '<text x="%d" y="496" font-family="%s" font-size="12" letter-spacing="2" fill="%s">%s</text>'
              ) % (x, PAPER, v, x, MONO, MUT, lb)
barcode = ''
import random
random.seed(7)
bx = 470
while bx < 720:
    bw_ = random.choice([2, 3, 5, 7])
    barcode += '<rect x="%d" y="520" width="%d" height="42" fill="%s"/>' % (bx, bw_, PAPER if random.random() > .3 else MUT)
    bx += bw_ + random.choice([2, 4])
idcard = head(W, H, 4) + card(W, H, 4) + '''
<text x="70" y="86" font-family="%s" font-size="16" letter-spacing="4" fill="%s">03 &#8212; CREATOR ID &#8226; VERIFIED OCT 2026</text>
<path d="M520,0 L580,86" stroke="%s" stroke-width="10" stroke-linecap="round"/>
<path d="M680,0 L620,86" stroke="%s" stroke-width="10" stroke-linecap="round"/>
<rect x="584" y="82" width="32" height="26" rx="6" fill="%s" stroke="%s"/>
<g transform="rotate(0 600 96)">
<animateTransform attributeName="transform" type="rotate" values="0 600 96;5 600 96;-4 600 96;3 600 96;-2 600 96;1.2 600 96;-0.7 600 96;0.4 600 96;0 600 96" keyTimes="0;0.12;0.26;0.4;0.54;0.68;0.82;0.92;1" dur="2.4s" fill="freeze"/>
<g>
<animateTransform attributeName="transform" type="rotate" values="-1.7 600 96;1.7 600 96;-1.7 600 96" dur="4.6s" begin="2.4s" repeatCount="indefinite" additive="sum"/>
<rect x="440" y="108" width="320" height="470" rx="20" fill="%s" stroke="%s" stroke-width="2"/>
<rect x="440" y="108" width="320" height="86" rx="20" fill="%s"/>
<image x="462" y="124" width="52" height="52" xlink:href="data:image/png;base64,%s"/>
<text x="528" y="150" font-family="%s" font-size="20" letter-spacing="3" fill="%s">MONARCH<tspan fill="%s">&#174;</tspan></text>
<text x="528" y="176" font-family="%s" font-size="12" letter-spacing="3" fill="%s">CREATOR ID &#8212; MMXXVI</text>
<image x="470" y="214" width="150" height="214" xlink:href="data:image/png;base64,%s"/>
<rect x="470" y="214" width="150" height="214" rx="10" fill="none" stroke="%s"/>
<text x="640" y="250" font-size="30" font-weight="800" fill="%s">ADIL</text>
<text x="640" y="284" font-size="30" font-weight="800" fill="%s">CHANDIO</text>
<text x="640" y="318" font-family="%s" font-size="13" letter-spacing="2" fill="%s">AI FILMS /</text>
<text x="640" y="338" font-family="%s" font-size="13" letter-spacing="2" fill="%s">YT AUTOMATION</text>
<rect x="640" y="360" width="90" height="26" rx="13" fill="%s"/>
<text x="685" y="378" text-anchor="middle" font-family="%s" font-size="12" letter-spacing="2" fill="#fff">VERIFIED</text>
%s%s
<g clip-path="url="foil4"><rect x="-260" y="108" width="180" height="470" fill="#ffffff" opacity=".07" transform="skewX(-18)"><animateTransform attributeName="transform" type="translate" values="-100 0;760 0;760 0" keyTimes="0;0.45;1" dur="6s" begin="1s" repeatCount="indefinite" additive="sum"/></rect></g>
<clipPath id="foil4"><rect x="440" y="108" width="320" height="470" rx="20"/></clipPath>
</g></g>
</svg>''' % (MONO, MUT, '#1c1c20', '#1c1c20', '#3a3a40', LINE, INK2, LINE, INK2, LOGO_B64, MONO, PAPER, RED, MONO, MUT, PORTRAIT_B64, LINE, PAPER, PAPER, MONO, MUT, MONO, MUT, RED, MONO, m_txt, barcode)
io.open(KIT + '/assets/id-dashboard.svg', 'w').write(idcard)

# ═══ 5. CONNECT ═══
W, H = 1200, 520
TK = 'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z'
IG = 'M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z'
GM = 'M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z'
GH = 'M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12'
soc = [(TK, 'TIKTOK', '@adil.chandiio'), (IG, 'INSTAGRAM', '@adill.chandio'),
       (GM, 'GMAIL', 'workadilchandio@gmail.com'), (GH, 'GITHUB', '@adil-chandio')]
cards = ''
for i, (path, name, handle) in enumerate(soc):
    x = 560 + (i % 2) * 300
    y = 120 + (i // 2) * 150
    cards += ('<g><rect x="%d" y="%d" width="280" height="120" rx="18" fill="%s" stroke="%s"/>'
              '<g transform="translate(%d,%d) scale(1.5)" fill="%s"><path d="%s"/></g>'
              '<text x="%d" y="%d" font-family="%s" font-size="19" letter-spacing="3" fill="%s">%s</text>'
              '<text x="%d" y="%d" font-family="%s" font-size="13" fill="%s">%s</text>'
              '<path d="M%d,%d l14,0 m-6,-6 l6,6 l-6,6" stroke="%s" stroke-width="2.4" fill="none" stroke-linecap="round">'
              '<animateTransform attributeName="transform" type="translate" values="0 0;6 0;0 0" dur="1.6s" begin="%ss" repeatCount="indefinite"/></path></g>'
              ) % (x, y, INK2, LINE, x + 24, y + 24, PAPER, path, x + 76, y + 52, MONO, PAPER, name, x + 76, y + 80, MONO, MUT, handle, x + 236, y + 60, RED, i * 0.25)
conn = head(W, H, 5) + card(W, H, 5) + '''
<image x="70" y="120" width="220" height="315" xlink:href="data:image/png;base64,%s"/>
<text x="330" y="200" font-size="76" font-weight="800" letter-spacing="-2" fill="%s">LET&#8217;S</text>
<text x="330" y="276" font-size="76" font-weight="800" letter-spacing="-2" fill="%s">TALK.</text>
<text x="330" y="330" font-size="19" fill="%s">I reply fast,</text>
<text x="330" y="358" font-size="19" fill="%s">usually with too many ideas.</text>
<rect x="330" y="386" width="64" height="4" fill="%s"/>
%s
</svg>''' % (PORTRAIT_B64, PAPER, RED, MUT, MUT, RED, cards)
io.open(KIT + '/assets/connect.svg', 'w').write(conn)

for f in ['hero', 'about-life', 'stack', 'id-dashboard', 'connect']:
    print(f, os.path.getsize(KIT + '/assets/%s.svg' % f) // 1024, 'KB')
print('KIT DONE')
