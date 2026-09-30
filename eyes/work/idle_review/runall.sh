for v in tpose left right; do python3 analyze.py $v $v > log_$v.txt 2>&1; done
for c in idle_arm_sway idle_weight_shift idle_arm_settle; do for v in apose tpose left right; do python3 analyze.py keys_${c}_$v $v > log_${c}_$v.txt 2>&1; done; done
echo ALLDONE > done.txt
