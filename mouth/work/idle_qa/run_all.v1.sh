#!/bin/bash
# sequential, one video at a time
I=/workspace/shadowveil/rig/previews/idle
for v in apose tpose left right; do
  for c in idle_breathe idle_weight_shift idle_arm_settle; do
    nice -n 10 python3 measure.py $v $I/keys/${c}_$v.mp4 mp4_${c}_$v
  done
  nice -n 10 python3 measure.py $v $I/${v}_idle.mp4 mp4_auto_$v
done
for v in apose tpose left right; do
  for c in idle_breathe idle_weight_shift idle_arm_settle; do
    nice -n 10 python3 measure.py $v $I/frames/keys_${c}_$v png_${c}_$v
  done
  nice -n 10 python3 measure.py $v $I/frames/$v png_auto_$v
done
echo ALLDONE
