#!/usr/bin/env python3
"""S01 v13 — procedural SFX/music bed (23.35s, 44.1kHz stereo).
Rebuilt on the reference's event map (same hits/whooshes/timing) because the
reference bed is a near-mono mix: its English VO cannot be extracted in this
sandbox (no ML separation models reachable), so the bed is recreated from
scratch instead of carrying the English voiceover. Our Urdunglish VO (voice-02)
is mixed on top at the approved anchors.
Usage: bed_s01.py <out.wav>
"""
import numpy as np, sys, wave

SR = 44100
DUR = 23.35
N = int(SR * DUR)
rng = np.random.default_rng(7)
buf = np.zeros(N, np.float64)

def t0(sec):
    return int(sec * SR)

def add(sec, sig, gain=1.0):
    i = t0(sec)
    n = min(len(sig), N - i)
    if n > 0:
        buf[i:i + n] += sig[:n] * gain

def env(n, a=0.005, d=0.2, curve=3.0):
    e = np.ones(n)
    na, nd = int(a * SR), int(d * SR)
    if na > 0:
        e[:na] = np.linspace(0, 1, na) ** 2
    if nd < n:
        e[nd:] = np.exp(-curve * np.arange(n - nd) / SR)
    return e

def noise(n):
    return rng.normal(0, 1, n)

def bp(sig, lo, hi, q=1.2):
    S = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / SR)
    m = np.exp(-0.5 * ((np.log(np.maximum(f, 1)) - np.log(np.sqrt(lo * hi))) / (np.log(hi / lo) * 0.5 * q)) ** 2)
    return np.fft.irfft(S * m, len(sig))

def whoosh(dur, f0, f1, gain=1.0, sec=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sig = np.sin(ph) * 0.3 + noise(n) * 0.7
    sig = bp(sig, min(f0, f1) * 0.5, max(f0, f1) * 1.5)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    add(sec, sig * e, gain)

def boom(sec, f=48, dur=0.7, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * t * (1 - 0.25 * t / dur)) * env(n, 0.002, 0.05, 5)
    sig += noise(n) * env(n, 0.001, 0.03, 8) * 0.4
    add(sec, sig, gain)

def knock(sec, gain=0.5):
    n = int(0.12 * SR)
    sig = bp(noise(n), 300, 900) * env(n, 0.001, 0.02, 9)
    add(sec, sig, gain)

def tick(sec, gain=0.35, f=2400):
    n = int(0.05 * SR)
    sig = bp(noise(n), f * 0.7, f * 1.4) * env(n, 0.001, 0.008, 12)
    add(sec, sig, gain)

def blip(sec, f=880, gain=0.3):
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    add(sec, np.sin(2 * np.pi * f * t) * env(n, 0.004, 0.04, 6), gain)

def pass_events(o):
    """one 11.675s pass of the event map"""
    whoosh(0.35, 300, 2400, 0.30, o + 0.10)          # stamp in
    whoosh(0.30, 2200, 240, 0.34, o + 0.43)          # black extrude (reverse)
    whoosh(0.45, 200, 3200, 0.40, o + 0.55)          # lime + bag rise
    boom(o + 0.60, 52, 0.8, 0.55)
    knock(o + 1.35, 0.55)                            # stool land
    boom(o + 1.55, 44, 0.9, 0.65)                    # bag land
    n = int(0.8 * SR)                                # smoke hiss
    add(o + 1.60, bp(noise(n), 3000, 9000) * env(n, 0.05, 0.3, 4), 0.22)
    for i, s in enumerate((2.05, 2.20, 2.45)):        # HE / SAID / NO
        boom(o + s, 60 + i * 8, 0.5, 0.5)
        tick(o + s, 0.3, 1800 + i * 300)
    whoosh(0.5, 300, 6000, 0.5, o + 2.55)            # riser into flash
    boom(o + 3.00, 40, 1.1, 0.8)                     # red flash impact
    n = int(0.3 * SR)
    add(o + 3.00, bp(noise(n), 2000, 10000) * env(n, 0.001, 0.05, 7), 0.4)
    whoosh(0.5, 500, 2600, 0.3, o + 3.25)            # cash fly
    tick(o + 3.45, 0.3, 3200); tick(o + 3.7, 0.25, 3600)
    blip(o + 3.55, 740, 0.25)                        # logo pop
    whoosh(0.35, 400, 1800, 0.22, o + 3.30)          # glove slide
    for i in range(4):                               # 2008 type-in
        tick(o + 4.75 + i * 0.2, 0.4, 2600)
    whoosh(0.7, 180, 2400, 0.42, o + 5.85)           # jen rise
    boom(o + 6.0, 50, 0.9, 0.5)
    blip(o + 7.5, 620, 0.3); tick(o + 7.5, 0.35, 3000)   # plate stamp
    n = int(0.6 * SR)
    add(o + 7.5, bp(noise(n), 4000, 12000) * env(n, 0.01, 0.2, 4), 0.18)
    whoosh(0.8, 2400, 200, 0.45, o + 8.95)           # grade down-sweep
    boom(o + 9.0, 46, 1.2, 0.6)
    n = int(1.4 * SR)                                # glow shimmer
    add(o + 9.0, bp(noise(n), 6000, 14000) * env(n, 0.2, 0.6, 2.5), 0.10)

# ---- music layer: dark pulse @ 100bpm ----
bpm = 100.0
spb = 60 / bpm
t = np.arange(N) / SR
pad = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 0.7) +
       0.35 * np.sin(2 * np.pi * 110 * t + 1.9))
pad *= 0.5 + 0.12 * np.sin(2 * np.pi * 0.25 * t)
buf += pad * 0.055
k = 0.0
while k < DUR:
    if k > 2.9:                                     # kicks from red scene
        n = int(0.35 * SR)
        tt = np.arange(n) / SR
        buf[t0(k):t0(k) + n] += np.sin(2 * np.pi * 50 * tt * (1 - 0.3 * tt / 0.35)) * env(n, 0.002, 0.04, 6) * 0.16
    if k > 3.2:                                     # hats
        n = int(0.06 * SR)
        buf[t0(k + spb / 2):t0(k + spb / 2) + n] += bp(noise(n), 6000, 14000) * env(n, 0.001, 0.01, 10) * 0.05
    k += spb
pass_events(0.0)
pass_events(11.675)

# master: soft clip + normalize
buf = np.tanh(buf * 1.15) * 0.85
buf /= max(1e-9, np.abs(buf).max()) * 1.12
st = np.stack([buf, buf], 1)
pcm = (st * 32767 * 0.9).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bed_s01.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('bed written', DUR, 's')
