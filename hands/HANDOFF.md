# Hands handoff (Base Hands), stopped 2026-09-30 05:05 PT

## Live and verified
- Rest check: total 0 px in all 5 views (apose, tpose, left, right, back); masks 5/5 match `masks.md5`.
- Rig: `views/*/hands/` (palm, 3 segments per finger, Thumb1-3), plus `hands/rig_all_views.json`.
- Clips: `hands/actions/hand_actions.json` has anger_hands, jump_hands and run_hands. The run clip's wrists follow ShoulderX from `body_tools/actions/run.json`, 2 frames behind.
- Showcase: `hands/showcase/hands_showcase.json`, 29.6 s long, starting and ending at rest.
- Live fixes made during this session (backups under `hands/work/idle_bend/`):
  - tpose frame lists changed to [f0,f1,f1,f1,f2]. Backup: `rig.tpose.pre_frames5.json`.
  - tpose art cleaned up on the palms and Ring1_f1/f2. Backups: `art_backup/`.
  - tpose Middle1 pivot moved on the curled frames only (data_F). Backup: `data_backup/tpose_rig.pre_dataF.json`.
  - apose Ring and Pinky maxCurlDeg sign flipped. This took whole-hand defects from 180/274/88 to 2/76/0.
- Line-art check (`hands/work/idle_bend/lineart.py`; full results in REPORT.md, "Follow-up 4"):
  - apose passes.
  - back fails on width only: R_Middle1 is +1.17 px at curl 0.13 and 0.2.
  - tpose fails on breaks: 2-7 px at curl 0.2 and 0.3, and 5-6 px at 0.87. All of them come from the hidden Ring1_f1 filler.

## Unfinished (stopped, nothing live changed)
1. **Art fixes (Follow-up 5).** Backups are staged in `hands/work/idle_bend/f5_backup/`, and the live files are byte-identical to those backups.
   - Next step: trim the tpose Ring1_f1 edge pixels that poke outside the silhouette. Back view: use frames [f0,f1,f1,f1,f2] (candidate c8) plus an opaque fill under the back f1 finger bases, to remove the partial alpha (L 28, R 30 px) and the R_Middle1 width problem.
   - Apply only if rest stays 0, the poses move 2 px or less, and the line-art check passes.
2. **Turn handoff** (`hands/work/turn_check/HANDOFF.md`).
   - f001 into apose is clean, within about 7 px.
   - f109 into back is off by 31-50 px outward and rotated about 8°.
   - f062 and f160 into the profiles: the turn frame's hand sits about 136 px higher and is drawn edge-on.
   - Both come from the arm pose. Next step: Body picks a closer turn frame, or we accept a visible jump.
3. **Older open items.**
   - apose fist: flat inside, with a lump where the index meets the thumb.
   - tpose: ring and pinky are hidden behind the index.
   - Profile thumbs only rotate.
   - Claw pose and thumb-wrapped fist need split parameters from Coder.
   - Rerun the wrist-skin check if Body changes the forearm skin.

## Push
Push all of `hands/` and `views/*/hands/`, including work and scratch. Leave out only `__pycache__/` and `hands/work/idle_bend/renders/` (regenerable renders).
