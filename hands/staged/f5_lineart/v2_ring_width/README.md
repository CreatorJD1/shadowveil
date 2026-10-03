# F5 v2_ring_width: back Ring1 curl-frame width fix (staged, not live)

Status: **PASS.** Both the 1 px hand-scale gate and all of F5's own checks pass, at linear and at ss2.
- Built 2026-10-03, 02:20–02:47 PT.
- Originals are kept unchanged: `../back`, `../tpose` and `../README.md` (F5 v1).

## Why
F5 v1 (`../back/{L,R}_Ring1_f1.png`) filled partial-alpha and hole px opaque with her skin. That added a 1–2 px opaque strip along the Middle-side edge of Ring1. The hand scale audit (hands/qa/scale_audit) measured the Ring1 median segment width vs the live curl frame at **L +1.34 / R +2.24 px**, which fails the 1 px gate.

## What changed vs v1
Only `back/L_Ring1_f1.png` and `back/R_Ring1_f1.png` differ. Every other file is a byte copy of v1 (`back/*`, `back/rig.json`, `tpose/*`).
- **Kept:** all of F5's fills on px that already carry her anti-alias alpha. These are flattened as `a*her_rgb + (1-a)*her_skin(180,120,77)`, and the skin colour is the mode of her own back-view Ring1 art.
- **Re-added greedily, nearest her silhouette first:** F5's fully new skin px, but only while the Ring1 median chord AND the max width stay ≤ 0.95 px over the live f1, and the reach is unchanged. This used `tools/greedy.py`.
- **Dropped (reverted to her live RGBA):** L 7 px, R 8 px.
- **Colour provenance:** every px in the v2 files equals either her live px or F5 v1's px at the same position. That is 0 px of new colour; the per-file counts and positions are in `back/v2_log.json`.

## Results (real rig, my server on 127.0.0.1:8779, md5 served == disk before each render)
- **Rig version:** live rig/index.html was 00892ccb, then changed to **562c32a7** at 02:38 PT, during this work. The only difference is an opt-in `?armsub=1` path.
  - The live, v1 and v3 renders made at 00892ccb are pixel-identical (0 px, all 11 cases, linear and ss2) to the same configs at 562c32a7.
  - The final checks below were run on 562c32a7.

| check | live f1 | F5 v1 | **v2** | gate |
|---|---|---|---|---|
| L_Ring1 median segment width Δ vs live f1 | 0 | +1.34 | **+0.45** | ≤ 1 → PASS |
| R_Ring1 median segment width Δ vs live f1 | 0 | +2.24 | **+0.90** | ≤ 1 → PASS |
| L/R_Ring1 max width Δ | 0 | +1.34/+1.35 | **+0.90/+0.90** | ≤ 1 |
| L/R_Ring1 reach Δ | 0 | 0 | **0** | |
| line-art breaks (lineart.py) | 0 | 0 | **0** | 0 |
| line width fails (\|dw\|>1 px) | 2 | 0 | **0** | 0 |
| new corners | 0 | 0 | **0** | 0 |
| pivot holes/tears/partial \| hand holes/tears/partial | 16/17/29 \| 149/365/83 | 13/13/6 \| 47/340/9 | **13/13/6 \| 47/340/27** | ≤ live |
| Fist/Point/Peace max Δ (pivot_qa) | – | 0 | **0** | ≤ 2 |
| rest px diff vs live (linear / ss2) | – | 0 / 0 | **0 / 0** | 0 |
| verdict.py (back, linear / ss2) | – | PASS / PASS | **PASS / PASS** | |

- **Trade-off:** hand_partial goes from 9 (v1) to 27 (v2); live is 83. These are the px where F5 v1's widening strip used to cover soft edges at curl 0.13/0.2. The v1 → v2 render diff is small: 11/11/2 px at curl 0.13/0.20/0.30 (linear), 35/30/8 (ss2), and 0 px elsewhere.
- **Files:**
  - Logs: `checks/` (verdicts, px diffs, qa_*/la_* for live and v2, render md5 log).
  - Before/after crops: `sheets/back_{L,R}_Ring1_v2.png`. Rows are the frame file, curl 0.13 and curl 0.20; columns are live, v1 and v2.

## Install (needs approval; staged only)
    cp hands/staged/f5_lineart/v2_ring_width/tpose/*_f1.png views/tpose/hands/
    cp hands/staged/f5_lineart/v2_ring_width/back/*_f1.png hands/staged/f5_lineart/v2_ring_width/back/rig.json views/back/hands/
