#!/usr/bin/env bash
# ytget.sh <url> <out.mp4> — multi-strategy YouTube fetcher for GH runners.
# 1) Invidious public APIs (progressive 720p)  2) Piped APIs (adaptive+merge)  3) yt-dlp variants
set -u
url="$1"; out="$2"
ID=$(echo "$url" | grep -oE "[A-Za-z0-9_-]{11}" | tail -1)
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
size() { stat -c%s "$1" 2>/dev/null || echo 0; }
good() { [ "$(size "$1")" -gt 200000 ]; }

echo "::strategy invidious for $ID"
echo "ID=$ID"
for api in yewtu.be invidious.nerdvpn.de inv.nadeko.net invidious.f5.si iv.melmac.space invidious.privacyredirect.com yt.artemislena.eu invidious.dhusch.com; do
  u=$(curl -s -m 12 -A "$UA" "https://$api/api/v1/videos/$ID" | jq -r '[.formatStreams[]? | select(.quality=="hd720" or .qualityLabel=="720p" or .quality=="medium")][0].url // empty' 2>/dev/null)
  if [ -n "$u" ]; then
    curl -s -L -m 300 -A "$UA" -o "$out" "$u" && good "$out" && { echo "OK invidious $api"; exit 0; }
  fi
done

echo "::strategy piped for $ID"
for api in pipedapi.kavin.rocks pipedapi.adminforge.de api.piped.private.coffee pipedapi.reallyaweso.me pipedapi.ducks.party pipedapi.leptons.xyz; do
  j=$(curl -s -m 12 -A "$UA" "https://$api/streams/$ID" 2>/dev/null)
  v=$(echo "$j" | jq -r '[.videoStreams[]? | select(.height<=720)][0].url // empty' 2>/dev/null)
  a=$(echo "$j" | jq -r '(.audioStreams // [])[0].url // empty' 2>/dev/null)
  if [ -n "$v" ] && [ -n "$a" ]; then
    curl -s -L -m 300 -o /tmp/_v.mp4 "$v" & curl -s -L -m 180 -o /tmp/_a.m4a "$a" & wait
    if good /tmp/_v.mp4 && good /tmp/_a.m4a; then
      ffmpeg -y -loglevel error -i /tmp/_v.mp4 -i /tmp/_a.m4a -c:v copy -c:a aac "$out" && good "$out" && { echo "OK piped $api"; exit 0; }
    fi
  fi
done

echo "::strategy yt-dlp for $ID"
F="bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/bv*[height<=720]+ba/b[height<=720]/b"
python3 -m yt_dlp --no-warnings --restrict-filenames -f "$F" --merge-output-format mp4 -o "$out" "$url" && good "$out" && { echo "OK ytdlp default"; exit 0; }
python3 -m yt_dlp --no-warnings --restrict-filenames --extractor-args "youtube:player_client=android,vr,tv,web_embedded,ios" -f "bv*[height<=720]+ba/b[height<=720]/b" --merge-output-format mp4 -o "$out" "$url" && good "$out" && { echo "OK ytdlp clients"; exit 0; }

echo "FAILED all strategies for $ID"
exit 1
