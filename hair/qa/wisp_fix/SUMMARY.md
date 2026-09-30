# Base Hair: tpose wisp underfill (done) + speck erase-mask proposal (on hold)

Run 2026-09-30, about 03:40 to 04:20 PT. Heavy jobs (rest check, validator, the two headless renders) ran one at a time.

## Task 1: tpose wisp underfill. DONE
- **Change:** `views/tpose/hair/hair_back.png` (id `hair_back`, layer 100, static). I added **320 opaque px**: the wisp mask `hair/tpose_eye_crossing_wisp_mask.png` (40 px, bbox x622-638, y194-212), grown by a radius-3 disk.
  - Colours are sampled from `base.png`. Off-wisp pixels use `base.png` as it is (skin, lid/lash line, eye corner).
  - Each of the 40 wisp pixels (hair colour in base) takes the nearest non-wisp `base.png` pixel. No colour was invented.
  - Chroma-rule px: 0. White px: 0.
- **Hidden at rest:** the stack above `hair_back` (skin, eyes, mouth, hands, other hair), rendered without `hair_back`, is alpha 255 on all 320 px (0 dropped). `rest_check.py`: 0 px in every view.
- **Backup:** `hair/backups/wisp_fix_20260930/tpose_hair_back.png` (sha256 0a78af8b…).
- **Validator (`hair/validate_hair.py`, Base Hair's own tool) needed two narrow rule fixes.** The backup of the original is in the same folder. Without these fixes the fill fails on rule artefacts, not on real defects:
  1. `hair_back_under_soft_px`: static hair parts drawn above `hair_back` (layer ≥200, i.e. `hair_front`'s alpha-255 wisp) now count as "above". Before the fix: 40 px flagged, all on the wisp, where `hair_front` is alpha 255.
  2. `rest_overlap`: a static part below the eye band (swayWeight 0, layer <400) can't cover a face part. Its pixels next to the eyes are now reported as `under_face_static_px` instead. tpose `hair_back`: 94 px. They sit **under** the eye parts, as the fill is meant to.
- **Result:** ALL PASS in five views.

### Smoothed re-render (real renderer, `rig/previews/idle/harness/render_idle.mjs`, same seed 20260938) → `render/`
Measured in the wisp area (wisp mask + 2 px, with head motion compensated from the per-frame head bone, root motion included). "Before" is the v1 frames; "after" is the re-render.

| clip | frames with alpha<255 at wisp | max px/frame | min alpha | fully transparent |
|---|---|---|---|---|
| tpose idle, before | 228/240 (every soft frame) | 54 (f20, t=0.700 s, head +0.163°) | 184 | 0 |
| tpose idle, after | **0/240** | **0** | **255** | 0 |
| keys_idle_weight_shift_tpose, before | 240/240 | 54 (f2); f183 = 53 at the worst head angle −3.757° | 185 | 0 |
| keys_idle_weight_shift_tpose, after | **0/240** | **0** (f183: 0) | **255** | 0 |

- tpose idle: after the fix, frames are identical to v1 outside the fill region (0 px differ). So the only change is the underfill.
- weight_shift: the current renderer differs from v1 elsewhere (about 35-70k px/frame, from v1.8 root motion and body work in progress; the head sits about 11 px lower). The wisp numbers use each render's own head transform.
- Data: `data_tpose_idle_wisp.json`, `data_keys_idle_weight_shift_tpose_wisp.json`.
- Crops (8×, on #0000FF, plus alpha maps where red means <255):
  - `crops/wisp_tpose_idle_f20_before_after.png`
  - `crops/wisp_keys_idle_weight_shift_tpose_f183_before_after.png`
  - `crops/wisp_rest_hair_back_before_after.png`
  - The few red px at the left edge of the f20 "after" tile are the ordinary `hair_front` outline seam (see the idle_battle "Seams" finding). They are outside the wisp area.

### Hair over eyes/mouth
- The only file that changed is layer 100, which draws under the eyes and mouth.
- Validator sweep: `rest_overlap` {} and sway `overlap_px_at_final` 0 in all views.
- Hair parts at layer ≥600 are unchanged, so **0 new px over eyes or mouth**.

## Task 2: specks. ON HOLD (steering). Proposal only, nothing applied
- Nothing was changed: hair erase masks, `base_body.png`, skins and strands are untouched (checked by sha).
- **How the mask is used:** the renderer never applies the hair erase mask. It only uses it for the preview overlay and the motion-quality stats. Base Body bakes it into `base_body.png` and the skins (`body_tools/clear_hair.py`, dilated 3 px, with skin fill). So a mask edit has no effect until Base Body rebuilds.
- **Proposal:** in `erase_mask_proposal/`:
  - `<view>_hair_erase_mask_ADD.png`: the pixels to add.
  - `<view>_hair_erase_mask_PROPOSED.png`: current mask OR add.
  - `proposal.json`: the criteria, plus `[x,y]` per nearest strand.
  - `speck_sites.json`: one entry per crop site.

| view | px | per strand (px) |
|---|---|---|
| apose | 58 | strand_01 24, strand_03_tip 13, strand_05 6, strand_06_tip 6 (incl. (752,321), (750,326), (751,327), (750,338)), strand_07 5, strand_02 4 |
| tpose | 54 | strand_01 17, strand_03 10, strand_06_tip 10, strand_06 9, strand_02 8 |
| left | 68 | strand_01 68 (46 isolated = the QA count) |
| right | 23 | strand_04 23 (12 isolated = the QA count) |
| back | 210 | strand_04 75, strand_02 73, strand_05 33, strand_01 29 |

The bun is excluded (it moves ≤0.45 px).

- **Blocker: the mask alone can't express this fix.**
  1. `validate_hair` requires the erase mask to equal the union of the swaying parts and to be fully covered at rest. Erasing these pixels from `base_body` with nothing covering them would break rest.
  2. So they would also have to be cut into their strands from `base.png`. But **410 of the 413 px fail the parts' chroma check** (b>r+40 and b>g+40). They are navy hair pixels, e.g. (5,6,52), and that is why the strand cuts dropped them.
  3. So this needs a decision, not just a mask edit. Either:
     - allow exact `base.png` copies past the chroma tolerance in hair parts, then add the pixels to both the strand and the mask; or
     - Base Body keeps or recolours them.
- **Simulation (scratch copies in `work/sim/`):** specks cleared from a scratch `base_body` and pasted into the nearest strand.
  - Rest is identical to the current stack (0 px, Python mirror) in all five views.
  - At max sway (s=±1) the left-behind speck px drop to 0. Before, for example: back strand_04 50/49, back strand_02 53/42, left strand_01 33/33, apose strand_01 21/23.
  - Running `clear_hair.py` (R=3) with the proposed mask would newly clear only 0-1 extra opaque `base_body` px per view. Underfill need is about nil.
- Crops `crops/speck_<view>_<strand>_<x>_<y>.png`: rest | before s=−1 | before s=+1 | proposed s=−1 | proposed s=+1, 6× on #0000FF.
  - These are Python-mirror stills at max sway (`hair/tools/render.py`, with `base_body.png`), not renderer frames.
  - apose f127 and back max sway were **not** re-rendered, because nothing was applied.

## Files
- **Changed:**
  - `views/tpose/hair/hair_back.png`
  - `hair/validate_hair.py` (two rules, see above)
  - `hair/validation.json` (validator output)
- **Backups:** `hair/backups/wisp_fix_20260930/`, holding `tpose_hair_back.png`, `validate_hair.py` and `validation.json`.
- **Scripts:** in `work/`:
  - `make_fill.py`
  - `above_alpha.py` (a tpose-only copy of `rest_check.py` without `hair_back`)
  - `wisp_frames2.py`
  - `wisp_crops.py`
  - `find_specks.py`
  - `speck_crops.py`
- **Logs:** `work/validate_before.txt`, `work/validate_after.txt`, `work/rest_after.json`.
