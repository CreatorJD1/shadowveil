# F10: T-pose wrist flaps (staged)

Status: **PASS** in the real rig on 0 holes, 0 breaks, rest 0 px, Fist/Point/Peace 0 px and line width. Two caveats are under "Rig check".

## What it is
- Files: `L_palm.png` and `R_palm.png`, with the flap added under the forearm past Base Body's tpose wrist lines.
  - Wrist lines: `body_tools/work/hairless_division_staged/tpose/wrist_line_{L,R}.json`. L x=1177, y 386–417; R x=188, y 385–417. Pivots (1177,400) and (188,400).
- Method (same as F7, `make_flap_t.py` = F7's make_flap.py pointed at tpose):
  - Flap px sit on the forearm side of the line, within radius 20 of the pivot.
  - They lie under Body's forearm piece where it is alpha 255, are transparent in her live palm, and are outside `hands/tpose_hand_erase_mask.png`.
  - Connectivity: flap | hand mask | palm alpha>0.
  - Fill: skin exactly **(186,129,86)**. The flap's outer boundary gets a 2 px line in **(13,8,21)**. That is her own tpose palm outline px (top edge, R x=191), and it exists in views/tpose/base.png. Her interior palm creases (53,25,15) are not in base.png, so they were not used.
- Size: L 388 px (143 line), R 363 px (136 line). 0 px changed where her live palm is opaque, 0 inside the hand mask.
- Colours: every new opaque colour is in views/tpose/base.png.
- R_Middle: her untouched live PNGs were used in every render. No F9 trims anywhere.

## Rig check (real rig, renders 2026-10-03 00:35–00:41 PT)
**Why a scratch copy of the renderer.** Live rig/index.html puts the hands under the forearm only for **apose** (`hairlessOrder`: `vw!=='apose'` returns). In tpose the hands draw above the body skin mesh, so any flap shows: 566 px at rest in a plain render.
- I therefore rendered with a **scratch copy** of rig/index.html, md5 db5cf270…, the same as live at render time.
- The copy is in `/workspace/scratch/f10rig/rig/`, diff in `scratch_rig_patch.diff`. It does three things:
  1. extends the hairless hands-under-forearm order (hands 300–335 → 210–219) to tpose;
  2. maps the tpose palms to this folder (`?f10=1`, `&f10dir=`);
  3. sets the hairless status text.
- rig/ itself was not edited. **For this to work live, Coder needs the same tpose extension in `hairlessOrder` plus the palm mapping.**

**Setup**
- `hb_render_f10.mjs`: the F7 harness plus a check that the served rig/index.html md5 equals the file on disk. Every run matched; it aborts otherwise.
- In-process server on 8777, rooted at /workspace/shadowveil with `--rigroot` for the scratch index.
- URL: `?view=tpose&hairless=1&quality=linear` (control) vs `&f10=1`.
- Body's tpose `live_patch_staged/base_body*.png` were used, with the hand cut baked in.

**Results** (control = the same rig with hands under the forearm and her live palms; per-case metrics in `rig_check.json`, sheet in `rig_check_sheet.png`):
- Rest vs control: **0 px**. Rest vs base.png in the hand mask is the same as the control (816 px, from Body's staged skin).
- Fist / Point / Peace vs control: **0 px** each.
- Wrist ±1, anger 0.14, jump −0.2/+0.2969, run ±0.12, both sides:
  - **holes 0, breaks 0** in every case (control 0/0);
  - max |Δ line width| 0.03 px.
  - Tears are +1 px in 4 cases (L run+0.12, R wrist ±1, R jump−0.2).
  - Partial alpha is +1…+6 px, all alpha ≥251.

**Warning.** An earlier variant (r20 with 2 px edge erosion, rendered then discarded) gave 6 and 4 new breaks at wrist +1 in the real rig. The scratch sim (`wrist_sim_t.py`) is not a reliable judge of breaks here.

## Alternative: `alt_r20d5_linestrip/`
Depth 5: only a 2 px strip of line colour (L 50 / R 26 px, no skin), because her tpose palm already reaches 3 px past the pivot.
- In the real rig it is closer to the control: tears and holes match the control everywhere, 0 breaks, except +1 tear on R jump−0.2 and +1 partial on 2 cases.
- It is not a skin flap, so it is offered only as a choice.

## Scratch sim
`wrist_sim_t.py`: the F7 sim on Body's tpose pieces, rigid ±25°.
- For r20 vs live-under, holes rise 0–4 → 7–11, while tears and breaks fall. Holes there are her thumb-root notch, sealed by the flap.
- The real rig does not show these holes; its fitted wrist edges differ.
- Files: `wrist_sim_r20.json`, `wrist_sim_live.json`, `before_after_bend1.png`.
