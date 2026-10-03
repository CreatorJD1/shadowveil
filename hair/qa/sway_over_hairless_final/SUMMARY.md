# Sway-over-hairless see-through, FINAL set: RERUN (Sat Oct 3 2026, 1:00 AM PT)

**This supersedes the 11:16 PM PT run.** That run was captured through port 8765, which was serving `/workspace/tmpsv_tree` rather than shadowveil. Its outputs are kept unchanged in `invalid_port8765/`.

**Server:** Hair's own scratch server, `python3 -m http.server 8780 --bind 127.0.0.1 --directory /workspace/shadowveil`.
- Before each view, the served `rig/index.html` md5 was checked against the file on disk (see `work/render*.log`).
- Coder's index.html had a syntax error from 00:06 to 00:22 PT, and its final version is md5 db5cf270…. Every view whose first render used another md5 (ad2e7083… / 040a0949…) was re-rendered at 00:43–00:57 PT. **All five views and all variants were rendered with db5cf270…** (`work/render4.log`, `render5.log`; per-file md5s in `work/<v>_meta.json`). The numbers matched the earlier passes exactly.
- Every served PNG/JSON was md5-compared to the shadowveil file on disk at capture and again after analysis: 0 mismatches, 0 changed since. Per-file md5s are in `work/<v>_meta.json`.

**Set rendered with `?hairless=1&hlhandcut=0`:**
- Body's re-toned `live_patch_staged` base_body/base_body_skin (apose/tpose 23:19, left/right/back 00:09 PT). The hand cut is baked in, so there is no in-memory cut.
- Hair, in order: speck_fix → ear_strands (apose) → hairfront_holes → lineart_fix Job D → merged apose strand_04 → tone_fix hair_back (apose, tpose, right, back).
- Eyes and mouth are live.
- Spring preset A. The 10 s auto run peaks at a drive of only 0.26–0.34.
- The `hlnofix` variant (apose/right) swaps hair_front back to the pre-fix file by Playwright request interception. Live files are never edited.

**Method:** the same as before (`work/render.py`, `analyze.py`, `classify.py`, `holes_eyecorner.py`).
- Poses: X ±1 × Y{0,±1}, Y ±1, and preset-A whips (14 sway poses + rest).
- See-through = px inside the rest silhouette (base.png alpha ≥ 250) that render with alpha < 250.
- NEW = see-through in hairless but not in live.

## Rest
0 px in all 5 views, live and hairless (in-page Check PASS).

## Table (worst pose per view)
| view | pose | live | hairless | NEW | real holes (inside static silhouette) | NEW chroma |
|---|---|---|---|---|---|---|
| apose | sx−1 | 696 | 755 | 62 | 0 | 0 |
| tpose | sx+1 | 344 | 380 | 36 | 0 | 0 |
| left | sx+1 sy+1 | 86 | 99 | 24 | 0 | 0 |
| right | sx+1 | 72 | 84 | 14 | 0 | 0 |
| back | sx−1 | 146 | 248 | 107 | 0 | 0 |

- All NEW px (100%) lie outside the static silhouette. They are background behind the trailing edge of hanging strands, where the live base_body still has a frozen hair copy. This is the expected hairless behaviour. Overlays: `overlay_<v>.png` (red = new, yellow = both, cyan = live only).
- NEW enclosed px at most: apose 14 (sy+1), back 5, tpose/left/right 2.

## hairfront_holes (`hair/staged/hairfront_holes/verify_sway.json`)
- apose (604,129) is open in 11 of 15 poses without the fix and 0 with it. right (780,169) is open in 13 without and 0 with.
- The fix changes only that 1 px per frame and makes 0 px newly see-through.

## A-pose eye-corner region x612–619 / x746–752, y214–238 (`eyecorner_apose.json`)
- Body changed 223 px (L 90, R 133), all now flat skin (186,129,86). That colour is in base.png, so it is from her palette.
- 0 partial alpha, 0 chroma, 0 isolated specks. base_body equals base_body_skin there.
- hair_front is alpha 255 on all 223. In all 15 poses the hairless frame equals live on 223/223 px, with 0 skin px showing and 0 px at alpha < 255.
