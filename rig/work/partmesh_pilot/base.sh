set -e; export PYTHONDONTWRITEBYTECODE=1; T=base0030
rm -rf r_$T; node hb_render_pm.mjs tpose cases_data.json r_$T --layers=1 --q='&quality=linear' --port=8796 > r_$T.log 2>&1
python3 lineart.py r_$T tpose /workspace/shadowveil/views/tpose/hands/rig.json la_$T.json > la_$T.txt
python3 pivot_qa.py r_$T tpose pq_$T.json > pq_$T.txt; echo BASE_DONE
