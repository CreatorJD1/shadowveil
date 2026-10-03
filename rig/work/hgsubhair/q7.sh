#!/bin/bash
cd /workspace/shadowveil
while pgrep -f "armsub/as_check.js" >/dev/null; do sleep 10; done
PORT=8795 timeout 3000 node rig/work/hgsubhair/hg_sub_rest_long.js > rig/work/hgsubhair/hg_sub_rest.json 2> rig/work/hgsubhair/hg_sub_rest.err
