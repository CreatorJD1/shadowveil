O=/workspace/shadowveil/body_tools/work/round2_staged/checks
cd /workspace/r2stagecheck && python3 /workspace/shadowveil/rig/rest_check.py > $O/rest_check.json 2>&1; cp rig/rest_diff_right.png $O/
cd /workspace/r2stage && python3 /workspace/shadowveil/body_tools/check_skin_rules.py right skin.json > $O/check_skin_rules.json 2>&1
python3 /workspace/shadowveil/body_tools/work/round2/tools/check_underlay_stage.py right > $O/check_underlay.json 2>&1; echo "exit $?" >> $O/check_underlay.json
echo STAGECHECKDONE > $O/done.txt
