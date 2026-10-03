cd /workspace/shadowveil/body_tools/work/round2
while pgrep -f "[b]ash queue1.sh" >/dev/null || pgrep -f "[b]aseL_weight_shift --seconds" >/dev/null; do sleep 10; done
find render/baseL_weight_shift/frames -size -3c -delete
for t in c2; do
./run.sh ${t}L "cand_${t}.json&quality=linear" arm_settle 5.9 150 176
./run.sh ${t}L "cand_${t}.json&quality=linear" weight_shift 8 150 215
./run.sh ${t}S "cand_${t}.json" arm_settle 5.9 150 176
./run.sh ${t}S "cand_${t}.json" weight_shift 8 150 215
done
echo Q3DONE
