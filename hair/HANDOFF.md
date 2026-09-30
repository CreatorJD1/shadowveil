# Hair handoff (Base Hair), Wed Sep 30 2026, 5:10 AM PT

All hair work is stopped. Nothing is half-written in the live files.

## Live and verified
- Hair parts live in `views/*/hair/`. Rest check (`rig/rest_check.py`) is 0 px in all five views, with no failing entries.
- Springs: preset A (4.0 Hz, damping 0.8) is the rig default, chosen by the user.
- Behind-the-ear skin fill: live. No white patches at full sway (`hair/qa/idle_battle/SUMMARY.md`).
- Tpose wisp fill: live in `views/tpose/hair/hair_back.png`. 320 px sit under the wisp above EyeR, hidden at rest. The wisp let the background through on 228/240 idle frames before and 0/240 after (`hair/qa/wisp_fix/SUMMARY.md`, with before and after crops in `crops/`).
- `hair/validate_hair.py` got two narrow rule changes for the fill: static hair above `hair_back` counts as covering it, and static fill under the face (layer < 400) is reported as `under_face_static_px`. Backups are in `hair/backups/wisp_fix_20260930/`.
- Keys: showcase `hair/showcase/hair_showcase.json`, actions `hair/actions/hair_actions.json` (jump, anger, run), and checker `hair/showcase/validate_hair_showcase.mjs`.
- Idle QA of the v1 renders passes, apart from the now-fixed wisp (`hair/qa/idle_battle/`). QA scripts accept `idle_arm_sway`.

## Unfinished (not live)
1. **Speck move** (`hair/staged/speck_fix/`). Stray hair pixels (413) left on `base_body.png` get moved into their strands as exact base.png copies, with a matching erase mask and a validator exception. See `SIMULATION.md` and `PIXELS.md`.
   - Blocked on Base Body clearing those pixels to alpha 0 in `base_body.png` and `base_body_skin.png`. The list is in `for_base_body/speck_px.json`.
   - The apply script only runs with `--apply` and backs up and restores on its own.
   - Open item: six faint speck clusters split off at sway (left and back). The decision was to cut them in together with the faint base.png pixels that connect them. That work was stopped before it started, so the staged set does NOT include it yet.
2. **Line-art check** (`hair/qa/lineart/SUMMARY.md`, crops included). Line width stays within 0.62 px and no strand comes apart. 7 live joints break a small piece of line or gain a sharp corner at half and full sway: apose strand_03_tip and strand_06_tip, tpose strand_03, left strand_03, right strand_02 and strand_02_tip, plus the tpose strand_02 part.
   - Next: measure the renderer's resampling baseline (the Coder has these joints in the renderer audit). Then fix whatever is left over by moving the pivots onto straight line runs with longer caps and re-cutting seams from base.png. Nothing is staged for this yet.
3. **Turn handoff hair offsets** (`hair/qa/turn_handoff/`, first pass, stopped before its summary). Offsets are frame minus live view, in view px, using Body's `angle_map.json` handoff fit.
   - apose f001: whole hair +1/−10, bun +1/−10, bun at layer 101.
   - left f062: whole hair −5/+3, bun +14/+1, fringe −10/+9, bun at 650.
   - right f160: whole hair +13/−2, bun −1/−6, fringe +17/+1, bun at 650.
   - back f109: bun −4/−6. The whole-hair numbers are NOT reliable (IoU 0.27, so the hair was probably mis-segmented).
   - Next: redo back f109 and write the overlays up. Most of this should hide in the ~80 ms crossfade. The profile fringe gaps (10–17 px) probably won't, and like the mouth gaps they look like head placement in the turn drawing.
4. **After v1.8 / v2 renders:** rerun `validate_hair.py` and `rest_check.py`. Check every tip's peak against its limit under A. Check the hair in the showcase, action and stress renders. Move the head offsets from BodyLean to HeadTilt/HeadNod once those controls exist.

## Push notes
Push all of `hair/` and `views/*/hair/`, including staged work, QA summaries, sheets, crops and data. Leave out only `__pycache__/` and `hair/qa/wisp_fix/render/` (245 MB of re-render frames and videos; the numbers are in its SUMMARY and data JSON).
