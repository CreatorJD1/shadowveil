#!/bin/bash
# side-by-side before|after mp4 of two RGBA frame dirs on grey, with labels. usage: make_sbs.sh <beforeFrames> <afterFrames> <out.mp4> '<labelA>' '<labelB>'
set -e
FONT="/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf"
ffmpeg -y -loglevel error -f lavfi -i color=c=0x808080:s=1366x1740:r=30 -framerate 30 -i "$1/f%04d.png" -f lavfi -i color=c=0x808080:s=1366x1740:r=30 -framerate 30 -i "$2/f%04d.png" \
 -filter_complex "[0][1]overlay=0:0:shortest=1,drawtext=fontfile='$FONT':text='$4':x=30:y=30:fontsize=44:fontcolor=white:box=1:boxcolor=black@0.6[a];[2][3]overlay=0:0:shortest=1,drawtext=fontfile='$FONT':text='$5':x=30:y=30:fontsize=44:fontcolor=white:box=1:boxcolor=black@0.6[b];[a][b]hstack=2,scale=2048:-2,format=yuv420p" \
 -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart -r 30 "$3"
