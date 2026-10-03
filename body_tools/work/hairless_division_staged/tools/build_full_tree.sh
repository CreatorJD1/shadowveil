#!/bin/bash
# Scratch tree, REAL COPIES ONLY (no symlinks anywhere). $1 = tree dir, $2 = live | round2 (right body skin.json+underlay from round2_staged)
set -e; R=/workspace/shadowveil; T=$1; rm -rf $T; mkdir -p $T
cp -r $R/views $T/views
mkdir -p $T/rig $T/hair/staged $T/hands/staged $T/body_tools/idle $T/body_tools/work/hairless_division_staged/apose
cp $R/rig/index.html $R/rig/rest_check.py $T/rig/; cp -r $R/rig/skin_tools $R/rig/partmesh $R/rig/twist_masks $R/rig/hand_angles $T/rig/
for d in speck_fix ear_strands lineart_fix merged tone_fix hairfront_holes; do cp -r $R/hair/staged/$d $T/hair/staged/; done
cp $R/hair/staged/speck_fix/hair/*_hair_erase_mask.png $T/hair/          # staged erase masks (live OR speck px); region labels only
cp $R/hands/*_hand_erase_mask.png $T/hands/; cp -r $R/hands/staged/f7_wrist_apose $T/hands/staged/
cp $R/body_tools/idle/idle_clips.json $R/body_tools/idle/body_showcase.json $T/body_tools/idle/ 2>/dev/null || true
for v in apose tpose left right back; do mkdir -p $T/body_tools/work/hairless_division_staged/$v; cp -r $R/body_tools/work/hairless_division_staged/$v/live_patch_staged $T/body_tools/work/hairless_division_staged/$v/; done
cp $R/body_tools/work/hairless_division_staged/apose/hand_mask.png $T/body_tools/work/hairless_division_staged/apose/
# hair, in order: speck_fix -> ear_strands (apose) -> lineart_fix Job D (png + rig.json) -> merged apose strand_04
for v in apose tpose left right back; do
  for st in $R/hair/staged/speck_fix/views/$v/hair $R/hair/staged/lineart_fix/views/$v/hair; do [ -d $st ] && cp $st/* $T/views/$v/hair/ ; done
  [ $v = apose ] && { cp $R/hair/staged/speck_fix/views/apose/hair/* $T/views/apose/hair/; cp $R/hair/staged/ear_strands/apose/views/apose/hair/* $T/views/apose/hair/; cp $R/hair/staged/lineart_fix/views/apose/hair/* $T/views/apose/hair/; cp $R/hair/staged/merged/apose/hair/strand_04.png $T/views/apose/hair/; }
  cp $R/body_tools/work/hairless_division_staged/$v/live_patch_staged/base_body.png $R/body_tools/work/hairless_division_staged/$v/live_patch_staged/base_body_skin.png $T/views/$v/
done
cp $R/hands/staged/f7_wrist_apose/L_palm.png $R/hands/staged/f7_wrist_apose/R_palm.png $T/views/apose/hands/
if [ "$2" = round2 ]; then cp $R/body_tools/work/round2_staged/skin.json $T/views/right/body/skin.json; cp $R/body_tools/work/round2_staged/base_body_underlay.png $T/views/right/base_body_underlay.png
  cmp $R/body_tools/work/round2_staged/with_specks/base_body_skin.png $T/views/right/base_body_skin.png; fi
n=$(find $T -type l | wc -l); echo "symlinks in tree: $n"; [ $n = 0 ]
