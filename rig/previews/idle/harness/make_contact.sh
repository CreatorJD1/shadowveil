#!/bin/bash
# side-by-side contact mp4 from per-view mp4s (each scaled to 870 px tall)
# usage: make_contact.sh out.mp4 in1.mp4 in2.mp4 ...
set -e; out=$1; shift; n=$#; args=(); f=""
for i in $(seq 0 $((n-1))); do f="$f[$i:v]scale=682:870:flags=lanczos,setsar=1[v$i];"; done
for x in "$@"; do args+=(-i "$x"); done
st=""; for i in $(seq 0 $((n-1))); do st="$st[v$i]"; done
ffmpeg -y -loglevel error "${args[@]}" -filter_complex "${f}${st}hstack=inputs=$n,format=yuv420p" -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart -r 30 "$out"
