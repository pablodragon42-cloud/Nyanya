#!/bin/bash
# Full build of the cartoon version: data -> mix -> frames (4 workers) -> 2-pass H.264 + AAC
#   BUILD=dir PY=python ./build.sh
set -e
cd "$(dirname "$0")"
BUILD=${BUILD:-build}; PY=${PY:-python3}; OUT=${OUT:-../jason_drug_idiot_v2_9x16.mp4}
mkdir -p "$BUILD"
$PY prep.py
( cd ../jason_src && BUILD="$BUILD" $PY timeline.py voice.mp3 words_asr.json > /dev/null && CARTOON=1 BUILD="$BUILD" $PY sound.py )
NF=$($PY -c "import json;print(json.loads(open('data.js').read().split('=',1)[1].strip().rstrip(';'))['nf'])")
J=4; STEP=$(( (NF + J - 1) / J ))
pids=()
for k in $(seq 0 $((J-1))); do
  a=$((k*STEP)); b=$(( (k+1)*STEP < NF ? (k+1)*STEP : NF ))
  node render.js $a $b "$BUILD/part$k.mp4" > "$BUILD/render$k.log" 2>&1 & pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
: > "$BUILD/list.txt"; for k in $(seq 0 $((J-1))); do echo "file 'part$k.mp4'" >> "$BUILD/list.txt"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$BUILD/list.txt" -c copy "$BUILD/video.mp4"
X="-c:v libx264 -preset slow -b:v 9M -maxrate 12M -bufsize 18M -pix_fmt yuv420p -profile:v high -r 30"
ffmpeg -y -loglevel error -i "$BUILD/video.mp4" $X -pass 1 -passlogfile "$BUILD/x264" -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i "$BUILD/video.mp4" -i "$BUILD/mix.wav" -map 0:v -map 1:a $X -pass 2 -passlogfile "$BUILD/x264" \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT"
