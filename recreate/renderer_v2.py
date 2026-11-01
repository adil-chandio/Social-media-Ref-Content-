"""
Recreation renderer v2 — built from fresh forensic breakdown (FORENSIC_REPORT_v2.md)
720x1280 @ 30fps, 6 sections matching original timings/palette.
Narration: s1_fast..s6_fast.mp3 (already 1.59x compressed to match original cadence).
"""
import cv2, numpy as np, subprocess, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 720, 1280, 30
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(sz, bold=True):
    return ImageFont.truetype(BOLD if bold else REG, sz)

# ---- palette from v2 forensic ----
BRIGHT_BG  = (194,194,194)   # #c0c0c0
BRIGHT_BG2 = (168,168,168)   # #a8a8a8
BRIGHT_HI  = (208,208,205)   # #d0d0cf
BRAND_RED  = (79,0,7)        # #4f0007
BRAND_RED2 = (104,3,13)      # #68030d
NEAR_BLACK = (20,3,5)        # #140305
NEAR_BLACK2= (23,8,10)       # #17080a
GREEN_FLASH = (130,144,135)  # #829087
DARK_GRAY  = (54,80,20)      # #365014

def lerp(a,b,t): return int(a+(b-a)*t)
def mix(c1,c2,t): return tuple(lerp(c1[i],c2[i],t) for i in range(3))

def base(color):
    return np.full((H,W,3), color, np.uint8)

def draw_text_cv(img, text, cx, cy, size, color, bold=True):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = font(size, bold)
    bbox = d.textbbox((0,0), text, font=f)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    d.text((cx-tw/2-bbox[0], cy-th/2-bbox[1]), text, font=f, fill=color)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def draw_text_cv_off(img, text, x, y, size, color, bold=True):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = font(size, bold)
    d.text((x,y), text, font=f, fill=color)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def rect(img, x0,y0,x1,y1, color):
    cv2.rectangle(img, (x0,y0), (x1,y1), color, -1)

def rounded_rect(img, x0,y0,x1,y1, rad, color):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    d.rounded_rectangle([x0,y0,x1,y1], radius=rad, fill=color)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def fade(img, alpha):
    return cv2.convertScaleAbs(img, alpha=alpha, beta=0)

