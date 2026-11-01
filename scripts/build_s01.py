#!/usr/bin/env python3
"""S01 MONARCH short builder: PIL 9:16 frames -> ffmpeg zoompan + xfade + SFX + VO."""
import os, subprocess, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = os.path.join(ROOT, 'docs/shorts/s01')
OUT = os.path.join(ROOT, 'deliverables/shorts'); os.makedirs(OUT, exist_ok=True)
TMP = '/tmp/s01'; os.makedirs(TMP, exist_ok=True)
F_MAN = os.path.join(ROOT, 'portfolio-site/assets/fonts/Manrope-800.ttf')
F_MONO = os.path.join(ROOT, 'portfolio-site/assets/fonts/IBMPlexMono-400.ttf')
INK=(10,10,11); PAPER=(236,233,226); RED=(210,31,43); YEL=(232,196,60)
W,H=1080,1920; CW,CH=640,1138; CX,CY=(W-CW)//2,(H-CH)//2

def font(p,s): return ImageFont.truetype(p,s)
def cover(im,w,h):
    r=max(w/im.width,h/im.height); im=im.resize((int(im.width*r),int(im.height*r)))
    return im.crop(((im.width-w)//2,(im.height-h)//2,(im.width-w)//2+w,(im.height-h)//2+h))
def condensed(txt,f,fill):
    tmp=Image.new('RGBA',(3000,600),(0,0,0,0)); d=ImageDraw.Draw(tmp)
    d.text((20,20),txt,font=f,fill=fill+(255,))
    bb=tmp.getbbox(); tmp=tmp.crop(bb) if bb else tmp
    return tmp.resize((max(1,int(tmp.width*0.86)),tmp.height))
def put(fr,im,x,y): fr.paste(im,(x,y),im)

def base(imgpath):
    im=Image.open(imgpath).convert('RGB')
    bleed=cover(im,W,H).filter(ImageFilter.GaussianBlur(26))
    bleed=ImageEnhance.Brightness(bleed).enhance(0.42)
    fr=bleed.copy()
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(sh)
    d.rectangle([CX-14,CY+10,CX+CW+14,CY+CH+16],fill=(0,0,0,160)); sh=sh.filter(ImageFilter.GaussianBlur(18))
    fr.paste(Image.alpha_composite(fr.convert('RGBA'),sh).convert('RGB'),(0,0))
    card=cover(im,CW,CH)
    fr.paste(card,(CX,CY))
    return fr

def tag(fr,txt,x,y,bg=RED,fg=PAPER,s=44):
    f=font(F_MONO,s); d=ImageDraw.Draw(fr); w=d.textlength(txt,font=f)
    d.rectangle([x,y,x+w+36,y+s+26],fill=bg); d.text((x+18,y+10),txt,font=f,fill=fg)

def beat1():
    fr=base(f'{SC}/sc1_moneybag.png'); d=ImageDraw.Draw(fr)
    tag(fr,'$20,000,000,000',CX+40,CY+70)
    put(fr,condensed('US NE KAHA',font(F_MAN,110),INK),CX+40,CY+180)
    put(fr,condensed('NAHI.',font(F_MAN,230),RED),CX+30,CY+320)
    d.rectangle([CX+40,CY+640,CX+300,CY+652],fill=INK)
    put(fr,condensed('INTEL KA OFFER — 2008',font(F_MONO,34),(90,88,84)),CX+40,CY+680)
    return fr
def beat2():
    fr=base(f'{SC}/sc2_boardroom.png')
    tag(fr,'2008',CX+40,CY+70,bg=YEL,fg=INK)
    put(fr,condensed('TABLE PAR',font(F_MAN,96),PAPER),CX+40,CY+200)
    put(fr,condensed('$20 BILLION',font(F_MAN,120),RED),CX+30,CY+330)
    put(fr,condensed('poori company ka offer',font(F_MONO,36),PAPER),CX+40,CY+500)
    return fr
def beat3():
    fr=base(f'{SC}/sc3_refuse.png'); d=ImageDraw.Draw(fr)
    put(fr,condensed('MANA KAR',font(F_MAN,130),PAPER),CX+40,CY+180)
    put(fr,condensed('DIYA.',font(F_MAN,130),RED),CX+40,CY+330)
    d.line([CX+50,CY+520,CX+560,CY+470],fill=RED,width=14)
    put(fr,condensed('paisa kam nahi tha…',font(F_MONO,40),PAPER),CX+40,CY+560)
    return fr
def beat4():
    fr=base(f'{SC}/sc4_chip.png')
    put(fr,condensed('WOH CHEEZ',font(F_MAN,110),PAPER),CX+40,CY+200)
    put(fr,condensed('JIS KA NAAM',font(F_MAN,86),(180,178,172)),CX+40,CY+340)
    put(fr,condensed('TAK NAHI THA',font(F_MAN,86),RED),CX+40,CY+450)
    return fr
def beat5():
    fr=base(f'{SC}/sc5_split.png'); d=ImageDraw.Draw(fr)
    d.rectangle([CX+CW//2-6,CY,CX+CW//2+6,CY+CH],fill=RED)
    put(fr,condensed('PAGALMAT',font(F_MAN,72),(150,148,144)),CX+24,CY+300)
    put(fr,condensed('VISION.',font(F_MAN,96),RED),CX+CW//2+26,CY+760)
    return fr
def beat6():
    fr=base(f'{SC}/sc6_empire.png'); d=ImageDraw.Draw(fr)
    put(fr,condensed('AAJ WOHI',font(F_MAN,90),PAPER),CX+40,CY+160)
    put(fr,condensed('SAB SE BARI',font(F_MAN,110),RED),CX+30,CY+290)
    put(fr,condensed('CHIP COMPANY',font(F_MAN,90),PAPER),CX+40,CY+430)
    pts=[(CX+60,CY+900),(CX+180,CY+860),(CX+300,CY+870),(CX+430,CY+760),(CX+560,CY+640)]
    d.line(pts,fill=RED,width=10,joint='curve')
    for p in pts: d.ellipse([p[0]-10,p[1]-10,p[0]+10,p[1]+10],fill=PAPER)
    return fr
def beat7():
    fr=Image.new('RGB',(W,H),INK)
    bleed=cover(Image.open(f'{SC}/sc1_moneybag.png').convert('RGB'),W,H).filter(ImageFilter.GaussianBlur(30))
    fr=ImageEnhance.Brightness(bleed).enhance(0.3)
    nw,nh=680,900; nx,ny=(W-nw)//2,(H-nh)//2
    paper=Image.new('RGB',(nw,nh),(238,234,224)); d=ImageDraw.Draw(paper)
    d.rectangle([0,0,nw,90],fill=(228,222,208))
    d.text((40,26),'THE MONARCH HERALD',font=font(F_MAN,44),fill=INK)
    y=140
    for i in range(14):
        wln=nw-90 if i%3 else nw-160
        d.rectangle([45,y,45+wln,y+10],fill=(120,116,108) if i!=9 else INK)
        y+=44
    d.ellipse([30,y-70,nw-30,y+6],outline=RED,width=8)
    d.text((45,y+30),'$20,000,000,000 — footnote 7, page 3',font=font(F_MONO,26),fill=INK)
    fr.paste(paper,(nx,ny))
    put(fr,condensed('SIRF EK FOOTNOTE.',font(F_MAN,92),RED),nx,CY+CH+40)
    return fr
def beat8():
    fr=Image.new('RGB',(W,H),INK)
    ch=Image.open(os.path.join(ROOT,'docs/lookdev/char.jpg')).convert('RGB')
    ch=ch.crop((250,60,830,1080)); ch=cover(ch,560,980)
    fr.paste(ch,((W-560)//2,300))
    d=ImageDraw.Draw(fr)
    d.polygon([(W//2-110,260),(W//2-62,168),(W//2-22,244),(W//2,150),(W//2+22,244),(W//2+62,168),(W//2+110,260)],fill=RED)
    put(fr,condensed('MONARCH RULE:',font(F_MAN,74),YEL),(W-560)//2,1320)
    put(fr,condensed('JO DUNIYA KO KAL',font(F_MAN,80),PAPER),(W-560)//2,1420)
    put(fr,condensed('DIKHEGA —',font(F_MAN,80),PAPER),(W-560)//2,1520)
    put(fr,condensed('WOH AAJ BANAO.',font(F_MAN,86),RED),(W-560)//2,1620)
    return fr

BEATS=[(beat1,0.0,5.0,'fadeblack'),(beat2,5.0,10.0,'slideleft'),(beat3,10.0,15.0,'wiperight'),
       (beat4,15.0,20.0,'circleopen'),(beat5,20.0,24.0,'slideleft'),(beat6,24.0,28.0,'wiperight'),
       (beat7,28.0,32.0,'fadeblack'),(beat8,32.0,36.6,'fadeblack')]
for i,(fn,_,_,_) in enumerate(BEATS):
    fn().save(f'{TMP}/b{i}.png'); print('frame',i)
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()+' -y -loglevel error'
clips=[]
for i,(fn,t0,t1,tr) in enumerate(BEATS):
    dur=t1-t0; out=f'{TMP}/c{i}.mp4'; clips.append(out)
    N=int(dur*30)
    subprocess.run(f"{FF} -i {TMP}/b{i}.png -vf \"zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps=30,format=yuv420p\" -frames:v {N} -c:v libx264 -preset fast -pix_fmt yuv420p {out}",shell=True,check=True)
# xfade chain
ins=''.join(f'-i {c} ' for c in clips)
X=[t[3] for t in BEATS]
fc=[]; prev='0:v'; prevlen=BEATS[0][2]-BEATS[0][1]
for i in range(1,len(clips)):
    off=prevlen-0.35
    lab=f'v{i}'
    fc.append(f'[{prev}][{i}:v]xfade=transition={X[i]}:duration=0.35:offset={off:.2f}[{lab}]')
    prevlen=off+(BEATS[i][2]-BEATS[i][1]); prev=lab
cmd=f"{FF} {ins}-filter_complex \"{';'.join(fc)};[{prev}]format=yuv420p[vv]\" -map [vv] -c:v libx264 -preset fast -pix_fmt yuv420p {TMP}/video.mp4"
subprocess.run(cmd,shell=True,check=True)
# SFX
subprocess.run(f"{FF} -f lavfi -i \"anoisesrc=d=0.5:color=pink:r=44100,afade=t=in:d=0.15,afade=t=out:st=0.2:d=0.3,volume=0.5\" -f lavfi -i \"sine=f=90:d=0.3,volume=0.9:eval=frame,afade=t=out:st=0.05:d=0.25\" -filter_complex \"[0:a][1:a]concat=n=2:v=0:a=1[w1];[w1]volume=1\" -t 0.8 {TMP}/hit.wav",shell=True,check=True)
delays='| '.join('')
mixins=[]; fc2=[]
for i,(fn,t0,t1,tr) in enumerate(BEATS[1:],start=1):
    mixins.append(f'-i {TMP}/hit.wav'); fc2.append(f'[{i+2}:a]adelay={int(t0*1000)}|{int(t0*1000)}[h{i}]')
allh=''.join(f'[h{i}]' for i in range(1,len(BEATS)))
fc2.append(f'{allh}amix=inputs={len(BEATS)-1}:normalize=0[sfx]')
subprocess.run(f"{FF} -f lavfi -i \"sine=f=55:d=37,volume=0.10\" -f lavfi -i \"sine=f=82.5:d=37,volume=0.07\" -f lavfi -i \"sine=f=110:d=37,volume=0.05\" -f lavfi -i \"anoisesrc=d=37:color=brown:amplitude=0.02\" -filter_complex \"[0:a][1:a][2:a][3:a]amix=inputs=4:normalize=0,tremolo=f=0.5:d=0.4[bed]\" -map [bed] {TMP}/bed.wav",shell=True,check=True)
cmd=f"{FF} -i {TMP}/video.mp4 -i {ROOT}/audio/shorts/S01_vo.mp3 -i {TMP}/bed.wav {' '.join(mixins)} -filter_complex \"[1:a]volume=1.0[vo];[3:a]volume=0.5[s0];\"+\"\".join([]) if False else '' "
# simpler: build sfx mix first
if True:
    ins2=' '.join(f'-i {TMP}/hit.wav' for _ in range(len(BEATS)-1))
    fc3=[]; 
    for k,(fn,t0,t1,tr) in enumerate(BEATS[1:],start=0):
        fc3.append(f'[{k}:a]adelay={int(t0*1000)}|{int(t0*1000)}[h{k}]')
    fc3.append(''.join(f'[h{k}]' for k in range(len(BEATS)-1))+f'amix=inputs={len(BEATS)-1}:normalize=0,volume=0.6[sfx]')
    subprocess.run(f"{FF} {ins2} -filter_complex \"{';'.join(fc3)}\" -map [sfx] -t 37 {TMP}/sfx.wav",shell=True,check=True)
subprocess.run(f"{FF} -i {TMP}/video.mp4 -i {ROOT}/audio/shorts/S01_vo.mp3 -i {TMP}/bed.wav -i {TMP}/sfx.wav -filter_complex \"[1:a][2:a][3:a]amix=inputs=3:normalize=0,alimiter=limit=0.95,aformat=sample_rates=44100:channel_layouts=stereo[a]\" -map 0:v -map [a] -c:v copy -c:a aac -b:a 160k -shortest {OUT}/S01_monarch_20billion.mp4",shell=True,check=True)
print('DONE', os.path.getsize(f'{OUT}/S01_monarch_20billion.mp4'))
