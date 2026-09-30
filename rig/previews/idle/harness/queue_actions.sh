#!/bin/bash
# actions (merged owner clips) in all 5 views; pass A = normal clips, pass B = Body's stress copies (stressTest)
cd /workspace/shadowveil/rig/previews/idle
A=../actions/v1
for pass in normal stress; do
 for c in jump anger run; do
  case $c in jump) s=1.6;; anger) s=3.0;; run) s=4.0;; esac
  f=$A/clips/$c.json; [ $pass = stress ] && f=$A/clips/${c}_stress.json
  for v in apose tpose left right back; do
   harness/render_retry.sh $A/work/${pass}_${c}_$v $v --page=index.html --seed=20260938 --seconds=$s --keys=$c --clipsfile=$f --nomq=1
  done
 done
done
echo QUEUE_DONE >> $A/work/queue.log
