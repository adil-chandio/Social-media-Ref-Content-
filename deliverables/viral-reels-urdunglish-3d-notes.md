# 3D Urdunglish reel — production notes

## What this version is

`viral-reels-urdunglish-3d.mp4` is a new, procedurally rendered 3D motion-graphics piece—not a recolor, crop, patch, or overlay on the flattened reference video. The reference was used only to guide the narrative order and approximate beat timing. Its visual frames are newly generated from Three.js 3D geometry and vector graphic treatments; no reference video frames are reused.

### Recreated story beats

1. **TWENTY BILLION** — extruded 3D typography and a modeled money bag/stool.
2. **HE SAID NO** — a dimensional title impact.
3. **2008 / NVIDIA** — a holographic year marker and new GPU model.
4. **Founder moment** — an original, stylized 3D bust with glasses and a dark jacket.
5. **AI / gaming** — a rotating GPU/chip scene with a circuit constellation.
6. **Subscribe** — a new 3D end card and CTA.

## Audio

- Easy Urdu-English narration uses the masculine Pakistani voice selected earlier.
- The original music bed is retained at a reduced level and continues through the ending.
- The voice fades before the final CTA hold; the music does not stop when narration ends.

Voice-over script:

> ایک bold idea نے future کا رخ بدل دیا۔ دو ہزار آٹھ میں، جب جواب تھا no، NVIDIA نے اپنے vision پر یقین رکھا۔ آج AI ہو یا gaming، ہر screen پر اُس سوچ کا اثر نظر آتا ہے۔ Innovation کا مطلب ہے آگے دیکھنا، اور اپنے vision پر قائم رہنا۔

## Technical and creative limits

- Target format: vertical 9:16, 720 × 1280, 30 fps, 698 frames, H.264 + AAC stereo.
- The founder figure is deliberately stylized and generic, not a photorealistic Jensen Huang likeness. Building a faithful human character would require a separate sourced/rigged 3D character asset.
- The source was flattened MP4, so this is a shot-by-shot reinterpretation of its story beats—not a recovery of the original editable 3D project or exact original keyframes.

## Editable source

The scene generator is in `tools/three-d-reel/` and uses Three.js geometry, camera animation, and the headless SVG renderer. `awesome-blender` is a resource list rather than Blender itself; ArtCraft is relevant for AI scene/video exploration but relies on a separate model setup; `img2threejs` is more suited to individual objects than a complete timed reel. The reproducible Three.js approach was chosen here to keep the new 3D shots deterministic and frame-accurate.
