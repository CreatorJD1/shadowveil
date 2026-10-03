# Hair sub-offsets on top of the eye-fit head group (Base Hair, Sat Oct 3 2026, 12:50 AM PT)

**Server and render.**
- Hair's scratch server `127.0.0.1:8780`, root `/workspace/shadowveil`. Served `rig/index.html` md5 is db5cf270…, equal to the file on disk (checked in `work/render_hg.py`). Rendered after 00:27 PT.
- Page: `?view=V&quality=linear&headgroup=1&hairless=1&hlhandcut=0`, with `RigHeadGroup.set` at the eye-fit offsets from `rig/partmesh/staged/headgroup.json`: apose (0,−9), left (0,+11), back (+2,+11), right (+3,+5). These equal the given values.
- The head group was confirmed to be applied: in the render, hair_front sits at exactly (dx,dy) in apose, left and right.

**Hair masks from the render** (`work/<v>_masks.npz`, `work/<v>_rest_hg.png`):
- Visible hair = hair drawn alone (preview solo of every hair item) AND the full frame shows that same px. Body's base_body still carries identical hair copies, so a hide-diff alone misses most of the hair.
- Bun = the same, with the bun soloed.

**Frame side.** Same as `hair/qa/turn_handoff/measure.py` v2: turn frame mapped with Body's `angle_map.json` handoff, blue key, dark-hair classifier, cleanup, ROI. The rig eye exclusion is moved with the head group.

**Score.** Best integer shift (±20 px) maximising IoU. Also reported: mean symmetric edge distance (px) at 0 and after the shift. Hair mass = all visible hair (hair_back + hair_front + strands + bun). "excl. bun" removes the bun window.

## Residual (sub-offset hair needs on top of the head group), view px, +y down
| handoff | head group | hair mass dx,dy | IoU 0 → after | edge dist 0 → after | hair excl. bun | bun dx,dy | bun IoU 0 → after | bun edge dist 0 → after |
|---|---|---|---|---|---|---|---|---|
| f001 apose | 0,−9 | **+1,−1** | 0.863 → 0.888 | 5.45 → 5.33 | +1,0 (0.847) | **+1,−1** | 0.948 → 0.954 | 1.13 → 1.06 |
| f062 left | 0,+11 | −5,−8 | 0.733 → 0.768 | 9.11 → 8.11 | **−10,0** (0.724) | **+14,−10** | 0.806 → 0.903 | 6.76 → 2.28 |
| f109 back | +2,+11 | +1,−3 | 0.847 → 0.850 | 4.81 → 4.69 | **+1,0** (0.864) | **−3,−15** | 0.830 → 0.947 | 5.57 → 1.27 |
| f160 right | +3,+5 | +9,−7 | 0.743 → 0.808 | 7.86 → 5.98 | **+13,−1** (0.746) | **−4,−11** | 0.843 → 0.902 | 4.27 → 2.64 |

**Cross-check.** These equal the 9:20 PM `turn_handoff` offsets minus the head group, to within 1–4 px:
- apose +1/−10 → +1/−1;
- left bun +14/+1 → +14/−10;
- back bun −1/−4 → −3/−15;
- right bun −1/−6 → −4/−11.

## Reading
- **apose f001: about 0.** Hair and bun both need +1/−1. One shared value of 0/0 (or +1/−1) is fine.
- **back f109:** the hair mass needs about +1/0, so 0. **The bun needs a different value, −3/−15.** The frame's bun is drawn higher and taller than the rig's (`overlay_back_f109.png`). A −15 dy fits the top edge, but part of the gap is shape, not just position.
- **left f062:** the mass excluding the bun needs about −10/0. **The bun needs +14/−10.** These point in opposite x directions, so hair and bun need different values.
- **right f160:** the mass excluding the bun needs about +13/−1. **The bun needs −4/−11.** These are different values.
- In the profiles the leftover gap after the best shift is still 6–8 px edge distance, IoU 0.72–0.81. The frame's profile hair is drawn differently, not just shifted, so no single offset fully hides the jump.

**Suggested `sub.hair` block (not written; Coder owns `rig/`):** per frame, `hair` = mass excluding the bun, `bun` = bun.
- apose: hair (0,0), bun (0,0)
- left: hair (−10,0), bun (+14,−10)
- back: hair (+1,0), bun (−3,−15)
- right: hair (+13,−1), bun (−4,−11)

Files: `subofs.json`, `overlay_<view>_f###.png` (orange = frame hair, cyan = rig hair with the head group, magenta = bun), `work/` (`render_hg.py`, `subofs.py`, masks, renders).
