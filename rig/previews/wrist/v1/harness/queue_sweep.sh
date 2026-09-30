#!/bin/bash
# wrist sweeps; left/right/back are provisional (pre-gate) until Body/Hands post done
cd /workspace/shadowveil/rig/previews/wrist/v1
for v in "$@"; do for a in 1 2 3; do node harness/sweep.mjs index.v19-wip.html $v work/sweep_$v > work/sweep_$v.log 2>&1 && break; done; python3 harness/qa_wrist.py work/sweep_$v > work/qa_$v.log 2>&1; done
