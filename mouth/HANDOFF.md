# Mouth handoff (Base Mouth), 2026-09-30 05:10 PT

Nothing is running. All mouth work is stopped.

## Live and verified
- Mouth v4 in `views/{apose,tpose,left,right}/mouth/`, nine 1365x1739 PNGs on layer 500 plus `rig.json`. The back view has no mouth.
- The grid, as (MouthOpen, MouthForm):
  - rest (0,0), M (0,-1), smile (0,1)
  - OH_half (0.5,-1), AA_half (0.5,0), EE_half (0.5,1)
  - OH (1,-1), AA (1,0), EE (1,1)
- Only two controls drive it: MouthOpen (0 to 1) and MouthForm (-1 to 1). It uses flat colour and the key blue #0000FF.
- `python3 rig/rest_check.py` gives 0 px of rest difference in all views.
- Anger mouth, the tenth shape at (0.25,-1): it's live in apose and tpose only, cut from the Clean room anger art (`public/puppet/emotions/anger.png`). The profiles fall back to M. Details are in `mouth/work/anger/summary.md`.
- Keys:
  - `mouth/showcase/mouth_showcase.json`
  - `mouth/actions/mouth_actions.json` (jump, run, and anger from 0.30 to 3.0 s)
  - the idle smile key, which is carried in Body's `idle_arm_sway`

## Waiting on the user
- The anger mouth breaks two rules: the lips are plum instead of her brown, and the line is about 3 px against her 1 px. It also keeps the art's gloss. The options are to keep it as drawn, recolour it to flat brown, or remove it. It's pushed as it is now.
- Gasp and grin need an OK to use the Clean room art, or new drawings.

## Unfinished, with next steps
1. **Turn handoff** (`mouth/work/turn_handoff/`). These are the frame mouth's offsets from the live mouth, using Body's handoff numbers:
   - apose f001: 0 across, -9 px (up)
   - left f062: +8 across, +13 px (down)
   - right f160: -7 across, +6 px (down)

   The profile turn frames draw thinner lips, so they don't swap pixel-exact. Next step: after Coder's crossfade lands, check the leftover jump. If it's visible, ask Body or Coder about a head-only offset during the fade. The mouth must stay hidden during the turn, with auto-talk paused and the controls at 0. It comes back only at f001, f062 and f160.
2. **Renderer changes for Coder** (accepted, not verified by me):
   - add `'anger'` to `TALK_EXCLUDE` in `rig/index.html`
   - regenerate `rig/previews/actions/v1/clips/anger.json` and the stress copy with `rig/tools/merge_clips.py`

   Next step: check that auto-talk never picks anger.
3. **v2 render QA**: check the mouth in Coder's v2 renders (apose, tpose, profiles, then back). Look for:
   - the sharp/soft lip-line flicker at exactly 0
   - the doubled smile-to-rest outline in the profiles
   - the switch frame drawn at 0%
   - the 0.5 threshold one frame late
   - the line staying within about 1 px of its rest width

   Scripts are in `mouth/work/idle_qa/` (`run_all.sh`, `report.py`, `fades.py`).
4. **Profile anger art**: there's no real side view of the anger face. The squashed proposals in `mouth/work/anger/proposal/` aren't recommended.
5. The auto idle mouth changes shape about 48 times in 8 s. That fix is on Coder's list.

## Push
Push all of `mouth/` and `views/*/mouth/`, including work and scratch. Leave out only `__pycache__/` and `mouth/work/anger/tmp/`.
