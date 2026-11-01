#!/usr/bin/env python3
"""
Viral Reels Animation Tutorial — ORIGINAL recreation renderer.
720x1280 @ 30fps. Renders frames procedurally with PIL+numpy and pipes
rawvideo to ffmpeg. Design follows the forensic breakdown of the
reference video: bright title card -> dark AE demo -> flash -> bright
text showcase -> dark demo -> dark outro.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess, math, os

W, H, FPS = 720, 1280, 30

# ---------------- palette (from forensic color analysis) ----------------
BLACK    = (0, 0, 0)
NEAR_BLK = (24, 3, 3)
DARK_RED = (72, 4, 4)
MAROON   = (96, 5, 5)
DEEP_RED = (48, 2, 2)
BRIGHT   = (192, 192, 192)
BRIGHT2  = (168, 168, 168)
WHITE    = (255, 255, 255)
ACCENT   = (255, 59, 48)
ACCENT2  = (232, 69, 60)
PANEL    = (38, 38, 42)
PANEL2   = (52, 52, 58)
BORDER   = (84, 84, 92)
TXT_DARK = (24, 24, 28)
TXT_LITE = (245, 245, 248)
GRAY_TXT = (120, 120, 128)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
def F(size, bold=True):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"{FONT_DIR}/{name}", size)

# ---------------- animation helpers ----------------
def lerp(a, b, t): return a + (b - a) * max(0.0, min(1.0, t))
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
def fade(t, dur=0.4): return ease(t / dur)
def slide_up(t, dist=80, dur=0.5):
    a = ease(t / dur)
    return 1 - a, -dist * (1 - a)
def slide_x(t, dist=60, dur=0.5):
    a = ease(t / dur)
    return 1 - a, dist * (1 - a)
def pop(t, dur=0.5):
    """scale pulse 1 -> 1.18 -> 1"""
    a = max(0.0, min(1.0, t / dur))
    if a < 0.5:
        return lerp(1.0, 1.18, a * 2)
    return lerp(1.18, 1.0, (a - 0.5) * 2)

def linear_gradient(w, h, top, bot):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / max(1, h - 1)
        arr[y, :] = tuple(int(lerp(top[i], bot[i], t)) for i in range(3))
    return arr

def radial_glow(img, cx, cy, radius, color, strength):
    arr = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    mask = np.clip(1 - d / radius, 0, 1) ** 2
    for i in range(3):
        arr[:, :, i] += mask * color[i] * strength
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def vgrad_bg(top, bot):
    return Image.fromarray(linear_gradient(W, H, top, bot))

def rgba_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def draw_text(img, text, cx, cy, font, fill, stroke=0, stroke_fill=None,
              alpha=1.0, shadow=None):
    """Centered text; optional outline stroke & drop shadow."""
    tmp = rgba_layer()
    d = ImageDraw.Draw(tmp)
    if shadow:
        sx, sy = shadow
        d.text((cx + sx, cy + sy), text, font=font, fill=shadow[2] if len(shadow) > 2 else (0,0,0,160))
    d.text((cx, cy), text, font=font, fill=fill + (int(255 * alpha),) if alpha < 1 else fill,
           stroke_width=stroke, stroke_fill=stroke_fill)
    img.paste(Image.alpha_composite(img.convert("RGBA"), tmp).convert("RGB"), (0, 0), tmp)

def text_alpha(img, layer_alpha):
    """composite an RGBA layer onto img with global alpha"""
    base = img.convert("RGBA")
    comp = Image.alpha_composite(base, layer_alpha)
    return comp.convert("RGB")

def rounded(img, box, radius, fill, outline=None, width=2):
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def panel(img, box, bg=PANEL, border=BORDER, width=2, radius=14):
    if border is None:
        rounded(img, box, radius, bg + (255,), None, 0)
    else:
        rounded(img, box, radius, bg + (255,), border + (255,), width)

def tick(n): return n % FPS

# ---------------- SECTION 1: title card (bright, high motion) ----------------
def scene1(t, dur):
    img = vgrad_bg((208, 208, 214), (138, 138, 144)).convert("RGBA")
    # top red accent bar grows
    bar_w = lerp(0, 220, ease(t / 0.5))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([W/2 - bar_w/2, 70, W/2 + bar_w/2, 78], 4, ACCENT + (255,))
    # main title: slide up + fade
    a1, dy1 = slide_up(t - 0.15, dist=120, dur=0.55)
    f1 = F(88)
    layer = rgba_layer()
    dl = ImageDraw.Draw(layer)
    dl.text((W/2, 330 + dy1), "VIRAL REELS", font=f1, fill=(TXT_DARK[0], TXT_DARK[1], TXT_DARK[2], int(255*a1)),
            stroke_width=2, stroke_fill=(0, 0, 0, int(60*a1)))
    a2, dy2 = slide_up(t - 0.45, dist=120, dur=0.55)
    dl.text((W/2, 440 + dy2), "ANIMATIONS", font=f1, fill=(TXT_DARK[0], TXT_DARK[1], TXT_DARK[2], int(255*a2)),
            stroke_width=2, stroke_fill=(0, 0, 0, int(60*a2)))
    img = text_alpha(img, layer)
    # red underline grows under text
    uw = lerp(0, 300, ease((t - 0.9) / 0.6))
    d = ImageDraw.Draw(img)
    if uw > 2:
        d.rounded_rectangle([W/2 - uw/2, 530, W/2 + uw/2, 538], 4, ACCENT + (255,))
    # subtitle
    a3 = fade(t - 1.2, 0.5)
    draw_text(img, "QUICK TUTORIAL · AFTER EFFECTS", W/2, 590, F(34, bold=False),
              (90, 90, 96), alpha=a3)
    # play badge with pulse
    a4 = fade(t - 1.8, 0.5)
    if a4 > 0:
        pulse = 1 + 0.06 * math.sin(t * 6)
        r = int(44 * pulse * a4)
        box = [W/2 - r, 780 - r, W/2 + r, 780 + r]
        rounded(img, box, r, (TXT_DARK[0], TXT_DARK[1], TXT_DARK[2], int(255*a4)), None, 0)
        d = ImageDraw.Draw(img)
        d.polygon([(W/2 - 16*a4, 780 - 22*a4), (W/2 - 16*a4, 780 + 22*a4), (W/2 + 26*a4, 780)], fill=WHITE + (int(255*a4),))
        draw_text(img, "TAP TO PLAY", W/2, 880, F(30, bold=False), (90, 90, 96), alpha=a4)
    # end fade to black
    if t > dur - 0.35:
        k = ease((t - (dur - 0.35)) / 0.35)
        img = text_alpha(img, Image.new("RGBA", (W, H), (0, 0, 0, int(255*k))))
    return img.convert("RGB")

# ---------------- SECTION 2: dark AE demo (dark red on black) ----------------
def ae_mock(t, dur, label, show_export=False):
    img = vgrad_bg((20, 6, 8), (6, 2, 3)).convert("RGBA")
    img = radial_glow(img, W/2, 120, 560, (120, 8, 8), 0.55)
    d = ImageDraw.Draw(img)
    # top bar
    panel(img, [24, 24, W-24, 96], bg=(28, 28, 32), border=(70, 70, 76))
    d = ImageDraw.Draw(img)
    d.text((48, 58), "AFTER EFFECTS", font=F(30), fill=TXT_LITE)
    for i, m in enumerate(["File", "Edit", "Composition", "Layer", "Effects", "Help"]):
        d.text((170 + i*86, 62), m, font=F(20, bold=False), fill=GRAY_TXT)
    # preview panel
    panel(img, [24, 116, 430, 560], bg=(18, 18, 22), border=(70, 70, 76))
    d.text((48, 134), "PREVIEW", font=F(24), fill=GRAY_TXT)
    # crosshair frame
    fx0, fy0, fx1, fy1 = 70, 170, 384, 500
    d.rectangle([fx0, fy0, fx1, fy1], outline=(150, 150, 158), width=3)
    for i in range(5):
        yy = fy0 + (fy1 - fy0) * i / 4
        d.line([fx0, yy, fx1, yy], fill=(60, 60, 66), width=1)
    d.line([(fx0 + fx1)/2, fy0, (fx0 + fx1)/2, fy1], fill=(60, 60, 66), width=1)
    # animated red scan line moving
    sy = fy0 + ((t / dur) % 1) * (fy1 - fy0)
    d.line([fx0, sy, fx1, sy], fill=ACCENT + (200,), width=4)
    # play button
    d.ellipse([fx0 + 40, fy0 + 40, fx0 + 120, fy0 + 120], fill=ACCENT + (230,))
    d.polygon([(fx0 + 62, fy0 + 55), (fx0 + 62, fy0 + 105), (fx0 + 108, fy0 + 80)], fill=WHITE)
    d.text((fx0 + 40, fy1 + 12), "00:00:00:00  →  00:00:05:00", font=F(22, bold=False), fill=GRAY_TXT)
    # layers panel
    panel(img, [446, 116, W-24, 560], bg=(22, 22, 26), border=(70, 70, 76))
    d.text((470, 134), "LAYERS", font=F(24), fill=GRAY_TXT)
    layers = [("VIDEO CLIP", (255, 59, 48)), ("TEXT LAYER", (86, 124, 246)), ("BACKGROUND MUSIC", (72, 198, 121))]
    for i, (name, col) in enumerate(layers):
        y = 180 + i * 110
        panel(img, [462, y, W-60, y + 92], bg=(30, 30, 34), border=(80, 80, 86), radius=10)
        d.rounded_rectangle([480, y + 20, 524, y + 64], 8, col + (230,))
        d.text((540, y + 30), name, font=F(24), fill=TXT_LITE)
        # eye icon
        d.ellipse([W-110, y + 34, W-82, y + 62], outline=GRAY_TXT, width=2)
        d.ellipse([W-100, y + 44, W-92, y + 52], fill=GRAY_TXT)
    # timeline panel
    panel(img, [24, 580, W-24, 950], bg=(20, 20, 24), border=(70, 70, 76))
    d.text((48, 596), "TIMELINE", font=F(24), fill=GRAY_TXT)
    # ruler
    ry = 640
    for i in range(17):
        x = 60 + i * 38
        d.line([x, ry, x, ry + 8], fill=(90, 90, 96), width=2)
    # track 1: red clip bar
    track_y = 668
    bar_x0, bar_x1 = 70, 380
    d.rounded_rectangle([bar_x0, track_y, bar_x1, track_y + 64], 10, ACCENT + (235,))
    d.text((bar_x0 + 14, track_y + 22), "CLIP 1", font=F(26), fill=WHITE)
    # waveform on clip
    for i in range(28):
        x = bar_x0 + 12 + i * 11
        hh = 10 + (6 * abs(math.sin(i * 1.3 + t * 3)))
        d.line([x, track_y + 64 - hh, x, track_y + 64 - 10], fill=(255, 120, 110, 220), width=2)
    # track 2: text bar
    track_y2 = 752
    d.rounded_rectangle([250, track_y2, 560, track_y2 + 64], 10, (86, 124, 246, 235))
    d.text((264, track_y2 + 22), "TEXT", font=F(26), fill=WHITE)
    # keyframes pulsing
    for kx in (250, 560):
        pulse = 1 + 0.25 * math.sin(t * 6)
        s = 12 * pulse
        d.polygon([(kx, track_y2 + 32 - s), (kx + s, track_y2 + 32), (kx, track_y2 + 32 + s), (kx - s, track_y2 + 32)],
                  fill=(255, 214, 64, 255), outline=(30, 30, 34))
    # moving playhead
    px = 60 + ((t / dur) % 1) * (W - 140)
    d.line([px, 636, px, 930], fill=ACCENT + (255,), width=3)
    d.polygon([(px - 8, 630), (px + 8, 630), (px, 642)], fill=ACCENT + (255,))
    # step label
    a = fade(t, 0.4)
    panel(img, [24, 975, W-24, 1055], bg=(60, 6, 6), border=ACCENT, width=2, radius=14)
    draw_text(img, label, W/2, 1015, F(38), WHITE, alpha=a)
    if show_export:
        # export settings rows
        panel(img, [24, 1080, W-24, 1230], bg=(26, 26, 30), border=(70, 70, 76))
        rows = [("FORMAT", "H.264 MP4"), ("SIZE", "1080 × 1920"), ("FPS", "30"), ("AUDIO", "AAC 320 kbps")]
        for i, (k, v) in enumerate(rows):
            y = 1102 + i * 36
            d.text((56, y), k, font=F(22, bold=False), fill=GRAY_TXT)
            d.text((W - 56 - d.textlength(v, font=F(22)), y), v, font=F(22), fill=TXT_LITE)
    if t > dur - 0.35:
        k = ease((t - (dur - 0.35)) / 0.35)
        img = text_alpha(img, Image.new("RGBA", (W, H), (0, 0, 0, int(255*k))))
    return img.convert("RGB")

def scene2(t, dur):
    img = ae_mock(t, dur, "STEP 1 · IMPORT CLIP & DROP ON TIMELINE")
    # fade in
    a = fade(t, 0.3)
    return text_alpha(img, Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - a)))))

# ---------------- SECTION 3: flash transition + text step (bright) ----------------
def scene3(t, dur):
    img = vgrad_bg((214, 214, 220), (150, 150, 156)).convert("RGBA")
    # opening flash
    if t < 0.5:
        k = 1 - ease(t / 0.5)
        img = text_alpha(img, Image.new("RGBA", (W, H), (255, 255, 255, int(230 * k))))
    d = ImageDraw.Draw(img)
    # step label
    a1, dy1 = slide_up(t - 0.2, dist=90, dur=0.5)
    draw_text(img, "STEP 2 · ADD TEXT", W/2, 280 + dy1, F(54), TXT_DARK, alpha=a1)
    # text layer mock on dark panel
    panel_img = img.copy().convert("RGBA")
    panel(panel_img, [120, 420, W-120, 820], bg=(24, 24, 28), border=(60, 60, 66))
    a2, dy2 = slide_up(t - 0.6, dist=70, dur=0.5)
    d = ImageDraw.Draw(panel_img)
    d.text((W/2, 540 + dy2), "YOUR TEXT", font=F(72), fill=(255, 59, 48, int(255*a2)),
            stroke_width=2, stroke_fill=(0, 0, 0, int(80*a2)))
    d.text((W/2, 650 + dy2), "heavy font · centered · punchy color", font=F(28, bold=False),
           fill=(200, 200, 208, int(255*a2)))
    # text tool cursor blinking
    if math.sin(t * 5) > 0 and a2 > 0:
        d.line([W/2 + 240, 500, W/2 + 240, 640], fill=(255, 59, 48, 255), width=4)
        d.polygon([(W/2 + 232, 500), (W/2 + 256, 500), (W/2 + 248, 488)], fill=(255, 59, 48, 255))
    img = text_alpha(img, panel_img)
    # bullets fade in
    bullets = ["TYPE ON A SEPARATE LAYER", "USE A BOLD, HEAVY FONT", "ALIGN CENTER · KEEP IT SHORT"]
    for i, b in enumerate(bullets):
        a = fade(t - (0.9 + i * 0.25), 0.4)
        if a > 0:
            draw_text(img, b, W/2, 900 + i * 62, F(32), TXT_DARK, alpha=a)
    # end fade
    if t > dur - 0.35:
        k = ease((t - (dur - 0.35)) / 0.35)
        img = text_alpha(img, Image.new("RGBA", (W, H), (0, 0, 0, int(255*k))))
    return img.convert("RGB")

# ---------------- SECTION 4: bright animation showcase ----------------
def scene4(t, dur):
    img = vgrad_bg((220, 220, 226), (150, 150, 156)).convert("RGBA")
    a = fade(t, 0.3)
    img = text_alpha(img, Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - a)))))
    draw_text(img, "ANIMATE THE TEXT", W/2, 170, F(44), TXT_DARK, alpha=a)
    # three demo rows: each text rendered to its own RGBA image for transforms
    demos = [
        ("FADE IN", "fade", 260),
        ("SLIDE UP", "slide", 520),
        ("POP", "pop", 780),
    ]
    for name, kind, y in demos:
        panel(img, [60, y - 60, W - 60, y + 90], bg=(238, 238, 242), border=(200, 200, 206), radius=16)
        f = F(58)
        # render text into tight RGBA image
        tmp = rgba_layer()
        td = ImageDraw.Draw(tmp)
        bbox = td.textbbox((0, 0), name, font=f, stroke_width=2)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tmp = tmp.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
        px = t - 0.3
        if kind == "fade":
            a2 = fade(px % 1.6, 0.4)
            dy = 0
            sc = 1.0
        elif kind == "slide":
            a2 = 1.0
            dy = -60 * ease((px % 1.6) / 0.6)
            sc = 1.0
        else:
            a2 = 1.0
            dy = 0
            sc = pop(px % 1.6, 0.6)
        if sc != 1.0:
            nw, nh = int(tw * sc), int(th * sc)
            tmp = tmp.resize((nw, nh), Image.LANCZOS)
        if a2 < 1.0:
            alpha = tmp.getchannel("A").point(lambda v: int(v * a2))
            tmp.putalpha(alpha)
        layer = rgba_layer()
        layer.paste(tmp, (int(W/2 - tmp.width/2), int(y + dy - tmp.height/2)), tmp)
        base = img.convert("RGBA")
        img = Image.alpha_composite(base, layer).convert("RGB")
        d = ImageDraw.Draw(img)
        d.text((W/2 - 200, y + 34), "▸", font=F(30), fill=ACCENT)
    # stats bar
    a3 = fade(t - 0.8, 0.5)
    panel(img, [60, 940, W - 60, 1120], bg=TXT_DARK, border=None, radius=16)
    draw_text(img, "1080 × 1920", W/2, 995, F(56), WHITE, alpha=a3)
    draw_text(img, "30 FPS · VERTICAL REEL FORMAT", W/2, 1085, F(30, bold=False), BRIGHT, alpha=a3)
    # end fade
    if t > dur - 0.35:
        k = ease((t - (dur - 0.35)) / 0.35)
        img = text_alpha(img, Image.new("RGBA", (W, H), (0, 0, 0, int(255*k))))
    return img.convert("RGB")

# ---------------- SECTION 5: dark demo 2 (transitions + export) ----------------
def scene5(t, dur):
    img = ae_mock(t, dur, "STEP 3 · TRANSITIONS & EXPORT", show_export=True)
    a = fade(t, 0.3)
    return text_alpha(img, Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - a)))))

# ---------------- SECTION 6: outro (dark red, low motion) ----------------
def scene6(t, dur):
    img = vgrad_bg(DARK_RED, DEEP_RED).convert("RGBA")
    img = radial_glow(img, W/2, 480, 620, (150, 10, 10), 0.5)
    a1, dy1 = slide_up(t - 0.1, dist=100, dur=0.6)
    draw_text(img, "THAT'S IT!", W/2, 400 + dy1, F(84), WHITE, stroke=3, stroke_fill=(0, 0, 0, 120), alpha=a1)
    a2 = fade(t - 0.4, 0.5)
    draw_text(img, "PRACTICE · REUSE · POST", W/2, 540, F(40), BRIGHT, alpha=a2)
    a3 = fade(t - 0.8, 0.5)
    if a3 > 0:
        pulse = 1 + 0.04 * math.sin(t * 3)
        r = int(40 * pulse * a3)
        rounded(img, [W/2 - r, 660 - r, W/2 + r, 660 + r], r, (255, 59, 48, int(255*a3)), None, 0)
    a4 = fade(t - 1.2, 0.5)
    draw_text(img, "ANIMATE · POST · GO VIRAL", W/2, 800, F(46), WHITE, alpha=a4)
    a5 = fade(t - 1.6, 0.5)
    panel(img, [W/2 - 170, 920, W/2 + 170, 1000], bg=(38, 38, 42), border=(120, 120, 126), width=2, radius=40)
    draw_text(img, "@yourstudio", W/2, 960, F(38), TXT_LITE, alpha=a5)
    # gentle rising confetti-ish accents (low motion)
    d = ImageDraw.Draw(img)
    for i in range(8):
        y = 1280 - ((t * 30 + i * 160) % 1280)
        x = 60 + (i * 89) % (W - 120)
        d.ellipse([x, y, x + 8, y + 8], fill=(255, 90, 80, 90))
    return img.convert("RGB")

# ---------------- main render ----------------
SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]
DURATIONS = [3.16, 5.09, 3.58, 3.94, 4.55, 3.11]  # from sped-up TTS

def main():
    total = int(sum(DURATIONS) * FPS)
    print(f"Rendering {total} frames @ {FPS}fps ({sum(DURATIONS):.2f}s)")
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "recreate/viral_reels_tutorial_recreated.mp4"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    seg_starts = []
    cum = 0.0
    for d in DURATIONS:
        seg_starts.append(cum)
        cum += d
    for fi in range(total):
        tt = fi / FPS
        # find section
        for si, (st, sfn) in enumerate(zip(seg_starts, SCENES)):
            st_end = seg_starts[si + 1] if si + 1 < len(seg_starts) else sum(DURATIONS)
            if st <= tt < st_end:
                frame = sfn(tt - st, st_end - st)
                break
        arr = np.asarray(frame)[:, :, ::-1]  # RGB -> BGR
        proc.stdin.write(arr.tobytes())
        if fi % 100 == 0:
            print(f"  frame {fi}/{total} t={tt:.2f}s")
    proc.stdin.close()
    proc.wait()
    print("video done, rc =", proc.returncode)

if __name__ == "__main__":
    main()
