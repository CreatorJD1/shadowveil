#!/bin/bash
# builds rig/index.v18-wip.html from a live-rig copy through all v1.8 patch steps
set -e; cd /workspace/shadowveil; H=rig/previews/idle/harness; SRC=${1:-/tmp/index.pre-idlefix.html}; DST=${2:-rig/index.v18-wip.html}
python3 $H/patch_v18.py $SRC /tmp/v18a.html; python3 $H/patch_v18b.py /tmp/v18a.html /tmp/v18b.html; python3 $H/patch_v18c.py /tmp/v18b.html /tmp/v18c.html
python3 $H/patch_v18d.py /tmp/v18c.html /tmp/v18d.html; python3 $H/patch_v18e.py /tmp/v18d.html $DST
sed -n '/<script>/,/<\/script>/p' $DST | sed '1d;$d' > /tmp/wip_check.js && node --check /tmp/wip_check.js && echo "built $DST"
