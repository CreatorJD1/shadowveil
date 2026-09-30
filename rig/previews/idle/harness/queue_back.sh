#!/bin/bash
# back gate released 05:02 (Hands: back rig.json unchanged). Fresh Chrome per render = fresh disk load.
cd /workspace/shadowveil/rig/previews/idle; A=../actions/v1
while ! grep -q DONE_TPOSE ../actions/v1/work/queue_tpose.log 2>/dev/null; do sleep 30; done
harness/render_retry.sh v2/life/work/life_back back --page=index.html --seed=20260938 --seconds=8 --q=hair=A\&life=1 --nomq=1
for c in jump anger run; do case $c in jump) s=1.6;; anger) s=3.0;; run) s=4.0;; esac
 harness/render_retry.sh $A/work/normal_${c}_back back --page=index.html --seed=20260938 --seconds=$s --keys=$c --clipsfile=$A/clips/${c}.json --nomq=1; done
for c in jump anger run; do case $c in jump) s=1.6;; anger) s=3.0;; run) s=4.0;; esac
 harness/render_retry.sh $A/work/stress_${c}_back back --page=index.html --seed=20260938 --seconds=$s --keys=$c --clipsfile=$A/clips/${c}_stress.json --nomq=1; done
echo DONE_BACK >> $A/work/queue_back.log
