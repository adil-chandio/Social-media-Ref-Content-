# Adil Chandio — Portfolio Intro

This repository contains two video treatments based on the supplied vertical reference. The reference-based edit retains the reference's scene flow, underlying footage, and soundtrack, while adding Adil's roles, eight skills, and approved proof points (6M+ views and 4+ channels). Instagram marks and the social handles beside them are removed; Adil's main title cards remain. The skill carousel is eased between the analyzed audio impacts (15.126–21.262 s), so each discipline locks into focus in sync with its sound-effect hit. It is a close reference-based edit, not a claim of pixel-perfect recreation; review the rendered file before publication.

The reference-based render is `deliverables/adil-chandio-reference-match.mp4`. Its audio is stream-copied from the source. Run:

```bash
python -m pip install -r requirements.txt
python src/render_reference_match.py path/to/reference.mp4 deliverables/adil-chandio-reference-match.mp4
```

The earlier redesigned treatment can still be rendered with `src/render_intro.py` to `deliverables/adil-chandio-monarch-intro.mp4`. See [`docs/storyboard-next-level.md`](docs/storyboard-next-level.md) and [`docs/next-level-video-prompt.md`](docs/next-level-video-prompt.md) for its storyboard and creative prompt.

The opening identity reveal uses the supplied black silhouette with transparent background. `tools/make_silhouette.py INPUT.png OUTPUT.png` extracts a clean antialiased alpha cutout from a black silhouette on a light checkerboard. In the reference-matched edit, the character beat (≈3.8–5.8 s) now shows Adil's own studio portrait as a clean alpha cutout (`assets/adil-photo-cutout.png`, matted from the supplied photo) in place of the placeholder silhouette, with the same placement, fade timing and a soft editorial drop shadow. Bundled Manrope and IBM Plex Mono fonts are in `assets/fonts/` (OFL licenses included). The source video is not committed; place it under `reference_media/` or pass its path directly. Output is 720×1280 at 30 fps.

## Construction-site reference match (18 s)

`src/render_newref_match.py` recreates the supplied 18-second construction-site reference
(`VID_20261027_190047_159.mp4`, kept privately under `google_drive/` per .gitignore) shot-for-shot:
all 22 cuts, camera moves and the original soundtrack are retained byte-for-byte (audio stream copied).
The on-screen model is replaced in every shot by Adil's supplied portrait cutout as a tracked,
grade- and grain-matched composite layer (per-shot ECC camera tracking with chained/first-frame
fallback), while the reference creator's Instagram glyph, handle and credit lines are inpainted out
(temporal-median top-hat text detection plus per-shot boxes). The closing card replaces the source
handle with an ADIL CHANDIO wordmark pulsed on the measured outro hits (14.466 / 14.721 / 15.0 s).

Honest limitation: this is a stylized cutout-composite recreation (collage grade with keyline and
contact shadow), not an invisible body-level replacement — AI image/video generation endpoints were
unavailable (403), so no pose-matched reshoots of the subject could be synthesized. Rendered output
is intentionally left out of Git by `.gitignore` (`deliverables/*.mp4`).
