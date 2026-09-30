#!/bin/bash
# worker 2: showcase sections for one view at 15 fps: body, hair x3 presets, mouth, eyes, hands
cd /workspace/shadowveil/rig/previews/idle; A=../actions/v1; v=${1:-apose}; R=/workspace/shadowveil
harness/render_retry.sh $A/work/show_body_$v $v --page=index.html --seed=20260938 --fps=15 --seconds=22.5 --keys=body_showcase --clipsfile=$R/body_tools/idle/body_showcase.json --nomq=1
for p in default A B; do harness/render_retry.sh $A/work/show_hair_${p}_$v $v --page=index.html --seed=20260938 --fps=15 --seconds=8.2 --keys=hair_showcase --clipsfile=$R/hair/showcase/hair_showcase.json --q=hair=$p --nomq=1; done
harness/render_retry.sh $A/work/show_mouth_$v $v --page=index.html --seed=20260938 --fps=15 --seconds=11.4 --keys=mouth_showcase --clipsfile=$R/mouth/showcase/mouth_showcase.json --nomq=1
harness/render_retry.sh $A/work/show_eyes_$v $v --page=index.html --seed=20260938 --fps=15 --seconds=10.4 --keys=eye_showcase --clipsfile=$R/eyes/showcase/eye_showcase.json --nomq=1
harness/render_retry.sh $A/work/show_hands_$v $v --page=index.html --seed=20260938 --fps=15 --seconds=29.6 --keys=hands_showcase --clipsfile=$R/hands/showcase/hands_showcase.json --nomq=1
echo DONE_$v >> $A/work/queue_showcase.log
