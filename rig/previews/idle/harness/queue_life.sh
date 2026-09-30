#!/bin/bash
cd /workspace/shadowveil/rig/previews/idle
for v in apose tpose left right back; do
  harness/render_retry.sh v2/life/work/life_$v $v --page=index.html --seed=20260938 --seconds=8 --q=hair=A\&life=1 --nomq=1
done
echo QUEUE_DONE >> v2/life/work/queue.log
