#!/bin/sh
# Usage: sh prep_footage.sh <mixkit_id> <name>
# Downloads a Mixkit clip (free licence, check https://mixkit.co/license/) and grades it to the house spec:
# 1920x1080, 30 fps, no audio, slightly muted colour so graphics sit on top cleanly.
set -e
ID="$1"; NAME="$2"
mkdir -p stock/raw stock/prep
[ -f "stock/raw/$ID.mp4" ] || curl -sSL -o "stock/raw/$ID.mp4" "https://assets.mixkit.co/videos/$ID/$ID-1080.mp4"
ffmpeg -v error -y -i "stock/raw/$ID.mp4" -an \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,eq=saturation=0.85:contrast=1.03:brightness=-0.01,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 "stock/prep/$NAME.mp4"
# mirrored variant (for a second, different-looking shot from the same clip)
ffmpeg -v error -y -i "stock/prep/$NAME.mp4" -vf hflip -c:v libx264 -preset veryfast -crf 18 "stock/prep/${NAME}_flip.mp4"
echo "ready: stock/prep/$NAME.mp4"
