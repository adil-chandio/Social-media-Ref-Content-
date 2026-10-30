#!/usr/bin/env python3
"""Reference-faithful Adil edit: retain the supplied reference frames and soundtrack,
then surgically replace creator-specific identity, cutout and skills text."""
import argparse, math, os, statistics, subprocess
from bisect import bisect_right
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import cv2
import numpy as np

W,H,FPS=720,1280,30
DURATION=33.9
# Measured source-audio accents inside the skill-scroll scene, prefixed by the
# scene cut. Each skill's focus lands exactly on the next impact (18.059 s included).
SKILL_SCROLL_ANCHORS=(15.0,15.126,16.991,18.059,19.127,20.194,21.262,22.329)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
SIL_PATH=os.path.join(ROOT,'assets','adil-silhouette.png')
FONT=os.path.join(ROOT,'assets','fonts','Manrope-400.ttf')
BOLD=os.path.join(ROOT,'assets','fonts','Manrope-700.ttf')
EXTRA=os.path.join(ROOT,'assets','fonts','Manrope-800.ttf')
MONO=os.path.join(ROOT,'assets','fonts','IBMPlexMono-400.ttf')
SIL=Image.open(SIL_PATH).convert('RGBA')


def fnt(size,kind='regular'):
    return ImageFont.truetype({'regular':FONT,'bold':BOLD,'extra':EXTRA,'mono':MONO}[kind],size)

def fit(draw,text,size,maxw,kind='bold'):
    while size>16 and draw.textlength(text,font=fnt(size,kind))>maxw:size-=1
    return fnt(size,kind)

def median_color(im,points):
    pix=im.load(); vals=[pix[x,y] for x,y in points]
    return tuple(int(statistics.median(c[i] for c in vals)) for i in range(3))

def patch(im,box,color=None,samples=None):
    x0,y0,x1,y1=box
    if color is None: color=median_color(im,samples or [(max(0,x0-8),max(0,y0-8)),(min(W-1,x1+8),max(0,y0-8)),(max(0,x0-8),min(H-1,y1+8)),(min(W-1,x1+8),min(H-1,y1+8))])
    ImageDraw.Draw(im).rectangle(box,fill=color)
    return color

def draw_split_name(d,text,center_x,y,size,color,second_bold=True):
    words=text.split(' ',1); first=words[0]; second=words[1] if len(words)>1 else ''
    a=fnt(size,'regular'); b=fnt(size,'bold' if second_bold else 'regular')
    gap=d.textlength(' ',font=a) if second else 0
    total=d.textlength(first,font=a)+gap+(d.textlength(second,font=b) if second else 0)
    x=center_x-total/2
    d.text((round(x),y),first,font=a,fill=color)
    if second:d.text((round(x+d.textlength(first,font=a)+gap),y),second,font=b,fill=color)

def reveal_name(d,text,center_x,y,size,color,progress):
    # Keep the same left-to-right type-on rhythm as the reference.
    count=max(0,min(len(text),int(math.floor(progress*len(text)+.5))))
    prefix=text[:count]
    if not prefix:return
    if ' ' in prefix:
        a,b=prefix.split(' ',1); draw_split_name(d,prefix,center_x,y,size,color)
    else:d.text((0,0),'',font=fnt(size),fill=color); d.text((center_x-d.textlength(prefix,font=fnt(size))/2,y),prefix,font=fnt(size),fill=color)

def spaced_center(d,text,center_x,y,font,color,tracking=1):
    widths=[d.textlength(ch,font=font) for ch in text]
    x=center_x-(sum(widths)+tracking*max(0,len(text)-1))/2
    for ch,ww in zip(text,widths):
        d.text((round(x),y),ch,font=font,fill=color);x+=ww+tracking

