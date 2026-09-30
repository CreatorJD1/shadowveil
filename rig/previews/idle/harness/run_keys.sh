#!/bin/bash
cd /workspace/shadowveil/rig/previews/idle
run(){ name=$1; view=$2; shift 2; for try in 1 2 3; do rm -rf work/$name; if node harness/render_idle.mjs $view work/$name --seconds=8 --fps=30 --sub=2 --seed=20260938 "$@"; then return 0; fi; echo "RETRY $name ($try)"; sleep 5; done; return 1; }
for c in idle_arm_sway idle_weight_shift idle_arm_settle; do for v in apose tpose left right back; do run keys_${c}_$v $v --keys=$c; done; done
echo ALLDONE
