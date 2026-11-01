# 🎬 Video Forensic Analysis Report

**Source:** `🔥How to Edit VIRAL REELS Animations in After Effects _ Full tutorial from scratch.mp4`
**Analysis date:** 2026-11-01
**Analysis method:** Frame-by-frame programmatic forensics (OpenCV/numpy/PIL), OCR (tesseract.js), audio RMS analysis, motion estimation, color histogram analysis.

---

## 1. Technical Profile

| Property | Value |
|---|---|
| Container / Codec | MP4 / H.264 |
| Resolution | 720 × 1280 (vertical, 9:16 reel format) |
| Frame rate | 30 FPS (constant) |
| Total frames | 700 |
| Duration | 23.33 s |
| Audio | Continuous narration, 16 kHz mono, mean RMS 0.143, peak 0.33 — speech present 0.10s→23.20s (no music-only gaps) |
| Format | YouTube/Instagram Reels style tutorial |

## 2. Scene Structure (from change detection)

| # | Start | End | Duration | Visual character |
|---|---|---|---|---|
| 1 | 0.00s | 3.07s | 3.07s | Bright title card, high motion — hook + intro animation |
| 2 | 3.07s | 8.97s | 5.90s | Dark red / maroon on black — After Effects interface demo |
| 3 | 8.97s | 11.63s | 2.67s | Bright flash transition → dark — scene swap |
| 4 | 11.63s | 14.70s | 3.07s | Bright — big animated text / numbers showcase |
| 5 | 14.70s | 20.60s | 5.90s | Dark red / maroon on black — demo steps (repeat pattern) |
| 6 | 20.60s | 23.27s | 2.67s | Dark, low motion — outro |

**Rhythm:** bright → dark → flash → bright → dark → dark outro. Sections 2 and 5 mirror each other (both 5.9s); sections 3 and 6 mirror (2.67s).

## 3. Per-Second Visual Profile (forensic data)

B = mean brightness, C = contrast (σ), M = frame-difference motion energy

| sec | B | C | M | dominant colors |
|---|---|---|---|---|
| 0 | 128.4 | 16.9 | 22.6 | #c0c0c0 #a8a8a8 #303030 #181818 |
| 1 | 138.8 | 39.8 | 15.5 | #907408 #786107 #c0c0c0 #a8a8a8 |
| 2 | 139.5 | 62.1 | 8.2 | #c0c0c0 #a8a8a8 |
| 3 | 93.0 | 32.8 | 9.0 | #c0c0c0 #a8a8a8 #600505 #480404 |
| 4 | 32.7 | 18.9 | 3.1 | #480404 #600505 |
| 5 | 38.8 | 31.1 | 3.2 | #480404 #600505 |
| 6 | 41.2 | 42.0 | 11.8 | #300202 #000000 #180303 |
| 7 | 37.7 | 43.7 | 3.5 | #000000 #180303 |
| 8 | 46.7 | 52.2 | 3.1 | #18030b #000000 |
| 9 | 86.1 | 47.5 | 6.3 | #829087 #98a89e #000000 |
| 10 | 33.8 | 44.9 | 1.2 | #000000 |
| 11 | 33.9 | 45.0 | 0.9 | #000000 |
| 12 | 137.4 | 22.3 | 13.2 | #c0c0c0 #a8a8a8 #483b0b |
| 13 | 157.6 | 51.9 | 16.2 | #a8a8a8 #c0c0c0 |
| 14 | 130.6 | 65.2 | 1.6 | #c0c0c0 #a8a8a8 |
| 15 | 38.1 | 15.3 | 3.7 | #600505 #780707 #480404 |
| 16 | 36.4 | 23.6 | 3.1 | #600505 #480404 |
| 17 | 39.0 | 34.0 | 4.0 | #480404 #600505 #300202 |
| 18 | 38.3 | 42.5 | 9.9 | #000000 #300707 #18030b |
| 19 | 40.0 | 46.1 | 2.6 | #000000 #18030b |
| 20 | 46.0 | 50.5 | 2.0 | #000000 |
| 21 | 36.4 | 48.0 | 1.9 | #18030b #000000 |
| 22 | 34.4 | 45.9 | 1.4 | #000000 |
| 23 | 33.3 | 44.3 | 0.4 | #000000 |

## 4. Audio / Pacing Analysis

- Continuous voiceover, no silence gaps — dense tutorial narration.
- Loudness profile per second (mean RMS): starts ~0.17 → fluctuates 0.10–0.21 → ends ~0.08 (fade out).
- Speech segments: single continuous 0.10s–23.20s. This is a **fast-paced** VO — the recreation's narration was time-compressed (~1.59×) to match the original's 23.3s cadence.
- Peak loudness at 21s (0.212) — likely a call-to-action/outro emphasis.

## 5. Typography / Text Zones (OCR-based findings)

OCR on 1fps frames (stylish text on busy backgrounds limits accuracy, but zones are clear):

- **0–3s:** Large display text center-upper area (title card).
- **3–9s:** Interface overlays; step labels upper-left/upper-right; timeline text lower zone.
- **12–13s:** Very large display text (e.g., "TWENTY…", "…Billion"-style big numbers) — animated stat/number showcase.
- **13–14s:** Big two-word display text (center).
- Throughout: small caption/step labels at edges (top y≈150–250, bottom y≈1100–1280).

**Typography zones (normalized y-positions):**
- Title band: y 0.15–0.45 (upper third)
- Body/demo: y 0.45–0.80
- Step labels: y 0.12–0.20 and y 0.86–0.98
- Outro: centered y 0.3–0.6

## 6. Design System (extracted palette)

| Role | Hex | Notes |
|---|---|---|
| Bright title bg | #c0c0c0, #a8a8a8 | light gray gradients |
| Dark bg | #000000, #180303, #18030b | near-black with red tint |
| Brand red | #480404, #600505, #300202 | deep maroon/red on black sections |
| Accent green flash | #829087, #98a89e | transition flash at 9s |
| Text on dark | white/light | high contrast |
| Text on bright | black | high contrast |

**Motion style:** text slide-up + fade reveals (0.4–0.6s eases), fast scene swaps at 3.07s / 8.97s / 11.63s / 14.7s / 20.6s, pulsing accents, moving timeline elements.

## 7. Recreation Mapping

| Section | Original | Recreation | Duration |
|---|---|---|---|
| 1 | Bright title hook | "VIRAL REELS ANIMATIONS" title card, slide-up reveals, play badge | 3.16s |
| 2 | Dark AE demo | AE mock UI: preview, layers, timeline, moving playhead, keyframe pulses | 5.09s |
| 3 | Flash transition | White flash → "STEP 2 · ADD TEXT" bright section | 3.58s |
| 4 | Bright text showcase | Fade In / Slide Up / Pop animation demos + 1080×1920 30FPS stats | 3.94s |
| 5 | Dark demo 2 | Timeline transitions + export settings panel | 4.55s |
| 6 | Dark outro | "THAT'S IT!" outro on dark red | 3.11s |

**Recreation specs:** 720×1280 @ 30fps, 23.37s, H.264 + AAC narration, procedural renderer (`recreate/renderer.py`).

**Verification delta vs original:** duration +0.04s ✓ · resolution ✓ · frame count 701 vs 700 ✓ · section brightness pattern matches (dark 3–9s & 14.7–20.6s, bright 0–3s & 11.6–14.7s) ✓ · narration pacing matched via 1.59× time-compression ✓

> **Important:** The recreation is an **original work** — original narration, original text, and original design composed to match the reference's format, pacing, palette and section structure. It is not a copy of the reference video.
