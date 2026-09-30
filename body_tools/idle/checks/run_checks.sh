cd /workspace/shadowveil/body_tools/idle/checks
for c in idle_arm_settle idle_weight_shift idle_arm_sway; do for v in right apose tpose left back; do nice python3 idle_check.py keys_${c}_$v || echo "FAIL keys_${c}_$v"; done; done
echo ALLDONE
