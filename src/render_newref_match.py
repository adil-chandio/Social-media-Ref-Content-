#!/usr/bin/env python3
"""Recreate the supplied 18 s construction-site reference shot-for-shot, replacing the
on-screen model with Adil's supplied portrait cutout. Reference footage supplies every
plate, cut and the untouched soundtrack; the replacement layer is camera-tracked per shot
(ECC affine), luminance/grade matched and grain-matched so it sits inside the footage.
Another creator's watermark glyph/handle is inpainted out; the outro card carries an
ADIL CHANDIO wordmark instead of the source handle."""
import json, math, os, subprocess, sys
import numpy as np, cv2
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H,FPS=720,1280,30
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
CACHE='/tmp/newref_cache'
CUTS=[0,88,106,124,144,150,161,180,198,216,224,234,253,272,291,309,327,344,364,383,401,423,539]
OUTRO_PULSE=(14.466,14.721,15.0)
FONT=os.path.join(ROOT,'assets','fonts','Manrope-800.ttf')
MONO=os.path.join(ROOT,'assets','fonts','IBMPlexMono-400.ttf')

MANUAL_WM={1:[(490,350,710,445)],2:[(490,350,710,445)],18:[(95,820,380,940)],19:[(95,820,380,940)],20:[(95,820,380,940)]}
MANUAL_BBOX={0:(255,395,465,955),1:(250,370,470,960),2:(250,430,470,960),3:(270,235,450,880),
 4:(280,255,560,690),5:(330,240,560,760),6:(330,240,680,1080),7:(50,290,640,780),
 8:(255,410,470,860),9:(300,415,470,790),10:(300,410,470,790),11:(140,300,600,940),
 12:(320,300,520,820),13:(260,300,610,1040),14:(110,340,390,760),15:(240,265,480,920),
 16:(300,300,500,820),17:(320,260,640,900),18:(320,260,640,905),19:(50,380,330,680),
 20:(230,230,530,1060),21:(230,220,510,980)}
CUT=Image.open(os.path.join(ROOT,'assets','adil-photo-cutout.png')).convert('RGBA')
ca=np.array(CUT)
al=ca[...,3]
ys,xs=np.where(al>128)
PB=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]   # person bbox inside cutout

