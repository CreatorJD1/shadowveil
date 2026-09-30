#!/bin/bash
# re-render anger (Mouth's anger shape live 04:5x; clips regenerated 04:54) for apose + tpose, both passes; waits for the tpose queue
cd /workspace/shadowveil/rig/previews/idle; A=../actions/v1
while ! grep -q DONE_TPOSE $A/work/queue_tpose.log 2>/dev/null; do sleep 30; done
for pass in normal stress; do f=$A/clips/anger.json; [ $pass = stress ] && f=$A/clips/anger_stress.json
 for v in apose tpose; do d=$A/work/${pass}_anger_$v; [ -d $d ] && mv $d $A/work/stale_pregate/${pass}_anger_${v}_premouth; mv -f $d.log $A/work/stale_pregate/ 2>/dev/null
  harness/render_retry.sh $d $v --page=index.html --seed=20260938 --seconds=3.0 --keys=anger --clipsfile=$f --nomq=1; done; done
echo DONE_ANGER >> $A/work/queue_anger_redo.log
