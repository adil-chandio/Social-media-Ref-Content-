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

# Each scene deliberately changes palette, composition and type rhythm like the reference.
BEATS = [(0,2.15),(2.15,5.15),(5.15,8.10),(8.10,10.05),(10.05,14.10),(14.10,16.45),(16.45,24.05),(24.05,28.10),(28.10,34.05)]
PALETTES = [(13,14,18),(239,237,230),(12,13,17),(239,237,230),(30,112,166),(239,149,94),(30,112,166),(30,112,166),(9,10,14)]

def centered(d, text, y, f, color, tracking=0):
    widths=[d.textlength(c,font=f) for c in text]
    x=(W-(sum(widths)+tracking*max(0,len(text)-1)))/2
    for c,ww in zip(text,widths):
        d.text((int(x),int(y)),c,font=f,fill=color); x+=ww+tracking

def fit_font(d,text,size,maxwidth,bold=True):
    f=font(size,bold=bold)
    while d.textlength(text,font=f)>maxwidth and size>20:
        size-=2; f=font(size,bold=bold)
    return f

def stroke_circle(d,cx,cy,r,color,width=2):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=color,width=width)

def background(t):
    i=max(0,next((k for k,(a,b) in enumerate(BEATS) if a<=t<b),len(BEATS)-1))
    col=PALETTES[i]
    # brief, clean palette transitions rather than one continuous dark treatment
    a,b=BEATS[i]
    if t-a<.22 and i>0:
        col=mix(PALETTES[i-1],col,ease((t-a)/.22))
    im=Image.new('RGB',(W,H),col)
    return im,i

