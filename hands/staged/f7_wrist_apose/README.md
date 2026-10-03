# F7 – A-pose wrist flaps (staged, not live)

Files: `L_palm.png`, `R_palm.png` (full canvas, replace `views/apose/hands/{L,R}_palm.png`), `flap_log.json`,
`metrics_live.json`, `metrics_r20.json`, `before_after_bend1.png` (top = live, bottom = staged; L+1, L-1, R+1, R-1).

Flap: her skin (186,129,85) added to each palm on the forearm side of the wrist line (Body's `wrist_line_{L,R}.json`),
radius 20 px round the palm pivot, only where Body's staged forearm piece is alpha 255, outside `hands/apose_hand_erase_mask.png`,
with a 2 px outer edge in her apose line colour (13,11,29). L 529 flap px (138 line px), R 505 (134 line px).
0 px changed inside the hand erase mask; 0 flap px outside opaque forearm.

Sim: `hands/work/idle_bend/f7/wrist_sim.py` – Body's staged pieces (body_tools/work/hairless_division_staged/apose), hand under forearm,
rigid wrist rotation = Wrist value x 25 deg about the palm pivot, bilinear premultiplied. Metrics in a 92 px box at the wrist, relative to rest.

| case | live new tears / breaks / holes | staged r20 new tears / breaks / holes | staged dw |
|---|---|---|---|
| L +1 (25 deg) | 29 / 20 / 1 | 1 / 0 / 0 | 0.037 |
| L -1 | 20 / 16 / 0 | -1 / 0 / 0 | 0.063 |
| R +1 | 27 / 18 / 0 | 1 / 0 / 0 | 0.041 |
| R -1 | 21 / 17 / 1 | 2 / 0 / 0 | 0.034 |
| action values (anger 0.14, jump -0.2/+0.2969, run +-0.12) | -1..1 / 0 / 0 | identical to live | <= 0.024 |

Rest: 0 px diff vs `hairless_apose.png` (hand under forearm).
Remaining 1-2 px at +-1 are single anti-aliased (alpha ~100) notches on the outline where hand and forearm contours meet, not wedge gaps
(see sheet). Tries: r20 (best), r26, r20+3px line, r22, r17 – larger flaps add notches and line width, r17 reopens wedges (7-8 px).

CAVEAT: this only holds when the hand draws UNDER the forearm (Body's staged layer order). The live apose rig.json note says
"palm draws above the forearm"; in that order the flap is visible at rest (1034 px rest diff). Do not install until the draw order is settled.

Install (only after approval and order change): `cp hands/staged/f7_wrist_apose/{L,R}_palm.png views/apose/hands/`
