#!/bin/bash
# mp4 (H.264, yuv420p) of rendered RGBA frames composited on flat mid-grey (#808080); canvas padded 1365x1739 -> 1366x1740 with grey
# usage: make_media.sh <framesdir> <out.mp4>
set -e
ffmpeg -y -loglevel error -f lavfi -i color=c=0x808080:s=1366x1740:r=30 -framerate 30 -i "$1/f%04d.png" \
 -filter_complex "[0][1]overlay=0:0:shortest=1,format=yuv420p" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart -r 30 "$2"
