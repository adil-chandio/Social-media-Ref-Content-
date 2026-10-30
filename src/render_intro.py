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

# Carefully timed to the reference's 34-second sequence. Palette and composition shifts
# follow its actual cuts; typography, portrait, brand and portfolio panels are rebuilt for Adil.
BEATS=[(0.00,1.55),(1.55,5.35),(5.35,6.40),(6.40,7.55),(7.55,8.65),(8.65,13.90),(13.90,15.55),(15.55,22.20),(22.20,23.10),(23.10,24.35),(24.35,26.25),(26.25,28.20),(28.20,31.05),(31.05,34.05)]
PALETTES=[(17,18,21),(239,237,230),(15,16,19),(35,111,162),(239,237,230),(35,111,162),(35,111,162),(35,111,162),(239,237,230),(239,237,230),(35,111,162),(14,15,18),(14,15,18),(4,5,7)]

def centered(d,text,y,f,color,tracking=0):
    widths=[d.textlength(c,font=f) for c in text]
    x=(W-(sum(widths)+tracking*max(0,len(text)-1)))/2
    for c,ww in zip(text,widths):
        d.text((int(x),int(y)),c,font=f,fill=color); x+=ww+tracking

def fit_font(d,text,size,maxwidth,bold=True):
    f=font(size,bold=bold)
    while d.textlength(text,font=f)>maxwidth and size>18:
        size-=2; f=font(size,bold=bold)
    return f

def scene_at(t):
    return max(0,next((k for k,(a,b) in enumerate(BEATS) if a<=t<b),len(BEATS)-1))

def color_at(t):
    i=scene_at(t); a,b=BEATS[i]; c=PALETTES[i]
    if i and t-a<.18: c=mix(PALETTES[i-1],c,ease((t-a)/.18))
    return c,i

def orbit(d,cx,cy,r,color,w=2):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=color,width=w)

def draw_vector_portrait(im,t,alpha):
    # Original graphic silhouette, intentionally anonymous; softly rounded jacket/head,
    # animated into the portrait reveal rather than reusing the reference creator's footage.
    lay=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(lay)
    a=alpha; bob=int(5*math.sin(t*4)); x=360; y=800+bob
    # shoulders/coat silhouette, overlap ellipses create a naturally curved shoulder line
    d.ellipse((x-154,y+90,x+154,y+420),fill=(18,19,21,a))
    d.polygon([(x-84,y+34),(x+85,y+34),(x+128,y+145),(x+154,y+340),(x-154,y+340),(x-128,y+145)],fill=(18,19,21,a))
    # neck, ears and head
    d.rounded_rectangle((x-29,y-5,x+29,y+99),radius=15,fill=(18,19,21,a))
    d.ellipse((x-65,y-142,x+65,y+32),fill=(18,19,21,a))
    d.ellipse((x-76,y-76,x-51,y-28),fill=(18,19,21,a));d.ellipse((x+51,y-76,x+76,y-28),fill=(18,19,21,a))
    # hairline/side-swept top: separate silhouette masses keep the portrait graphic.
    d.ellipse((x-70,y-158,x+66,y-77),fill=(18,19,21,a))
    d.polygon([(x-67,y-107),(x-22,y-149),(x+55,y-145),(x+67,y-95),(x+27,y-119),(x-4,y-100)],fill=(18,19,21,a))
    im.alpha_composite(lay)

