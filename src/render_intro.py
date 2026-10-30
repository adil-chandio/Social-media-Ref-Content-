#!/usr/bin/env python3
"""Render an original 9:16 Adil Chandio / Monarch portfolio intro.
Uses the supplied reference's audio track only; all visuals are original typography/motion design.
"""
import argparse, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import imageio_ffmpeg

W, H, FPS = 720, 1280, 30
DURATION = 34.05
BG = (9, 12, 20)
WHITE = (242, 246, 255)
MUTED = (132, 149, 173)
CYAN = (66, 224, 255)
AMBER = (255, 155, 76)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

def font(size, bold=False, mono=False):
    return ImageFont.truetype(MONO if mono else (BOLD if bold else FONT), size)
def ease(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def mix(a,b,t): return tuple(int(x+(y-x)*t) for x,y in zip(a,b))
def center_text(draw, text, y, f, fill, tracking=0):
    if tracking:
        widths=[draw.textlength(c,font=f) for c in text]
        x=(W-(sum(widths)+tracking*(len(text)-1)))/2
        for c,ww in zip(text,widths): draw.text((int(x),int(y)),c,font=f,fill=fill); x+=ww+tracking
    else:
        box=draw.textbbox((0,0),text,font=f); draw.text(((W-(box[2]-box[0]))/2,int(y)),text,font=f,fill=fill)
def text_width(d, text, f):
    b=d.textbbox((0,0),text,font=f); return b[2]-b[0]

SCENES=[
 (0.0,4.2,'HELLO,','ADIL CHANDIO','A mind that learns. A builder who ships.'),
 (4.2,9.1,'AI, IN MOTION','LEARN AI.','Turn curiosity into capability.'),
 (9.1,14.0,'MAKE IT MATTER','CREATE.','Ideas made clear, useful and unforgettable.'),
 (14.0,19.0,'YOUTUBE SYSTEMS','AUTOMATE.','Smarter content workflows. Bigger creative reach.'),
 (19.0,24.0,'CODE THE FUTURE','DEVELOPER.','From concept to working product.'),
 (24.0,29.0,'BUILT DIFFERENT','MONARCH','AI × creativity × engineering'),
 (29.0,34.05,'THE NEXT CHAPTER','ADIL CHANDIO','Learn boldly. Create relentlessly. Build what’s next.'),
]

# Precompute the soft radial-light background once; NumPy avoids per-pixel Python loops.
_yy, _xx = np.mgrid[0:H, 0:W]
_glow = np.maximum(0, 1-np.sqrt(((_xx-510)/610)**2+((_yy-410)/790)**2))
_bg = np.empty((H,W,3),dtype=np.uint8)
_bg[:,:,0] = np.clip(BG[0]+4*_glow,0,255)
_bg[:,:,1] = np.clip(BG[1]+11*_glow+(_yy/H)*0.055*15,0,255)
_bg[:,:,2] = np.clip(BG[2]+20*_glow+(_yy/H)*0.055*35,0,255)
BASE = Image.fromarray(_bg,'RGB')

def render_frame(t):
    # restrained midnight canvas with filmic corner vignette and moving technical grid
    im=BASE.copy(); d=ImageDraw.Draw(im,'RGBA')
    # Tracking grid, offset drift, central crosshair echoing reference's graphic language
    drift=int((t*13)%120)
    for x in range(-120+drift,W+120,120): d.line((x,0,x,H),fill=(105,151,184,17),width=1)
    for y in range(-120+drift,H+120,120): d.line((0,y,W,y),fill=(105,151,184,14),width=1)
    # Fine frame / registration marks
    d.rounded_rectangle((30,30,W-30,H-30),radius=22,outline=(121,168,199,35),width=1)
    d.line((W//2,170,W//2,H-170),fill=(125,166,190,24),width=1)
    # Orbit rings pulse in and out; the amber point follows a circular trajectory
    pulse=.5+.5*math.sin(t*1.45)
    cx,cy=W//2,H//2+22
    for r,alpha in ((104,36),(175,22),(245,12)):
        rr=int(r*(.95+.045*pulse))
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=(77,187,220,alpha),width=2)
    ang=t*1.0
    px=cx+int(175*math.cos(ang)); py=cy+int(175*math.sin(ang))
    # blurred glow layer
    glow=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.ellipse((px-18,py-18,px+18,py+18),fill=(*AMBER,150)); glow=glow.filter(ImageFilter.GaussianBlur(20)); im=Image.alpha_composite(im.convert('RGBA'),glow)
    d=ImageDraw.Draw(im,'RGBA'); d.ellipse((px-5,py-5,px+5,py+5),fill=(*AMBER,255))

    # scene transition: fades and short vertical glide keep text readable on mobile
    si=max(0,next((i for i,s in enumerate(SCENES) if s[0]<=t<s[1]),len(SCENES)-1))
    start,end,kicker,title,sub=SCENES[si]
    local=t-start; length=end-start
    fade=min(1,ease(local/.55),ease((length-local)/.5))
    slide=int(28*(1-ease(local/.65)))
    white=(*WHITE,int(255*fade)); muted=(*MUTED,int(240*fade)); cyan=(*CYAN,int(255*fade))
    # top micro-label
    d.text((54,70),'MONARCH  /  CREATIVE SYSTEMS',font=font(16,mono=True),fill=(cyan[0],cyan[1],cyan[2],int(205*fade)))
    d.text((W-103,70),f'{si+1:02d} / 07',font=font(16,mono=True),fill=(muted[0],muted[1],muted[2],int(185*fade)))
    # graphic sequence indicator
    d.line((54,111,W-54,111),fill=(137,177,200,int(48*fade)),width=1)
    d.line((54,111,int(54+(W-108)*(t/DURATION)),111),fill=(*CYAN,int(165*fade)),width=2)
    center_text(d,kicker,cy-166+slide,font(18,mono=True),cyan,tracking=2)
    title_size=62 if len(title)<14 else 49
    tf=font(title_size,bold=True)
    # dynamically fit title
    while text_width(d,title,tf)>W-70: title_size-=2; tf=font(title_size,bold=True)
    center_text(d,title,cy-82+slide,tf,white)
    d.rounded_rectangle((W//2-28,cy+20+slide,W//2+28,cy+25+slide),radius=3,fill=(*AMBER,int(245*fade)))
    subf=font(21)
    center_text(d,sub,cy+57+slide,subf,muted)
    # typography accents and safe-zone footer
    center_text(d,'AI  •  CONTENT  •  AUTOMATION  •  DEVELOPMENT',H-139,font(13,mono=True),(*MUTED,int(175*fade)),tracking=1)
    d.text((54,H-78),'ADIL CHANDIO',font=font(17,bold=True),fill=(*WHITE,int(220*fade)))
    d.text((W-224,H-78),'LEARN  /  CREATE  /  BUILD',font=font(12,mono=True),fill=(*MUTED,int(200*fade)))
    # Tiny moving spark for a tactile, deliberately minimal motion detail
    sx=int(54+(W-108)*((t*0.12)%1)); d.ellipse((sx,H-46,sx+3,H-43),fill=(*CYAN,int(160*fade)))
    return im.convert('RGB')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('reference'); ap.add_argument('output'); args=ap.parse_args()
    ff=imageio_ffmpeg.get_ffmpeg_exe(); total=round(DURATION*FPS)
    cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',args.reference,'-map','0:v:0','-map','1:a:0','-t',str(DURATION),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-shortest','-movflags','+faststart',args.output]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(total):
            proc.stdin.write(render_frame(i/FPS).tobytes())
            if i%150==0: print(f'Rendering {i/total:.0%}',flush=True)
        proc.stdin.close(); code=proc.wait()
        if code: raise RuntimeError(f'ffmpeg failed ({code})')
    except Exception:
        proc.kill(); raise
    print(f'Created {args.output}')
if __name__=='__main__': main()
