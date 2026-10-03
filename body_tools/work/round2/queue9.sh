cd /workspace/shadowveil/body_tools/work/round2; O=/workspace/shadowveil/body_tools/work/round2_staged/checks
./run_stage.sh stL "skin.json&quality=linear" arm_settle 5.9 150 176
./run_stage.sh stL "skin.json&quality=linear" weight_shift 8 150 215
./run_stage.sh stS "skin.json&quality=ss2" arm_settle 5.9 150 176
./run_stage.sh stS "skin.json&quality=ss2" weight_shift 8 150 215
node page_check_stage.mjs right "quality=linear" 25,12.5 > $O/page_linear.json 2>>$O/page_err.txt
node page_check_stage.mjs right "quality=ss2" 25,12.5 > $O/page_ss2.json 2>>$O/page_err.txt
echo Q9A
./run_stage.sh stLfull "skin.json&quality=linear" arm_settle 5.9 0 176
./run_stage.sh stLfull "skin.json&quality=linear" weight_shift 8 0 239
echo Q9DONE