def make_tilted_card(t):
    # Draw original Adil identity card and perspective, inspired by the reference's 3D card beat.
    card=Image.new('RGBA',(500,310),(0,0,0,0)); d=ImageDraw.Draw(card)
    d.rounded_rectangle((15,15,485,295),radius=7,fill=(235,137,83,255))
    d.rectangle((15,15,485,55),fill=(252,205,164,255))
    for x,y,r in [(95,105,22),(410,104,20),(405,230,19)]: d.ellipse((x-r,y-r,x+r,y+r),fill=(15,16,19,255))
    d.text((80,133),'Adil Chandio',font=font(42,bold=True),fill=(18,19,21,255))
    d.text((82,190),'AI  /  CREATOR  /  DEVELOPER',font=font(13,mono=True),fill=(50,42,37,255))
    d.text((82,242),'MONARCH • CREATIVE SYSTEMS',font=font(12,mono=True),fill=(79,57,43,255))
    # A restrained perspective skew plus rotation and ground shadow make a real card stage.
    skew=card.transform((560,330),Image.Transform.AFFINE,(1,-.15,40,.08,1,0),resample=Image.Resampling.BICUBIC)
    shadow=Image.new('RGBA',skew.size,(0,0,0,0)); shadow.alpha_composite(skew); shadow=shadow.getchannel('A').filter(ImageFilter.GaussianBlur(18))
    sh=Image.new('RGBA',skew.size,(0,0,0,105));sh.putalpha(shadow.point(lambda q:int(q*.52)))
    angle=-5+2*math.sin(t*2.2)
    sk=skew.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    ss=sh.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    x=int(84+24*math.sin(t*2)); y=int(406-18*math.sin(t*1.6))
    return sk,ss,x,y

