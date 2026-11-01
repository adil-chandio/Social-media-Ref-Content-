#!/usr/bin/env bash
# Mix S01 v13 audio: procedural bed + Urdunglish VO (voice-02) at approved anchors.
# Usage: bash tools/mix_vo_s01.sh <bed.wav> <out.wav>
set -e
FF=$(cat /tmp/ffpath)
BED=$1; OUT=$2
VO=audio/vo_s01
$FF -y -v error \
 -i "$BED" \
 -i $VO/m1.mp3  -i $VO/m2.mp3  -i $VO/m3.mp3  -i $VO/m4.mp3  -i $VO/m5.mp3 \
 -i $VO/m6.mp3  -i $VO/m7.mp3  -i $VO/m8.mp3  -i $VO/m9.mp3  -i $VO/m10.mp3 \
 -filter_complex "\
[0:a]volume=0.80[bed];\
[1:a]adelay=200|200,volume=1.9[v1];\
[2:a]adelay=2000|2000,volume=1.9[v2];\
[3:a]adelay=4800|4800,volume=1.9[v3];\
[4:a]adelay=6100|6100,volume=1.9[v4];\
[5:a]adelay=7600|7600,volume=1.9[v5];\
[6:a]adelay=9100|9100,volume=1.9[v6];\
[7:a]adelay=11800|11800,volume=1.9[v7];\
[8:a]adelay=14900|14900,volume=1.9[v8];\
[9:a]adelay=18200|18200,volume=1.9[v9];\
[10:a]adelay=21300|21300,volume=1.9[v10];\
[bed][v1][v2][v3][v4][v5][v6][v7][v8][v9][v10]amix=inputs=11:duration=first:normalize=0,alimiter=limit=0.90:attack=2,volume=0.94[out]" \
 -map "[out]" -ar 44100 -ac 2 "$OUT"
echo "mix ok: $OUT"
