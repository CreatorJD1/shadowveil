#!/bin/bash
# build.sh <tag> "<extra build_skin args>" "<host-strip spec>" ["<extra underlay args>"]   -> /workspace/r2tree/views/right/body/cand_<tag>.json + ul_<tag>.png
set -e; cd /workspace/shadowveil; T=/workspace/r2tree/views/right/body; tag=$1
python3 body_tools/build_skin.py right --sigma-shoulder 12 --sigma-hip-outer 24 --hip-outer-ramp 20 50 $2 --out $T/cand_$tag.json
python3 body_tools/work/round2/tools/build_underlay_r2.py right --skin $T/cand_$tag.json --image body/ul_$tag.png --from-parts --margin 1 --depth 24 --bgk 8 --flat-skin-only --flat-override --pairs pelvis:thigh_R:0,upperArm_R:torso+pelvis:4,forearm_R:torso+pelvis+thigh_R:12 --flat-pairs thigh_R:pelvis --parts-bg upperArm_R:*:12,pelvis:thigh_R:12,forearm_R:*:8 --host-edge-line torso:632:639:643:714:2 ${3:+--host-strip $3} $4 | python3 -c "import json,sys;d=json.load(sys.stdin);print('UL px',d['px'],'strips',[(s['host'],s['limb'],s['px']) for s in d['hostStrip']])"
