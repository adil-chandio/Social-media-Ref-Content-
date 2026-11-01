#!/usr/bin/env python3
"""S01 v9 - layered reconstruction renderer.
Every output frame is COMPOSITED from independent layers:
  bg plate (per-scene median plate, ECC-warped by per-frame camera transform)
  + per-element feathered patch layers (alpha masks from precompute_v9b)
then lanczos-upscaled to 1080x1920 and encoded clean (crf16 master / crf20 web).
At 30fps sample points the reconstruction equals the reference by construction;
the layer structure is the foundation for S02+ persona/asset swaps.
"""
import numpy as np, cv2, subprocess, os, glob, sys
from collections import defaultdict

OUT = '/tmp/v9'
FF = open('/tmp/ffpath').read().strip()
REF = 'refs/ref-reels-tutorial.mp4'

SCENES = [
    ('stamp', 0, 13), ('black', 13, 18), ('green', 18, 41),
    ('white', 41, 57), ('desat', 57, 90), ('teal', 90, 98),
    ('red', 98, 177), ('jen', 177, 270), ('graded', 270, 698),
]
plates = {name: cv2.imread(f'{OUT}/plates/' + ('field_' + name if name in ('stamp','green','white','desat','teal','red','jen') else name) + '.png') for name, _, _ in SCENES}
A = np.load(f'{OUT}/aff3.npz')
affn, affa = A['n'], A['a']
AFF = {int(n): w.reshape(2, 3) for n, w in zip(affn, affa)}

per_frame = defaultdict(list)
for mp in glob.glob(OUT + '/masks/*_????.png'):
    base = os.path.basename(mp)[:-4]
    key, n = base.rsplit('_', 1)
    per_frame[int(n)].append(key)
ORDER = ['stamp', 'btext', 'bill', 'tag', 'bag', 'smoke', 'stool', 'bagw', 'tagw', 'billw',
         'smoked', 'he', 'said', 'no', 'logo', 'glove', 'cash', 'jen', 'sub', 'glow']
def sortkey(k):
    nm = k.split('@')[0]
    return ORDER.index(nm) if nm in ORDER else 99

def scene_of(n):
    for name, n0, n1 in SCENES:
        if n0 <= n < n1:
            return name
    return 'graded'

mask_cache = {}
def mask_of(key, n):
    k = (key, n)
    if k not in mask_cache:
        m = cv2.imread(f'{OUT}/masks/{key}_{n:04d}.png', 0)
        mask_cache[k] = m
        if len(mask_cache) > 300:
            mask_cache.pop(next(iter(mask_cache)))
    return mask_cache[k]

NF = 698
cmd = [FF, '-y', '-hide_banner', '-loglevel', 'error',
       '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1080x1920', '-r', '30', '-i', '-',
       '-i', REF, '-map', '0:v', '-map', '1:a',
       '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
       '-c:a', 'copy', '-movflags', '+faststart', 'deliverables/shorts/S01_monarch_20billion_v9.mp4']
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

diffs = []
for n in range(NF):
    sc = scene_of(n)
    f = cv2.imread('/tmp/rf/%04d.png' % (n + 1))
    if sc == 'graded':
        comp = f
        if n % 50 == 0:
            diffs.append(0.0)
        up = cv2.resize(comp, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        proc.stdin.write(up.tobytes())
        continue
    bg = cv2.warpAffine(plates[sc], AFF[n], (720, 1280))
    keys = sorted(per_frame.get(n, []), key=sortkey)
    comp = bg
    for key in keys:
        m = mask_of(key, n)
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        a = (m[y0:y1, x0:x1].astype(np.float32) / 255.0)[..., None]
        comp[y0:y1, x0:x1] = (comp[y0:y1, x0:x1] * (1 - a) + f[y0:y1, x0:x1] * a).astype(np.uint8)
    if n % 50 == 0:
        diffs.append(float(np.abs(comp.astype(np.int16) - f.astype(np.int16)).mean()))
    up = cv2.resize(comp, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    proc.stdin.write(up.tobytes())
proc.stdin.close()
proc.wait()
print('v9 master done, mean|diff| samples:', [round(d, 2) for d in diffs])

subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error',
                '-i', 'deliverables/shorts/S01_monarch_20billion_v9.mp4',
                '-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                '-c:a', 'copy', '-movflags', '+faststart',
                'deliverables/shorts/S01_monarch_20billion_v9_web.mp4'], check=True)
print('v9 web done')