# ---------- SECTION 1: Bright title card (0-3.16s) ----------
def scene1(t):
    img = base(BRIGHT_BG)
    # subtle vertical gradient (lower to match original ~154-194)
    grad = np.linspace(200, 165, H)[:,None].astype(np.uint8)
    img[:,:,0] = grad; img[:,:,1] = grad; img[:,:,2] = grad
    # slide-up title
    slide = min(1.0, t/0.4)
    ease = 1-(1-slide)**3
    cy = int((1280*0.28) + (1-ease)*(-200))
    draw_text_cv(img, "VIRAL REELS", W//2, cy, 120, (40,40,40))
    draw_text_cv(img, "ANIMATIONS", W//2, cy+140, 80, (70,70,70))
    # play badge bottom
    if t>0.8:
        badge = min(1.0, (t-0.8)/0.3)
        a = int(badge*255)
        cv2.circle(img, (W//2, int(H*0.78)), 50, (30,30,30), -1)
        cv2.circle(img, (W//2, int(H*0.78)), 50, (255,255,255), 4)
        cv2.circle(img, (W//2, int(H*0.78)), 50, (255,255,255), 2)
        cv2.drawText if False else None
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(pil)
        d.polygon([(W//2-8,int(H*0.78)-18),(W//2-8,int(H*0.78)+18),(W//2+20,int(H*0.78))], fill=(255,255,255))
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return img

# ---------- SECTION 2: Dark AE demo (3.16-8.25s) ----------
def scene2(t, sec):
    img = base(NEAR_BLACK)
    # neutral-dark base + slight red tint (match original mean ~35-45)
    grad = np.linspace(52, 34, H)[:,None].astype(np.uint8)
    img[:,:,0] = grad + 6; img[:,:,1] = grad; img[:,:,2] = grad
    # TR brightest = timeline panel on right
    # Left: preview window (middle-center brighter)
    px0,py0,px1,py1 = 80, 180, 480, 760
    rounded_rect(img, px0,py0,px1,py1, 16, (35,35,40))
    rounded_rect(img, px0+8,py0+8,px1-8,py1-8, 12, (50,50,58))
    # preview content (animated bars)
    bar_t = (t*0.8) % 1.0
    for i in range(5):
        bx = px0+40 + i*70
        bh = int(120 + 80*np.sin(t*2 + i*0.7))
        rect(img, bx, py1-40-bh, bx+40, py1-40, (180,180,190))
    # Layers panel top-left
    rounded_rect(img, 80, 80, 480, 160, 8, (40,40,48))
    for i in range(3):
        rect(img, 95, 95+i*30, 105, 110+i*30, BRAND_RED2)
        draw_text_cv_off(img, f"Layer {i+1}", 120, 92+i*30, 22, (200,200,200))
    # Timeline panel right (TR brightest)
    tx0,ty0,tx1,ty1 = 500, 180, 680, 760
    rounded_rect(img, tx0,ty0,tx1,ty1, 12, (55,55,62))
    # timeline ruler
    rect(img, tx0, ty0, tx1, ty0+24, (70,70,80))
    # moving playhead
    ph_x = tx0 + int(180*(t*0.7 % 1.0))
    cv2.line(img, (ph_x, ty0), (ph_x, ty1), (255,255,255), 3)
    # keyframe pulses
    for i in range(4):
        kx = tx0 + 30 + i*40
        ky = ty0 + 100 + int(40*np.sin(t*3+i))
        cv2.circle(img, (kx,ky), 6, (80,200,255), -1)
    # step label top
    draw_text_cv_off(img, "STEP 1 · IMPORT", 80, 50, 26, (220,220,220))
    return img

# ---------- SECTION 3: Flash transition (8.25-11.83s) ----------
def scene3(t):
    # green flash -> bright "STEP 2 · ADD TEXT"
    flash_dur = 0.5
    if t < flash_dur:
        # green flash on black
        a = int(t/flash_dur * 255)
        img = base(NEAR_BLACK)
        img = cv2.addWeighted(img, 1-t/flash_dur, base(GREEN_FLASH), t/flash_dur, 0)
        return img
    # bright section (use BRIGHT_BG not HI for closer match to original)
    img = base(BRIGHT_BG)
    slide = min(1.0, (t-flash_dur)/0.4)
    ease = 1-(1-slide)**3
    cy = int(1280*0.35) + (1-ease)*(-150)
    draw_text_cv(img, "STEP 2", W//2, cy, 90, (30,30,30))
    draw_text_cv(img, "· ADD TEXT", W//2, cy+110, 70, (50,50,50))
    # animated text layer
    if t > flash_dur+0.6:
        pat = t*2 % 2.0
        cy2 = int(H*0.6 + 30*np.sin(pat))
        draw_text_cv(img, "Hello Reels", W//2, cy2, 60, (200,40,40))
    return img

# ---------- SECTION 4: Bright text showcase (11.83-15.77s) ----------
def scene4(t):
    img = base(BRIGHT_BG)
    grad = np.linspace(205, 168, H)[:,None].astype(np.uint8)
    img[:,:,0] = grad; img[:,:,1] = grad; img[:,:,2] = grad
    # big number showcase (matches "TWENTY"/"Billion" from original OCR)
    draw_text_cv(img, "1,000,000+", W//2, 300, 90, (30,30,30))
    draw_text_cv(img, "VIEWS", W//2, 400, 40, (80,80,80))
    # animation demos
    anim = (t*1.2) % 3.0
    if anim < 1.0:
        # fade in
        a = min(1.0, anim)
        img = cv2.addWeighted(base((255,255,255)), a, img, 1-a, 0)
        draw_text_cv(img, "FADE IN", W//2, 650, 60, (30,30,30))
    elif anim < 2.0:
        # slide up
        dy = int((2-anim)*(-200)+200)
        draw_text_cv(img, "SLIDE UP", W//2, 650+dy, 60, (30,30,30))
    else:
        # pop
        s = 0.5 + (anim-2.0)*2
        draw_text_cv(img, "POP", W//2, 650, int(60*s), (30,30,30))
    # stats bottom
    draw_text_cv(img, "1080×1920 · 30FPS", W//2, 900, 36, (60,60,60))
    draw_text_cv(img, "EXPORT", W//2, 1000, 50, (180,40,40))
    return img

# ---------- SECTION 5: Dark demo 2 (15.77-20.32s) ----------
def scene5(t):
    img = base(NEAR_BLACK)
    grad = np.linspace(50, 32, H)[:,None].astype(np.uint8)
    img[:,:,0] = grad + 6; img[:,:,1] = grad; img[:,:,2] = grad
    # preview window left
    rounded_rect(img, 80, 180, 480, 760, 16, (35,35,40))
    rounded_rect(img, 88,188, 472,752, 12, (50,50,58))
    # transition wave
    for i in range(12):
        px = 100 + i*30
        off = int(30*np.sin(t*2.5 + i*0.5))
        cv2.line(img, (px, 470), (px, 470+off), BRAND_RED2, 4)
    # timeline right (TR brightest)
    rounded_rect(img, 500, 180, 680, 760, 12, (55,55,62))
    rect(img, 500, 180, 680, 204, (70,70,80))
    # transition marker
    mx = 520 + int(140*(t*0.5 % 1.0))
    cv2.line(img, (mx,180),(mx,760),(255,255,255),3)
    # keyframe pulses
    for i in range(5):
        kx = 530 + i*30
        ky = 300 + int(30*np.sin(t*3+i))
        cv2.circle(img,(kx,ky),5,(80,200,255),-1)
    # export settings
    draw_text_cv_off(img, "STEP 3 · EXPORT", 80, 50, 26, (220,220,220))
    draw_text_cv_off(img, "H.264 · CRF 18", 80, 820, 24, (180,180,180))
    draw_text_cv_off(img, "AAC 320kbps", 80, 860, 24, (180,180,180))
    return img

# ---------- SECTION 6: Dark outro (20.32-23.43s) ----------
def scene6(t):
    img = base(NEAR_BLACK)
    grad = np.linspace(48, 30, H)[:,None].astype(np.uint8)
    img[:,:,0] = grad + 6; img[:,:,1] = grad; img[:,:,2] = grad
    slide = min(1.0, t/0.5)
    ease = 1-(1-slide)**3
    cy = int(1280*0.4) + (1-ease)*(-200)
    draw_text_cv(img, "THAT'S IT!", W//2, cy, 100, (220,60,60))
    draw_text_cv(img, "Tag someone who needs this 🔥", W//2, cy+150, 36, (160,160,160))
    # fade out last 0.6s
    if t > 2.6:
        a = 1 - min(1.0, (t-2.6)/0.6)
        img = cv2.convertScaleAbs(img, alpha=a, beta=0)
    return img

# ---------- main render ----------
SECTIONS = [
    (0.00, 3.16, scene1),
    (3.16, 8.25, lambda t: scene2(t, 0)),
    (8.25, 11.83, scene3),
    (11.83, 15.77, scene4),
    (15.77, 20.32, lambda t: scene5(t)),
    (20.32, 23.43, scene6),
]

def render_frame(idx):
    t = idx / FPS
    for start, end, fn in SECTIONS:
        if start <= t < end:
            return fn(t - start)
    return scene6(t - SECTIONS[-1][0])

def main():
    os.makedirs("recreate/v2_frames", exist_ok=True)
    cmd = [
        "ffmpeg","-y","-f","image2pipe","-vcodec","png","-r",str(FPS),"-i","-",
        "-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-preset","medium",
        "recreate/v2_silent.mp4"
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    total = int(SECTIONS[-1][1] * FPS)
    for i in range(total):
        img = render_frame(i)
        # downscale-encode PNG
        cv2.imwrite("/tmp/f.png", img)
        with open("/tmp/f.png","rb") as fh:
            p.stdin.write(fh.read())
    p.stdin.close(); p.wait()
    print(f"Rendered {total} frames -> recreate/v2_silent.mp4")
    print(f"Exit: {p.returncode}")

if __name__ == "__main__":
    main()