def draw_role(d,text,y,color,progress=1.0):
    f=fit(d,text,76,590,'regular')
    bbox=d.textbbox((0,0),text,font=f)
    tw=bbox[2]-bbox[0]; th=bbox[3]-bbox[1]
    visible=max(0,min(tw,int(tw*progress)))
    if not visible:return Image.new('RGBA',(W,H),(0,0,0,0))
    layer=Image.new('RGBA',(W,H),(0,0,0,0));ld=ImageDraw.Draw(layer)
    x=(W-tw)//2
    # Offset by bbox origin so ascenders/descenders are not clipped.
    ld.text((x-bbox[0],y-bbox[1]),text,font=f,fill=(*color,255))
    reveal=Image.new('L',(W,H),0);ImageDraw.Draw(reveal).rectangle((x,y,x+visible,y+th+2),fill=255)
    layer.putalpha(Image.composite(layer.getchannel('A'),Image.new('L',(W,H),0),reveal))
    return layer

def erase_text(im,box,threshold=36,skip_boxes=()):
    """Inpaint only contrasting glyphs in a tight source-text crop, preserving its backdrop."""
    x0,y0,x1,y1=box
    arr=np.asarray(im).copy();roi=arr[y0:y1,x0:x1]
    if roi.size==0:return im,None
    # Estimate each scanline's true backdrop from the clear margins beside the centered word.
    side=np.concatenate((roi[:,:14,:].reshape(-1,3),roi[:,-14:,:].reshape(-1,3))).reshape(roi.shape[0],28,3)
    bg=np.median(side,axis=1,keepdims=True)
    diff=np.max(np.abs(roi.astype(np.float32)-bg.astype(np.float32)),axis=2)
    keep=(diff>max(2,min(threshold,8))).astype(np.uint8)
    keep[:5,:]=0;keep[-5:,:]=0;keep[:,:14]=0;keep[:,-14:]=0
    for sx0,sy0,sx1,sy1 in skip_boxes:
        keep[max(0,sy0-y0):max(0,sy1-y0),max(0,sx0-x0):max(0,sx1-x0)]=0
    if int(keep.sum())<18:return im,None
    keep=cv2.dilate(keep,np.ones((3,3),np.uint8),iterations=1)
    ys,xs=np.where(keep>0)
    if len(xs)<18:return im,None
    # Color and baseline angle are sampled from the original lettering.
    strong=keep.astype(bool)&(diff>30)
    # Ignore peripheral circles/graphics when estimating the source text ink.
    sy0=max(0,590-y0);sy1=min(roi.shape[0],680-y0);sx0=max(0,188-x0);sx1=min(roi.shape[1],542-x0)
    text_samples=roi[sy0:sy1,sx0:sx1][strong[sy0:sy1,sx0:sx1]]
    if len(text_samples)<12:text_samples=roi[strong]
    if len(text_samples)<12:text_samples=roi[keep>0]
    color=tuple(int(v) for v in np.median(text_samples,axis=0))
    pts=np.column_stack((xs,ys)).astype(np.float32)
    cov=np.cov(pts.T)
    vals,vecs=np.linalg.eigh(cov);v=vecs[:,int(np.argmax(vals))]
    angle=math.degrees(math.atan2(float(v[1]),float(v[0])))
    if abs(angle)>28:angle=0
    result=arr.copy()
    result[y0:y1,x0:x1]=cv2.inpaint(roi,keep*255,5,cv2.INPAINT_TELEA)
    im.paste(Image.fromarray(result))
    return im,{'bbox':(x0+int(xs.min()),y0+int(ys.min()),x0+int(xs.max())+1,y0+int(ys.max())+1),'color':color,'angle':angle,'height':int(ys.max()-ys.min()+1)}

