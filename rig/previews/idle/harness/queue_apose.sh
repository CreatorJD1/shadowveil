#!/bin/bash
# worker 1: apose actions (normal run, then stress jump/anger/run)
cd /workspace/shadowveil/rig/previews/idle; A=../actions/v1
harness/render_retry.sh $A/work/normal_run_apose apose --page=index.html --seed=20260938 --seconds=4.0 --keys=run --clipsfile=$A/clips/run.json --nomq=1
for c in jump anger run; do case $c in jump) s=1.6;; anger) s=3.0;; run) s=4.0;; esac
 harness/render_retry.sh $A/work/stress_${c}_apose apose --page=index.html --seed=20260938 --seconds=$s --keys=$c --clipsfile=$A/clips/${c}_stress.json --nomq=1; done
echo DONE1 >> $A/work/queue_apose.log
