# Procedural 3D reel source

This renderer rebuilds the reference's story beats as a fresh, stylized 3D motion-graphics sequence. It does **not** place text or patches over the source frames. The source MP4 is used only for story/timing reference and, when requested, as a quiet music bed.

The six shots are: **TWENTY BILLION** with a modeled money bag; **HE SAID NO**; **2008 / NVIDIA**; an original stylized founder bust; a rotating GPU with AI and gaming labels; and a 3D subscribe end card. The founder is an intentionally stylized generic model, not a photorealistic likeness.

## Renderer

- Three.js procedural geometry, TextGeometry, lights, camera movement, and animated groups.
- Three.js `SVGRenderer` plus `@resvg/resvg-js` for deterministic, headless frame rendering.
- Output target: 720 × 1280, 30 fps, 698 frames.

## Run

Requires Node.js 22+ and FFmpeg. In this folder:

```sh
npm install
npm run preview
```

The preview command writes selected frames to `preview3d/`. For a complete render directly to MP4, provide the source music-bed MP4, a narration WAV, and the FFmpeg executable:

```sh
FFMPEG_PATH=/path/to/ffmpeg node render.mjs --stream \
  /path/to/reference-music-bed.mp4 \
  /path/to/urdunglish-voiceover.wav \
  /path/to/viral-reels-urdunglish-3d.mp4
```

A parallel frame mode is available for faster renders:

```sh
mkdir -p /tmp/reel-frames
node render.mjs --frames 0 2 /tmp/reel-frames &
node render.mjs --frames 1 2 /tmp/reel-frames &
wait
```

Frame rendering creates PNG files named `frame_0000.png` through `frame_0697.png`; FFmpeg can encode that image sequence and mix audio separately. The audio-mix graph in `render.mjs` keeps the bed through the final CTA and fades the narration cleanly.
