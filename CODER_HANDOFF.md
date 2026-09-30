# Coder handoff (Expert Coder Agent), stopped 2026-09-30 05:10 PT

All coder work was stopped at the user's request. Nothing is running. This file lists what is live, what is partway done, and the next steps.

## Live and verified
- **Master app** `app/index.html` + `app/registry.json`, served at http://127.0.0.1:8765/app/. The status dashboard is in `status/` (`update.py` handles scan, check and build).
- **Body > Rig controls** tab (`app/rigctl.js`). It drives the rig's own `set()` and `draw()`. 33 live controllers: finger curl and spread with presets, WristL/R, HeadTilt/Nod, the body joints, root, the hair preset and the view dial. Rest after reset is 0 px, with 0 console errors (`app/qa/body_controls.png`). WristRot, PalmTwist, the per-joint twists and split finger curl appear disabled as "in progress" and switch on automatically once the rig exposes matching params.
- **Clean room reference page** fix (`app/cleanroom/`). Rerun `app/cleanroom/build.py` whenever the clone updates.
- **Renderer**: `rig/index.html` = `index.v18-wip.html` (contract v1.8). Base Mouth's anger exclusion is in the auto-talk set at line 237 (`TALK_EXCLUDE` includes 'anger').
- **Decisions in force:** hair spring preset A (4.0 Hz, zeta 0.8) is the default, and the anger face uses the Clean room anger art (authored images only).

## Partway done
1. **Pose driver turn** (`app/driver/`). The generated stills `clean-room/layers/rotation/turn-*.png` are removed (they had wrong feet, knees and head at 135-270 deg). The driver now plays `reference/apose_turn/` f001-f232 through `body_tools/work/apose_turn/angle_map.json`.
   - Not finished: the final local and tunnel verification, whose last run crashed when it was stopped (`app/qa/driver_turn/check_turn_local.txt`).
   - Not yet confirmed in the driver: hiding every live part overlay during the turn; holding eyes open at 1, gaze at 0, mouth 0 and fingers/wrists 0; freezing the springs; and the handoffs at f001, f062, f160 and f109 (no eyes or mouth at f109), with an ~80 ms whole-frame crossfade using `angle_map.json` `handoff` scale/offset, plus the hair-edge despill.
   - Known gaps no crossfade hides: hands at f062, f160 and f109 (`hands/work/turn_check/HANDOFF.md`), and the mouth 6-13 px off in the profiles (`mouth/work/turn_handoff/offsets.json`). Either pick better frames or accept a visible jump.
2. **Rig v1.8 to v2 queue** (not done): root motion and foot plant; one resampling path plus premultiplied-alpha compositing (and the interior partial-alpha QA metric); the idle life layer; action clips; the showcase; stress pass B; `AUDIT.md`.
   - **Regenerate `rig/previews/actions/v1/clips/anger.json` and `anger_stress.json`** with `rig/tools/merge_clips.py`, since they still carry the old M keys. Then check that rest is 0 px and that auto-talk never picks anger.
3. **Hand rotation:** WristRot, PalmTwist (switching between authored angles, squash at most 15%, forearm following at 50%), the wrist block leak fix, and twist on every joint. Only the apose sweep started (`rig/previews/wrist/v1/`), and it has no results yet.
4. **Split finger curl / claw** and the rig-side manual rotation control are not started.
5. **Line-art pass mark for all v2 QA:** outline within about 1 px of its rest width, no seam breaks, no new kinks. Hair's 7 break joints (`hair/qa/lineart/`) need a resampling attribution.
6. **Render gates:** apose and tpose may render; back is released with the current live files; left and right wait for Body's profile and bikini fixes (see `body_tools/HANDOFF.md`).
7. **Beauty mark audit** of 1,323 stills (`app/qa/beauty_marks/`) may be incomplete. Check before using it.

## Hard rules
Show only authored PNGs. Never draw over her eyes or mouth, never mirror her (the mark under her eye; amber right eye, green left), never write to `views/` or any `rig.json` from coder work, and keep rest at 0 px in all five views.
