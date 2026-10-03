# usage: bash loop.sh <tag> <builder args...>   (own in-process server on 8796 rooted at /workspace/shadowveil, serves disk directly)
set -e; T=$1; shift; export PYTHONDONTWRITEBYTECODE=1; PORT=8796
D=/workspace/shadowveil/rig/work/partmesh_pilot/cand_$T; mkdir -p $D
PARTMESH_OUT=$D python3 /workspace/shadowveil/rig/partmesh/tools/build_pilot.py R_Middle1=4 R_Middle2=4 R_Middle3=3 "$@" > $D/build.txt
rm -rf r_$T; node hb_render_pm.mjs tpose cases_data.json r_$T --layers=1 --q='&partmesh=1&quality=linear' --port=$PORT --pmdir=$D > r_$T.log 2>&1
python3 lineart.py r_$T tpose /workspace/shadowveil/views/tpose/hands/rig.json la_$T.json > la_$T.txt
python3 pivot_qa.py r_$T tpose pq_$T.json > pq_$T.txt
python3 -c "
import sys,json;sys.argv=['x'];from eval_hand import evaluate
ok,rows=evaluate('$T',base='base0030');print('$T','PASS' if ok else 'FAIL')
for cn,r in rows.items(): print('  ',cn,{k:r[k] for k in ('width_max_abs_dw','middle_breaks','new_stray_ink_px','new_hole_px_in_reach','changed_px_outside_middle_reach','vertex_disp_outside_blend','PASS')})
json.dump(dict(PASS=ok,rows=rows),open('eval_$T.json','w'),indent=1)" > ev_$T.txt; cat ev_$T.txt; echo LOOP_DONE $T
