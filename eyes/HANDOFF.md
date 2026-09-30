# Base Eyes handoff (stopped 2026-09-30 5:03 AM PT, on the user's request)

## Live state (shipped, verified)
- `views/*/eyes/` parts and `rig.json` are untouched by the unfinished work. Rest matches `base.png` at 0 px in all five views (back has no eyes).
- Params: EyeLOpen/EyeROpen 0..1 (lid frame = round((1-v)*7), 8 frames, upper lid only), EyeBallX/EyeBallY -1..1 (X -1 = her right, Y -1 = up). EyeR amber (layers 400-403), EyeL green (410-413). Parts drawn on #0000FF and keyed. Never paint new eyes over her drawing.
- Left-profile gaze fix applied (drive dxAtXminus1 0, dxAtXplus1 1); backups `work/*_before_gazefix.*`.
- Showcase/test eye keys: `showcase/eye_showcase.json` (generator `make_eye_showcase.py`).
- Idle-render review: `work/idle_review/` (notes.md, summary.json, sheets). Blink timing reference: `work/reference_timing/`.

## Unfinished work (stopped mid-way, not applied to live files)
1. **Blink lash/crease fix** - `work/lashfix/` (scripts + `lashfix_log.json`). Defect: the lid crease and lash thin out at the start of a blink (lid frames 1-2). Pass mark: outline stays within ~1 px of its rest width, no breaks, no new kinks. Backups of the live files before any write are in `work/backups_lashfix/`. Next step: finish `lashfix.py`, re-export the lid frames, run `rig/rest_check.py` (must stay 0 px), check lash width across lid frames 0-7.
2. **Turn handoff eye offsets** - `work/handoff/` (measure.py, warp.py, seg tries). Goal: eye offset (frame minus live view, view px) at f001, f062, f160 using Body's `body_tools/work/apose_turn/angle_map.json`. Mouth measured 0/-9, 8/+13, 7/+6; eyes are expected to show the same head gap. No numbers produced yet. Read-only; changes nothing.

## Known defects waiting on the user's OK
- Pale 1 px line of white above the iris on a downward glance (front views).
- 1-4 px specks in the right profile.
- Optional: thicker right-profile lashes; tone down the flat white exposed at strong side glances.
- Anger eyes/brows need the user's OK or new drawings.

## Push exclusions
`work/*/tmp/`, `work/reference_timing/raw*/`, `__pycache__/`.
