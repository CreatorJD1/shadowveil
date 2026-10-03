cd /workspace/shadowveil/body_tools/work/round2
./run.sh baseL "skin.json&quality=linear" weight_shift 8 150 215
./run.sh c2L "cand_c2.json&quality=linear" arm_settle 5.9 150 176
./run.sh c2L "cand_c2.json&quality=linear" weight_shift 8 150 215
./run.sh c2S "cand_c2.json" arm_settle 5.9 150 176
./run.sh c2S "cand_c2.json" weight_shift 8 150 215
echo Q2DONE
