cd /workspace/shadowveil/body_tools/work/round2
while ! grep -q Q3DONE q3.log; do sleep 10; done
for t in c1 c2; do node page_check.mjs right "skin=cand_$t.json&quality=linear" 25,12.5 > pc_${t}_linear.json 2>>pc_err.txt; done
for t in skin c1 c2; do f=cand_$t.json; [ $t = skin ] && f=skin.json; node page_check.mjs right "skin=$f&quality=ss2" 25,12.5 > pc_${t}_ss2.json 2>>pc_err.txt; done
echo Q4DONE
