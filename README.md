# Adil Chandio — Monarch Portfolio Intro

See [`docs/storyboard-next-level.md`](docs/storyboard-next-level.md) for the proposed frame-accurate structure for the next pass. That shot map is an approval checkpoint; it is not rendered into a new video yet.

A 9:16 portfolio intro adapted to the supplied reference's timed sequence: type-on greeting, paper-white identity reveal, quick role cards, blue orbital manifesto, moving skills list, portfolio/stat panels, a floating 3-D identity card, and the final grid signature. Original audio is stream-copied from the supplied clip; all visuals are rebuilt for Adil and the reference creator's watermark is not reused.

The opening identity reveal uses the supplied AI-generated silhouette with the checkerboard removed to real transparency; the person remains a pure-black cutout with no face or clothing detail visible. `tools/make_silhouette.py INPUT.png OUTPUT.png` extracts a clean antialiased alpha cutout from a black silhouette on a light checkerboard. The project also uses bundled Manrope and IBM Plex Mono fonts (OFL licenses in `assets/fonts/`). Public profile figures shown in the portfolio panels (6M+ views and 4+ channels) come from Adil Chandio's GitHub profile.

## Render

```bash
python -m pip install -r requirements.txt
python src/render_intro.py path/to/reference.mp4 deliverables/adil-chandio-monarch-intro.mp4
```

The source video is not included. Put it in `reference_media/` (ignored by Git), or pass another source path. Output is 720×1280, 30 fps, AAC audio.
