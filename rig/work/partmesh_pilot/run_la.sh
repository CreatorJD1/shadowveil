export PYTHONDONTWRITEBYTECODE=1
for t in "$@"; do python3 lineart.py r_${t} tpose /workspace/shadowveil/views/tpose/hands/rig.json la_${t}.json > la_${t}.txt 2>&1; done
echo LA_DONE
