# adil-chandio/portfolio

Personal portfolio website of **Adil Chandio** — AI learner • content creator • developer.

- Opens with a 28-second portfolio film (sound on, one-tap enter, skippable, once per session, replayable from the nav).
- Single-page site: hero, about, skills, featured work, contact — original design, no templates.
- Plain HTML/CSS/JS, no build step. Fonts: Manrope + IBM Plex Mono (OFL, see `assets/fonts/`).

## Run locally

```bash
python3 -m http.server 4173
# open http://localhost:4173
```

## Structure

```
index.html            single-page site + intro curtains
assets/styles.css     design system (ink / paper / red)
assets/main.js        intro flow, reveals, contact form
assets/portrait-masked.png   masked portrait cutout (RGBA)
assets/work-*.jpg     poster frames for work cards
media/intro.mp4       28s portfolio film (audio baked in)
```

© 2026 Adil Chandio — built from scratch.
