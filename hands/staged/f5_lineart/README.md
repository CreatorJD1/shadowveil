# F5: line-art fixes (staged, not live)

Status: **PASS for tpose and back, at linear and at 2x (ss2).** apose, left and right are untouched.
Everything was re-verified from scratch on 2026-10-02, 22:18–22:30 PT, rendering straight from this folder as the overlay
(the files were written at 21:22 PT, around the time headless Chrome was killed at about 21:20 PT, so the earlier
results were thrown away). Renderer: the pulled rig/index.html (main 6d5b239), loaded read-only.
Tools are in hands/work/idle_bend/: f5/run_cand.sh (hb_render_main.mjs, then pivot_qa.py, then lineart.py) and f5/verdict.py.

## Files
- `tpose/L_Ring1_f1.png`, `tpose/R_Ring1_f1.png`, plus `edit_log.json`.
  - Ring1 frame 1: the top knuckle filler blob is trimmed (L 18 px plus 2 speck px, R 12 px).
  - The bottom flat-skin skirt is kept, because trimming it opens holes at curl 0.3 to 0.87.
  - The skirt's exposed outer edge gets her line colour: outer px (53,25,15) on L and (51,26,25) on R, inner px (86,50,32) on L and (84,50,40) on R.
  - Alpha is kept. Two alpha-255 skin anchor px per side keep the frame bounding box unchanged (the renderer crops to the alpha bbox).
  - Changed px: L 81, R 89.
- `back/{L_Index1,L_Middle1,L_Pinky1,L_Ring1,R_Middle1,R_Ring1}_f1.png`, `back/rig.json`, `back/fill_log.json`.
  - rig.json: the back finger frame lists become [f0,f1,f1,f1,f2].
  - Partial-alpha and hole px at curl 0.13/0.2 are filled opaque in the frame-1 base with her skin (180,120,77). Counts (flattened/added): L_Ring1 24/22, L_Pinky1 4/2, L_Middle1 10/5, L_Index1 2/1, R_Ring1 23/17, R_Middle1 4/0.
- `sheets/{tpose,back}_{L,R}.png`: before/after crops. Top row is live, bottom row is staged.

## Numbers (L+R summed over 10 cases: rest, curl 0.13/0.2/0.3/0.5/0.7/0.87/1.0, Fist, Point, Peace)
Totals are pivot holes/tears/partial | hand holes/tears/partial.

| view | quality | live | staged | line-art breaks | width fails | new corners | verdict |
|---|---|---|---|---|---|---|---|
| tpose | linear | 12/46/80 \| 141/583/264 | 12/42/80 \| 141/577/264 | 26 -> 0 | 0 -> 0 | 1 -> 0 | PASS |
| tpose | ss2 | 12/46/80 \| 141/583/264 | 12/42/80 \| 141/577/264 | 26 -> 0 | 0 -> 0 | 1 -> 0 | PASS |
| back | linear | 16/17/29 \| 149/365/83 | 13/13/6 \| 47/340/9 | 0 -> 0 | 2 -> 0 | 0 -> 0 | PASS |
| back | ss2 | 16/17/29 \| 149/365/83 | 13/13/6 \| 47/340/9 | 0 -> 0 | 2 -> 0 | 0 -> 0 | PASS |

Full-frame px diff, live vs staged (criterion: Fist/Point/Peace at most 2 px):

| view | quality | rest | Fist | Point | Peace | curl 0.2 (intended change) |
|---|---|---|---|---|---|---|
| tpose | linear | 0 | 0 | 0 | 0 | 254 |
| tpose | ss2 | 0 | 0 | 0 | 0 | 327 |
| back | linear | 0 | 0 | 0 | 0 | 8078 |
| back | ss2 | 0 | 0 | 0 | 0 | 8115 |

- rig/rest_check.py was run on a fresh scratch root (/workspace/scratch/f5v/root_f5) with rig/ files copied, views/*/hands copied, and this folder laid over the top.
  - Result: total 0 in all 5 views (apose, tpose, left, right, back), 0 in the hand mask, no missing frames, no finger-frame problems.
- hands/work/masks.md5: 5/5 OK.
- No live file changed.

## Install (needs approval; this folder is staged only)
    cp hands/staged/f5_lineart/tpose/L_Ring1_f1.png hands/staged/f5_lineart/tpose/R_Ring1_f1.png views/tpose/hands/
    cp hands/staged/f5_lineart/back/*_f1.png hands/staged/f5_lineart/back/rig.json views/back/hands/

If F6 (hands/staged/f6_overlap) is installed as well, its R_Ring1_f1.png is byte-identical to the one here.
