# hgSub hair/bun sub-offsets v2 (Base Hair, 2026-10-03 ~03:10 PT)

Renders: work/render_parts.py, on index 00892ccb, with the subs cleared (layers nohair/hback/hfront/bun/full; composite = full, 0 px).
Search: work/search.py. Integer shifts in [-15,15]^2 with a rigid bun, then the bun at ±4 relative to the hair. Scoring uses the Coder's measure.py segmentation.
Each cell gives mass_edge / dark_ring_px (baked body dark px newly exposed) / new_hole_px.

| view | (0,0) | Coder live | best edge any |
|---|---|---|---|
| back | 10.97 / 0 / 0 | [1, 0],[-3, -15]: 7.53 / 2 / 64 | [-2, -12]: 7.25 / 16 / 173 |
| left | 9.11 / 0 / 0 | [-10, 0],[14, -10]: 7.83 / 2506 / 170 | [-4, -8]: 8.02 / 1896 / 162 |
| right | 7.86 / 0 / 0 | [13, -1],[-4, -11]: 6.34 / 3448 / 303 | [8, -7]: 6.03 / 2649 / 291 |

## Recommendation
Set **hair = bun = (0,0) in all 3 views**. Out of the full grid, (0,0) is the only shift with 0 ring and 0 holes.
Edge alignment gains of 1.5 to 3.7 px are only possible by exposing the hair that is baked into Body's live_patch base_body (the dark ring: up to 3448 px) or by opening holes.
Shifting the bun on its own (split) makes it worse.
Revisit this only when the posed frames use a truly hairless body.
Rest is unaffected: hgSub only applies to posed frames.
Data: values.json, work/search_back_left_right.json.
