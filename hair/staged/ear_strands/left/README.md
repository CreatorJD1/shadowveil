# left: Body's kept hair ink staged into the static hair_front (STAGED ONLY), Base Hair, 1:45 AM PT Oct 3

**Source and files**
- Source mask: `body_tools/work/hairless_division_staged/left/kept_ink_mask.png` (642 px).
- New file: `views/left/hair/hair_front.png`, built on `hair/staged/lineart_fix/views/left/hair/hair_front.png`.
- **621 px** were copied unchanged from `views/left/base.png`. All are hair-silhouette outline ink plus its anti-aliasing, and all were alpha 0 before.

**Excluded px** (listed with reasons in `excluded` in the json; `left_excluded_mask.png` marks contour = 128, flyaway = 64):
- Lock px: 0 in the eye lock, 0 in the mouth lock, 0 in the hand lock (back has no eye/mouth locks).
- **Contour, 21 px** (left in the body as drawn): comp 12 at x595–598 y154–158, where the forehead/face outline meets the hairline; comp 25 at x727–728 y278–283, the top of the back-of-neck outline.
- **Flyaway, 0 px.** Faint ink with alpha ≤ 80 that is nearer a swaying strand than any static hair. Proposal, as for A-pose: add these as exact copies to that strand, and Body sets them to alpha 0. They are not staged yet; leave them as drawn until then.
  - none

**For Body** (`for_base_body/` and the `for_eyes/` copy, each with `left_px.json`, `left_mask.png`, `left_body_skin_mask.png`, `left_body_clear_mask.png`, `left_excluded_mask.png`):
- **68 px** with base alpha 255 → skin (185,122,78).
- **553 px** with base alpha < 255 → **alpha 0.** These are the anti-aliased outline over the background, outside the skin.
  - Turning them to skin would paint skin outside her silhouette.
  - Keeping them in the body double-composites them with hair_front.

**Checks**
- Rest in the copy-only overlay `/tmp/hl4`, script `../work4/restsim4.py`:
  - **0 px** with Body's staged copies after the skin/alpha-0 change.
  - 0 px with Body's copies and the old hair_front.
  - If Body's copies are left as-is, or every px is turned to skin, rest is not 0. These are the semi-transparent px, so the alpha-0 rule is required.
- 0 off-palette colours (all exact base.png px), 0 chroma, 0 lock px. The file is unchanged outside the mask, and line art is unchanged (rest composite equals base).
- **Sway on 8780** (index.html served as db5cf270), 15 poses: the `job4` frames (staged hair_front + Body's copies changed) vs the `hairless` baseline give **0 px different and 0 new see-through**.
