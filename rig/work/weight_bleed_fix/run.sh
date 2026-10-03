#!/bin/bash
# rebuild left/right skins into rig/work/weight_bleed_fix/: *_ref (no flag, must equal live) and *_fix (--chain-bleed-fix); underlay via the copy
set -e; cd /workspace/shadowveil; W=rig/work/weight_bleed_fix
for tag in ref fix; do F=""; [ $tag = fix ] && F="--chain-bleed-fix"
python3 $W/build_skin_bleedfix.py left --sigma-shoulder 12 --radius-shoulder 45 $F --out $W/left_skin_$tag.json
python3 $W/build_underlay_copy.py left --skin $W/left_skin_$tag.json --image left_underlay_$tag.png --from-parts --margin 1 --depth 24 --bgk 8 --flat-skin-only --flat-override --pairs pelvis:thigh_L:0,upperArm_L:torso+pelvis:4,forearm_L:torso+pelvis+thigh_L:12 --flat-pairs thigh_L:pelvis --peel-keep pelvis:thigh_L:8
python3 $W/build_skin_bleedfix.py right --sigma-shoulder 12 --sigma-hip-outer 24 --hip-outer-ramp 20 50 --torso-arm-clamp 520:4 $F --out $W/right_skin_$tag.json
python3 $W/build_underlay_copy.py right --skin $W/right_skin_$tag.json --image right_underlay_$tag.png --from-parts --margin 1 --depth 24 --bgk 8 --flat-skin-only --flat-override --pairs pelvis:thigh_R:0,upperArm_R:torso+pelvis:4,forearm_R:torso+pelvis+thigh_R:12 --flat-pairs thigh_R:pelvis --parts-bg upperArm_R:*:12,pelvis:thigh_R:12,forearm_R:*:8 --host-edge-line torso:632:639:643:714:2 --host-strip pelvis:forearm_R:8:710:858
done
