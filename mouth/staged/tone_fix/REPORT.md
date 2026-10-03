# Mouth tone fix (staged) — Base Mouth

Generated Fri Oct 2 2026, PT. Staged only: `mouth/staged/tone_fix/views/<view>/mouth/<shape>.png`. Live `views/` untouched (sha256 of all 42 views/*/mouth files identical before/after). Script: `tone_fix.py`.

## Method

- Palette = exact RGB of opaque base.png pixels inside (rest.png alpha OR handoff_hairless/<view>_mouth_lock.png) dilated 10 px (Chebyshev), opaque base.png pixels only. Region masks: `views/<view>/palette_region.png`.
- An opaque shape pixel already equal to some opaque base.png colour is left as is. Otherwise it is snapped to the nearest regional tone (Chebyshev) only if that tone is <= 5 levels away AND the same kind: hue class (neutral if max-min<12; warm [345,60) deg; green [60,170); blue [170,260); purple [260,345)) + line band (luma<32 = line). Snap must keep both.
- Anything else is left unchanged and listed (`unsnapped_pixels.csv`, `tone_fix_log.json`).
- Alpha never changed; partially transparent edge pixels (0<a<255) untouched. rest.png not staged (exact). anger.png not changed or staged (approved Clean room art).

## Results per view/shape

| view | shape | opaque | off before (>5, max) | snapped | left unsnapped (>5 / kind) | max change | off after | partial α untouched |
|---|---|---|---|---|---|---|---|---|
| apose | AA | 879 | 812 (79, 8) | 646 | 166 (166 / 0) | 5 | 166 | 230 |
| apose | AA_half | 749 | 658 (0, 4) | 617 | 41 (41 / 0) | 5 | 41 | 282 |
| apose | EE | 755 | 678 (0, 4) | 567 | 111 (111 / 0) | 5 | 111 | 284 |
| apose | EE_half | 758 | 696 (0, 4) | 666 | 30 (30 / 0) | 5 | 30 | 289 |
| apose | M | 749 | 669 (0, 2) | 669 | 0 (0 / 0) | 3 | 0 | 282 |
| apose | OH | 760 | 723 (30, 7) | 679 | 44 (44 / 0) | 5 | 44 | 271 |
| apose | OH_half | 749 | 692 (6, 8) | 682 | 10 (10 / 0) | 5 | 10 | 282 |
| apose | smile | 758 | 689 (0, 2) | 689 | 0 (0 / 0) | 3 | 0 | 291 |
| tpose | AA | 793 | 584 (10, 7) | 439 | 145 (145 / 0) | 5 | 145 | 240 |
| tpose | AA_half | 730 | 347 (4, 7) | 309 | 38 (38 / 0) | 5 | 38 | 279 |
| tpose | EE | 749 | 290 (5, 6) | 199 | 91 (91 / 0) | 5 | 91 | 270 |
| tpose | EE_half | 757 | 232 (1, 6) | 213 | 19 (19 / 0) | 5 | 19 | 272 |
| tpose | M | 730 | 172 (0, 2) | 171 | 1 (1 / 0) | 4 | 1 | 279 |
| tpose | OH | 742 | 299 (11, 8) | 257 | 42 (42 / 0) | 5 | 42 | 267 |
| tpose | OH_half | 730 | 244 (1, 6) | 234 | 10 (10 / 0) | 5 | 10 | 279 |
| tpose | smile | 750 | 190 (0, 2) | 188 | 2 (2 / 0) | 5 | 2 | 275 |
| left | AA | 570 | 402 (8, 10) | 267 | 135 (134 / 1) | 5 | 135 | 240 |
| left | AA_half | 505 | 358 (4, 8) | 261 | 97 (96 / 1) | 5 | 97 | 228 |
| left | EE | 443 | 307 (4, 8) | 255 | 52 (52 / 0) | 5 | 52 | 222 |
| left | EE_half | 428 | 286 (4, 9) | 242 | 44 (43 / 1) | 5 | 44 | 218 |
| left | M | 428 | 204 (0, 3) | 183 | 21 (21 / 0) | 5 | 21 | 218 |
| left | OH | 450 | 287 (1, 6) | 231 | 56 (55 / 1) | 5 | 56 | 220 |
| left | OH_half | 440 | 285 (1, 6) | 240 | 45 (45 / 0) | 5 | 45 | 221 |
| left | smile | 428 | 241 (0, 2) | 217 | 24 (24 / 0) | 5 | 24 | 218 |
| right | AA | 530 | 385 (12, 8) | 246 | 139 (137 / 2) | 5 | 139 | 229 |
| right | AA_half | 481 | 341 (5, 7) | 252 | 89 (88 / 1) | 5 | 89 | 226 |
| right | EE | 428 | 274 (5, 10) | 215 | 59 (56 / 3) | 5 | 59 | 215 |
| right | EE_half | 412 | 283 (3, 10) | 237 | 46 (44 / 2) | 5 | 46 | 220 |
| right | M | 412 | 203 (0, 2) | 178 | 25 (23 / 2) | 5 | 25 | 220 |
| right | OH | 436 | 286 (3, 8) | 218 | 68 (65 / 3) | 5 | 68 | 220 |
| right | OH_half | 426 | 277 (3, 6) | 227 | 50 (47 / 3) | 5 | 50 | 215 |
| right | smile | 412 | 234 (0, 2) | 210 | 24 (21 / 3) | 5 | 24 | 220 |

Totals (32 shapes): snapped 10904, left unsnapped 1724, partial-alpha px untouched 7922.

## What is left unsnapped (needs your call)

Almost all unsnapped pixels are tones that do not exist on her closed lips at all, so the lip region has no same-kind tone within 5 — though each is only 1–6 from a base.png tone somewhere else on the body:

- **Teeth** `#efe4da` and grey-white teeth shading (`#ad9c92`, `#bcaea4`, `#d5c9bf`…): nearest lip tone 15–100 away.
- **Tongue** `#9c5a4a` (apose/tpose AA, OH): 9 from lip tones.
- **Mouth interior** `#3f2319` (left/right AA, AA_half, OH, OH_half): 7–11 from lip tones.
- **Near-black profile line tones** (`#170517`, `#100810`, `#120910`, `#1b0e11`…): either >5 away, or the near tone is across the warm/purple hue boundary (counted as `kind`).

Options: (a) leave them as drawn (current staged state); (b) allow teeth/interior/tongue to snap to a named second region (for example eye whites for teeth), which would need your OK; (c) redraw those tones.

Top unsnapped colours per shape (count):

- apose AA: #9c5a4a×71, #ad9c92×9, #bcaea4×6, #c2b5aa×4
- apose AA_half: #ad9c92×21, #554236×4, #58453a×2, #7c6a5f×2
- apose EE: #efe4da×38, #88786d×10, #816b61×5, #e5dad0×4
- apose EE_half: #554236×5, #d5c9bf×5, #928277×4, #a5968c×2
- apose OH: #9c5a4a×21, #854c3e×3, #8c7b70×2, #938177×2
- apose OH_half: #8d5041×3, #493429×2, #4e342a×2, #7e4638×2
- tpose AA: #9c5a4a×65, #ad9c92×9, #c0afa4×6, #a89588×4
- tpose AA_half: #ad9c92×17, #ab998e×4, #794538×3, #7a6255×2
- tpose EE: #efe4da×32, #907a6d×7, #e3d7cc×4, #cbbcb1×3
- tpose EE_half: #9f8b7e×3, #ae9b8f×3, #8d7768×2, #9b8679×2
- tpose M: #794e2c×1
- tpose OH: #9c5a4a×20, #8a7467×2, #9e8a7e×2, #734235×2
- tpose OH_half: #743f2e×3, #693c2f×2, #834b3d×2, #6a3827×2
- tpose smile: #794e2c×2
- left AA: #3f2319×80, #d9ccc2×4, #40241a×3, #efe4da×2
- left AA_half: #3f2319×45, #4e2b1a×6, #97847a×4, #3f1f1a×3
- left EE: #efe4da×18, #3f2319×5, #170517×4, #1e0a1a×3
- left EE_half: #beaea4×10, #170517×3, #3f2319×3, #220c18×2
- left M: #170517×5, #220c18×2, #381d22×2, #6c4230×1
- left OH: #3f2319×30, #502915×2, #3d2016×2, #220c18×1
- left OH_half: #3f2319×23, #170517×4, #1e0a1a×2, #220c18×1
- left smile: #170517×5, #220c18×2, #381d22×2, #6c4230×1
- right AA: #3f2319×73, #100810×6, #432619×5, #c3b4aa×4
- right AA_half: #3f2319×44, #382014×5, #100810×4, #97847a×4
- right EE: #efe4da×20, #442a1d×11, #3f2319×5, #100810×4
- right EE_half: #beafa4×11, #120910×3, #794f36×2, #170d12×2
- right M: #120910×3, #794f36×2, #170d12×2, #402921×2
- right OH: #3f2319×30, #1a0e11×2, #100810×2, #3d2016×2
- right OH_half: #3f2319×21, #1b0e11×2, #864d3f×2, #100810×2
- right smile: #120910×3, #794f36×2, #170d12×2, #36221e×1

Full per-pixel list (coordinates in view px, colour, reason, nearest tones): `unsnapped_pixels.csv` and `tone_fix_log.json` → views.<view>.shapes.<shape>.unsnapped.

## Checks

- Line art width: line mask (opaque, luma<32) identical before/after in all 32 shapes, so the width did not change (median 1 px; the snap may not cross the line threshold).
- Key blue: 0 key-blue pixels (#0000FF-like) before and after in every shape, 0 new.
- Alpha identical and partial-alpha pixels byte-identical in every staged file.
- Rest: rest.png differs from base.png in 0 px in all four views; not modified or staged.

## anger.png (approved art, unchanged; numbers only)

| view | opaque | partial α | off palette (>5, max) | off vs lip-region palette (>5) | line px median width | kinds |
|---|---|---|---|---|---|---|
| apose | 1140 | 371 | 1039 (12, 8) | 1137 (568) | 7.0 px (max 13) | {'warm/fill': 394, 'warm/line': 77, 'purple/line': 237, 'purple/fill': 254, 'neutral/line': 176, 'neutral/fill': 2} |
| tpose | 1127 | 362 | 723 (1, 6) | 886 (452) | 7.0 px (max 13) | {'warm/fill': 381, 'warm/line': 77, 'purple/line': 237, 'purple/fill': 254, 'neutral/line': 176, 'neutral/fill': 2} |

Profiles (left/right) have no anger shape.

## Files

- Staged shapes: `views/{apose,tpose,left,right}/mouth/{AA,AA_half,EE,EE_half,M,OH,OH_half,smile}.png`
- Sheet (all views): `sheet.png`; per view: `sheet_<view>.png` (before | after | changes, 6x zoom, on base)
- `tone_fix_log.json`, `unsnapped_pixels.csv`, `tone_fix.py`, `views/<view>/palette_region.png`

## Registry / check

Registered in `app/registry.json` (mouth): reports REPORT.md and tone_fix_log.json; media sheet.png and sheet_<view>.png. `status/update.py check` on the default port 8765 gave 323 of 349 broken, because that port was being served by another agent's server rooted at `/workspace/tmpsv_tree`, not shadowveil. A temporary server of my own on 8795, rooted at shadowveil and stopped afterwards, gave 349 checked, 0 broken.
