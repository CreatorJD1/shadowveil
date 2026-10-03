# right: Body's kept hair ink staged into the static hair_front (STAGED ONLY), Base Hair, 1:45 AM PT Oct 3

**Source and files**
- Source mask: `body_tools/work/hairless_division_staged/right/kept_ink_mask.png` (652 px).
- New file: `views/right/hair/hair_front.png`, built on `hair/staged/hairfront_holes/right/hair/hair_front.png`.
- **640 px** were copied unchanged from `views/right/base.png`. All are hair-silhouette outline ink plus its anti-aliasing, and all were alpha 0 before.

**Excluded px** (listed with reasons in `excluded` in the json; `right_excluded_mask.png` marks contour = 128, flyaway = 64):
- Lock px: 0 in the eye lock, 0 in the mouth lock, 0 in the hand lock (back has no eye/mouth locks).
- **Contour, 9 px** (left in the body as drawn): comp 23 at x644–646 y283–288, the top of the back-of-neck outline at the nape.
- **Flyaway, 3 px.** Faint ink with alpha ≤ 80 that is nearer a swaying strand than any static hair. Proposal, as for A-pose: add these as exact copies to that strand, and Body sets them to alpha 0. They are not staged yet; leave them as drawn until then.
  - `strand_04`: 3 px, x781–793 y148–179, alpha 1–19

**For Body** (`for_base_body/` and the `for_eyes/` copy, each with `right_px.json`, `right_mask.png`, `right_body_skin_mask.png`, `right_body_clear_mask.png`, `right_excluded_mask.png`):
- **64 px** with base alpha 255 → skin (183,120,76).
- **576 px** with base alpha < 255 → **alpha 0.** These are the anti-aliased outline over the background, outside the skin.
  - Turning them to skin would paint skin outside her silhouette.
  - Keeping them in the body double-composites them with hair_front.

**Checks**
- Rest in the copy-only overlay `/tmp/hl4`, script `../work4/restsim4.py`:
  - **0 px** with Body's staged copies after the skin/alpha-0 change.
  - 0 px with Body's copies and the old hair_front.
  - If Body's copies are left as-is, or every px is turned to skin, rest is not 0. These are the semi-transparent px, so the alpha-0 rule is required.
- 0 off-palette colours (all exact base.png px), 0 chroma, 0 lock px. The file is unchanged outside the mask, and line art is unchanged (rest composite equals base).
- **Sway on 8780** (index.html served as db5cf270), 15 poses: the `job4` frames (staged hair_front + Body's copies changed) vs the `hairless` baseline give **0 px different and 0 new see-through**.
