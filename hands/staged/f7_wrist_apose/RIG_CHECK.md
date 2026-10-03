# F7 wrist flaps: check in the real rig (rerun 2026-10-02, 23:36–23:41 PT)

**The earlier run (about 23:05–23:15 PT, port 8765) is superseded.** Port 8765 was serving /workspace/tmpsv_tree, not this repo.

## Setup
- **Server:** my own static server, `python3 -m http.server 8775 --bind 127.0.0.1 --directory /workspace/shadowveil`.
- **Root check:** before each render, the served `rig/index.html` md5 matched the file on disk. It was `ad2e7083397a29f34903b786fe0fb4b4` before and after both runs.
- **URLs:**
  - `http://127.0.0.1:8775/rig/index.html?view=apose&hairless=1&quality=linear`
  - Comparison without the flag: `?view=apose&quality=linear`
  - QUAL was also forced to linear in the page.
- **Server log:** shows the flagged run fetched `hands/staged/f7_wrist_apose/{L,R}_palm.png` and Body's `live_patch_staged/base_body.png`.
- **Palms used:** the current staged palms, after the parent's in-place re-tone of the flap skin to (186,129,86) (`tone_fix_log.json`; originals in `pre_tone/`).
- **Jobs:** each render ran headless Chrome as its own job. The harness's internal port was 8776.
- **Cases:** rest; WristL ±1; WristR ±1; and both wrists at anger 0.14, jump −0.2 / +0.2969, run ±0.12.
- **Metrics:** the same as `hands/work/idle_bend/f7/wrist_sim.py`: a 92 px box at each palm pivot, each case minus that run's rest.
- **Files:**
  - `rig_check.json`
  - `rig_check_sheet.png` (top row without the flag, bottom row hairless)
  - renders in `hands/work/f7rig/{hl2,plain2}/`
  - tools: `hands/work/f7rig/hb_render_q.mjs` and `rigcheck2.py`

## Rest
- Hairless rest vs the rest without the flag: **0 px**.
- Rest vs her drawing (`views/apose/base.png`): 6182 px differ, 799 of them in the hand mask. The largest channel difference in the mask is **4/255**, and 0 px differ by more than 8.
  - The run without the flag gives the same numbers. This is the renderer's linear resampling, not the flaps.
- The flaps are invisible at rest.

## Wrist bends: new vs rest (holes / tears / partial / breaks, Δ line width)

| case | hairless + F7 | no flag (live) | wrist_sim r20 |
|---|---|---|---|
| L +1 | 0 / 2 / 0 / 0, 0.000 | 0 / 2 / 0 / 0, 0.000 | 0 / 1 / 0 / 0 |
| L −1 | 0 / −1 / 0 / 0, 0.005 | 0 / 3 / 0 / 0, 0.000 | 0 / −1 / 0 / 0 |
| R +1 | 0 / 1 / 0 / 0, 0.010 | 0 / 3 / 0 / 0, 0.005 | 0 / 1 / 0 / 0 |
| R −1 | 0 / 3 / 0 / 0, 0.010 | 0 / 4 / 0 / 0, 0.000 | 0 / 2 / 0 / 0 |
| anger, jump, run (L and R) | 0 / −1..2 / 0 / 0, ≤ 0.03 | the same, except two width deltas (L run −0.12: 0.000 vs 0.012; R run −0.12: 0.006 vs 0.012) | 0 / −1..1 / 0 / 0 |

- Hairless + F7: **0 holes, 0 breaks, 0 partial px**, |Δw| ≤ 0.03, and at most 3 new tear px (1-px outline notches).
  - That matches wrist_sim (1–2), and it is slightly better than the run without the flag at ±1 (2–4).
- The run without the flag already does much better than the sim's live baseline (20–29). The real rig fits and softens its own wrist edges.
  - In the real rig the flaps take the wrist from 2–4 notch px to −1..3. There were no wedge gaps to close.
- The flagged and unflagged images differ by about 1575 px at ±1, which is the different draw order and the flap.
  - On the sheet, the flap's 2 px edge line shows as a small bump where hand and forearm meet at L −1 and R +1.
- The numbers equal the superseded 8765 run case for case. The conclusion is unchanged, but only this run counts.
