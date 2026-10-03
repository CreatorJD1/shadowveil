# Ear strands, A-pose (STAGED ONLY) — Base Hair, Fri Oct 2 2026, 9:39 PM PT

Source checked: `body_tools/work/hairless_division_staged/apose/hairless_apose.png`, boxes x595–618 y216–260 (image-left ear) and x746–768 y216–264 (image-right ear).
Every moved pixel is copied unchanged from `views/apose/base.png` (no new paint, no redraw). Nothing in `views/` or `rig/` was written.

## What is hair and what stays body
| group | px | where | goes into | why |
|---|---|---|---|---|
| L_crescent | 90 | x612–618 y216–234 | `hair_front` (layer 600, no sway) | dark strand piece beside the outer eye corner, touches hair_back/hair_front |
| R_crescent | 151 | x746–754 y214–243 | `hair_front` | same, right side (touches hair_back + strand_06) |
| L_flyaway | 3 | x603–604 y258–260 | `strand_03_tip` | faint flyaway below the earlobe (the rest of the left flyaways are already in strand_03_tip) |
| R_flyaway | 32 | x759–769 y254–274 | `strand_06_tip` | faint flyaway lines below the right earlobe (alpha 12–80) |
| **total** | **276** | | | |

Stays body (not cut): 22 faint px that touch the opaque ear/neck outline (its anti-aliasing: L 5, R 17, listed by work/select.py rule "alpha<=80 and not 4-adjacent to alpha>=200"); the ear's outer outline (alpha-AA navy line x595–608 and x757–768), the curved inner ear lines (warm dark, x605–608 y236–248 and x758–760 y238–242),
the face/jaw contour that continues below the crescents (x617–620 y235–260, x743–746 y243–264) and the neck line below the right lobe.
Crescents go into the static `hair_front`, not a swaying strand, so they never move, never uncover and never reach the eyes; hair_back (layer 100) is
not used because base_body (layer 220) would hide them.

## Files
- `views/apose/hair/hair_front.png` (live + crescents), `strand_03_tip.png`, `strand_06_tip.png` (built on the **speck_fix** staged copies, so apply after/with speck_fix)
- `for_base_body/ear_strand_px.json` (x, y, group, part, rgba), `ear_strand_px.png` (RGBA of the moved px), `ear_strand_mask.png`
- `ear_strands_zoom.png` (base | moved px in magenta, both ears, 8x)
- scripts and results in `hair/staged/ear_strands/work/`: `select.py`, `stage.py`, `restsim.sh` (now also overlays brow_strand), `other_views.py` (+ `.json`), `face_check.json`

## Checks
- Rest (rig/rest_check.py in a scratch overlay, speck_fix + ear staging): **0 px all five views** with Body's delivery (crescent px = hairless skin, flyaway px alpha 0).
  With today's base_body left as is: apose 35 px (exactly the 35 flyaway px, double-composited) -> Body must make those alpha 0.
- Hair over eyes/mouth at LINEAR quality (r18, 41 manual x steps + auto-chain extremes, HairSwayY -1/0/+1, 129 poses): **0 px new** (0 staged, 0 baseline).
- Body note: 14 flyaway px are repainted in hairless_apose.png (orange-brown stroke + dot at x759–762 y258–264; x603–604 y258–260). base.png has faint ink over transparent background there; they should be alpha 0.

## Other views (read-only scan, not cut — no hairless sheet from Body yet)
- tpose: same crescent ink beside both outer eye corners is still in base_body: ~x615–624 y192–248 (232 px) and x743–748 y192–242 (176 px).
- left/right/back: dark hair-edge loops along the hair silhouette remain in base_body (listed in `work/other_views.json`); no ear crescents like A-pose. Needs Body's hairless sheet per view to confirm.
