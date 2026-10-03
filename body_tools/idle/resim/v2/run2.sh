while kill -0 1054045 2>/dev/null; do sleep 5; done
find /workspace/shadowveil/body_tools/idle/resim/v2/v0_keys_idle_arm_settle_right/frames -size -3c -delete; echo "done v0 arm_settle $(date +%T)"
cd /workspace/shadowveil/rig/previews/idle
H=harness/render_idle.mjs; O=/workspace/shadowveil/body_tools/idle/resim/v2
for job in ${JOBS:-"v0 weight_shift 6.6 163 197" "vA arm_settle 5.9 158 176" "vA weight_shift 6.6 163 197" "vB weight_shift 6.6 163 197"}; do set -- $job
  x=$1; D=$O/${x}_keys_idle_$2_right; mkdir -p $D/frames; N=$(python3 -c "print(round($3*30))")
  for ((f=0; f<N; f++)); do if (( f < $4 || f > $5 )); then p=$D/frames/f$(printf %04d $f).png; [ -s $p ] || echo x > $p; fi; done
  nice node $H right $D --seconds=$3 --fps=30 --sub=2 --seed=20260938 --keys=idle_$2 --q=skin=skin_$x.json --resume=1 || echo "FAIL $job"
  find $D/frames -size -3c -delete; echo "done $x $2 $(date +%T)"; done
echo ALLDONE