def draw_replacement(im,text,meta,center_x=360,progress=1.0):
    if not meta:return
    x0,y0,x1,y1=meta['bbox'];size=70
    probe=ImageDraw.Draw(Image.new('RGB',(W,20)))
    while size>42 and probe.textlength(text,font=fnt(size,'bold'))>455:size-=1
    d=ImageDraw.Draw(im)
    full=Image.new('RGBA',(W,150),(0,0,0,0));fd=ImageDraw.Draw(full)
    if progress<.999:
        reveal_name(fd,text,W//2,20,size,(*meta['color'],255),progress)
    else:draw_split_name(fd,text,W//2,20,size,(*meta['color'],255))
    bb=full.getbbox()
    if not bb:return
    glyph=full.crop(bb)
    if abs(meta['angle'])>2:glyph=glyph.rotate(-meta['angle'],resample=Image.Resampling.BICUBIC,expand=True)
    cx=360;cy=635
    im.paste(glyph,(cx-glyph.width//2,cy-glyph.height//2),glyph)

def replace_small_copy(im,box,text,color=(225,225,225),size=15,tracking=1):
    paint_row_patch(im,box)
    x0,y0,x1,y1=box;d=ImageDraw.Draw(im);font=fnt(size,'mono')
    spaced_center(d,text,(x0+x1)//2,y0+2,font,color,tracking)
    return im

def center_patch_text(im,box,sample_points,text,size,color,y,second_bold=True):
    patch(im,box,samples=sample_points)
    d=ImageDraw.Draw(im)
    draw_split_name(d,text,W//2,y,size,color,second_bold)

def paint_row_patch(im,box):
    x0,y0,x1,y1=box
    arr=np.asarray(im).copy()
    for y in range(y0,y1):
        left=arr[y,max(0,x0-10):x0];right=arr[y,x1:min(W,x1+10)]
        edge=np.concatenate((left,right),axis=0)
        c=np.median(edge,axis=0).astype(np.uint8) if len(edge) else np.median(arr[y,max(0,x0-2):min(W,x1+2)],axis=0).astype(np.uint8)
        arr[y,x0:x1]=c
    im.paste(Image.fromarray(arr))
    return tuple(int(v) for v in c)

def row_background(im,x0,x1,y0,y1):
    """Erase the original silhouette with each row's true background tone."""
    p=im.load()
    for y in range(y0,y1):
        c=median_color(im,[(x,y) for x in (24,55,95,625,665,696)])
        for x in range(x0,x1):p[x,y]=c

def replace_silhouette(im,t):
    if not 3.83<=t<5.82:return
    row_background(im,145,575,770,1280)
    # The supplied cutout replaces the reference figure at the same lower-center scale.
    h=480;w=round(h*SIL.width/SIL.height);sil=SIL.resize((w,h),Image.Resampling.LANCZOS)
    alpha=sil.getchannel('A')
    q=max(0,min(1,(t-3.90)/.28))
    if t>5.54:q*=max(0,min(1,(5.82-t)/.28))
    alpha=alpha.point(lambda a:int(a*q));sil.putalpha(alpha)
    im.paste(sil,((W-w)//2,800),sil)

def draw_orbits(d):
    c=(71,143,193)
    for cx,cy,r in [(360,340,157),(108,640,157),(612,640,157),(360,940,157),(360,640,226)]:
        d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=c,width=1)
    for x,y in [(360,414),(201,481),(519,481),(134,640),(586,640),(201,799),(519,799),(360,866)]:
        d.ellipse((x-5,y-5,x+5,y+5),outline=(114,168,205),width=1)

def remove_instagram_icon(im,box):
    """Clear the icon's small reserved flat-color slot without disturbing adjacent copy."""
    paint_row_patch(im,box)
    return im

def draw_rotated_skill(im,label,center_x,center_y,size,color,angle):
    layer=Image.new('RGBA',(460,64),(0,0,0,0));d=ImageDraw.Draw(layer);font=fnt(size,'regular')
    width=d.textlength(label,font=font);d.text(((460-width)/2,5),label,font=font,fill=(*color,255))
    if angle:layer=layer.rotate(-angle,resample=Image.Resampling.BICUBIC,expand=False)
    im.paste(layer,(center_x-230,center_y-32),layer)

def draw_adil_skills_carousel(im,t):
    """Keep the reference's cobalt orbital panel, but use Adil's eight approved skills."""
    bg=(9,95,163)
    ImageDraw.Draw(im).rectangle((40,180,680,1100),fill=bg)
    d=ImageDraw.Draw(im)
    # Rebuild the original thin orbit guides exactly in their reference positions.
    orbit=(28,111,170);axis=(22,105,164)
    d.ellipse((80,360,640,920),outline=orbit,width=1)
    d.ellipse((193,473,527,807),outline=orbit,width=1)
    d.line((360,186,360,1094),fill=axis,width=1)
    d.line((43,640,678,640),fill=axis,width=1)
    d.text((43,202),'DISCIPLINES',font=fnt(12,'mono'),fill=(177,204,224))
    d.text((654,202),'11',font=fnt(12,'mono'),fill=(177,204,224))
    d.text((44,624),'to play',font=fnt(39,'bold'),fill=(240,243,245))
    labels=['AI Learning','AI Content Creation','YouTube Automation','Workflow Automation',
            'Software Development','Monarch Agent Builds','Creator Tools & Systems','Motion & Video Editing']
    # Scroll phase follows the analyzed source hits rather than a guessed fixed-rate timer.
    # Each interval eases into the next skill so its focus lands exactly on the next impact.
    hit_index=max(0,min(len(SKILL_SCROLL_ANCHORS)-2,bisect_right(SKILL_SCROLL_ANCHORS,t)-1))
    hit0,hit1=SKILL_SCROLL_ANCHORS[hit_index:hit_index+2]
    beat_fraction=max(0.0,min(1.0,(t-hit0)/(hit1-hit0)))
    beat_fraction=beat_fraction*beat_fraction*(3-2*beat_fraction)
    scroll=float(hit_index)+beat_fraction
    active=int(math.floor(scroll))%len(labels);fraction=scroll-math.floor(scroll)
    accents=SKILL_SCROLL_ANCHORS[1:-1]
    pulse=max((math.exp(-.5*((t-hit)/.055)**2) for hit in accents),default=0.0)
    dot_r=6+round(2*pulse)
    d.ellipse((195-dot_r,641-dot_r,195+dot_r,641+dot_r),fill=(239,148,87))
    for slot in range(-3,5):
        pos=slot-fraction;y=640+round(pos*57);dist=abs(pos)
        if not 390<=y<=890:continue
        if dist<.58:size,ink=31+round(2*pulse),(237,243,247)
        elif dist<1.55:size,ink=25,(190,220,238)
        else:size,ink=19,(133,181,209)
        # The slight angle/scale falloff echoes the reference's curved text plane.
        angle=max(-7,min(7,-pos*1.8))
        draw_rotated_skill(im,labels[(active+slot)%len(labels)],422,y,size,ink,angle)
    # Keep the source's footer counter, but clear the creator-name stamp at lower left.
    paint_row_patch(im,(22,1070,190,1135))
    return im

def render_reference_frame(frame_bytes,t):
    im=Image.frombytes('RGB',(W,H),frame_bytes)
    # Instagram marks are removed wherever the reference placed them; no replacement icon is added.
    if 0.0<=t<9.6 or 22.0<=t<26.0:
        im=remove_instagram_icon(im,(620,298,675,360))
    if 8.8<=t<15.0 or 22.0<=t<29.95:
        im=remove_instagram_icon(im,(80,838,138,897))
    if 15.0<=t<22.0:
        im=draw_adil_skills_carousel(im,t)
    # Replace source creator handles in place, retaining per-row colors and exact shot timing.
    if 0.0<=t<9.6 or 22.0<=t<26.0:
        paint_row_patch(im,(520,369,683,412))
    if 8.8<=t<15.0 or 22.0<=t<30.0:
        paint_row_patch(im,(82,914,262,949))
    # Replace the source creator's centered name in-place, retaining source background, cut and type motion.
    name_window=(100,560,620,690)
    if 2.68<=t<4.94 or 7.82<=t<8.88 or 22.0<=t<26.12 or 25.85<=t<34.05:
        if t>=29.95:
            # Keep Adil's main signature title; the Instagram icon and social handle remain absent.
            patch(im,(120,535,600,665),color=(4,3,6))
            meta={'bbox':(200,600,520,650),'color':(43,43,45),'angle':0,'height':50}
            draw_replacement(im,'Adil Chandio',meta)
        else:
            # Replace the source creator's main title with Adil's, without restoring any social badges.
            im,meta=erase_text(im,name_window,threshold=4)
            if meta:
                progress=1.0
                if 2.68<=t<4.94:
                    if t<3.58:progress=max(0,min(1,(t-2.68)/.90))
                    elif t>4.56:progress=max(0,min(1,(4.94-t)/.34))
                draw_replacement(im,'Adil Chandio',meta,progress=progress)
    if 22.0<=t<22.98:
        d=ImageDraw.Draw(im)
        spaced_center(d,'6M+ VIEWS  •  4+ CHANNELS',360,703,fnt(13,'mono'),(69,69,69),1)
        spaced_center(d,'AI × CREATIVITY  •  LEARNING IN PUBLIC',360,732,fnt(11,'mono'),(96,92,88),0)
        spaced_center(d,'MONARCH BUILDS  •  DEVELOPMENT',360,756,fnt(10,'mono'),(96,92,88),0)
    # Identity portrait: retain reference scene and position; insert only the supplied cutout.
    replace_silhouette(im,t)
    # Match the role-title beats while replacing only their letters, never the scene itself.
    if 5.22<=t<5.90 or 5.92<=t<6.92 or 6.92<=t<7.84:
        paint_row_patch(im,(94,588,626,716))
        label='Content Creator' if t<5.90 else 'AI Learner' if t<6.92 else 'Developer'
        bg=median_color(im,[(102,610),(615,610),(102,690),(615,690)])
        col=(18,19,24) if sum(bg)>400 else (239,238,235)
        progress=max(.08,min(1,(t-(5.20 if t<5.90 else 5.93 if t<6.92 else 6.93))/.48))
        layer=draw_role(ImageDraw.Draw(im),label,605,col,progress)
        im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
    # Replace creator-specific discipline copy where it appears, leaving the reference's visual language intact.
    if 3.70<=t<4.90:
        replace_small_copy(im,(175,704,545,750),'AI LEARNER • CONTENT CREATOR • DEVELOPER',color=(35,35,37),size=12,tracking=0)
    if 26.25<=t<30.0:
        replace_small_copy(im,(145,674,575,730),'AI LEARNER • CONTENT CREATOR • DEVELOPER',color=(177,177,178),size=12,tracking=0)
    # No social handle or name is shown in the closing lock-up; use only Adil's role line.
    if 29.95<=t<34.05:
        replace_small_copy(im,(246,686,474,755),'AI LEARNER • CONTENT CREATOR • DEVELOPER',color=(155,155,158),size=8,tracking=0)
    return im

def main():
    ap=argparse.ArgumentParser();ap.add_argument('reference');ap.add_argument('output');args=ap.parse_args()
    ff=imageio_ffmpeg.get_ffmpeg_exe();frame_bytes=W*H*3
    dec=subprocess.Popen([ff,'-v','error','-i',args.reference,'-an','-f','rawvideo','-pix_fmt','rgb24','-vsync','0','-'],stdout=subprocess.PIPE)
    total=round(DURATION*FPS)
    enc=subprocess.Popen([ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',args.reference,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','14','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',args.output],stdin=subprocess.PIPE)
    try:
        for i in range(total):
            buf=dec.stdout.read(frame_bytes)
            if len(buf)<frame_bytes:break
            t=i/FPS
            out=render_reference_frame(buf,t)
            enc.stdin.write(out.tobytes())
            if i%150==0:print(f'Recreating reference {i/total:.0%}',flush=True)
        dec.stdout.close();dec.wait();enc.stdin.close();code=enc.wait()
        if code:raise RuntimeError(f'ffmpeg encode failed: {code}')
    except Exception:
        dec.kill();enc.kill();raise
    print('Created reference-matched video:',args.output)
if __name__=='__main__':main()
