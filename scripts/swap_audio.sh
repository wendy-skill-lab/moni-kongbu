#!/usr/bin/env bash
# swap_audio.sh：给已经编码好的成片换一条音轨（不重渲画面），或者截一段出试听片段，让用户对着真实画面挑声音。
#
#   bash swap_audio.sh <成片.mp4> <soundtrack.wav> <输出.mp4>              # 整片换音轨，视频流直接复制
#   bash swap_audio.sh <成片.mp4> <soundtrack.wav> <输出.mp4> <起> <止>    # 截一段 720p 试听片段，秒数按成片计
#
# 成片是带 3.5 秒观看提示的发布版；soundtrack.wav 是 soundtrack.py 写出的原始混音，从正片 0 秒开始，
# 所以会自动延后 ADVISORY 秒（默认 3.5）。限幅参数和 encode.sh 一致，试听片段里听到的就是正片里的声音。
set -euo pipefail
FILM=$1; WAV=$2; OUT=$3; START=${4:-}; END=${5:-}
ADV_MS=$(awk -v a="${ADVISORY:-3.5}" 'BEGIN{printf "%d", a*1000}')
LIM="alimiter=limit=0.79:attack=2:release=60:level=false,adelay=${ADV_MS}|${ADV_MS},apad"
if [ -z "$START" ]; then
  ffmpeg -hide_banner -loglevel error -nostdin -y -i "$FILM" -i "$WAV" -filter_complex "[1:a]${LIM}[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
else
  DUR=$(awk -v s="$START" -v e="$END" 'BEGIN{printf "%.3f", e-s}')
  TMP=$(mktemp --suffix .mp4)
  ffmpeg -hide_banner -loglevel error -nostdin -y -ss "$START" -t "$DUR" -i "$FILM" -an -vf scale=720:1280 \
    -c:v libx264 -preset medium -crf 21 -pix_fmt yuv420p "$TMP"
  ffmpeg -hide_banner -loglevel error -nostdin -y -i "$TMP" -i "$WAV" \
    -filter_complex "[1:a]${LIM},atrim=start=${START},asetpts=PTS-STARTPTS[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
  rm -f "$TMP"
fi
echo "wrote $OUT"
