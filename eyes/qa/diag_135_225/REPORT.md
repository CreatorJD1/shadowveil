# Eye visibility at 135° (f087) and 225° (f131): read-only diagnosis (2026-10-03)

**Verdict: neither frame shows any eye pixels.** No lash, lid line, white or iris of EyeR (amber) or EyeL (green) is visible at 135° or 225°.

| angle | frame | eye pixels visible | count / bbox | eye |
|---|---|---|---|---|
| 135 (back 3/4, her left side) | reference/apose_turn/frames/f087.png | **no** | 0 | none (EyeL would be the near one, but it is hidden) |
| 225 (back 3/4, her right side) | reference/apose_turn/frames/f131.png | **no** | 0 | none (EyeR would be the near one, but it is hidden) |

## Source
The frame source is the same as in cut_diag.py / render_diag.py: `reference/apose_turn/frames/fNNN.png` (768x1168 on #0000FF). The ring comes from `body_tools/work/apose_turn/diagonals/diagonals.json` (135=f087, 225=f131), and its notes say "Face not visible" for both frames. This check confirms that.
Head crop, frame px: x 290-480, y 40-250. The eye line in f033/f191 is y≈166-183, about 105-115 px below the head top. f087/f131 have their head tops at y 52/54, so the eyes would be at y≈160-180.

## Method
- **Palette:** eye tones taken from eyes/staged/diagonals/045 and 315, plus the live views/{apose,tpose,left,right}/eyes parts. It has white (lum>150), amber and green iris tones (filtered by cut_diag `classes()`), and lash/lid_0 dark tones (lum<90).
- **Stage 1 (tools/diag.py → results.json, *_eye_mask_overlay_x4.png):** a pixel is flagged if it is within 16 RGB of a palette tone and passes the `classes()` test. Most of what it flags is her skin: lit skin on her ear, jaw and neck is the same colour family as the amber iris (683 / 716 px, in large blobs on the ear and jaw). Lash tones are the same as her hair (about 15k px). So this stage alone can't settle anything. The overlays show where the hits land.
- **Stage 2 (tools/diag2.py → results_discriminative.json, *_eye_mask_discriminative_x4.png):** a pixel counts only if it is closer to an eye tone than to any non-eye head tone of f033/f191 (eye-part alphas, grown by 3 px, are excluded). It also has to pass `classes()` and must not sit in the 2 px anti-aliased band along the silhouette.
  - Validation on f033/f191: the stage finds the known eyes. White, iris and green hits are 100% inside the known eye parts; for lash, 197/212 and 177/188 hits are inside. The known parts come from those same frames, so this is a sanity check, not a blind test.
  - f087 leftovers: white 2 px (largest blob 1), amber 11 px (largest 3), green 0, lash/line 234 px in 113 specks (largest 9).
  - f131 leftovers: white 5 px (largest 3), amber 42 px (largest 11), green 0, lash/line 174 px in 93 specks (largest 8).
  - I checked every leftover pixel by eye. They are hair-strand anti-aliasing, the lit rim of her ear (f087 x335-337 y163-171; f131 x421-422 y163-164 and x421 y181), or skin glimpsed between hair strands. In f131 the amber hits at x431-435 y165-197 are a 1-2 px yellow skin highlight running between strands down the far cheek, and x408-416 y223-233 is the jaw. None of them has a white next to an iris, a lash band over an opening, or anything shaped like an eye. No green-iris pixel was found in either frame.
- **Visual check of the 4x crops:** both frames show the back of the head, the bun, the near ear, the jaw and neck. The cheek silhouette at eye height is covered by loose hair strands, and no lash tip sticks out past it.

## Files (all in this folder)
- f087_135_head_x4.png, f131_225_head_x4.png: head crops, 4x nearest
- f087_135_eye_mask_discriminative_x4.png, f131_225_eye_mask_discriminative_x4.png: final candidate overlay (magenta=white, orange=amber, green=green, red=lash/line). Also made for f033/f191 as the validation case.
- f087_135_eye_mask_overlay_x4.png, f131_225_eye_mask_overlay_x4.png: stage-1 overlay (slate = skin along the cheek edge)
- f087_135_palette_only_x4.png, f131_225_palette_only_x4.png: tone-only hits with no class test
- f087_cheek_zone_x8.png, f131_cheek_zone_x8.png: 8x close-up of the ear/cheek/jaw zone
- results.json, results_discriminative.json, tools/diag.py, tools/diag2.py

## Implication
135 and 225 need no eye parts. Treat them like views/back: no EyeR/EyeL drawn, and the eye params do nothing at those angles.

Note: the stage-1 run imported cut_diag.py (for `classes()`), which regenerated the bytecode cache `eyes/staged/diagonals/__pycache__/cut_diag.cpython-313.pyc`. That is only a cache file, and no source or part files changed. Later runs use `sys.dont_write_bytecode`.
