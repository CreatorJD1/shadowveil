# hair_front hole fills (STAGED ONLY, not live), 11:20 PM PT

Two 1 px holes opened in static hair at sway in the ?hairless=1 final set (`hair/qa/sway_over_hairless_final/SUMMARY.md`, diagnosis b). In each case, a navy speck px that speck_fix moved into a swinging strand had been cleared from base_body by Body, as requested. Fix: copy the same base.png px into the static hair_front, which is layer 600, under the strands. One px per view. It is an exact base.png RGBA copy, with no new paint. Details are in `px.json`.

| view | px | RGBA (from base.png) | start file | output | strand above it |
|---|---|---|---|---|---|
| apose | (604,129) | 0,24,70,255 | hair/staged/ear_strands/apose/views/apose/hair/hair_front.png | apose/hair/hair_front.png | strand_02 (layer 604) |
| right | (780,169) | 4,4,88,255 | views/right/hair/hair_front.png (live; the hairless set has no right hair_front override) | right/hair/hair_front.png | strand_04 (layer 610) |

**Load order for the Coder (HAIRLESS_HAIR):**
- apose: speck_fix → ear_strands → **hairfront_holes** → lineart_fix → merged. Map `../views/apose/hair/hair_front.png` → `../hair/staged/hairfront_holes/apose/hair/hair_front.png`, replacing the ear_strands entry. The file already contains the ear_strands crescents. lineart_fix and merged do not touch apose hair_front.
- right: add `../views/right/hair/hair_front.png` → `../hair/staged/hairfront_holes/right/hair/hair_front.png`. No other staging touches right hair_front.

**Verification:**
- Rest: `rig/rest_check.py` in the scratch overlay `/tmp/hlfinal` (final body files plus the full hair set plus these two files, each copied with the destination removed first, no links under rig/) gives 0 px in all 5 views. In-page Check: PASS 0 px for apose and right.
- Sway (`verify_sway.json`): renders of the `?hairless=1` page with these files swapped in by request interception (live index.html untouched), over 15 poses (rest, X±1 × Y{0,±1}, Y±1, preset-A whips).
  - The hole px is alpha 255 in every pose. Before the fix it was alpha 0–241 in 11 apose poses and 13 right poses.
  - Only that 1 px changes in each frame, and 0 px become newly see-through. NEW-vs-live goes down by 1 in each affected pose (apose max 63 → 62, right 15 → 14).
- Eye and mouth locks (`eyes/handoff_hairless/*lock*.png`, `mouth/handoff_hairless/*lock*.png`): 0 px touched, and 0 lock px within 2 px of either fill.
- Live `rig/rest_diff_*.png` md5s and `git status` of rig/ and views/ are unchanged.

**Rerun (Oct 3, 1:00 AM PT; supersedes the sway check above, which went through port 8765 serving tmpsv_tree):**
- Server: Hair's own `127.0.0.1:8780`, root `/workspace/shadowveil`, index.html md5 db5cf270. The page is `?hairless=1&hlhandcut=0`, which maps these files itself.
- Pre-fix comparison: hair_front swapped back by request interception.
- Result: the hole is open in 11/15 apose poses and 13/15 right poses without the fix, and 0 with it. The fix changes only that 1 px per frame and makes 0 px newly see-through. Data: `verify_sway.json`.
