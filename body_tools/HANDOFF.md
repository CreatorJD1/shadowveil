# Base Body handoff (Sep 30, 2026, 5:06 AM PT)

## Live and verified
- apose, tpose, back: skin.json, base_body_skin.png and base_body_underlay.png are unchanged from the last verified build (rest 0 px, skin rules and underlay checks pass).
- left: restored to the pre-fix backup (body_tools/work/pre_torso_weights/left/). The hip strip there was a pure regression.
- right: round-1 fix live (build_skin.py --torso-arm-clamp, build_underlay.py --host-strip). Rest 0 px in all five views, check_skin_rules and check_underlay pass, and the ±25° joint test is unchanged.
  - arm_settle armpit hole: 415 px → 56 px (f168); f160–176 total 3246 → 557.
  - weight_shift hip slit: NOT fixed. Peak 48 → 46 px, now split into 3 cracks (x695–699, y777–835), and worse in f173–190.
- Turnaround: body_tools/work/apose_turn/angle_map.json (angle→frame table, loop f001–f232, handoff scale/offset for f001/f062/f160/f109), with angle_map_sheet.png, direction_check.png and handoff_overlay.png. All five views pass the direction check.
- Idle and action keys: body_tools/idle/ (idle_arm_sway, showcase) and body_tools/actions/ (jump, run, anger, plus stress copies).

## Unfinished (stopped at the user's request)
1. Right hip slit and last 56 px of the armpit hole. Round-2 candidates (not verified) are in body_tools/work/torso_round2_candidates/skin_v*.json. Plan: clamp distance about 2 px or an armpit underlay; rebuild the hip strip as 100% pelvis with a clean split from the thigh (or host it on forearm_R, or drop it); then re-sim arm_settle and weight_shift right. Backup: body_tools/work/pre_torso_weights/.
2. Bikini bottom (user report): grey-white smudges at the leg openings and waistband, a blue notch at the crotch, and the fabric doesn't follow the thigh. Diagnosis was not finished, and no live file changed. Plan: find whether the smudges are in base.png or in our skin/underlay; blend the leg-opening weights from pelvis to thigh. Pass mark: outline within about 1 px of rest width at 12.5° and 25°, no breaks, no new kinks. Backup: body_tools/work/pre_bikini_fix/; scratch in body_tools/work/bikini_fix/.
3. Turn handoff: Hands measured arm-pose gaps at f062, f160 and f109 (about 136 px and 31–50 px) that the crossfade can't hide. Next step: search the turn frames near those handoffs for an arm pose closer to the live views, or accept the jump.
4. Hair speck move into base_body.png's hair mask is on hold until item 1 is done (hair/staged/speck_fix/). After it lands, rebuild the body parts for all five views and rerun the rest checks.
5. Known flaws: tpose hip_R 122%, left hip_L 60% and shoulder_L 127%; foot lift in weight_shift (fixed by v1.8 root motion).

## Leave out of the push
body_tools/idle/resim/ (scratch renders), body_tools/work/*/frames/, __pycache__/.
