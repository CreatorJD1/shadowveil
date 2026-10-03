# Eyes handoff (Base Eyes), 2026-10-03 03:55 PT

This covers what is live, what is staged, and the open issues. All paths are relative to the repo root. Nothing staged is live until the user OKs it on `status/status.json`.

## Hard rules
- Never paint new eyes over her drawing. The parts are cut from her own pixels.
- EyeR is her right eye, amber, layers 400–403. EyeL is her left eye, green, layers 410–413. Never mirror them.
- Params: `EyeLOpen`/`EyeROpen` run 0–1, lid frame = round((1−v)×7) across 8 frames, and only the upper lid moves. `EyeBallX`/`EyeBallY` run −1..1, where X −1 is her right and Y −1 is up.
- Parts are built on `#0000FF` and keyed. They use only her colours (exact tones from `base.png` or the turn frame). Flat colour, no shadows.
- Rest (eyes open, gaze 0) must match her art with 0 px off.
- Don't run `serve-driver.py`, and don't run `render_diag.py check` (it overwrites `rest_check.json` in an old format).

## Live (main model: apose, tpose, left, right)
- `views/<view>/eyes/`: lids, whites, irises and lashes with `rig.json`. Rest is 0 px. The left-profile gaze fix is in.
- Blink timing reference: `eyes/work/reference_timing/`. A blink is about 333 ms (closes in about 42 ms, holds about 250 ms, opens over about 125 ms), and she blinks every 2.5–5 s.

## Staged, waiting on the user's OK
1. Lash fix going live (A-pose lash px restored to her drawing).
2. Closed-frame crease: show it or hide it (the user's choice).
3. Side-glance white tone: the whites use her own white tone at a side glance.
4. 45°/315° diagonal eyes: `eyes/staged/diagonals/{045,315}/`, in frame px (768×1168, frames f033/f191). This includes the blue fix, the lash trim under her hair, and the edge clear. Rest is 0 inside her face and 0 at the edge (`rest_check.json`). Backups are in `backups_*`.
5. Diagonal iris limits v4 (`rig/work/irislimits/diag_irislimits_v4.json`, flag `?irislimits=diag`). Trade-off: looking up-left or up-right goes straight up.

## Decided
- 135° (f087) and 225° (f131) have no eye parts, because no eye is visible in her frames (`eyes/qa/diag_135_225/`).
- Diagonal eye whites need parenting to Body's diagonal `head` piece. The rest of each eye follows its white.
- The diagonal work is paused by the user, who wants focus on fixing the main model.

## Open issues and how to fix them
- Pale line above the iris, and specks in the right profile: both small. Fix by recutting from her pixels and checking that rest stays at 0.
- Eye mesh lid for FORMAT v0.2: not started.
- Expressions and brows (benchmark laugh/smirk/angry/sad): parked by the user. Partial, unverified work is in `eyes/staged/expressions/work/`, and targets are in `eyes/qa/benchmark_targets/`. Anger needs her OK.
- If her head or face bends during posing, weight the whole face fully to the head, because rigid eye parts will slide off her lids otherwise.

## Checks
- QA gates: `eyes/qa/qa_gates/` (0 off-palette, 0 chroma, 0 rotation leak).
- Diagonal rest: `python3 eyes/qa/qa_gates/check_diag_chroma_fix.py`.
- Register reports with `python3 status/update.py register eyes reports <path> '<label>'`.
