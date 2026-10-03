cd /workspace/shadowveil/body_tools/work/round2; O=/workspace/shadowveil/body_tools/work/round2_staged/checks
while ! grep -q Q7DONE q7.log; do sleep 10; done
node page_check_stage.mjs right "quality=linear" 25,12.5 > $O/page_linear.json 2>>$O/page_err.txt
node page_check_stage.mjs right "quality=ss2" 25,12.5 > $O/page_ss2.json 2>>$O/page_err.txt
echo Q8DONE
