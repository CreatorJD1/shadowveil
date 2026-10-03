# Widow's-peak light outline: design px allow-list (Base Hair, 2:00 AM PT Oct 3)
The user ruled that the faint light outline along her widow's peak is a design choice.

**Allow-list masks** for the colour sweep (white = design px; `wp.py`, `widows_peak.json`):

| View | px | bbox (x / y) | Mask |
|---|---|---|---|
| apose | 53 | x665–698 / y157–174 | `apose_widows_peak_mask.png` |
| tpose | 42 | x668–698 / y155–170 | `tpose_widows_peak_mask.png` |
| left, right, back | 0 | — | empty masks written |

- Selection: base.png px with luminance ≥ 160 within 2 px of dark hair ink, inside the peak box.
- The peak faces away from the camera in left/right/back, so no peak outline was found there.

**No staged fix touched them:**
- Every staged hair file for apose (15) and tpose (10) was compared with live in the mask region (mask + 3 px): **0 px different.** This covers tone_fix, hairfront_holes, lineart_fix, ear_strands (the T-pose 181 px included), merged, speck_fix and brow_strand.
- No hair part has alpha on these px, live or staged. They live in the body: `views/<v>/base_body.png` and Body's `live_patch_staged/base_body.png` equal base.png at all 53 / 42 px.
- diagonals_v2 is a separate angle set, not drawn over these views, so it does not apply.
- Nothing needed restoring.
