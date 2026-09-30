#!/bin/bash
# mkcand.sh VIEW NAME <build_skin args...>  -> rig/skin_tools/drafts/VIEW_bk_NAME.json (underlay block copied from the current skin.json)
set -e
V=$1; N=$2; shift 2
cd /workspace/shadowveil
python3 body_tools/build_skin.py $V "$@" --out body_tools/work/bikini_fix/cand/${V}_${N}.json 2>body_tools/work/bikini_fix/cand/${V}_${N}.log
python3 - "$V" "$N" <<'PY'
import json,sys
v,n=sys.argv[1:]
c=json.load(open(f'body_tools/work/bikini_fix/cand/{v}_{n}.json')); cur=json.load(open(f'views/{v}/body/skin.json'))
c['underlay']=cur['underlay']
# draft lives under rig/skin_tools/drafts: images are resolved relative to the view dir by the loader? keep names as-is
json.dump(c,open(f'rig/skin_tools/drafts/{v}_bk_{n}.json','w'),separators=(',',':'))
print('draft',f'rig/skin_tools/drafts/{v}_bk_{n}.json')
PY
grep bikini-blend body_tools/work/bikini_fix/cand/${V}_${N}.log | cut -c1-600
