#!/bin/bash
# anger clip re-render with ?mouthfix=1: same args as rig/previews/idle/harness/queue_anger_redo.sh + --q=mouthfix=1.
# Own server on 8779 (root /workspace/shadowveil); outputs only under rig/work/mouthfix/anger
A=/workspace/shadowveil/rig/previews/actions/v1; O=/workspace/shadowveil/rig/work/mouthfix/anger
for pass in normal stress; do f=$A/clips/anger.json; [ $pass = stress ] && f=$A/clips/anger_stress.json
 for v in apose tpose left right; do d=$O/${pass}_anger_$v
  for i in 1 2 3 4 5 6; do rm -f $d/meta.json; node $O/render_idle_8779.mjs $v $d --resume=1 --page=index.html --seed=20260938 --seconds=3.0 --keys=anger --clipsfile=$f --nomq=1 --q=mouthfix=1 >> $d.log 2>&1; [ -s $d/meta.json ] && break; echo retry $i >> $d.log; sleep 5; done
 done; done
echo DONE_ANGER >> $O/queue.log
