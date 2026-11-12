#!/usr/bin/env bash
# 把 frames.ffconcat 和 soundtrack.wav 编码成片，再在片头接上 3.5 秒观看提示。
# 在任何目录运行都行；需要 <项目>/frames.ffconcat（render.js full 生成）和 <项目>/soundtrack.wav。
set -euo pipefail
cd "$(dirname "$0")/.."
TITLE="${TITLE:-$(cat src/TITLE)}"
RAW="${TITLE}_无提示.mp4"; OUT="${TITLE}.mp4"
DUR=$(python3 -c "import json;print(json.load(open('src/film_data.json'))['duration'])")
# soundtrack.py 已经按对白定好了电平，这里只加安全限幅，不做响度归一化。
ffmpeg -hide_banner -loglevel warning -y \
  -f concat -safe 0 -i frames.ffconcat -i soundtrack.wav \
  -vf "fps=30,scale=1080:1920:flags=lanczos,format=yuv420p" -t "$DUR" \
  -af "alimiter=limit=0.79:attack=2:release=60:level=false" \
  -c:v libx264 -preset medium -crf 18 -tune stillimage \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$RAW"
python3 src/warning_card.py
ffmpeg -hide_banner -loglevel warning -y \
  -loop 1 -framerate 30 -t 3.5 -i assets/warning_card.png \
  -f lavfi -t 3.5 -i anullsrc=r=48000:cl=stereo -i "$RAW" \
  -filter_complex "[0:v]format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st=3.1:d=0.4,setsar=1[c];[2:v]setsar=1[m];[c][1:a][m][2:a]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 18 -tune stillimage \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
  -show_entries format=duration,size -of json "$OUT" > final_probe.json
echo "Encoded $OUT (+3.5 s advisory) and $RAW"
