#!/bin/bash
# one view at a time (memory), retry up to 3x if the process is killed
cd /workspace/shadowveil/rig/previews/idle
run(){ name=$1; view=$2; shift 2; for try in 1 2 3; do rm -rf work/$name; if node harness/render_idle.mjs $view work/$name --seconds=8 --fps=30 --sub=2 --seed=20260938 "$@"; then return 0; fi; echo "RETRY $name ($try)"; sleep 5; done; return 1; }
for v in apose tpose left right back; do run $v $v; done
run apose_hair_stiff apose --hair=10,0.9,10,0.9,0.01
run apose_hair_middle apose --hair=2.2,0.6,2.2,0.6,0.04
echo ALLDONE
