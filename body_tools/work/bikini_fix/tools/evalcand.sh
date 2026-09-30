#!/bin/bash
# evalcand.sh VIEW SKINARG OUTDIR [SKINJSON]  render the hip set with ?skin=SKINARG, then measure
set -e
V=$1; S=$2; O=$3; J=${4:-/workspace/shadowveil/rig/skin_tools/drafts/${S#draft:}}
cd /workspace/jt && VIEW=$V timeout 600 node shots.js $S $O bk_spec_meas.json
cd /workspace/shadowveil && timeout 1200 python3 body_tools/work/bikini_fix/tools/bk_measure.py $V $J $O --out $O/measure.json --overlay $O/qa 2>&1 | grep -v -E "Warning|x0 = np.clip"
