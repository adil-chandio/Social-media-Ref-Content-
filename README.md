# Adil Chandio — Portfolio Intro

This repository contains two video treatments based on the supplied vertical reference. The reference-based edit retains the reference's scene flow, underlying footage, and soundtrack, while adding Adil's roles, eight skills, and approved proof points (6M+ views and 4+ channels). Instagram marks and the social handles beside them are removed; Adil's main title cards remain. It is a close reference-based edit, not a claim of pixel-perfect recreation; review the rendered file before publication.

The reference-based render is `deliverables/adil-chandio-reference-match.mp4`. Its audio is stream-copied from the source. Run:

```bash
python -m pip install -r requirements.txt
python src/render_reference_match.py path/to/reference.mp4 deliverables/adil-chandio-reference-match.mp4
```

The earlier redesigned treatment can still be rendered with `src/render_intro.py` to `deliverables/adil-chandio-monarch-intro.mp4`. See [`docs/storyboard-next-level.md`](docs/storyboard-next-level.md) and [`docs/next-level-video-prompt.md`](docs/next-level-video-prompt.md) for its storyboard and creative prompt.

The opening identity reveal uses the supplied black silhouette with transparent background. `tools/make_silhouette.py INPUT.png OUTPUT.png` extracts a clean antialiased alpha cutout from a black silhouette on a light checkerboard. Bundled Manrope and IBM Plex Mono fonts are in `assets/fonts/` (OFL licenses included). The source video is not committed; place it under `reference_media/` or pass its path directly. Output is 720×1280 at 30 fps.
