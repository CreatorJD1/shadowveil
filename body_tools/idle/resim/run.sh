cd /workspace/shadowveil/rig/previews/idle
H=harness/render_idle.mjs; O=/workspace/shadowveil/body_tools/idle/resim
for spec in "arm_settle right 5.9" "arm_settle left 5.9" "weight_shift right 6.6" "weight_shift left 6.6"; do set -- $spec
  nice node $H $2 $O/keys_idle_$1_$2 --seconds=$3 --fps=30 --sub=2 --seed=20260938 --keys=idle_$1 || echo "FAIL $spec"; done
echo ALLDONE
