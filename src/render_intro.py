#!/usr/bin/env python3
"""Render an original 9:16 Adil Chandio / Monarch portfolio intro.
Uses the supplied reference's audio track only; all visuals are original typography/motion design.
"""
import argparse, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

W, H, FPS = 720, 1280, 30
DURATION = 34.05
BG = (9, 12, 20)
WHITE = (242, 246, 255)
MUTED = (132, 149, 173)
CYAN = (66, 224, 255)
AMBER = (255, 155, 76)
FONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts'))
FONT = os.path.join(FONT_DIR, 'Manrope-400.ttf')
BOLD = os.path.join(FONT_DIR, 'Manrope-700.ttf')
EXTRA_BOLD = os.path.join(FONT_DIR, 'Manrope-800.ttf')
MONO = os.path.join(FONT_DIR, 'IBMPlexMono-400.ttf')

def font(size, bold=False, mono=False, extra=False):
    path = MONO if mono else (EXTRA_BOLD if extra else (BOLD if bold else FONT))
    return ImageFont.truetype(path, size)
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

class AlphaDraw:
    """ImageDraw proxy that correctly honors RGBA alpha for text on an RGB frame."""
    def __init__(self, image):
        self.image=image
        self.draw=ImageDraw.Draw(image,'RGBA')
    def __getattr__(self,name):
        return getattr(self.draw,name)
    def text(self,xy,text,*args,**kwargs):
        fill=kwargs.get('fill')
        if not isinstance(fill,(tuple,list)) or len(fill)<4 or fill[3]>=255:
            return self.draw.text(xy,text,*args,**kwargs)
        opacity=max(0,min(255,int(fill[3])))
        if opacity==0:return
        bbox=self.draw.textbbox(xy,text,font=kwargs.get('font'),anchor=kwargs.get('anchor'),stroke_width=kwargs.get('stroke_width',0))
        pad=3; left=max(0,int(math.floor(bbox[0]-pad))); top=max(0,int(math.floor(bbox[1]-pad)))
        right=min(self.image.width,int(math.ceil(bbox[2]+pad))); bottom=min(self.image.height,int(math.ceil(bbox[3]+pad)))
        if right<=left or bottom<=top:return
        layer=Image.new('RGBA',(right-left,bottom-top),(0,0,0,0)); ld=ImageDraw.Draw(layer)
        opt=dict(kwargs); opt['fill']=(*fill[:3],255)
        ld.text((xy[0]-left,xy[1]-top),text,*args,**opt)
        layer.putalpha(layer.getchannel('A').point(lambda a:a*opacity//255))
        self.image.paste(layer,(left,top),layer.getchannel('A'))

# Scene boundaries are snapped to audible attacks measured from the untouched source track.
# The source has a steady ~1.067 s accent cycle from 0.988 to 27.15 s, plus two closing hits.
# At 30 fps, cuts land on the nearest frame to those attacks; visual elements use the same clock.
AUDIO_GRID_START=0.988
AUDIO_GRID_PERIOD=1.067
AUDIO_GRID_END=27.15
AUDIO_HITS=(0.190,0.399,0.988,1.397,1.796,2.055,2.325,2.594,2.794,3.123,3.392,3.662,3.981,4.190,4.460,4.859,5.258,5.657,6.056,6.326,6.595,6.854,7.124,7.393,7.663,8.191,8.461,8.730,9.129,9.528,9.927,10.327,10.596,10.865,11.125,11.394,11.663,11.923,12.462,12.731,12.990,13.260,13.529,13.789,14.198,14.597,14.856,15.126,15.395,15.664,15.924,16.193,16.592,16.991,17.261,17.790,18.059,18.458,18.857,19.127,19.396,19.795,20.194,21.262,21.790,22.060,22.329,22.589,22.858,23.127,23.397,23.926,24.325,24.724,24.993,25.392,25.702,26.061,26.240,27.258,30.391,30.890,31.079)
ACCENT_HITS=(0.190,0.988,1.397,2.055,3.123,4.190,5.258,6.595,7.663,8.730,9.528,10.596,11.125,12.990,13.789,15.126,16.991,18.059,19.127,20.194,21.262,22.329,22.858,23.127,23.926,24.993,26.061,30.391,30.890,31.079)
# Ordered scene map, frame-accurately locked to the audible accent around every cut.
BEATS=[(0.00,1.397),(1.397,5.258),(5.258,6.595),(6.595,7.663),(7.663,8.730),(8.730,13.789),(13.789,15.395),(15.395,22.329),(22.329,23.127),(23.127,24.464),(24.464,26.061),(26.061,28.20),(28.20,30.391),(30.391,34.05)]
PALETTES=[(17,18,21),(239,237,230),(15,16,19),(35,111,162),(239,237,230),(35,111,162),(35,111,162),(35,111,162),(239,237,230),(239,237,230),(35,111,162),(14,15,18),(14,15,18),(4,5,7)]

def centered(d,text,y,f,color,tracking=0):
    widths=[d.textlength(c,font=f) for c in text]
    x=(W-(sum(widths)+tracking*max(0,len(text)-1)))/2
    for c,ww in zip(text,widths):
        d.text((int(x),int(y)),c,font=f,fill=color); x+=ww+tracking

def fit_font(d,text,size,maxwidth,bold=True,extra=False):
    f=font(size,bold=bold,extra=extra)
    while d.textlength(text,font=f)>maxwidth and size>18:
        size-=2; f=font(size,bold=bold,extra=extra)
    return f

def scene_at(t):
    return max(0,next((k for k,(a,b) in enumerate(BEATS) if a<=t<b),len(BEATS)-1))

def beat_phase(t):
    """Phase-lock continuous motion to the measured 1.067-second accent cycle."""
    return 2*math.pi*(t-AUDIO_GRID_START)/AUDIO_GRID_PERIOD

def hit_pulse(t):
    """Short visual accents on strong source-audio attacks; ignore speech-level micro-transients."""
    nearest=min(ACCENT_HITS,key=lambda onset:abs(t-onset))
    dt=abs(t-nearest)
    return math.exp(-.5*(dt/.045)**2) if dt<.11 else 0.0

def color_at(t):
    i=scene_at(t); a,b=BEATS[i]; c=PALETTES[i]
    if i and t-a<.08: c=mix(PALETTES[i-1],c,ease((t-a)/.08))
    return c,i

def orbit(d,cx,cy,r,color,w=2):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=color,width=w)

def halo(im,x,y,color,radius=5,strength=120):
    # Small, restrained optical bloom on accent markers; keep the typography crisp.
    size=76; layer=Image.new('RGBA',(size,size),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    q=size//2
    ld.ellipse((q-radius,q-radius,q+radius,q+radius),fill=(*color,strength))
    layer=layer.filter(ImageFilter.GaussianBlur(17))
    im.paste(layer,(int(x-q),int(y-q)),layer)

CUTOUT_PATH=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','assets','adil-photo-cutout-intro.png'))
CUTOUT=Image.open(CUTOUT_PATH).convert('RGBA')

def draw_black_silhouette(im,t,alpha):
    # Adil's supplied photo cutout replaces the earlier pure-black silhouette shape.
    # Same reveal timing, placement and scale behaviour as the silhouette beat.
    progress=ease((t-2.08)/.78)
    if progress<=0:return
    height=int(470+50*progress)
    width=round(height*CUTOUT.width/CUTOUT.height)
    x=(W-width)//2; settle=int(7*math.sin(progress*math.pi)*(1-progress))
    y=1142-height+int(30*(1-progress))-settle
    cut=CUTOUT.resize((width,height),Image.Resampling.LANCZOS)
    # Whole-shape opacity + scale reveal; no hard crop line crosses the head or shoulders.
    opacity=max(0,min(255,int(alpha*progress)))
    cut.putalpha(cut.getchannel('A').point(lambda q:q*opacity//255))
    im.paste(cut,(x,y),cut)

def make_tilted_card(t):
    # Draw original Adil identity card and perspective, inspired by the reference's 3D card beat.
    card=Image.new('RGBA',(500,310),(0,0,0,0)); d=ImageDraw.Draw(card)
    d.rounded_rectangle((15,15,485,295),radius=7,fill=(235,137,83,255))
    d.rectangle((15,15,485,55),fill=(252,205,164,255))
    for x,y,r in [(95,105,22),(410,104,20),(405,230,19)]: d.ellipse((x-r,y-r,x+r,y+r),fill=(15,16,19,255))
    d.text((80,133),'Adil Chandio',font=font(42,bold=True),fill=(18,19,21,255))
    d.text((82,190),'AI  /  CREATOR  /  DEVELOPER',font=font(13,mono=True),fill=(50,42,37,255))
    d.text((82,242),'MONARCH • CREATIVE SYSTEMS',font=font(12,mono=True),fill=(79,57,43,255))
    # A soft traveling specular sweep makes the printed surface feel tactile, not flat.
    shine=Image.new('RGBA',card.size,(0,0,0,0)); sd=ImageDraw.Draw(shine)
    sweep=int(((t-23.127)/1.067)*560)-65
    sd.polygon([(sweep-34,58),(sweep-8,58),(sweep+84,290),(sweep+58,290)],fill=(255,247,234,34))
    card=Image.alpha_composite(card,shine)
    # A restrained perspective skew plus rotation and ground shadow make a real card stage.
    skew=card.transform((560,330),Image.Transform.AFFINE,(1,-.15,40,.08,1,0),resample=Image.Resampling.BICUBIC)
    shadow=Image.new('RGBA',skew.size,(0,0,0,0)); shadow.alpha_composite(skew); shadow=shadow.getchannel('A').filter(ImageFilter.GaussianBlur(18))
    sh=Image.new('RGBA',skew.size,(0,0,0,105));sh.putalpha(shadow.point(lambda q:int(q*.52)))
    card_phase=2*math.pi*(t-23.127)/1.067
    angle=-7+3.5*math.sin(card_phase)
    sk=skew.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    ss=sh.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    x=int(78+16*math.sin(card_phase)); y=int(397-21*math.sin(card_phase+.62))
    return sk,ss,x,y

def draw_tool_icon(d,x,y,kind,scale,alpha):
    """Compact hand-drawn vector icon; avoids font-dependent symbol glyphs."""
    s=scale; c=(247,249,250,alpha); w=max(2,int(2.4*s))
    def p(points): return [(int(x+u*s),int(y+v*s)) for u,v in points]
    if kind==0: # cursor
        d.polygon(p([(-12,-15),(13,3),(2,5),(8,16),(2,19),(-4,7),(-10,14)]),outline=c,fill=(0,0,0,0))
        d.line(p([(-12,-15),(-10,14)]),fill=c,width=w)
    elif kind==1: # pen nib
        d.polygon(p([(0,-17),(13,0),(0,16),(-13,0)]),outline=c,width=w)
        d.ellipse((int(x-3*s),int(y-3*s),int(x+3*s),int(y+3*s)),outline=c,width=w)
        d.line(p([(0,16),(0,4)]),fill=c,width=w)
    elif kind==2: # frame/shape
        d.rectangle((int(x-13*s),int(y-13*s),int(x+13*s),int(y+13*s)),outline=c,width=w)
        for u,v in [(-13,-13),(13,-13),(-13,13),(13,13)]:
            d.ellipse((int(x+(u-2)*s),int(y+(v-2)*s),int(x+(u+2)*s),int(y+(v+2)*s)),fill=c)
    elif kind==3: # brush
        d.line(p([(-12,11),(7,-8)]),fill=c,width=max(3,int(4*s)))
        d.ellipse((int(x+4*s),int(y-14*s),int(x+16*s),int(y-2*s)),outline=c,width=w)
        d.line(p([(-16,15),(-6,5)]),fill=c,width=w)
    elif kind==4: # nodes / automation flow
        d.line(p([(-13,0),(0,-10),(13,1),(0,12),(-13,0)]),fill=c,width=w)
        for u,v in [(-13,0),(0,-10),(13,1),(0,12)]: d.ellipse((int(x+(u-3)*s),int(y+(v-3)*s),int(x+(u+3)*s),int(y+(v+3)*s)),fill=(35,112,164,255),outline=c,width=w)
    elif kind==5: # spark
        d.polygon(p([(0,-17),(4,-4),(17,0),(4,4),(0,17),(-4,4),(-17,0),(-4,-4)]),outline=c,width=w)
    elif kind==6: # undo/loop
        box=(int(x-14*s),int(y-14*s),int(x+14*s),int(y+14*s))
        d.arc(box,start=45,end=315,fill=c,width=w)
        d.polygon(p([(-15,-3),(-15,-14),(-4,-11)]),fill=c)
    else: # media/layout card
        d.rounded_rectangle((int(x-16*s),int(y-12*s),int(x+16*s),int(y+12*s)),radius=int(3*s),outline=c,width=w)
        d.line(p([(-7,-11),(-7,11)]),fill=c,width=w);d.line(p([(-4,-4),(13,-4)]),fill=c,width=w);d.line(p([(-4,3),(8,3)]),fill=c,width=w)

def render_frame(t):
    scene=scene_at(t); start,end=BEATS[scene]; local=t-start; dur=end-start
    # 80 ms attack/release keeps each visual landing on its source-audio transient.
    enter=ease(local/.08); leave=ease((dur-local)/.055); alpha=int(255*min(enter,leave))
    bg,_=color_at(t); im=Image.new('RGB',(W,H),bg);d=AlphaDraw(im)
    cream=scene in (1,4,8,9); blue=scene in (3,5,6,7,10)
    ink=(20,21,23,alpha) if cream else (246,246,244,alpha)
    muted=(105,106,106,alpha) if cream else (214,227,235,alpha)
    orange=(231,137,85,alpha)
    cx,cy=W//2,H//2
    drift=int((t*18)%140)
    # A recurring Monarch-amber runner bridges every cut in one continuous visual language.
    if local<.16:
        runner=ease(local/.16)
        endx=50+int((W-100)*runner)
        # The runner's first pixel lands on the audio hit even while the new title is fading up.
        run_alpha=255 if local<.10 else int(255*max(0,(.16-local)/.06))
        d.line((50,128,endx,128),fill=(239,150,91,int(run_alpha*.86)),width=2)
        halo(im,endx,128,(239,150,91),4,int(70*run_alpha/255))
        d=AlphaDraw(im)

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
        # Begin on the opening hit, then reveal one glyph per 267 ms subdivision.
        n=min(5,max(0,int(max(0,local-.190)/.267)+1)); label='Hello'; f=font(77,bold=True,extra=True); shown=label[:n]
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
        centered(d,'Adil Chandio',cy-150,fit_font(d,'Adil Chandio',56,W-90,extra=True),(20,21,22,alpha))
        centered(d,'AI LEARNING  /  CONTENT CREATION',cy-88,font(13,mono=True),(91,93,93,alpha),1)
        draw_black_silhouette(im,t,alpha); d=AlphaDraw(im)
        d.line((52,H-96,W-52,H-96),fill=(49,52,53,55),width=1)
        d.text((53,H-75),'LEARNING OUT LOUD. BUILDING WHAT’S NEXT.',font=font(12,mono=True),fill=(82,85,86,alpha))

    elif scene in (2,3):
        labels={2:'AI LEARNER',3:'CONTENT CREATOR'}
        label=labels[scene]
        # Letter-by-letter mask reveal over the cut, with a moving amber cursor.
        count=min(len(label),int(max(0,local)*len(label)/.42))
        shown=label[:count]
        f=fit_font(d,label,46,W-70)
        y=cy-25+int((1-enter)*28)
        centered(d,shown,y,f,(246,247,245,alpha))
        if count<len(label):
            x=(W-d.textlength(label,font=f))/2+d.textlength(shown,font=f)+2
            d.rounded_rectangle((x,cy-17,x+4,cy+31),radius=2,fill=orange)
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
        # Six-second motion-design playground: phrase changes, tool glyphs orbit, multiple
        # markers sweep different rings, and the phrase resolves before the next shot.
        for k,(r,op) in enumerate(((117,48),(195,31),(269,18))):
            orbit(d,cx,cy,r,(213,238,248,op),1)
            startang=int((beat_phase(t)*.184*180/math.pi+k*108)%360)
            d.arc((cx-r,cy-r,cx+r,cy+r),start=startang,end=startang+84,fill=(232,244,249,min(alpha,92-k*15)),width=2)
        d.line((cx,188,cx,H-180),fill=(216,239,248,24),width=1)
        # Three independent orbiting points replace the single slow dot.
        for k,r in enumerate((117,195,269)):
            ang=beat_phase(t)*(.212+.029*k)+k*2.18
            px=cx+int(r*math.cos(ang));py=cy+int(r*math.sin(ang))
            if k==1: halo(im,px,py,(243,154,91),5,92);d=AlphaDraw(im)
            marker=(243,154,91,alpha) if k==1 else (222,240,248,alpha)
            d.ellipse((px-4-k,py-4-k,px+4+k,py+4+k),fill=marker)
        if local<1.25:
            # First hook: one bold short phrase, with a different entrance on each line.
            q=ease(local/.34)
            centered(d,'Creativity is',cy-34+int(25*(1-q)),font(39,bold=True),(245,248,249,alpha))
            d.line((cx-68,cy+27,cx-68+int(136*q),cy+27),fill=(245,153,91,alpha),width=2)
        elif local<2.45:
            q=ease((local-1.25)/.28)
            centered(d,'like a game,',cy-20+int(26*(1-q)),font(42,bold=True),(245,248,249,alpha))
            centered(d,'CREATIVITY IN PLAY',cy+42,font(12,mono=True),(203,225,235,alpha),1)
        elif local<4.0:
            # Eight bespoke vector tools travel around the orbit. No missing-font glyphs.
            p=local-2.45
            for k in range(8):
                icon_phase=2*math.pi*(t-11.125)/1.067
                ang=2*math.pi*k/8 + icon_phase*.146
                ix=cx+int(153*math.cos(ang));iy=cy+int(153*math.sin(ang))
                pulse=.82+.18*(.5+.5*math.sin(icon_phase*4+k))
                icon_kind=int(max(0,t-11.125)/.267+k)%8
                draw_tool_icon(d,ix,iy,icon_kind,pulse,alpha)
            centered(d,'like',cy-20,font(37,bold=True),(246,249,250,alpha))
            centered(d,'TOOLS  /  IDEAS  /  PLAY',cy+34,font(11,mono=True),(208,228,237,alpha),1)
        else:
            p=ease((local-4.0)/.32)
            centered(d,'and yes, we',cy-51+int(16*(1-p)),font(29),(246,248,249,alpha))
            centered(d,'like to',cy-7,font(30),(246,248,249,alpha))
            centered(d,'play.',cy+37,font(46,bold=True),(255,255,255,alpha))
            d.line((cx-56,cy+94,cx-56+int(112*p),cy+94),fill=(246,153,91,alpha),width=3)
        d.text((50,H-108),'ADIL CHANDIO',font=font(12,bold=True),fill=(247,249,250,alpha))
        d.text((51,H-88),'AI  /  CREATOR  /  BUILDER',font=font(10,mono=True),fill=(199,222,233,alpha))

    elif scene==6:
        # Phrase gets a second, more energetic composition—not a 1.6-second frozen hold.
        q=local/1.65
        for k,r in enumerate((94,184,260)):
            orbit(d,cx,cy,r,(215,239,248,30-k*7),1)
            ang=int((beat_phase(t)*.25*180/math.pi+k*130)%360)
            d.arc((cx-r,cy-r,cx+r,cy+r),start=ang,end=ang+104,fill=(234,243,248,65-k*13),width=2)
            px=cx+int(r*math.cos(math.radians(ang+104)));py=cy+int(r*math.sin(math.radians(ang+104)))
            d.ellipse((px-3,py-3,px+3,py+3),fill=(244,151,90,alpha))
        centered(d,'AND YES, WE',cy-77,font(16,mono=True),(207,227,237,alpha),2)
        # Split words enter from opposite sides and snap to a strong, readable lockup.
        left=int(-80*(1-ease(local/.34))); right=int(80*(1-ease(max(0,local-.12)/.34)))
        d.text((119+left,cy-32),'LIKE TO',font=font(41,bold=True),fill=(245,248,250,alpha))
        d.text((376+right,cy-32),'PLAY.',font=font(49,bold=True,extra=True),fill=(255,255,255,alpha))
        d.rounded_rectangle((W//2-30,cy+44,W//2-30+int(60*ease(local/.5)),cy+50),radius=3,fill=(246,153,91,alpha))
        d.text((50,H-108),'ADIL CHANDIO',font=font(12,bold=True),fill=(247,249,250,alpha))
        d.text((51,H-88),'MAKE SOMETHING THAT MOVES.',font=font(10,mono=True),fill=(199,222,233,alpha))

    elif scene==7:
        # Eight-item infinite capability conveyor. One selected line gets a clean highlight;
        # neighbouring lines stay visible so the viewer sees the breadth, not just two choices.
        d.line((cx,210,cx,H-143),fill=(219,239,247,24),width=1)
        d.text((52,cy-8),'to',font=font(17),fill=(240,246,249,alpha))
        d.text((52,cy+18),'build',font=font(17,bold=True),fill=(240,246,249,alpha))
        d.ellipse((118,cy+24,127,cy+33),fill=(245,153,88,alpha))
        labels=['AI Learning','AI Content Creation','YouTube Automation','Workflow Automation','Software Development','Monarch Agent Builds','Creator Tools & Systems','Motion & Video Editing']
        # One capability advances every 1.5 measured beats (0.800 s), anchored to the first skill hit.
        scroll=max(0,(t-15.395)/.800); active=int(scroll)%len(labels); fraction=scroll%1
        spacing=94
        for slot in range(-3,5):
            idx=(active+slot)%len(labels)
            y=cy+int((slot-fraction)*spacing)
            if cy-337<y<cy+405:
                dist=abs(y-cy); opacity=int(alpha*max(.17,1-dist/490))
                focused=(slot==0)
                fsize=34 if focused else 23 if dist<210 else 17
                color=(250,251,250,opacity) if focused else (205,228,239,opacity)
                x=187+int(10*math.sin(beat_phase(t)*.25+slot))
                d.text((146,int(y)+5),f'{idx+1:02d}',font=font(10,mono=True),fill=(245,159,99,opacity))
                if focused:
                    d.rounded_rectangle((x-12,int(y)-8,W-40,int(y)+45),radius=5,fill=(13,73,115,int(alpha*.28)))
                    d.line((x-12,int(y)+49,W-40,int(y)+49),fill=(247,159,93,opacity),width=2)
                d.text((x,int(y)),labels[idx],font=fit_font(d,labels[idx],fsize,490),fill=color)
        d.text((W-174,78),f'SKILLS / {active+1:02d} / 08',font=font(11,mono=True),fill=(201,224,234,alpha))
        # Moving progress ticks make the 7-second list feel active between words too.
        for k in range(8):
            xx=50+k*18; tick=alpha if k==(active%8) else int(alpha*.32)
            d.rounded_rectangle((xx,H-116,xx+10,H-113),radius=1,fill=(240,244,246,tick))
        d.text((50,H-91),'AI  •  CONTENT  •  SYSTEMS  •  SOFTWARE',font=font(11,mono=True),fill=(205,226,235,alpha))

    elif scene==8:
        # Four minimalist portfolio panels flash in like a typographic case-study board.
        cards=[('6M+ VIEWS','CREATOR REACH',(35,112,164)),('4+ CHANNELS','YOUTUBE AUTOMATION',(238,145,92)),('AI × CREATIVITY','LEARNING IN PUBLIC',(235,232,223)),('MONARCH / BUILDS','DEVELOPMENT',(13,15,18))]
        for j,(headline,caption,col) in enumerate(cards):
            # Four panel landings use the source's half-beat subdivisions; count-ups resolve on the next hit.
            cp=ease((local-j*.134)/.267)
            panel_alpha=int(alpha*ease((local-j*.134)/.08))
            y=91+j*275+int(5*math.sin(beat_phase(t)*.5+j))+int((1-cp)*20)
            x=49+int((1-cp)*(-48 if j%2==0 else 48))
            # Each panel opacity/landing is staggered on successive audible subdivisions.
            d.rectangle((x+7,y+8,W-42,y+261),fill=(20,27,34,int(28*cp)))
            d.rectangle((x,y,W-49,y+253),fill=(*col,panel_alpha))
            dark=j in (1,2); tc=(23,24,25,panel_alpha) if dark else (245,247,247,panel_alpha)
            accent=(246,161,99,panel_alpha)
            d.text((x+25,y+21),f'0{j+1} / ADIL CHANDIO',font=font(11,mono=True),fill=tc)
            d.ellipse((W-88,y+24,W-76,y+36),fill=accent)
            stat=headline
            if j==0:
                count=int(6*ease((local)/.48))
                stat=f'{count}M+ VIEWS' if count>=6 else f'{count}M VIEWS' if count else 'CREATOR REACH'
            elif j==1:
                count=int(4*ease((local-.12)/.48))
                stat=f'{count}+ CHANNELS' if count>=4 else f'{count} CHANNELS' if count else 'YOUTUBE AUTOMATION'
            f=fit_font(d,stat,43,W-100,extra=True)
            d.text((x+25,y+93),stat,font=f,fill=tc)
            d.text((x+27,y+158),caption,font=font(13,mono=True),fill=tc)
            d.line((x+25,y+205,x+25+int((W-123)*cp),y+205),fill=(*tc[:3],160),width=2)
            d.text((x+25,y+221),'MONARCH  /  CREATIVE SYSTEMS',font=font(10,mono=True),fill=tc)

    elif scene==9:
        # Hero 3-D name card showcase; unique artwork, layered stock-free vector geometry.
        sk,sh,x,y=make_tilted_card(t)
        im.paste(sh,(x+10,y+22),sh)
        edge=Image.new('RGBA',sk.size,(102,57,39,0));edge.putalpha(sk.getchannel('A').point(lambda q:int(q*.86)))
        im.paste(edge,(x+3,y+7),edge); im.paste(sk,(x,y),sk)
        d=AlphaDraw(im)
        # Secondary paper stock drifts by a few pixels for a tactile parallax stack.
        dy=int(5*math.sin(t*2.6))
        d.polygon([(142,993+dy),(568,910+dy),(626,1004+dy),(200,1094+dy)],fill=(244,243,238,255))
        d.polygon([(93,1014+dy),(198,994+dy),(232,1057+dy),(123,1085+dy)],fill=(17,19,22,255))
        d.text((50,90),'IDENTITY / MONARCH',font=font(12,mono=True),fill=(87,90,91,alpha))

    elif scene==10:
        # Three orbit system collects around the name, as in the reference's blue brand transition.
        positions=[(cx,cy-135),(cx-116,cy+76),(cx+116,cy+76)]
        radius=int(128-13*ease(local/1.2))
        for j,(ox,oy) in enumerate(positions):
            orbit(d,ox,oy,radius,(223,242,250,99),2)
            a=beat_phase(t)*.424+j*2.1; px=ox+int(radius*math.cos(a));py=oy+int(radius*math.sin(a))
            halo(im,px,py,(247,159,93),4,105);d=AlphaDraw(im)
            d.ellipse((px-5,py-5,px+5,py+5),fill=(247,159,93,alpha))
        centered(d,'Adil Chandio',cy-25,fit_font(d,'Adil Chandio',39,W-75),(246,249,251,alpha))
        centered(d,'AI  •  CREATOR  •  AUTOMATION  •  DEVELOPER',cy+25,font(10,mono=True),(206,229,239,alpha),1)
        d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=(248,162,93,alpha))

    elif scene in (11,12):
        # Name lock-up grows from a clean type card into the final grid-guided signature.
        if scene==11:
            # Split-word signature locks together from opposite sides, then holds cleanly.
            q=ease(local/.42); f1=font(40); f2=font(40,bold=True)
            w1=d.textlength('Adil',font=f1); ws=d.textlength(' ',font=f1); w2=d.textlength('Chandio',font=f2)
            x=(W-(w1+ws+w2))/2; slide=int(52*(1-q))
            d.text((x-slide,cy-30),'Adil',font=f1,fill=(245,246,246,alpha))
            d.text((x+w1+ws+slide,cy-30),'Chandio',font=f2,fill=(245,246,246,alpha))
            d.line((cx-68,cy+29,cx-68+int(136*q),cy+29),fill=(239,150,91,alpha),width=2)
            d.text((51,H-126),'ADIL CHANDIO',font=font(12,bold=True),fill=(228,231,232,alpha))
            d.text((51,H-104),'AI LEARNING  •  CREATOR  •  DEVELOPER',font=font(10,mono=True),fill=(141,151,160,alpha))
        else:
            # Double line wipe sweeps behind the signature, then settles to exact horizontal guides.
            # One soft sweep resolves on entry; the long source-audio pause becomes a deliberate visual hold.
            sweep=int(ease(local/.40)*W)
            d.line((0,cy-23,W,cy-23),fill=(114,130,143,36),width=1)
            d.line((0,cy+24,W,cy+24),fill=(114,130,143,36),width=1)
            if sweep>0: d.line((max(0,sweep-125),cy-23,sweep,cy-23),fill=(227,235,239,112),width=2)
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
        # Logo impact swells exactly on the paired 30.391/30.890 s audio hits, then holds.
        pulse=max(.20,hit_pulse(t)); ring_alpha=max(alpha,int(245*hit_pulse(t)))
        r=int(42+7*pulse); ix,iy=cx,cy-5
        d.rounded_rectangle((ix-r,iy-r,ix+r,iy+r),radius=20,outline=(243,245,248,ring_alpha),width=5)
        d.ellipse((ix-17,iy-17,ix+17,iy+17),outline=(243,245,248,ring_alpha),width=5)
        d.ellipse((ix+23,iy-25,ix+31,iy-17),fill=(239,150,91,ring_alpha))
        d.text((cx-142,cy+82),'Adil Chandio',font=font(30,bold=False),fill=(137,142,149,alpha))
        centered(d,'LEARN  /  CREATE  /  BUILD',cy+128,font(10,mono=True),(102,109,117,alpha),2)

    return im.convert('RGB')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('reference'); ap.add_argument('output'); args=ap.parse_args()
    ff=imageio_ffmpeg.get_ffmpeg_exe(); total=round(DURATION*FPS)
    cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',args.reference,'-map','0:v:0','-map','1:a:0','-t',str(DURATION),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',args.output]
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
