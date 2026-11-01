# Reference-video restyle — production notes

## What changed

`viral-reels-urdunglish-restyled.mp4` uses the reference video as its locked visual base. It preserves the same footage, shot order, cuts, framing, camera/object motion, and timing. No new scenes, 3D shots, hard panels, or unrelated graphics were added.

The grade shifts the green/lime imagery toward teal, reduces the red-heavy environments toward graphite, and adds a restrained cool-shadow/warm-highlight finish. The existing red “HE SAID” and “NO” title pixels are recolored cyan and amber in place. Existing CTA artwork remains in its original position and animation.

## Flattened typography limitation

The supplied MP4 is flattened: its lettering, shadows, perspective, animation, and occlusion are already pixels in the video. I retained the original glyph silhouettes and motion, changing their color treatment where it could be done cleanly. I did **not** claim a font-family replacement. Rebuilding the background beneath the baked text—especially where titles cross clouds or a moving presenter—would risk changing the scene or creating duplicate/ghosted letters. A clean font swap requires the editable source project or separate title/background layers.

## Audio

- Urdu-English voice-over uses the previously selected masculine Pakistani voice (`voice-00`).
- The reference's original audio/music bed remains underneath, gently reduced and ducked while the narration is speaking; it continues through the end.
- The narration runs about 19.2 seconds, leaving the original bed on the final hold.

Voice-over script:

> ایک bold idea نے future کا رخ بدل دیا۔ دو ہزار آٹھ میں، جب جواب تھا no، NVIDIA نے اپنے vision پر یقین رکھا۔ آج AI ہو یا gaming، ہر screen پر اُس سوچ کا اثر نظر آتا ہے۔ Innovation کا مطلب ہے آگے دیکھنا، اور اپنے vision پر قائم رہنا۔

## Output profile and integrity

- MP4, H.264 video + AAC stereo audio
- 720 × 1280, vertical 9:16, nominal 30 fps
- 698 decoded video frames; output duration about 23.35 seconds
- `viral-reels-exact-copy.mp4` remains unchanged; its SHA-256 is recorded in `forensic-analysis.md`.
