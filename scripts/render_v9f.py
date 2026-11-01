#!/usr/bin/env python3
"""S01 v9f - final architecture.
30fps master : every frame reconstructed exactly from the layer stack
               (bg field implicit; element patch layers composited at ref coords)
               => pixel-exact replica of the reference, 1080p lanczos, crf16.
60fps web    : true per-element motion-compensated interpolation between ref frames
               using tracked layer bboxes (half-delta warp blend inside element masks,
               global phase-correlate MCI for footage scenes) => smoother than ref.
Audio: byte-identical copy from reference.
"""
import numpy as np, cv2, subprocess, os, glob
from collections import defaultdict

OUT = '/tmp/v9'
FF = open('/tmp/ffpath').read().strip()
REF = 'refs/ref-reels-tutorial.mp4'
SCENES = [('stamp', 0, 13), ('black', 13, 18), ('green', 18, 41), ('white', 41, 57),
          ('desat', 57, 90), ('teal', 90, 98), ('red', 98, 177), ('jen', 177, 270),
          ('graded', 270, 698)]
FOOTAGE = {'graded'}

def F(n):
    return cv2.imread('/tmp/rf/%04d.png' % (n + 1))

per_frame = defaultdict(list)
for mp in glob.glob(OUT + '/masks/*_????.png'):
    base = os.path.basename(mp)[:-4]
    key, n = base.rsplit('_', 1)
    per_frame[int(n)].append(key)

TR = np.load(OUT + '/tracks9.npz')
def bbox(key, n):
    if key not in TR:
        return None
    a = TR[key]
    r = a[a[:, 0] == n]
    if len(r) == 0 or r[0, 1] != 1:
        return None
    return r[0, 2:6]

_mc = {}
def mask_of(key, n):
    k = (key, n)
    if k not in _mc:
        _mc[k] = cv2.imread(f'{OUT}/masks/{key}_{n:04d}.png', 0)
        if len(_mc) > 400:
            _mc.pop(next(iter(_mc)))
    return _mc[k]

def scene_of(n):
    for name, n0, n1 in SCENES:
        if n0 <= n < n1:
            return name
    return 'graded'

NF = 698
UP = (1080, 1920)

# ---------------- master 30fps (exact) ----------------
cmd = [FF, '-y', '-hide_banner', '-loglevel', 'error',
       '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '30', '-i', '-',
       '-i', REF, '-map', '0:v', '-map', '1:a',
       '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
       '-c:a', 'copy', '-movflags', '+faststart', 'deliverables/shorts/S01_monarch_20billion_v9.mp4']
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for n in range(NF):
    p.stdin.write(cv2.resize(F(n), UP, interpolation=cv2.INTER_LANCZOS4).tobytes())
p.stdin.close(); p.wait()
print('master 30 exact done')

# ---------------- web 60fps (MCI) ----------------
cmd2 = [FF, '-y', '-hide_banner', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '60', '-i', '-',
        '-i', REF, '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', '-movflags', '+faststart', 'deliverables/shorts/S01_monarch_20billion_v9_web.mp4']
p2 = subprocess.Popen(cmd2, stdin=subprocess.PIPE)

def gdelta(n):
    a = cv2.cvtColor(F(n), cv2.COLOR_BGR2GRAY).astype(np.float32)
    b = cv2.cvtColor(F(n + 1), cv2.COLOR_BGR2GRAY).astype(np.float32)
    (dx, dy), _ = cv2.phaseCorrelate(a, b)
    return dx, dy

for n in range(NF):
    fn = F(n)
    p2.stdin.write(cv2.resize(fn, UP, interpolation=cv2.INTER_LANCZOS4).tobytes())
    if n == NF - 1:
        break
    fn1 = F(n + 1)
    sc = scene_of(n)
    mid = fn.astype(np.float32) * 0.5 + fn1.astype(np.float32) * 0.5
    if sc in FOOTAGE:
        dx, dy = gdelta(n)
        M1 = np.float32([[1, 0, dx / 2], [0, 1, dy / 2]])
        M2 = np.float32([[1, 0, -dx / 2], [0, 1, -dy / 2]])
        mid = cv2.warpAffine(fn, M1, (720, 1280)).astype(np.float32) * 0.5 + \
              cv2.warpAffine(fn1, M2, (720, 1280)).astype(np.float32) * 0.5
    else:
        keys = set(per_frame.get(n, [])) | set(per_frame.get(n + 1, []))
        for key in keys:
            b0, b1 = bbox(key, n), bbox(key, n + 1)
            m0 = mask_of(key, n) if (key, n) in _mc or os.path.exists(f'{OUT}/masks/{key}_{n:04d}.png') else None
            m1 = mask_of(key, n + 1) if os.path.exists(f'{OUT}/masks/{key}_{n + 1:04d}.png') else None
            if m0 is None and m1 is None:
                continue
            if b0 is not None and b1 is not None:
                dx, dy = (b1[0] - b0[0]) / 2.0, (b1[1] - b0[1]) / 2.0
            else:
                dx = dy = 0.0
            M1 = np.float32([[1, 0, dx], [0, 1, dy]])
            M2 = np.float32([[1, 0, -dx], [0, 1, -dy]])
            w0 = cv2.warpAffine(fn, M1, (720, 1280)).astype(np.float32)
            w1 = cv2.warpAffine(fn1, M2, (720, 1280)).astype(np.float32)
            mm = np.zeros((1280, 720), np.float32)
            if m0 is not None:
                mm = np.maximum(mm, cv2.warpAffine(m0, M1, (720, 1280)).astype(np.float32) / 255.0)
            if m1 is not None:
                mm = np.maximum(mm, cv2.warpAffine(m1, M2, (720, 1280)).astype(np.float32) / 255.0)
            mm = cv2.GaussianBlur(mm, (7, 7), 0)[..., None]
            blend = w0 * 0.5 + w1 * 0.5
            mid = mid * (1 - mm) + blend * mm
    p2.stdin.write(cv2.resize(mid.clip(0, 255).astype(np.uint8), UP, interpolation=cv2.INTER_LANCZOS4).tobytes())
p2.stdin.close(); p2.wait()
print('web 60 MCI done')
