cd /workspace/shadowveil/body_tools/work/round2
./run.sh baseL "skin.json&quality=linear" arm_settle 5.9 150 176
./run.sh c1L "cand_c1.json&quality=linear" arm_settle 5.9 150 176
./run.sh c1L "cand_c1.json&quality=linear" weight_shift 8 150 215
./run.sh c1S "cand_c1.json" arm_settle 5.9 150 176
./run.sh c1S "cand_c1.json" weight_shift 8 150 215
echo Q1DONE
