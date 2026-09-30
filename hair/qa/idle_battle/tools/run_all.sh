#!/bin/bash
# Sequential (one decoder at a time). Clip list accepts v1 idle_breathe and v2 idle_arm_sway; missing inputs are skipped.
cd "$(dirname "$0")"
I=/workspace/shadowveil/rig/previews/idle
CLIPS="idle_breathe idle_arm_sway idle_weight_shift idle_arm_settle"
VIEWS="apose tpose left right back"
run(){ # name video view
  if [ -f "$2" ] && [ -f "$I/frames/$1/meta.json" ]; then python3 analyze.py "$1" "$2" "$3" || echo "FAIL $1"; else echo "SKIP $1 (missing video or meta)"; fi; }
for v in $VIEWS; do run $v $I/${v}_idle.mp4 $v; done
run apose_hair_stiff $I/apose_idle_hair_stiff.mp4 apose
run apose_hair_middle $I/apose_idle_hair_middle.mp4 apose
for c in $CLIPS; do for v in $VIEWS; do run keys_${c}_${v} $I/keys/${c}_${v}.mp4 $v; done; done
echo ALLDONE
[ -f $I/idle_all.mp4 ] && python3 analyze_composite.py $I/idle_all.mp4 idle_all '[""]'
ROWS=()
for c in $CLIPS; do
  if [ -f $I/keys/${c}_all5.mp4 ] && [ -f $I/frames/keys_${c}_apose/meta.json ]; then
    python3 analyze_composite.py $I/keys/${c}_all5.mp4 ${c}_all5 "[\"$c\"]"; ROWS+=("\"$c\"")
  else echo "SKIP ${c}_all5"; fi
done
# idle_keys_all rows are assumed to follow the clip order above (verified for v1 with tileorder.py)
if [ -f $I/keys/idle_keys_all.mp4 ] && [ ${#ROWS[@]} -gt 0 ]; then
  R=$(IFS=,; echo "${ROWS[*]}"); python3 analyze_composite.py $I/keys/idle_keys_all.mp4 idle_keys_all "[$R]"; fi
echo COMPDONE
python3 alpha_seams.py; python3 clearance.py; python3 aggregate.py; python3 sheet.py
echo FINISHED
