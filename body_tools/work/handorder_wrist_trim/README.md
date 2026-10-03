# Handorder wrist trim (Base Body, STAGED, Sat Oct 3 2026 PT) - RESULT: FAIL, do not promote
Trimmed copies of hairless_division_staged/<view>/live_patch_staged/base_body_skin.png (alpha 0 at Coder's diff px from rig/work/handorder/ho_pts.json):
left 53 px (rows 852-853, x 656-703), right 24 px (rows 856-857, x 687-705); apose/tpose/back are unchanged copies. Originals: backup_originals/<view>/. trim_report.json.
Load: ?hairless=1&handorder=1&hlbody=../body_tools/work/handorder_wrist_trim/{view}/ (browser rig md5 562c32a7 on scratch copy tree, port 8773).
- Rest: left 53 -> 0, right 24 -> 0; apose/tpose/back 0; default (no flags) 0 in all 5 and loads no staged files.
- FAIL 1: the rig's underlay gate then REJECTS the skin underlay ("rest footprint touches 53 / 24 transparent px"), so ElbowL+-1 opens 7577 / 7902 new hole px (left), ElbowR+-1 8296 / 8011 (right).
- FAIL 2: wrist bend alone opens new holes at the wrist: left WristL+1 55, WristL-1 35; right WristR+1 63, WristR-1 4.
- FAIL 3 (rule): all 53 + 24 trimmed px lie inside hands/<view>_hand_erase_mask.png (locked mask). 0 px on Hands' F11 flap px, eye/mouth/hair locks not near.
Metrics: render_metrics.json; sheet: sheet_wrist_trim.png. Needs Coder (draw order / underlay gate) or Hands; Body cannot fix this alone.
