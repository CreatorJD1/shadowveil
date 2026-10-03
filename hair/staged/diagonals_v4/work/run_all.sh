#!/bin/sh
cd /workspace/shadowveil/hair/staged/diagonals_v4/work
python3 caps.py > /tmp/ear/caps.log 2>&1
python3 before_nocap.py > /tmp/ear/bnc.log 2>&1
cd /workspace/shadowveil
for t in diagv4 diagv4_frame; do PYTHONDONTWRITEBYTECODE=1 python3 hair/qa/qa_gates_runs/qa_gates_$t.py --gate leak --part hair --json hair/qa/qa_gates_runs/after_$t.json > hair/qa/qa_gates_runs/after_$t.txt 2>&1; done
cd hair/staged/diagonals_v4/work && python3 sheet_v4.py > /tmp/ear/sheet.log 2>&1
echo ALLDONE >> /tmp/ear/caps.log
