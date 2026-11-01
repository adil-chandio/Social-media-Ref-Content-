#!/usr/bin/env python3
"""S01 v2 — real motion-graphics renderer (per-frame PIL, layered keyframes)."""
import os, math, subprocess, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import imageio_ffmpeg

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC=os.path.join(ROOT,'docs/shorts/s01'); TMP='/tmp/s01v2'; os.makedirs(TMP,exist_ok=True)
F_MAN=ROOT+'/portfolio-site/assets/fonts/Manrope-800.ttf'; F_MONO=ROOT+'/portfolio-site/assets/fonts/IBMPlexMono-400.ttf'
INK=(10,10,11); PAPER=(236,233,226); RED=(210,31,43); YEL=(232,196,60)
W,H=1080,1920; FPS=30
random.seed(7)

def font(s,mono=False): return ImageFont.truetype(F_MONO if mono else F_MAN,s)
def cover(im,w,h):
    r=max(w/im.width,h/im.height); im=im.resize((int(im.width*r),int(im.height*r)))
    return im.crop(((im.width-w)//2,(im.height-h)//2,(im.width-w)//2+w,(im.height-h)//2+h))
def condensed(txt,s,fill,mono=False):
    f=font(s,mono); tmp=Image.new('RGBA',(4000,700),(0,0,0,0)); d=ImageDraw.Draw(tmp)
    d.text((30,30),txt,font=f,fill=fill+(255,)); bb=tmp.getbbox()
    tmp=tmp.crop(bb) if bb else tmp
    return tmp.resize((max(1,int(tmp.width*0.86)),tmp.height))
def clamp(u): return max(0.0,min(1.0,u))
def eoc(u): u=clamp(u); return 1-(1-u)**3
def eob(u):
    u=clamp(u); c1,c3=1.70158,2.70158
    return 1+c3*(u-1)**3+c1*(u-1)**2
def ebounce(u):
    u=clamp(u); n1,d1=7.5625,2.75
    if u<1/d1: return n1*u*u
    if u<2/d1: u-=1.5/d1; return n1*u*u+0.75
    if u<2.5/d1: u-=2.25/d1; return n1*u*u+0.9375
    u-=2.625/d1; return n1*u*u+0.984375
def paste(fr,im,x,y,scale=1.0,rot=0.0,alpha=1.0):
    if alpha<=0 or scale<=0.01: return
    w=max(1,int(im.width*scale)); h=max(1,int(im.height*scale))
    im2=im.resize((w,h))
    if rot: im2=im2.rotate(rot,expand=True,resample=Image.BICUBIC)
    if alpha<1:
        im2=im2.copy(); a=im2.split()[-1].point(lambda p:int(p*alpha)); im2.putalpha(a)
    fr.paste(im2,(int(x-im2.width/2),int(y-im2.height/2)),im2)

# ---- assets
sc1=Image.open(SC+'/sc1_moneybag.png').convert('RGB')
sc2=Image.open(SC+'/sc2_boardroom.png').convert('RGB')
sc3=Image.open(SC+'/sc3_refuse.png').convert('RGB')
sc4=Image.open(SC+'/sc4_chip.png').convert('RGB')
sc5=Image.open(SC+'/sc5_split.png').convert('RGB')
sc6=Image.open(SC+'/sc6_empire.png').convert('RGB')
char=Image.open(ROOT+'/docs/lookdev/char.jpg').convert('RGB').crop((250,60,830,1080))
bag=cover(sc1,700,1000); board=cover(sc2,800,1160); refuse=cover(sc3,800,1280)
chip=cover(sc4,W,H); crowd=cover(sc5.crop((0,0,372,1376)),540,1920); perso=cover(sc5.crop((396,0,768,1376)),540,1920)
empire=cover(sc6,W,H); charc=cover(char,760,1330)
T_usne=condensed('US NE KAHA',150,INK); T_nahi=condensed('NAHI.',300,RED)
T_tag=condensed('$20,000,000,000',56,PAPER,mono=True)
T_tab=condensed('TABLE PAR',124,PAPER); T_20b=condensed('$20 BILLION',152,RED)
T_offer=condensed('poori company ka offer',44,PAPER,mono=True); T_2008=condensed('2008',56,INK,mono=True)
T_mana=condensed('MANA KAR',170,PAPER); T_diya=condensed('DIYA.',170,RED)
T_paisa=condensed('paisa kam nahi tha…',48,PAPER,mono=True)
T_woh=condensed('WOH CHEEZ',140,PAPER); T_naam=condensed('JIS KA NAAM',110,(180,178,172)); T_tha=condensed('TAK NAHI THA',110,RED)
T_pag=condensed('PAGALMAT',92,(150,148,144)); T_vis=condensed('VISION.',124,RED)
T_aaj=condensed('AAJ WOHI',116,PAPER); T_bari=condensed('SAB SE BARI',140,RED); T_chip=condensed('CHIP COMPANY',116,PAPER)
T_foot=condensed('SIRF EK FOOTNOTE.',116,RED)
T_rule=condensed('MONARCH RULE:',94,YEL); T_r1=condensed('JO DUNIYA KO KAL',102,PAPER); T_r2=condensed('DIKHEGA —',102,PAPER); T_r3=condensed('WOH AAJ BANAO.',110,RED)
# paper card + news card
card=Image.new('RGBA',(900,1600),(0,0,0,0)); cd=ImageDraw.Draw(card)
cd.rounded_rectangle([0,0,899,1599],radius=34,fill=PAPER+(255,))
news=Image.new('RGBA',(860,1140),(0,0,0,0)); nd=ImageDraw.Draw(news)
nd.rectangle([0,0,859,1139],fill=(238,234,224,255)); nd.rectangle([0,0,859,114],fill=(228,222,208,255))
nd.text((50,32),'THE MONARCH HERALD',font=font(56),fill=INK)
yy=176
for i in range(14):
    wl=860-110 if i%3 else 860-200
    nd.rectangle([56,yy,56+wl,yy+12],fill=((120,116,108) if i!=9 else INK)+(255,)); yy+=56
nd.text((56,yy+38),'$20,000,000,000 — footnote 7, page 3',font=font(32,mono=True),fill=INK)
# grain + vignette
grains=[]
for g in range(4):
    gr=Image.effect_noise((W//2,H//2),60).convert('RGBA'); gr.putalpha(20)
    grains.append(gr)
vig=Image.new('L',(W,H),110); vd=ImageDraw.Draw(vig)
vd.ellipse([-W*0.25,-H*0.2,W*1.25,H*1.2],fill=255); vig=vig.filter(ImageFilter.GaussianBlur(160))
particles=[]
def shake_amt(t,hits):
    a=0
    for h in hits:
        dt=t-h
        if 0<=dt<0.25: a=max(a,(0.25-dt)/0.25)
    return a
HITS=[1.8,5.0,6.2,10.6,13.2,20.4,21.4,24.6,31.2,32.4]
DURS=[5,5,5,5,4,4,4,4.6]; STARTS=[]; a=0
for d in DURS: STARTS.append(a); a+=d
TOTAL=a

def beat(fr,bi,tl):
    cx,cy=W/2,H/2
    if bi==0:
        paste(fr,cover(sc1,W,H).filter(ImageFilter.GaussianBlur(30)).resize((W,H)).convert('RGBA'),cx,cy,alpha=0.35)
        s=eob(tl/0.4)*0+ (1.45-0.45*eob(tl/0.4))
        paste(fr,card,cx,cy,scale=s)
        by=-1000+1000*ebounce(tl/0.9) if tl<0.9 else 60*math.sin(tl*2.2)
        paste(fr,bag.convert('RGBA'),cx,cy+40+by,scale=1.0,rot=-6+6*eoc(tl/0.9)+2*math.sin(tl*1.7))
        tx=-700+700*eoc((tl-0.5)/0.4) if tl>0.5 else -700
        paste(fr,T_tag,cx,cy-660,alpha=clamp((tl-0.5)/0.2))
        if tl>1.2: paste(fr,T_usne,cx,cy-480,scale=1.6-0.6*eob((tl-1.2)/0.25),alpha=clamp((tl-1.2)/0.12))
        if tl>1.8:
            paste(fr,T_nahi,cx,cy-220,scale=1.9-0.9*eob((tl-1.8)/0.3),alpha=clamp((tl-1.8)/0.1))
            if tl<2.1:
                fl=Image.new('RGBA',(W,H),RED+(int(70*(1-(tl-1.8)/0.3)),)); fr.paste(Image.alpha_composite(fr.convert('RGBA'),fl).convert('RGB'),(0,0))
        push=1+0.05*clamp(tl/5)
        return push
    if bi==1:
        fr.paste(cover(sc2,W,H).filter(ImageFilter.GaussianBlur(34)).convert('RGB'),(0,0)); fr.paste(ImageEnhance.Brightness(fr).enhance(0.5),(0,0))
        glow=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
        g=int(40+18*math.sin(tl*6)); gd.ellipse([cx-420,cy-520,cx+420,cy+420],fill=(232,196,60,g))
        glow=glow.filter(ImageFilter.GaussianBlur(120)); fr.paste(Image.alpha_composite(fr.convert('RGBA'),glow).convert('RGB'),(0,0))
        bx=W+400-(W+400-cx)*eoc(tl/0.6)
        back=Image.new('RGBA',(880,1240),(0,0,0,0)); bd=ImageDraw.Draw(back); bd.rounded_rectangle([0,0,879,1239],radius=30,fill=PAPER+(255,))
        paste(fr,back,bx,cy+80,rot=4-4*eoc(tl/0.6))
        bim=ImageEnhance.Brightness(board.convert('RGB')).enhance(1.6).resize((760,1080)).convert('RGBA')
        paste(fr,bim,bx,cy+80,rot=4-4*eoc(tl/0.6))
        if tl>0.7: paste(fr,T_2008,cx-300,cy-660,scale=1.5-0.5*eob((tl-0.7)/0.25),rot=-12+12*eoc((tl-0.7)/0.3),alpha=clamp((tl-0.7)/0.12))
        if tl>1.3: paste(fr,T_tab,cx,cy-480,alpha=clamp((tl-1.3)/0.2))
        if tl>1.8: paste(fr,T_20b,cx,cy-320,scale=1.5-0.5*eob((tl-1.8)/0.3),alpha=clamp((tl-1.8)/0.12))
        if tl>2.6:
            n=int(len('poori company ka offer')*clamp((tl-2.6)/1.2))
            paste(fr,condensed('poori company ka offer'[:n],44,PAPER,mono=True),cx,cy+520,alpha=1)
        return 1+0.06*clamp(tl/5)
    if bi==2:
        fr.paste(ImageEnhance.Brightness(cover(sc3,W,H).filter(ImageFilter.GaussianBlur(34))).enhance(0.3).convert('RGB'),(0,0))
        ry=H+700-(H+700-cy)*eoc(tl/0.7)
        paste(fr,refuse.convert('RGBA'),cx,ry)
        py=cy-460+26*math.sin(tl*2.4); pr=8*math.sin(tl*1.9)
        flame=Image.new('RGBA',(140,180),(0,0,0,0)); fd=ImageDraw.Draw(flame)
        fd.ellipse([20,40,120,160],fill=(255,120,40,200)); fd.ellipse([45,70,95,140],fill=(255,220,120,220))
        flame=flame.filter(ImageFilter.GaussianBlur(6))
        paste(fr,flame.resize((220,280)),cx+220,py,rot=pr)
        if tl>1.2:
            u=clamp((tl-1.2)/0.22); x0=cx-400; x1=cx-400+800*u
            d=ImageDraw.Draw(fr); d.line([x0,cy+220,x1,cy+150],fill=RED,width=16)
        if tl>0.9: paste(fr,T_mana,cx,cy-620,scale=1.6-0.6*eob((tl-0.9)/0.25),alpha=clamp((tl-0.9)/0.12))
        if tl>1.4: paste(fr,T_diya,cx-140,cy-440,scale=1.6-0.6*eob((tl-1.4)/0.25),alpha=clamp((tl-1.4)/0.12))
        if tl>2.4: paste(fr,T_paisa,cx,cy+560,alpha=clamp((tl-2.4)/0.3))
        return 1+0.05*clamp(tl/5)
    if bi==3:
        push=1.12+0.12*clamp(tl/4)
        paste(fr,chip.convert('RGBA'),cx,cy,scale=push)
        for k in range(14):
            px=cx-300+((k*173)%600); pyy=(cy+500-((tl*120+k*140)%1100))
            d=ImageDraw.Draw(fr); r=3+(k%3); d.ellipse([px-r,pyy-r,px+r,pyy+r],fill=(255,90,90))
        if tl>0.6: paste(fr,T_woh,cx,cy-380,scale=1.4-0.4*eob((tl-0.6)/0.3),alpha=clamp((tl-0.6)/0.15))
        if tl>1.3: paste(fr,T_naam,cx,cy-250,alpha=clamp((tl-1.3)/0.25))
        if tl>1.9: paste(fr,T_tha,cx,cy-140,alpha=clamp((tl-1.9)/0.25))
        g2=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g2)
        gd.ellipse([cx-260,cy-60,cx+260,cy+420],fill=(210,31,43,int(30+20*math.sin(tl*4))))
        g2=g2.filter(ImageFilter.GaussianBlur(90)); fr.paste(Image.alpha_composite(fr.convert('RGBA'),g2).convert('RGB'),(0,0))
        return 1.0
    if bi==4:
        fr.paste(Image.new('RGB',(W,H),INK),(0,0))
        u=eoc(tl/0.5); gap=int(540*(1-u))
        paste(fr,crowd.convert('RGBA'),cx-270-gap*0.6-40*clamp(tl/4),cy)
        paste(fr,perso.convert('RGBA'),cx+270+gap*0.6+40*clamp(tl/4),cy)
        d=ImageDraw.Draw(fr); lh=int(H*u*0.5)
        d.rectangle([cx-6,cy-lh,cx+6,cy+lh],fill=RED)
        d.rounded_rectangle([cx-520,cy-880,cx+520,cy+880],radius=26,outline=PAPER,width=16)
        if tl>0.8: paste(fr,T_pag,cx-270,cy-420,scale=1.5-0.5*eob((tl-0.8)/0.25),alpha=clamp((tl-0.8)/0.12))
        if tl>1.5: paste(fr,T_vis,cx+270,cy+380,scale=1.6-0.6*eob((tl-1.5)/0.25),alpha=clamp((tl-1.5)/0.12))
        return 1.0
    if bi==5:
        push=1.05+0.06*clamp(tl/4)
        paste(fr,empire.convert('RGBA'),cx,cy,scale=push)
        pts=[(cx-260,cy+340),(cx-140,cy+300),(cx-20,cy+310),(cx+110,cy+200),(cx+240,cy+80)]
        u=clamp((tl-0.8)/1.4); n=int(len(pts)*u); d=ImageDraw.Draw(fr)
        if n>1: d.line(pts[:n],fill=RED,width=10,joint='curve')
        for i,p in enumerate(pts[:n]):
            pp=1.4-0.4*eob((tl-0.8-i*1.4/5)/0.2)
            r=int(10*pp); d.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r],fill=PAPER)
        if tl>0.4: paste(fr,T_aaj,cx,cy-460,alpha=clamp((tl-0.4)/0.2))
        if tl>0.9: paste(fr,T_bari,cx,cy-320,scale=1.5-0.5*eob((tl-0.9)/0.3),alpha=clamp((tl-0.9)/0.12))
        if tl>1.5: paste(fr,T_chip,cx,cy-190,alpha=clamp((tl-1.5)/0.2))
        return 1.0
    if bi==6:
        fr.paste(ImageEnhance.Brightness(cover(sc1,W,H).filter(ImageFilter.GaussianBlur(34))).enhance(0.3).convert('RGB'),(0,0))
        sy=0.08+0.92*eob(tl/0.5)
        im2=news.resize((news.width,max(1,int(news.height*sy))))
        paste(fr,im2,cx,cy-60,rot=3*eoc(tl/0.6))
        if tl>1.0:
            u=clamp((tl-1.0)/0.8); d=ImageDraw.Draw(fr)
            d.arc([cx-400,cy+300,cx+400,cy+460],start=-90,end=-90+360*u,fill=RED,width=8)
        if tl>2.2: paste(fr,T_foot,cx,cy+700,scale=1.5-0.5*eob((tl-2.2)/0.25),alpha=clamp((tl-2.2)/0.12))
        return 1+0.04*clamp(tl/4)
    if bi==7:
        fr.paste(ImageEnhance.Brightness(cover(char,W,H).filter(ImageFilter.GaussianBlur(34))).enhance(0.28).convert('RGB'),(0,0))
        dy=-1300+1300*ebounce(tl/0.8) if tl<0.8 else 0
        paste(fr,charc.convert('RGBA'),cx,cy-180+dy)
        if tl>0.7:
            u=eob((tl-0.7)/0.3); d=ImageDraw.Draw(fr)
            s=1.4-0.4*u
            pts=[(W//2-150,170),(W//2-85,60),(W//2-30,150),(W//2,40),(W//2+30,150),(W//2+85,60),(W//2+150,170)]
            pts=[(W//2+(p[0]-W//2)*s,170+(p[1]-170)*s+40) for p in pts]
            d.polygon(pts,fill=RED)
        for i,(T,yy) in enumerate([(T_rule,1480),(T_r1,1600),(T_r2,1710),(T_r3,1820)]):
            t0=1.1+i*0.35
            if tl>t0: paste(fr,T,cx,yy+40*(1-eoc((tl-t0)/0.3)),alpha=clamp((tl-t0)/0.15))
        if tl>3.9:
            u=clamp((tl-3.9)/0.7); fr.paste(Image.blend(fr,Image.new('RGB',(W,H),INK),u),(0,0))
        return 1.0

ff=imageio_ffmpeg.get_ffmpeg_exe()
proc=subprocess.Popen([ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p',TMP+'/video2.mp4'],stdin=subprocess.PIPE)
NF=int(TOTAL*FPS)
for fno in range(NF):
    t=fno/FPS
    bi=0
    for i,st in enumerate(STARTS):
        if t>=st: bi=i
    tl=t-STARTS[bi]
    fr=Image.new('RGB',(W,H),INK)
    push=beat(fr,bi,tl)
    if push!=1.0:
        w2,h2=int(W*push),int(H*push)
        fr=cover(fr,w2,h2).resize((W,H))
    # cut flash + shake
    sh=shake_amt(t,HITS)
    if sh>0:
        dx=int(14*sh*math.sin(fno*2.1)); dy=int(10*sh*math.cos(fno*1.7))
        fr=fr.transform((W,H),Image.AFFINE,(1,0,dx,0,1,dy),fillcolor=(10,10,11))
    for st in STARTS[1:]:
        dt=t-st
        if 0<=dt<0.12:
            fl=Image.new('RGB',(W,H),(255,240,235)); fr=Image.blend(fr,fl,0.5*(1-dt/0.12))
    gr=grains[fno%4].resize((W,H)); fr.paste(Image.alpha_composite(fr.convert('RGBA'),gr).convert('RGB'),(0,0))
    fr.paste(Image.composite(fr,Image.new('RGB',(W,H),INK),vig),(0,0))
    proc.stdin.write(fr.tobytes())
proc.stdin.close(); proc.wait()
# mux with existing audio
subprocess.run(f"{ff} -y -loglevel error -i {TMP}/video2.mp4 -i {ROOT}/deliverables/shorts/S01_monarch_20billion.mp4 -map 0:v -map 1:a -c:v copy -c:a copy -shortest {ROOT}/deliverables/shorts/S01_monarch_20billion_v2.mp4",shell=True,check=True)
subprocess.run(f"{ff} -y -loglevel error -i {ROOT}/deliverables/shorts/S01_monarch_20billion_v2.mp4 -c:v libx264 -preset slow -crf 28 -c:a copy {ROOT}/deliverables/shorts/S01_monarch_20billion_v2_web.mp4",shell=True,check=True)
print('DONE v2',os.path.getsize(ROOT+'/deliverables/shorts/S01_monarch_20billion_v2_web.mp4'))
