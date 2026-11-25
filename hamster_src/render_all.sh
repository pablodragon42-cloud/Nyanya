#!/bin/bash
# Full render: voice -> mix -> frames (4 workers) -> final mp4
set -e
cd "$(dirname "$0")"
python3 voice.py > /dev/null
python3 mix.py
NF=$(python3 -c "import json;print(json.loads(open('data.js').read().split('=',1)[1].rstrip().rstrip(';'))['nf'])")
J=4; STEP=$(( (NF + J - 1) / J ))
mkdir -p build/seg
pids=()
for k in $(seq 0 $((J-1))); do
  a=$((k*STEP)); b=$(( (k+1)*STEP < NF ? (k+1)*STEP : NF ))
  node render.js $a $b build/seg/part$k.mp4 & pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
: > build/seg/list.txt
for k in $(seq 0 $((J-1))); do echo "file 'part$k.mp4'" >> build/seg/list.txt; done
ffmpeg -y -loglevel error -f concat -safe 0 -i build/seg/list.txt -i build/mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart ../hamster_boss_of_hell_9x16.mp4
echo done
