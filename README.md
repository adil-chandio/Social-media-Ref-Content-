# Adil Chandio — Monarch Portfolio Intro

A 9:16 portfolio intro adapted to the supplied reference's timed sequence: type-on greeting, paper-white identity reveal, quick role cards, blue orbital manifesto, moving skills list, portfolio/stat panels, a floating 3-D identity card, and the final grid signature. Original audio is stream-copied from the supplied clip; all visuals are rebuilt for Adil and the reference creator's watermark is not reused.

The opening identity reveal uses a photo-derived, background-free pure-black silhouette; no face or clothing detail is visible in the video. `tools/make_silhouette.py` regenerates the antialiased cutout. The project also uses bundled Manrope and IBM Plex Mono fonts (OFL licenses in `assets/fonts/`). Public profile figures shown in the portfolio panels (6M+ views and 4+ channels) come from Adil Chandio's GitHub profile.

## Render

```bash
python -m pip install -r requirements.txt
python src/render_intro.py path/to/reference.mp4 deliverables/adil-chandio-monarch-intro.mp4
```

The source video is not included. Put it in `reference_media/` (ignored by Git), or pass another source path. Output is 720×1280, 30 fps, AAC audio.