def render_frame(t):
    scene=scene_at(t); start,end=BEATS[scene]; local=t-start; dur=end-start
    enter=ease(local/.20); leave=ease((dur-local)/.20); alpha=int(255*min(enter,leave))
    bg,_=color_at(t); im=Image.new('RGBA',(W,H),(*bg,255));d=ImageDraw.Draw(im,'RGBA')
    cream=scene in (1,4,8,9); blue=scene in (3,5,6,7,10)
    ink=(20,21,23,alpha) if cream else (246,246,244,alpha)
    muted=(105,106,106,alpha) if cream else (214,227,235,alpha)
    orange=(231,137,85,alpha)
    cx,cy=W//2,H//2
    drift=int((t*18)%140)

    if scene in (0,1,2,3,4,11,12,13):
        # Reference's fine editing-grid system; shifts positions per frame and resolves into clean title card.
        ga=28 if scene in (0,11,12) else 24
        for x in range(-140+drift,W+140,140):d.line((x,0,x,H),fill=(115,127,136,ga),width=1)
        for y in range(-140+drift,H+140,140):d.line((0,y,W,y),fill=(115,127,136,ga),width=1)
        d.line((140,0,140,H),fill=(135,145,151,23),width=1);d.line((W//2,0,W//2,H),fill=(135,145,151,20),width=1)
        d.line((0,cy,W,cy),fill=(130,143,151,26),width=1)
        for x in (140,cx,W-140):
            for y in (cy-14,cy+14):
                d.ellipse((x-4,y-4,x+4,y+4),outline=(174,185,190,83),width=1)

    if scene==0:
        # Original reference's typewriter hello with center guides and orange cursor dot.
        n=min(5,int(local*6.0)); label='Hello'; f=font(77,bold=True); shown=label[:n]
        centered(d,shown,cy-55,f,(244,244,242,alpha))
        if n<len(label):
            x=(W-d.textlength(label,font=f))/2+d.textlength(shown,font=f)+2
            d.rounded_rectangle((x,cy-50,x+6,cy+20),radius=3,fill=(239,147,91,alpha))
        else:
            x=(W+d.textlength(label,font=f))/2+12;d.ellipse((x,cy+13,x+10,cy+23),fill=(239,147,91,alpha))
        d.text((48,72),'01 / MONARCH',font=font(13,mono=True),fill=(145,153,160,alpha))
        d.text((W-164,72),'INTRODUCING',font=font(13,mono=True),fill=(145,153,160,alpha))

    elif scene==1:
        d.text((49,65),'AI LEARNER     CONTENT CREATOR     DEVELOPER',font=font(12,mono=True),fill=(94,98,99,alpha))
        d.line((50,100,W-50,100),fill=(44,48,49,54),width=1)
        d.text((130,cy-208),'I’m',font=font(39),fill=(31,32,33,alpha))
        centered(d,'Adil Chandio',cy-150,fit_font(d,'Adil Chandio',56,W-90),(20,21,22,alpha))
        centered(d,'AI LEARNING  /  CONTENT CREATION',cy-88,font(13,mono=True),(91,93,93,alpha),1)
        draw_vector_portrait(im,t,alpha); d=ImageDraw.Draw(im,'RGBA')
        d.line((52,H-96,W-52,H-96),fill=(49,52,53,55),width=1)
        d.text((53,H-75),'LEARNING OUT LOUD. BUILDING WHAT’S NEXT.',font=font(12,mono=True),fill=(82,85,86,alpha))

    elif scene in (2,3):
        labels={2:'AI LEARNER',3:'CONTENT CREATOR'}
        f=fit_font(d,labels[scene],46,W-70)
        # One-beat role card; slight vertical settle instead of an unmoving caption.
        y=cy-25+int((1-enter)*28)
        centered(d,labels[scene],y,f,(246,247,245,alpha))
        d.rounded_rectangle((cx-28,cy+50,cx+28,cy+55),radius=2,fill=orange)
        small='CURIOUS BY DESIGN' if scene==2 else 'IDEAS INTO STORIES'
        centered(d,small,H-168,font(12,mono=True),(148,157,166,alpha),1)
        d.text((W-159,74),f'0{scene+1} / 04',font=font(12,mono=True),fill=(142,151,161,alpha))

    elif scene==4:
        # Clean name reveal between role cards and the main blue motion sequence.
        off=int((1-enter)*85)
        d.text((69,cy-29-off),'Adil',font=font(45),fill=(45,47,48,alpha))
        d.text((171,cy-37+int((1-enter)*50)),'Chandio',font=font(51,bold=True),fill=(20,21,22,alpha))
        d.text((71,cy+27),'AI LEARNER  •  CONTENT CREATOR  •  DEVELOPER',font=font(11,mono=True),fill=(91,93,93,alpha))
        d.line((68,cy+67,652,cy+67),fill=(60,64,65,54),width=1)

    elif scene==5:
        # Blue manifesto. Three concentric rings, tiny orbiting point and icon-like geometric marks.
        for r,op in ((117,49),(195,31),(269,19)):orbit(d,cx,cy,r,(213,238,248,op),1)
        d.line((cx,188,cx,H-180),fill=(216,239,248,23),width=1)
        phase=local
        if phase<2.5:
            centered(d,'Creativity is',cy-40,font(34),(245,248,249,alpha))
            centered(d,'like a game,',cy+4,font(34),(245,248,249,alpha))
        elif phase<4.0:
            # Symbols swap/morph in four positions, matching original's little design-tool icon parade.
            glyphs=['✦','◇','↗','□','✎','⌘','◈','↔']
            for k in range(4):
                x=cx-102+k*68; y=cy-10+int(9*math.sin(phase*7+k))
                g=glyphs[(int((phase-2.2)*4)+k)%len(glyphs)]
                d.text((x,y),g,font=font(29,bold=True),fill=(247,249,250,alpha))
            centered(d,'like',cy+47,font(30),(245,248,249,alpha))
        else:
            centered(d,'and yes, we',cy-31,font(31),(245,248,249,alpha))
            centered(d,'like to play.',cy+11,font(31,bold=True),(245,248,249,alpha))
        ang=local*2.1; px=cx+int(195*math.cos(ang)); py=cy+int(195*math.sin(ang))
        d.ellipse((px-5,py-5,px+5,py+5),fill=(243,154,91,alpha))
        d.text((50,H-108),'ADIL CHANDIO',font=font(12,bold=True),fill=(247,249,250,alpha))
        d.text((51,H-88),'@ADIL CHANDIO',font=font(10,mono=True),fill=(199,222,233,alpha))

    elif scene==6:
        # Exact reference structure: phrase anchors left; portfolio skills stream through center.
        orbit(d,cx,cy+8,184,(215,239,248,36),1);d.line((cx,300,cx,H-200),fill=(215,239,248,22),width=1)
        centered(d,'and yes, we',cy-29,font(28),(246,249,250,alpha))
        centered(d,'like to play.',cy+10,font(28,bold=True),(246,249,250,alpha))
        d.ellipse((cx+135,cy+5,cx+144,cy+14),fill=(245,153,88,alpha))

    elif scene==7:
        # Continuous staggered skill conveyor; the bright selected capability travels upward
        # while the surrounding words drift/fade like the reference's animated service cloud.
        d.line((cx,220,cx,H-155),fill=(219,239,247,22),width=1)
        d.text((52,cy-8),'to',font=font(17),fill=(240,246,249,alpha))
        d.text((52,cy+18),'build',font=font(17,bold=True),fill=(240,246,249,alpha))
        d.ellipse((118,cy+24,127,cy+33),fill=(245,153,88,alpha))
        labels=[('AI Learning',0),('Content Creation',1),('YouTube Automation',2),('Developer / Product Builds',3),('Creative Workflows',4),('AI Education',5)]
        offset=(local*1.1)%1; base=cy-145
        for text,k in labels:
            y=base+(k-offset)*84
            if cy-235<y<cy+246:
                dist=abs(y-cy); opacity=int(alpha*max(.18,1-dist/440))
                fsize=25 if dist<45 else 19 if dist<120 else 16
                if dist<45: color=(250,251,250,opacity)
                else: color=(206,226,237,opacity)
                x=193+int(16*math.sin(local*2.4+k))
                d.text((x,int(y)),text,font=fit_font(d,text,fsize,470),fill=color)
        d.text((W-167,78),'SKILLS / 01–06',font=font(11,mono=True),fill=(201,224,234,alpha))
        d.text((50,H-105),'AI  •  CONTENT  •  SYSTEMS  •  SOFTWARE',font=font(11,mono=True),fill=(205,226,235,alpha))

    elif scene==8:
        # Four minimalist portfolio panels flash in like a typographic case-study board.
        cards=[('AI LEARNING',(34,113,163)),('CREATOR SYSTEMS',(240,145,91)),('AUTOMATION',(236,233,224)),('DEVELOPMENT',(14,15,18))]
        for j,(name,col) in enumerate(cards):
            y=175+j*207+int(14*math.sin(local*8+j)); x=56+int((1-enter)*(-90 if j%2==0 else 90))
            d.rounded_rectangle((x,y,W-56,y+177),radius=2,fill=(*col,255))
            dark=j in (1,2); tc=(23,24,25,alpha) if dark else (245,247,247,alpha)
            d.text((x+23,y+18),f'0{j+1} / MONARCH',font=font(10,mono=True),fill=tc)
            d.text((x+23,y+87),name,font=fit_font(d,name,23,W-110),fill=tc)
            d.line((x+23,y+143,W-79,y+143),fill=(*tc[:3],100),width=1)
            d.ellipse((W-99,y+17,W-91,y+25),fill=(244,150,89,255))

    elif scene==9:
        # Hero 3-D name card showcase; unique artwork, layered stock-free vector geometry.
        sk,sh,x,y=make_tilted_card(t)
        im.alpha_composite(sh,(x+8,y+19)); im.alpha_composite(sk,(x,y))
        d=ImageDraw.Draw(im,'RGBA')
        # secondary paper stock peeking from underneath
        d.polygon([(142,993),(568,910),(626,1004),(200,1094)],fill=(244,243,238,255))
        d.polygon([(93,1014),(198,994),(232,1057),(123,1085)],fill=(17,19,22,255))
        d.text((50,90),'IDENTITY / MONARCH',font=font(12,mono=True),fill=(87,90,91,alpha))

    elif scene==10:
        # Three orbit system collects around the name, as in the reference's blue brand transition.
        positions=[(cx,cy-135),(cx-116,cy+76),(cx+116,cy+76)]
        radius=int(128-13*ease(local/1.2))
        for j,(ox,oy) in enumerate(positions):
            orbit(d,ox,oy,radius,(223,242,250,99),2)
            a=local*2.5+j*2.1; px=ox+int(radius*math.cos(a));py=oy+int(radius*math.sin(a))
            d.ellipse((px-5,py-5,px+5,py+5),fill=(247,159,93,alpha))
        centered(d,'Adil Chandio',cy-25,fit_font(d,'Adil Chandio',39,W-75),(246,249,251,alpha))
        centered(d,'AI  •  CREATOR  •  AUTOMATION  •  DEVELOPER',cy+25,font(10,mono=True),(206,229,239,alpha),1)
        d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=(248,162,93,alpha))

    elif scene in (11,12):
        # Name lock-up grows from a clean type card into the final grid-guided signature.
        if scene==11:
            centered(d,'Adil Chandio',cy-30,fit_font(d,'Adil Chandio',40,W-84),(245,246,246,alpha))
            d.text((51,H-126),'ADIL CHANDIO',font=font(12,bold=True),fill=(228,231,232,alpha))
            d.text((51,H-104),'AI LEARNING  •  CREATOR  •  DEVELOPER',font=font(10,mono=True),fill=(141,151,160,alpha))
        else:
            # Double line wipe sweeps behind the signature, then settles to exact horizontal guides.
            sweep=int((local%dur)/dur*W)
            d.line((0,cy-23,W,cy-23),fill=(114,130,143,36),width=1)
            d.line((0,cy+24,W,cy+24),fill=(114,130,143,36),width=1)
            d.line((max(0,sweep-125),cy-23,sweep,cy-23),fill=(227,235,239,112),width=2)
            f=font(44,bold=False); width=d.textlength('Adil Chandio',font=f)
            x=(W-width)/2
            d.text((x,cy-32),'Adil',font=f,fill=(235,237,239,alpha))
            d.text((x+d.textlength('Adil ',font=f),cy-32),'Chandio',font=font(44,bold=True),fill=(235,237,239,alpha))
            centered(d,'AI LEARNING  /  CONTENT  /  AUTOMATION',cy+39,font(10,mono=True),(131,142,151,alpha),1)
            d.text((50,H-90),'ADIL CHANDIO',font=font(12,bold=True),fill=(235,237,239,alpha))

    elif scene==13:
        # Social-style closing icon reveal: replace creator handle with known personal name, no invented username.
        # Icon is drawn as clean vector, animates in over the finished wordmark.
        d.text((50,H-86),'ADIL CHANDIO',font=font(13,bold=True),fill=(165,170,176,alpha))
        d.text((W-153,H-86),'MONARCH / 01',font=font(11,mono=True),fill=(102,108,116,alpha))
        pulse=.5+.5*math.sin(local*3.3)
        r=int(42+4*pulse); ix,iy=cx,cy-5
        d.rounded_rectangle((ix-r,iy-r,ix+r,iy+r),radius=20,outline=(243,245,248,alpha),width=5)
        d.ellipse((ix-17,iy-17,ix+17,iy+17),outline=(243,245,248,alpha),width=5)
        d.ellipse((ix+23,iy-25,ix+31,iy-17),fill=(234,92,190,alpha))
        d.text((cx-142,cy+82),'Adil Chandio',font=font(30,bold=False),fill=(137,142,149,alpha))
        centered(d,'LEARN  /  CREATE  /  BUILD',cy+128,font(10,mono=True),(102,109,117,alpha),2)

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