def render_frame(t):
    im,scene=background(t); d=ImageDraw.Draw(im,'RGBA')
    start,end=BEATS[scene]; local=t-start; duration=end-start
    enter=ease(local/.32); leave=ease((duration-local)/.26); alpha=int(255*min(enter,leave))
    cream=scene in (1,3,5); blue=scene in (4,6,7)
    ink=(18,20,24,alpha) if cream else (245,246,248,alpha)
    soft=(72,76,81,alpha) if cream else (238,241,247,alpha)
    accent=(221,116,67,alpha) if cream or scene==5 else (255,157,91,alpha)
    cx,cy=W//2,H//2
    drift=int((t*22)%120)

    if scene in (0,2,8):
        # Architectural grid and editor registration marks; final settles into a quiet title plate.
        grid_alpha=36 if scene==8 else 28
        for x in range(-120+drift,W+120,120): d.line((x,0,x,H),fill=(180,189,197,grid_alpha),width=1)
        for y in range(-120+drift,H+120,120): d.line((0,y,W,y),fill=(180,189,197,grid_alpha),width=1)
        for x in (140,340,580):
            d.line((x,0,x,H),fill=(210,215,219,26),width=1)
        d.line((0,cy,W,cy),fill=(210,215,219,28),width=1)
        if scene==0:
            # Type-on greeting with editorial cursor and small alignment ticks.
            reveal=min(5,int(local*5.1)); label='HELLO'
            f=font(94,bold=True); shown=label[:reveal]
            centered(d,shown,cy-78,f,(248,248,246,alpha))
            if reveal<5:
                x=(W-d.textlength(label,font=f))/2+d.textlength(shown,font=f)+3
                d.rounded_rectangle((x,cy-72,x+7,cy+16),radius=3,fill=(242,151,92,alpha))
            else:
                x=(W+d.textlength(label,font=f))/2+17
                d.ellipse((x,cy+22,x+12,cy+34),fill=(242,151,92,alpha))
            d.text((46,77),'MONARCH / 01',font=font(14,mono=True),fill=(154,164,176,alpha))
            d.text((W-165,77),'INTRODUCING',font=font(14,mono=True),fill=(154,164,176,alpha))
            d.line((138,cy-9,582,cy-9),fill=(170,178,184,58),width=1)
            d.line((140,300,140,980),fill=(170,178,184,45),width=1)
        elif scene==2:
            # Dark role card echoes the reference's simple, confident type-only reveal.
            words=['AI LEARNER','CONTENT CREATOR','YOUTUBE AUTOMATION','DEVELOPER']
            row=int(local*1.45)%len(words); sub=(local*1.45)%1
            y=cy-22-int(34*(1-ease(sub)))
            d.text((54,92),'WHAT I DO',font=font(15,mono=True),fill=(132,143,157,alpha))
            centered(d,words[row],y,fit_font(d,words[row],48,W-68),(247,247,246,alpha))
            d.rounded_rectangle((W//2-32,cy+71,W//2+32,cy+76),radius=2,fill=(242,151,92,alpha))
            centered(d,'LEARN  /  CREATE  /  AUTOMATE  /  BUILD',H-176,font(13,mono=True),(143,152,163,alpha),1)
        else:
            # End card: quiet measured scale-up, cut to near-black logo-like wordmark.
            p=ease(local/.75); f=font(int(54+12*p),bold=True)
            centered(d,'Adil Chandio',cy-56,f,(239,240,241,alpha))
            centered(d,'AI  •  CONTENT  •  AUTOMATION  •  DEVELOPMENT',cy+31,font(13,mono=True),(130,137,145,alpha),1)
            if local<2.0:
                d.line((W//2-75,cy+82,W//2+75,cy+82),fill=(225,130,82,alpha),width=2)
            d.text((54,H-80),'MONARCH STUDIO',font=font(13,mono=True),fill=(114,124,137,alpha))
            d.text((W-149,H-80),'ADIL / 01',font=font(13,mono=True),fill=(114,124,137,alpha))

    elif scene==1:
        # Warm-paper nameplate with custom editorial silhouette / portrait mark.
        d.text((54,72),'AI LEARNER   /   CREATOR   /   DEVELOPER',font=font(13,mono=True),fill=(92,96,98,alpha))
        d.line((54,108,W-54,108),fill=(38,43,45,55),width=1)
        d.text((130,cy-208),'I’m',font=font(42),fill=(29,31,33,alpha))
        centered(d,'Adil Chandio',cy-150,fit_font(d,'Adil Chandio',64,W-92),(18,19,21,alpha))
        centered(d,'AI LEARNING  &  CONTENT CREATION',cy-73,font(14,mono=True),(84,87,90,alpha),1)
        # Original abstract silhouette (not a stock photo or copied creator portrait).
        bob=int(8*math.sin(local*3)); headx,heady=367,cy+148+bob
        d.ellipse((headx-62,heady-85,headx+62,heady+45),fill=(19,20,22,alpha))
        d.polygon([(headx-49,heady+15),(headx+48,heady+15),(headx+73,heady+57),(headx+146,heady+187),(headx-150,heady+187),(headx-78,heady+58)],fill=(19,20,22,alpha))
        d.line((56,H-93,W-56,H-93),fill=(52,56,58,60),width=1)
        d.text((56,H-71),'CURIOUS BY NATURE. BUILDER BY CHOICE.',font=font(13,mono=True),fill=(83,87,90,alpha))

    elif scene==3:
        # Short sliding wordmark—name resolves with typographic hierarchy.
        offset=int((1-enter)*100)
        d.text((65,cy-40-offset),'Adil',font=font(48),fill=(41,43,44,alpha))
        d.text((184,cy-44+int((1-enter)*72)),'Chandio',font=font(55,bold=True),fill=(20,21,23,alpha))
        d.text((68,cy+29),'LEARNING AI  /  MAKING CONTENT  /  BUILDING SOFTWARE',font=font(12,mono=True),fill=(100,101,99,alpha))
        d.line((66,cy+68,654,cy+68),fill=(47,49,50,54),width=1)

    elif scene==4:
        # Bright blue kinetic concept: sweeping orbital rings, dot, and changing headline.
        # Rings scale out in a deliberate, slow loop, with one marker moving around the orbit.
        pulse=.5+.5*math.sin(local*1.5)
        for r in (94,167,241):
            rr=int(r*(.93+.06*pulse)); stroke_circle(d,cx,cy+16,rr,(220,241,250,41 if r<200 else 25),1)
        ang=local*1.9; px=cx+int(167*math.cos(ang)); py=cy+16+int(167*math.sin(ang))
        d.ellipse((px-7,py-7,px+7,py+7),fill=(245,153,83,255))
        if local<2.25:
            centered(d,'Creativity is',cy-66,font(40),(244,248,250,alpha))
            centered(d,'like a game,',cy-16,font(40),(244,248,250,alpha))
            # Simple illustrated game symbols orbit through the open space.
            qx=int(cx+205*math.cos(local*1.4+1)); qy=int(cy-195+32*math.sin(local*2))
            d.ellipse((qx-15,qy-15,qx+15,qy+15),outline=(244,248,250,alpha),width=2)
            d.line((qx-8,qy,qx+8,qy),fill=(244,248,250,alpha),width=3); d.line((qx,qy-8,qx,qy+8),fill=(244,248,250,alpha),width=3)
        else:
            centered(d,'Ideas are',cy-46,font(42),(244,248,250,alpha))
            centered(d,'made to play.',cy+6,font(42),(244,248,250,alpha))
        d.text((54,H-118),'ADIL CHANDIO',font=font(15,bold=True),fill=(244,248,250,alpha))
        d.text((W-210,H-118),'AI × CREATIVITY',font=font(12,mono=True),fill=(207,228,239,alpha))

    elif scene==5:
        # Warm punchy beat, quick split alignment and contrasting orange focal line.
        centered(d,'AND YES,',cy-123,font(30,mono=True),(43,39,36,alpha),2)
        x=54+int(150*(1-enter))
        d.text((x,cy-59),'WE LIKE',font=fit_font(d,'WE LIKE',77,W-105),fill=(22,22,22,alpha))
        centered(d,'TO PLAY.',cy+39,fit_font(d,'TO PLAY.',81,W-80),(255,248,236,alpha))
        d.rounded_rectangle((W-94,cy+55,W-82,cy+67),radius=5,fill=(44,42,39,alpha))
        d.text((54,80),'THE WORK IS SERIOUS.',font=font(14,mono=True),fill=(69,57,49,alpha))
        d.text((54,106),'THE PROCESS SHOULD FEEL ALIVE.',font=font(14,mono=True),fill=(69,57,49,alpha))

    elif scene==6:
        # Skill board inspired by reference's moving portfolio word cloud, but true to Adil.
        d.text((49,74),'WHAT I’M BUILDING',font=font(14,mono=True),fill=(197,225,239,alpha))
        d.text((W-170,74),'CAPABILITIES',font=font(13,mono=True),fill=(197,225,239,alpha))
        d.line((50,110,W-50,110),fill=(229,242,249,61),width=1)
        items=[('01','AI LEARNING','Curiosity → capability'),('02','CONTENT CREATION','Ideas made clear'),('03','YOUTUBE AUTOMATION','Repeatable creative systems'),('04','DEVELOPMENT','From prompt to product')]
        for j,(num,title,desc) in enumerate(items):
            y=cy-237+j*126
            progress=ease((local-(.16+j*.19))/.42)
            shift=int((1-progress)*80)
            y+=int(15*math.sin(local*2.3+j))
            d.text((54+shift,y),num,font=font(14,mono=True),fill=(241,159,99,alpha))
            d.text((112+shift,y-13),title,font=fit_font(d,title,28,W-176),fill=(245,248,250,alpha))
            d.text((113+shift,y+29),desc,font=font(15),fill=(193,220,233,alpha))
            d.line((112+shift,y+70,W-54,y+70),fill=(223,239,246,39),width=1)
        # Floating status mark, scanning softly across rows
        scan=cy-228+int((local%1.8)/1.8*500)
        d.ellipse((W-72,scan-4,W-64,scan+4),fill=(255,169,105,alpha))
        d.text((54,H-104),'LEARNING IN PUBLIC. BUILDING IN REAL TIME.',font=font(13,mono=True),fill=(198,222,234,alpha))

    elif scene==7:
        # Orbit rings gather into a name lock-up, using the same blue/circle vocabulary as reference.
        pulse=ease(local/1.0); radii=[int(128*(1-.14*pulse)),int(128*(1-.14*pulse)),int(128*(1-.14*pulse))]
        centers=[(cx,cy-127),(cx-112,cy+90),(cx+112,cy+90)]
        for k,((ox,oy),r) in enumerate(zip(centers,radii)):
            stroke_circle(d,ox,oy,r,(220,241,250,112),2)
            th=local*2+k*2.1; dotx=ox+int(r*math.cos(th)); doty=oy+int(r*math.sin(th))
            d.ellipse((dotx-5,doty-5,dotx+5,doty+5),fill=(255,160,91,alpha))
        # dissolve circles toward a sharp typographic centre
        centered(d,'Adil Chandio',cy-25,fit_font(d,'Adil Chandio',39,W-90),(250,251,252,alpha))
        centered(d,'AI  /  CREATOR  /  AUTOMATION  /  DEVELOPER',cy+28,font(11,mono=True),(202,227,239,alpha),1)
        d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=(247,161,91,alpha))

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
