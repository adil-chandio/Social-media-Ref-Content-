# S01 Source Forensics — Vane Motion `Ld5LkPkQodQ` (decoded from vision CDN stills, 2026-11-01)

Video bytes remain bot-walled on every automated route (yt-dlp nightly + 2026 client
rotation `tv/web_embedded/android_vr/tv_downgraded`, `ejs:github` remote components,
videodl, invidious/piped/cobalt frontends, storyboard sprites = 403). Grammar below is
decoded from the REAL frames we could pull: `maxresdefault/0/hqdefault/hq1-3/sd1-3`.

## Layer stack (scene type A — "paper strip")
1. **L0** charcoal field (~#1a1818) with soft center lift.
2. **L1** GIANT condensed display type (Anton-class) in crimson, bleeding off both
   canvas edges, centered so the strip cuts the word; slow sinusoidal drift (parallax
   vs strip push-in). Second darker echo word lower.
3. **L2** grey smoke wisps (blurred blob clusters) drifting L→R, drawn OVER strip
   edges but UNDER type/cutouts.
4. **L3** center vertical PAPER strip, ~43-45% width, full height, soft side shadows,
   paper grain.
5. **L4** red condensed type stack on strip: small kicker (70-80px) + giant word
   (200-250px), stamp-in on VO beats.
6. **L5** grayscale photo cutout (soft drop shadow) filling ~75% of strip width,
   bounce-settle entry; red marker underline/slash draws after.
7. **L6** global: per-beat push-in 4-7%, screen-shake on SFX hits, white flash at cut,
   grain, mild vignette.

## Layer stack (scene type B — "maroon band")
1. Full-bleed = SAME photo enlarged ~2.5x, brightness ~0.4, slight blur, maroon wash.
2. Center band (~43% width) = sharp maroon panel.
3. White/gold giant year or word at band top, BEHIND subject head.
4. Color photo cutout (waist-up) filling band width, head overlapping the year type.
5. Small caption plate (source: yellow "subscribe & like" → ours: gold MONARCH plate,
   mono ink text) stamped at chest.
6. Mono figure line (e.g. `$20,000,000,000`) in gold at band bottom.

## Palette (source → MONARCH shift)
- source pure red #e00000 → MONARCH crimson (196,18,46); dark echo (120,10,24)
- paper (242,240,235); charcoal (26,24,24); maroon field (72,12,18)
- source yellow plate → MONARCH gold (212,175,55)

## Type
- Display: Anton (google/fonts via api.github.com blob) — matches source ultra-condensed.
- Mono: IBM Plex Mono; body: Manrope 700.

## Reuse for S02–S10
Engine: `scripts/motion_s01_v3.py` (layer helpers: giant/strip/smoke_layer/cutw/stamp/
plate/maroon_field/char_field + shake/flash/grain/vignette). Per short: swap palette pop
color, words, cutouts, beat timings from VO length.
