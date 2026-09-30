#!/bin/bash
# tpose gate opened 04:22 (Hair wisp fill). Fresh Chrome per render = fresh disk load.
cd /workspace/shadowveil/rig/previews/idle; A=../actions/v1
harness/render_retry.sh v2/life/work/life_tpose tpose --page=index.html --seed=20260938 --seconds=8 --q=hair=A\&life=1 --nomq=1
for c in jump anger run; do case $c in jump) s=1.6;; anger) s=3.0;; run) s=4.0;; esac
 harness/render_retry.sh $A/work/normal_${c}_tpose tpose --page=index.html --seed=20260938 --seconds=$s --keys=$c --clipsfile=$A/clips/${c}.json --nomq=1; done
for c in jump anger run; do case $c in jump) s=1.6;; anger) s=3.0;; run) s=4.0;; esac
 harness/render_retry.sh $A/work/stress_${c}_tpose tpose --page=index.html --seed=20260938 --seconds=$s --keys=$c --clipsfile=$A/clips/${c}_stress.json --nomq=1; done
echo DONE_TPOSE >> $A/work/queue_tpose.log
