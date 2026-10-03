# Hair at the turn handoff frames: offsets vs the live view (Base Hair), Fri Oct 2 2026, 9:20 PM PT

Read-only QA. The offsets are frame minus live view, in view px (+x = right, +y = down). The frame is mapped into the view with Body's `body_tools/work/apose_turn/angle_map.json` → `handoff` (uniform scale + dx/dy; head top and sole fitted).
Script: `measure.py` (v2). The v1 copy is in `_scratch/measure_v1.py`. Per-view data is in `<view>.json`; images are `overlay_<view>_f###.png` and `sidebyside_<view>_f###.png`.

## Fix in v2 (back f109)
In v1 the back view's whole-hair IoU was 0.27. **This was a mis-segmentation of the live hair, not of the frame.** In the back view, hair_back (layer 100, below the body) carries the whole hair mass, and `base_body.png` carries an identical copy of 20,805 of those px. v1 counted any hair px under an opaque body px as hidden, so the live mask held only the strands.
v2 counts a layer-<200 hair px as visible wherever the body px is transparent or identical to it. For back, the IoU is now 0.85 after the shift. The other views move by 0 px with this change, which confirms the first-pass numbers.

## Offsets
| view | frame | whole hair dx/dy | IoU after | bun dx/dy | bun layer | fringe dx/dy | head silhouette dx/dy | whole ≤6 px? | bun ≤6 px? | fringe ≤6 px? |
|---|---|---|---|---|---|---|---|---|---|---|
| apose | f001 | +1/-10 | 0.88 | +1/-10 | 101 | +1/-10 | +0/-10 | no (10.0) | no (10.0) | no (10.0) |
| left | f062 | -5/+3 | 0.77 | +14/+1 | 650 | -10/+9 | +0/+0 | yes (5.8) | no (14.0) | no (13.5) |
| right | f160 | +13/-2 | 0.81 | -1/-6 | 650 | +17/+1 | +7/+0 | no (13.2) | no (6.1) | no (17.0) |
| back | f109 | +2/+4 | 0.85 | -1/-4 | 650 | — | -1/+0 | yes (4.5) | yes (4.1) | — |

Values in brackets are the offset magnitude in px. "≤6 px?" means whether the jump should hide inside the ~80 ms whole-frame crossfade (≤ ~6 px).

## Reading
- **back f109: hides.** Whole hair +2/+4 and bun −1/−4 (the old −4/−6 came from the bad mask). There is no fringe in back view, and no eyes or mouth at f109.
- **apose f001: does not hide as it stands.** Hair, bun and fringe all sit at +1/−10, but the head silhouette is also 0/−10. So this is head placement in the turn frame (the whole head is drawn 10 px higher), not a hair-only offset. Fixing the head/handoff dy for this frame (Body/Coder `handoff` fit) would bring the hair to about +1/0.
- **left f062: does not hide.** Bun +14/+1 and fringe −10/+9, while the head silhouette is 0/0, so the frame's bun and fringe are drawn in different places from the live profile.
- **right f160: mostly does not hide.**
  - The bun (−1/−6, 6.1 px) is borderline.
  - The fringe (+17/+1) and whole hair (+13/−2) do not hide. The head silhouette is +7/0, so about half of it is head placement and the rest is the drawing.
- The profile fringe gaps (10–17 px), like the mouth gaps (6–13 px, `mouth/work/turn_handoff/offsets.json`), are drawing and placement differences in the turn video. The crossfade will not hide them. Options:
  - pick a nearby frame whose fringe lines up;
  - accept a visible jump;
  - or (Coder/Body) apply a per-view head offset at the handoff: apose 0/+10, and right about −7/0 for the head part.