def glyph_template(size=56):
    t=np.zeros((size,size),np.float32)
    im=Image.fromarray(t); d=ImageDraw.Draw(im)
    d.rounded_rectangle((4,4,size-5,size-5),radius=14,outline=255,width=4)
    d.ellipse((size//2-11,size//2-11,size//2+11,size//2+11),outline=255,width=4)
    d.ellipse((size-20,12,size-12,20),fill=255)
    return np.array(im,np.float32)

def find_watermark(gray):
    """Locate the source creator's instagram glyph + handle line; returns patch boxes."""
    boxes=[]; best=None
    gf=gray.astype(np.float32)
    for size in (40,48,56,64,72):
        res=cv2.matchTemplate(gf,glyph_template(size),cv2.TM_CCOEFF_NORMED)
        _,mx,_,loc=cv2.minMaxLoc(res)
        if best is None or mx>best[0]: best=(mx,size,loc,res)
    mx,size,loc,res=best
    for _ in range(3):
        if mx<0.28: break
        x,y=loc; boxes.append((x-4,y-4,x+size+4,y+size+4))
        band=gray[max(0,y+16):y+150, max(0,x-140):x+180]
        if band.size:
            m=band>200
            if m.any():
                yy,xx=np.where(m)
                bx0,by0=max(0,x-140)+xx.min(), max(0,y+16)+yy.min()
                bx1,by1=max(0,x-140)+xx.max(), max(0,y+16)+yy.max()
                if bx1-bx0>40: boxes.append((bx0-4,by0-4,bx1+4,by1+6))
        res[max(0,y-40):y+44, max(0,x-40):x+44]=-1
        _,mx,_,loc=cv2.minMaxLoc(res)
    return boxes

def build_person(si, bbox, plate):
    """Adil cutout placed over the model, collage-graded: keyline, shadow, grade match."""
    x0,y0,x1,y1=bbox; bw,bh=x1-x0,y1-y0
    pw,ph=PB[2]-PB[0],PB[3]-PB[1]
    wfac={6:1.34,8:1.34,13:1.34,17:1.5,19:1.34,20:1.34}.get(si,1.04)
    scl=max(bw*wfac/pw, bh*1.08/ph)
    anchor=y1+0.03*bh; fade_px=26
    if bh>=430 and (H-y0)/ph<=2.05:
        scl=(H-y0)/ph; anchor=float(H); fade_px=0
    cw,ch=int(512*scl),int(512*scl)
    img=CUT.resize((cw,ch),Image.Resampling.LANCZOS)
    a=np.array(img)
    g=cv2.cvtColor(a[...,:3],cv2.COLOR_RGB2GRAY).astype(np.float32)
    m=a[...,3]>128
    gm,gs=g[m].mean(), g[m].std()+1e-3
    lg=cv2.cvtColor(plate,cv2.COLOR_RGB2GRAY).astype(np.float32)
    tm=float(np.clip(np.median(lg[H//2:, :])*0.35+18,40,95))
    ts=62.0
    g=np.clip((g-gm)/gs*ts+tm,0,255)
    tint=plate.reshape(-1,3).mean(0).astype(np.float32)
    rgb=np.stack([g*(0.78+0.22*tint[i]/255) for i in range(3)],-1).astype(np.uint8)
    a[...,:3]=rgb
    al=a[...,3].astype(np.float32)
    # kill the hard bottom crop line with a short fade
    fade=np.ones((ch,1),np.float32)
    if fade_px: fade[-fade_px:]=np.linspace(1,0,fade_px)[:,None]
    al=al*fade
    a[...,3]=al.astype(np.uint8)
    px=int((x0+x1)/2-(PB[0]+PB[2])/2*scl); py=int(anchor-PB[3]*scl)
    layer=np.zeros((H,W,4),np.uint8)
    xs0,ys0=max(0,px),max(0,py)
    xs1,ys1=min(W,px+cw),min(H,py+ch)
    layer[ys0:ys1,xs0:xs1]=a[ys0-py:ys1-py, xs0-px:xs1-px]
    # keyline + contact shadow baked into layer stack
    alpha=layer[...,3]
    dil=cv2.dilate(alpha,np.ones((3,3),np.uint8),iterations=1)
    key=((dil>60)&(alpha<=60)).astype(np.uint8)*150
    sh=cv2.GaussianBlur(alpha,(0,0),9).astype(np.float32)/255*95
    return layer, key, sh

def main():
    src=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,'google_drive','VID_20261027_190047_159.mp4')
    dst=sys.argv[2] if len(sys.argv)>2 else os.path.join(ROOT,'deliverables','adil-chandio-site-match.mp4')
    frames=np.load('/tmp/newref_frames.npy')
    shots=json.load(open(f'{CACHE}/shots.json'))
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    # per-shot prep: watermark patches, grade stats, tracked layers
    prep={}
    for si in range(len(CUTS)-1):
        a,b=CUTS[si],CUTS[si+1]; mid=(a+b)//2
        fr=frames[mid]; gray=cv2.cvtColor(fr,cv2.COLOR_RGB2GRAY)
        boxes=find_watermark(gray)
        mask=np.zeros((H,W),np.uint8)
        for (bx0,by0,bx1,by1) in boxes:
            mask[max(0,by0):min(H,by1), max(0,bx0):min(W,bx1)]=255
        layer,key,sh=build_person(si, MANUAL_BBOX[si], frames[a])
        stack=np.array([cv2.cvtColor(frames[f],cv2.COLOR_RGB2GRAY) for f in range(a,min(b,a+56),4)])
        med=np.median(stack,axis=0).astype(np.uint8)
        th=cv2.morphologyEx(med,cv2.MORPH_TOPHAT,np.ones((11,11),np.uint8))
        gt=cv2.dilate(((th>26)|(med>215)).astype(np.uint8)*255,np.ones((5,3),np.uint8))
        ncc,lab2,st2,_=cv2.connectedComponentsWithStats(gt,8)
        laya=layer[...,3]
        for i in range(1,ncc):
            x,y,w,h,area=st2[i]
            if 10<=h<=90 and 40<=w<=340 and area>=220:
                mask[max(0,y-3):y+h+3, max(0,x-3):x+w+3]=255
        mimg=cv2.imread(f'{CACHE}/mask_{si:02d}.png',0)
        region=fr[mimg>128]
        if region.size:
            lg=cv2.cvtColor(fr,cv2.COLOR_RGB2GRAY).astype(np.float32)
            tm=float(lg[mimg>128].mean()); ts=float(lg[mimg>128].std())
        else: tm,ts=110.0,55.0
        if si==len(CUTS)-2: tm,ts=92.0,46.0     # outro keeps him readable in the dark
        tint=fr.reshape(-1,3).mean(0)
        rx0,ry0,rx1,ry1=MANUAL_BBOX[si]
        rectm=np.zeros((H,W),np.uint8); rectm[ry0:ry1,rx0:rx1]=255
        rem=cv2.bitwise_and(rectm,cv2.bitwise_not(cv2.dilate(layer[...,3],np.ones((9,9),np.uint8))))
        for (mx0,my0,mx1,my1) in MANUAL_WM.get(si,[]):
            mask[my0:my1,mx0:mx1]=255
        if si==len(CUTS)-2:
            mask[1040:1100,240:480]=255
            frf=frames[mid].astype(np.int16)
            mag=((frf[...,0]>140)&(frf[...,2]>110)&(frf[...,1]<120)).astype(np.uint8)*255
            mag=cv2.dilate(mag,np.ones((9,9),np.uint8))
            mask=cv2.bitwise_or(mask,mag)
        blur=0.0
        lap=cv2.Laplacian(gray,cv2.CV_32F).var()
        if lap<120: blur=2.2
        elif lap<260: blur=1.1
        prep[si]=dict(boxes=boxes,mask=mask,layer=layer,key=key,sh=sh,blur=blur,rem=rem)
        print('shot',si,'wm',len(boxes),'rem',int((mask>0).sum()),'blur',blur)
    trs=[]
    for si in range(len(CUTS)-1):
        a,b=CUTS[si],CUTS[si+1]
        ref=cv2.cvtColor(frames[a],cv2.COLOR_RGB2GRAY)
        Wc=np.eye(2,3,dtype=np.float32); prev=ref
        chain=[]
        for f in range(a,b):
            if f>a:
                cur=cv2.cvtColor(frames[f],cv2.COLOR_RGB2GRAY)
                Ws=np.eye(2,3,dtype=np.float32)
                try:
                    cc,Ws=cv2.findTransformECC(prev,cur,Ws,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,50,1e-4))
                except cv2.error:
                    Ws=np.eye(2,3,dtype=np.float32)
                sc=math.hypot(Ws[0,0],Ws[1,0])
                if abs(sc-1)>0.10 or abs(Ws[0,2])>90 or abs(Ws[1,2])>90:
                    Ws=np.eye(2,3,dtype=np.float32)
                Wc=np.vstack([Ws @ np.vstack([Wc,[0,0,1]])])[:2].astype(np.float32)
                prev=cur
            Wf=np.eye(2,3,dtype=np.float32)
            try:
                cc,Wf=cv2.findTransformECC(ref,cv2.cvtColor(frames[f],cv2.COLOR_RGB2GRAY),Wf,cv2.MOTION_EUCLIDEAN,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,50,1e-4))
            except cv2.error:
                Wf=Wc
            Wuse=Wc if (abs(Wc[0,2]-Wf[0,2])<=60 and abs(Wc[1,2]-Wf[1,2])<=60) else Wf
            chain.append(Wuse.copy())
        trs.append(np.array(chain))
        print('tracked',si)
    # render
    cmd=[ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','30','-i','-',
         '-i',src,'-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','18',
         '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',dst]
    enc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    rng=np.random.default_rng(7)
    for f in range(len(frames)):
        si=int(np.searchsorted(CUTS,f,side='right')-1)
        fr=frames[f].copy()
        p=prep[si]
        if p['mask'].any(): fr=cv2.inpaint(fr,p['mask'],3,cv2.INPAINT_TELEA)
        Wm=trs[si][f-CUTS[si]]
        if p['rem'].any():
            remf=cv2.warpAffine(p['rem'],Wm,(W,H),flags=cv2.INTER_NEAREST,borderValue=0)
            fr=cv2.inpaint(fr,remf,3,cv2.INPAINT_TELEA)
        lay=cv2.warpAffine(p['layer'],Wm,(W,H),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
        key=cv2.warpAffine(p['key'],Wm,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
        shd=cv2.warpAffine(p['sh'],Wm,(W,H),flags=cv2.INTER_LINEAR,borderValue=0)
        fr=fr.astype(np.float32)
        sa=(shd/255.0)[...,None]
        fr=fr*(1-sa*0.55)+np.array([8,8,10],np.float32)*sa*0.55
        ka=(key/255.0)[...,None]
        fr=fr*(1-ka)+np.array([238,238,236],np.float32)*ka
        la=(lay[...,3:4].astype(np.float32)/255)
        fr=(lay[...,:3].astype(np.float32)*la+fr*(1-la))
        fr=np.clip(fr,0,255).astype(np.uint8)
        if p['blur']: fr=cv2.GaussianBlur(fr,(0,0),p['blur']*0.7)
        if si==len(CUTS)-2:
            t=f/FPS
            pulse=max((math.exp(-.5*((t-h_)/.06)**2) for h_ in OUTRO_PULSE),default=0.0)
            img=Image.fromarray(fr); d=ImageDraw.Draw(img,'RGBA')
            fade=max(0,min(1,(t-14.35)/.35))
            fnt=ImageFont.truetype(FONT,int(58+6*pulse))
            txt='ADIL CHANDIO'
            wbox=d.textbbox((0,0),txt,font=fnt)
            d.text(((W-wbox[2])/2,905),txt,font=fnt,fill=(245,245,245,int(255*fade)))
            mf=ImageFont.truetype(MONO,17)
            d.text(((W-330)/2,985),'AI LEARNER  •  CONTENT CREATOR  •  DEVELOPER',font=mf,fill=(214,178,148,int(235*fade)))
            fr=np.array(img)
        fr=fr.astype(np.int16)+rng.integers(-3,4,(H,W,1))
        fr=np.clip(fr,0,255).astype(np.uint8)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait()
    print('rendered',dst)

if __name__=='__main__':
    main()
