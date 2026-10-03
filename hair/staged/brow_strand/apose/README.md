# Brow strand, A-pose (STAGED ONLY): Base Hair, Fri Oct 2 2026, 9:49 PM PT

This follows Base Eyes' change. Only the strand pixels **above and below** the brow stroke are cut. Eyes keeps the crossing pixels (rows y201–203, x630–635) in its lock, so the brow stays exactly as drawn.
Source: `eyes/handoff_hairless/apose_eye_brow_lock.png`, area x618–637, y187–199. The strand is the thin line that continues `strand_04` (pivot 635.3,160.5, 8.2°, swayY 0.75). The other curve in that box (x619–624) is the face/temple contour. It stays body.
All pixels are copied unchanged from `views/apose/base.png`. No new paint. Nothing in `views/`, `eyes/` or `rig/` was written.

## Pixels (`for_eyes_body/brow_strand_px.json`, `.png`, `_mask.png`)
- Above the brow: **24 px**, y191–200, x631–640. This is strand_04's line from its current end (y194) down to the top of the brow, plus 3 anti-aliasing pixels at the tip. 3 px sit just outside the box, at x638/640.
- Below the brow: **11 px**, y204–208, x630–633.
- Total **35 px** in `views/apose/hair/strand_04.png`. The staged file differs from live at exactly these 35 px.
- Crossing kept by Eyes: 18 px (listed in the JSON).
- **Not cut:** a 6 px stub at y209–211 (x628–630) stays body. If cut, it would put strand_04 over the eye at HairSwayY +1: 21 px when cut down to y211, 2 px down to y209, 0 px down to y208. Below y212 the line belongs to the eye parts.
- Lock overlap for Eyes: 19 of the 35 px are inside `apose_eye_brow_lock.png` (all below the brow) and 34 are inside `apose_eye_brow_lock_v2.png`. They now belong to strand_04, so Eyes should drop them from the lock.

## Full-sway check (preset A limits, LINEAR quality, r18 = rig/index.html drawM; `work/gap.json`)
- Pure rotation (x = ±1, HairSwayY 0): **0 px gap** at the brow. Both segments stay on the brow and slide along it by up to 5.7 px; the brow hides the crossing.
- HairSwayY ±1 (2 px drop/lift): **2 px gap** at the brow. The upper piece lifts 2 px off the brow at y −1; the lower piece drops 2 px below it at y +1.
- On the other side, the moving ink overlaps the brow by up to 8 px. That is ink on ink, so no doubled line shows.
- Lower end vs the static stub: the gap is 0 at rest, 2–3 px at half sway and **up to 6 px at x = −1** (end shifts 6.9 px sideways). That is a visible break where the line runs into the eye.
- Hair over eyes/mouth (129 poses): **0 new px**.
- Rest check (rig/rest_check.py, scratch overlay, together with speck_fix and ear_strands): **0 px in all five views**.
- Compared with live today: strand_04 ends at y194, and at full sway that end already breaks ~5.7 px from the static line in mid-forehead. Staging moves the upper break onto the brow, where it is hidden.

## Option for Eyes/Body to choose
`variant_above_only/views/apose/hair/strand_04.png` cuts only the 24 px above the brow. Below the brow stays static, so the line from brow to eye never breaks (0 px). The brow gap is the same 2 px at HairSwayY ±1.
