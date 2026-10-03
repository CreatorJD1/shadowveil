cd /workspace/shadowveil/rig/previews/idle
H=/workspace/shadowveil/body_tools/idle/resim/render_idle_body.mjs; O=/workspace/shadowveil/body_tools/idle/resim/v2
for job in "$@"; do set -- $job
  x=$1; D=$O/${x}_keys_idle_$2_right; mkdir -p $D/frames; N=$(python3 -c "print(round($3*30))")
  for ((f=0; f<N; f++)); do if (( f < $4 || f > $5 )); then p=$D/frames/f$(printf %04d $f).png; [ -s $p ] || echo x > $p; fi; done
  ok=0; for try in 1 2 3; do nice node $H right $D --seconds=$3 --fps=30 --sub=2 --seed=20260938 --keys=idle_$2 --q=skin=skin_$x.json --resume=1 --skipsim=1 --navtimeout=600000 && { ok=1; break; }; echo "retry $try $job"; sleep 20; done
  find $D/frames -size -3c -delete; echo "done $x $2 ok=$ok $(date +%T)"; done
echo ALLDONE
