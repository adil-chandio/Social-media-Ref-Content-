#!/usr/bin/env bash
# S01 v7 - reference-native NEXT-LEVEL master.
# Base = user's Drive reference (720x1280). Pipeline: light denoise (kill 720p
# compression blocks) -> 1.5x lanczos upscale to 1080x1920 -> mild luma sharpen
# -> high-bitrate x264. Audio stream copied byte-identical from the reference.
set -euo pipefail
FF="$(cat /tmp/ffpath)"
REF="refs/ref-reels-tutorial.mp4"
VF="hqdn3d=2:1.5:6:6,scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int,unsharp=5:5:0.30:5:5:0.0,format=yuv420p"

"$FF" -y -hide_banner -loglevel error -i "$REF" \
  -vf "$VF" -c:v libx264 -crf 14 -preset slow -colorspace bt709 -color_trc bt709 -color_primaries bt709 \
  -c:a copy -movflags +faststart deliverables/shorts/S01_monarch_20billion_v7.mp4

"$FF" -y -hide_banner -loglevel error -i "$REF" \
  -vf "$VF" -c:v libx264 -crf 23 -preset medium -colorspace bt709 -color_trc bt709 -color_primaries bt709 \
  -c:a copy -movflags +faststart deliverables/shorts/S01_monarch_20billion_v7_web.mp4

echo "DONE v7"
