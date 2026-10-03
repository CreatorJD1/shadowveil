#!/bin/bash
# usage: run.sh <tag> <skinfile in views/right/body> <clip> <seconds> <f0> <f1>
cd /workspace/shadowveil/body_tools/work/round2
H=/workspace/shadowveil/body_tools/work/round2/render_stage.mjs; O=/workspace/shadowveil/body_tools/work/round2_staged/render
x=$1; S=$2; clip=$3; sec=$4; a=$5; b=$6
D=$O/${x}_$clip; mkdir -p $D/frames; N=$(python3 -c "print(round($sec*30))")
for ((f=0; f<N; f++)); do if (( f < a || f > b )); then p=$D/frames/f$(printf %04d $f).png; [ -s $p ] || echo x > $p; fi; done
ok=0; for try in 1 2; do nice node $H right $D --seconds=$sec --fps=30 --sub=2 --seed=20260938 --keys=idle_$clip --q=skin=$S --resume=1 --skipsim=1 --navtimeout=600000 && { ok=1; break; }; echo "retry $try"; sleep 5; done
find $D/frames -size -3c -delete; echo "done $x $clip ok=$ok $(date +%T)"
