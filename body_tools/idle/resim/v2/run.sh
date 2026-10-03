cd /workspace/shadowveil/rig/previews/idle
H=harness/render_idle.mjs; O=/workspace/shadowveil/body_tools/idle/resim/v2
for x in ${VARS:-v0 vcur vA vB vC}; do for spec in "arm_settle 5.9 158 176" "weight_shift 6.6 163 197"; do set -- $spec
  D=$O/${x}_keys_idle_$1_right; mkdir -p $D/frames; N=$(python3 -c "print(round($2*30))")
  for ((f=0; f<N; f++)); do if (( f < $3 || f > $4 )); then p=$D/frames/f$(printf %04d $f).png; [ -s $p ] || echo x > $p; fi; done
  nice node $H right $D --seconds=$2 --fps=30 --sub=2 --seed=20260938 --keys=idle_$1 --q=skin=skin_$x.json --resume=1 || echo "FAIL $x $spec"
  find $D/frames -size -3c -delete; echo "done $x $1 $(date +%T)"; done; done
echo ALLDONE
