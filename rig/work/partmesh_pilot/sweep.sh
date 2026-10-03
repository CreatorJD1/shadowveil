# usage: bash sweep.sh <tag> <port> M1 M2 M3   (root blend px per Middle segment; 0 = rigid root)
set -e; T=$1; PORT=$2; export PYTHONDONTWRITEBYTECODE=1
D=/workspace/shadowveil/rig/work/partmesh_pilot/cand_$T; mkdir -p $D
PARTMESH_OUT=$D python3 /workspace/shadowveil/rig/partmesh/tools/build_pilot.py R_Middle1=$3 R_Middle2=$4 R_Middle3=$5 > $D/build.txt
rm -rf r_$T; node hb_render_pm.mjs tpose cases_data.json r_$T --layers=1 --q='&partmesh=1&quality=linear' --port=$PORT --pmdir=$D > r_$T.log 2>&1
python3 lineart.py r_$T tpose /workspace/shadowveil/views/tpose/hands/rig.json la_$T.json > la_$T.txt
python3 pivot_qa.py r_$T tpose pq_$T.json > pq_$T.txt
echo SWEEP_DONE $T
