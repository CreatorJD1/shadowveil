cd /workspace/shadowveil/body_tools/work/round2
while ! grep -q Q4DONE q4.log; do sleep 10; done
t=c3
./run.sh ${t}L "cand_${t}.json&quality=linear" arm_settle 5.9 150 176
./run.sh ${t}L "cand_${t}.json&quality=linear" weight_shift 8 150 215
node page_check.mjs right "skin=cand_$t.json&quality=linear" 25,12.5 > pc_${t}_linear.json 2>>pc_err.txt
./run.sh ${t}S "cand_${t}.json" arm_settle 5.9 150 176
./run.sh ${t}S "cand_${t}.json" weight_shift 8 150 215
node page_check.mjs right "skin=cand_$t.json&quality=ss2" 25,12.5 > pc_${t}_ss2.json 2>>pc_err.txt
echo Q5DONE
