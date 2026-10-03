# T-pose eye-corner strand ink (STAGED ONLY), Base Hair, 12:36 AM PT

Same method as `../apose/`: hair pixels are copied unchanged from `views/tpose/base.png` into the **static** `hair_front` (layer 600, swayWeight 0, swayY 0). There is no new paint, and nothing in views/ or rig/ was written.

- **Start file:** `hair/staged/lineart_fix/views/tpose/hair/hair_front.png`, the one the ?hairless=1 set loads for tpose. The 68 target px were all alpha 0 in it.
- **Pixels:** exactly the 68 px Eyes trimmed from the tpose lock, i.e. `tpose_eye_brow_lock_v1.png` minus `tpose_eye_brow_lock.png` (3,425 px):
  - image-left corner: **39 px** at x618–622, y206–226;
  - image-right corner: **29 px** at x744–746, y209–219.
- **Exclusions:** 0 px are in the eye lock, 0 px in `mouth/handoff_hairless/tpose_mouth_lock.png`, and the 3 lash px at x741 y209–211 are left out.
- **Colours:** 68 distinct colours, all exact base.png pixels, all alpha 255, 0 chroma.

**For Body (`for_base_body/`):**
- `tpose_eye_corner_px.json`: x, y, group, part, rgba.
- `tpose_eye_corner_mask.png`: white = px.
- `tpose_eye_corner_px.png`: the RGBA of those px.

Turn these px to flat skin (186,129,86,255) in base_body.png and base_body_skin.png. hair_front covers them.

## Checks
Rest was simulated with `work/restsim.py` in the scratch overlay `/tmp/hltp` (mk_overlay `--lineart --no-clear`, files copied with the destination removed first, no links under rig/).

| body | tpose rest |
|---|---|
| live body | 23 px, identical with the old hair_front |
| Body's staged tpose copies (+ tone_fix hair_back) | **0 px** |
| Body's staged copies with the 68 px turned to (186,129,86) | **0 px** |

- The 23 px in the live-body case are the known speck_fix px double-composited over the uncleared live body. My change adds 0 px.
- **Line art:** the rest composite is pixel-identical before and after, and hair_front is static and drawn above the body, so these strokes render with the same px in every sway pose. Width change is 0 px.
- **Not covered:** in Body's 2 boxes (x615–624 / x743–748), 113 more dark px remain in `hairless_tpose.png`. They are not in the lock and not in this cut, and are mostly the face/eye contour columns x617–621 and x744–748. They are left as body; Body/Eyes to confirm.

## Update, 1:10 AM PT Oct 3: added the 113 extra px (Eyes + Body confirmed they are hair strands)
- `views/tpose/hair/hair_front.png` now holds **181 px**: the 68 px above plus **113 px** of strand columns: L 52 px at x617–621, y192–207; R 61 px at x744–747, y192–207. All are exact base.png copies with alpha 255.
- The 113 px are the dark px (max RGB < 120, a stable plateau from 114 to 120) of `hairless_tpose.png` inside Body's keep_boxes. The eye lock, the 68-px cut, Body's `face_lock_mask` and the lash px x741 y209–211 are removed. 0 px are in the eye or mouth lock.
- The 68-only version is backed up as `views/tpose/hair/hair_front_68only.png`.
- **For Body:**
  - `for_base_body/tpose_eye_corner_px_combined.json` lists every px with its `set` (68_lock_trim / 113_extra).
  - The matching mask is `..._mask_combined.png` and the px are in `..._px_combined.png`.
  - Turn all 181 px to (186,129,86,255) in base_body + base_body_skin.
- **Rest checks** (`work/restsim_combined.py`, overlay `/tmp/hltp` now all real copies, no links):

  | body | tpose rest |
  |---|---|
  | Body's staged tpose copies | **0 px** |
  | the same, with the 181 px turned to (186,129,86) | **0 px** |
  | live body | 23 px, the known speck baseline, unchanged |

- **Other checks:** 0 off-palette colours, 0 chroma, the file is unchanged outside the 181 px, and line art is unchanged (rest composite equals the target).
- Script: `work/stage_combined.py`.
