# Reference video — forensic notes

## Exact-copy result

Reference MP4 se `viral-reels-exact-copy.mp4` banaya gaya hai. Exact visual/audio match ko maximize karne ke liye video ko re-render ya transcode nahi kiya—original encoded file ko byte-for-byte copy kiya gaya hai. Is tarah timing, every frame, effects, audio, aur compression bilkul waise hi rehte hain.

## Integrity verification

- Source size: **3,244,599 bytes**
- SHA-256 (source aur output dono): `fdffc719aa2ca39c63a0c2137fbcb0927f38333ed383b6ffebbd1ea6639ebe50`
- File-level comparison: **identical**
- Decoded video: **698 frames**; all 698 frame checksums source/output mein identical
- Decoded audio: **1,004 checksum records** source/output mein identical

## Media profile

- Container: MP4
- Duration: **23.35 s**
- Canvas: **720 × 1280**, vertical **9:16**
- Video: H.264 High, YUV 4:2:0, BT.709, progressive, nominal 30 fps
- Audio: AAC-LC, 44.1 kHz, stereo
- Reported overall bitrate: approx. 1,111 kb/s

## Visual timeline (har second ka sample review)

- **00 s:** halka grey/white background; neon-green “TWENTY” title.
- **01 s:** “BILLION” typography; green money-bag visual aur stool.
- **02 s:** “HE SAID”; grayscale money bag, clouds/smoke aur dark floor.
- **03–06 s:** red NVIDIA-themed graphics; angular background, GPU/card elements aur NVIDIA eye logo; “2008” text aata hai.
- **07–09 s:** Jensen Huang portrait, leather jacket, red background aur “2008”; “subscribe & like” CTA enter hota hai.
- **10–12 s:** portrait par CTA; red-eye glow, grayscale/blur aur glitch-style treatment.
- **13 s:** green-tinted motion-blur transition.
- **14–15 s:** money-bag vignette wapas; bold “HE SAID NO”.
- **16–18 s:** red NVIDIA/GPU section dobara; logo, card elements aur “20/2008” typography.
- **19–23.35 s:** portrait aur “subscribe & like” CTA return; red-eye/glitch look ke saath ending.

Audio stream ko bilkul unchanged rakha gaya hai; is report mein uska transcript ya remix shamil nahi hai.
