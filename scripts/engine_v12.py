#!/usr/bin/env python3
"""S01 v12 compositor: Blender 3D renders (/tmp/b3d) + graded footage + grade.
Timeline 23.35s: graphics 0-9 (loop x2), graded footage 9-11.675 & 20.675-23.35.
Audio = refs/ref-audio.m4a verbatim (-c:a copy).
Usage: engine_v12.py [stills n,n,...]
"""
import cv2, numpy as np, math, subprocess, os, sys

W, H = 720, 1280
FPS = 30
PASS = 11.675
NF = 701
B3D = '/tmp/b3d'
RF = '/tmp/rf'

INK = (16, 16, 18); BONE = (244, 241, 234); GOLD = (212, 175, 55); RED = (255, 85, 96)

def bgr(c): return (c[2], c[1], c[0])

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt((( _xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) / 1.4142
_vig = (1 - 0.13 * (_r ** 2.2))[..., None]

GC = {}
def gframe(g):
    if g not in GC:
        GC[g] = cv2.imread(f'{B3D}/{g:04d}.png')
        if len(GC) > 40:
            GC.pop(next(iter(GC)))
    return GC[g]

FC = {}
def fframe(e):
    e = max(0, min(697, e))
    if e not in FC:
        FC[e] = cv2.imread(f'{RF}/{e + 1:04d}.png')
        if len(FC) > 8:
            FC.pop(next(iter(FC)))
    return FC[e]

SM = {}
GROUND = cv2.imread('/tmp/v11b/ground.png')

def smoke(n):
    if n not in SM:
        SM[n] = cv2.imread(f'/tmp/v11b/smoke/{n:04d}.png', 0)
    return SM[n]

GFX_END = 5.9

def scene_at(t):
    t = t % PASS
    if t < GFX_END:
        return 'gfx', t
    return 'graded', t

BC = {}
def bframe(g):
    if g not in BC:
        BC[g] = cv2.imread(f'/tmp/b3dB/{g:04d}.png', cv2.IMREAD_UNCHANGED)
        if len(BC) > 40:
            BC.pop(next(iter(BC)))
    return BC[g]

def graded(fr, t, tl):
    e = min(int(tl * 30), 696)
    f = fframe(e)
    out = f.astype(np.float32)
    fr[:] = out.clip(0, 255).astype(np.uint8)
    gk = min(1, seg(tl, 9.0, .6, lin) if tl < 11 else 1)
    if gk > 0:
        lum = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
        desat = fr.astype(np.float32) * 0.65 + lum * 0.35
        mul = np.array((0.64, 0.50, 0.67), np.float32)[None, None, :]
        gr = (desat * mul * 1.35).clip(0, 255)
        fr[:] = (fr.astype(np.float32) * (1 - gk) + gr * gk).astype(np.uint8)
    if gk > 0:
        g = np.zeros((H, W), np.float32)
        for ex in (-60, 60):
            cv2.ellipse(g, (360 + ex, 392), (30, 16), 0, 0, 360, 1.0, -1)
        g = cv2.GaussianBlur(g, (21, 21), 0) * gk
        fr[:] = np.clip(fr.astype(np.float32) + g[..., None] * np.array((30, 30, 255), np.float32) * 0.85, 0, 255).astype(np.uint8)

def lin(x): return x
def seg(t, t0, d, fn=None):
    return max(0.0, min(1.0, (t - t0) / d))

def render_frame(n):
    t = n / FPS
    sc, tl = scene_at(t)
    if sc == 'gfx':
        g = int(tl * 30) + 1
        fr = gframe(g).copy()
        # desat grade 1.90-3.00
        if 1.90 <= tl < 3.00:
            gsy = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            gsy = cv2.cvtColor(gsy, cv2.COLOR_GRAY2BGR).astype(np.float32)
            des = (fr.astype(np.float32) * 0.12 + gsy * 0.88).clip(0, 255)
            hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV).astype(np.int16)
            keep = (((hsv[..., 0] < 12) | (hsv[..., 0] > 168)) & (hsv[..., 1] > 110) & (hsv[..., 2] > 110)).astype(np.float32)
            keep = cv2.GaussianBlur(keep, (5, 5), 0)[..., None]
            fr = (des * (1 - keep) + fr.astype(np.float32) * keep).clip(0, 255).astype(np.uint8)
        # ground band (ref photo-bg grass blur) 41-89
        if 57 <= g <= 89:
            gd = GROUND
            if gd is not None:
                gh = 280
                gd2 = gd[gd.shape[0] - gh:]
                ramp = (np.linspace(0.0, 0.92, gh, dtype=np.float32) ** 1.6)[:, None, None]
                fr[H - gh:H] = (fr[H - gh:H].astype(np.float32) * (1 - ramp) + gd2.astype(np.float32) * ramp).astype(np.uint8)
        # smoke puffs 1.58-2.35
        if 1.55 <= tl < 2.45:
            sn = int(47 + (tl - 1.35) / .55 * 25)
            sm = smoke(min(72, max(47, sn)))
            if sm is not None:
                sa = min(1, (tl - 1.55) / .12) * min(1, (2.45 - tl) / .2) * 1.0
                scl = 0.95 + 0.35 * seg(tl, 1.6, .3)
                smi = cv2.resize(sm, (int(sm.shape[1] * scl), int(sm.shape[0] * scl)))
                a = (smi.astype(np.float32) / 255 * sa)[..., None]
                col = np.array((150, 148, 145), np.float32)
                for (px_, py_) in ((108, 410), (634, 512)):
                    x0 = px_ - smi.shape[1] // 2; y0 = py_ - smi.shape[0] // 2
                    xs, ye = max(x0, 0), min(y0 + smi.shape[0], H)
                    xe = min(x0 + smi.shape[1], W); ys = max(y0, 0)
                    aa = a[ys - y0:ye - y0, xs - x0:xe - x0]
                    fr[ys:ye, xs:xe] = (fr[ys:ye, xs:xe].astype(np.float32) * (1 - aa) + col * aa).astype(np.uint8)
    else:
        fr = np.zeros((H, W, 3), np.uint8)
        graded(fr, t, tl)
        g = int(tl * 30) + 1
        if 225 <= g <= 270:
            b = bframe(g)
            if b is not None and b.shape[2] == 4:
                a = (b[..., 3:4].astype(np.float32) / 255)
                fr = (fr.astype(np.float32) * (1 - a) + b[..., :3].astype(np.float32) * a).clip(0, 255).astype(np.uint8)
        # crossfade from last gfx frame at scene cut (5.9s / 17.575s)
        cut = GFX_END if t < PASS else PASS + GFX_END
        dt = t - cut
        if 0 <= dt < 0.25:
            g0 = gframe(177)
            k = dt / 0.25
            fr = (g0.astype(np.float32) * (1 - k) + fr.astype(np.float32) * k).clip(0, 255).astype(np.uint8)
    fr = (fr.astype(np.float32) * _vig).clip(0, 255).astype(np.uint8)
    grain = np.random.default_rng(n).normal(0, 1.1, (H, W, 1))
    fr = np.clip(fr.astype(np.float32) + grain, 0, 255).astype(np.uint8)
    return fr

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stills':
        for n in [int(x) for x in sys.argv[2].split(',')]:
            cv2.imwrite(f'/tmp/v12_still_{n}.png', render_frame(n))
        print('stills ok')
        sys.exit(0)
    AUDIO = os.environ.get('AUDIO', 'refs/ref-audio.m4a')
    OUTMP4 = os.environ.get('OUTMP4', 'deliverables/shorts/S01_monarch_20billion_v12.mp4')
    acodec = ['copy'] if AUDIO.endswith('.m4a') else ['aac', '-b:a', '192k']
    cmd = [open('/tmp/ffpath').read().strip(),
           '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', AUDIO,
           '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p',
           '-c:a'] + acodec + ['-shortest', OUTMP4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for n in range(NF):
        p.stdin.write(render_frame(n).tobytes())
        if n % 50 == 0:
            print('frame', n, flush=True)
    p.stdin.close(); p.wait()
    print('v12 master done', flush=True)
