# apose-turn reference: eye positions across the turn (measurement only)

**Source frames:** `reference/apose_turn/frames/f001–f241.png`
- 768×1168, 24 fps.
- fNNN is decoded frame index +1; I checked this pixel-for-pixel.
- My first probes decoded the mp4 directly before the frames set was pointed out. Every number below uses the f-numbering.
- Nothing was painted, copied or cut from these frames into our parts, and nothing under `views/` was changed.

## Scale
- Video figure height (bun top to feet) is 1055 px. Ours is 1642 px, so S = 1.56.
- Cross-checks:
  - Front eye width: 22 × 1.56 = 34, ours 34.
  - Eye-to-eye distance: 45 × 1.56 = 70, ours 71.
  - Head width at the eye row: 109 × 1.56 = 170, ours 172.

## The turn
- She turns to her right (nose goes to viewer-left) through a full 360° and ends at the front around f229, holding to f241.
- **Profile 1: f061–f067.** This is where the nose reaches its furthest point. She faces viewer-left, and the visible eye is her left eye (green, EyeL). This matches our `left` view.
- **Back view:** about f105–f115.
- **Profile 2: f151–f163, taking f157.** She faces viewer-right, and the visible eye is her right eye (amber, EyeR). This matches our `right` view.
- **Yaw values are approximate.** They are interpolated linearly between the anchors f001 = 0°, f063 = 90°, f157 = 270° and f229 = 360°. The rotation is eased, so treat them as ±10°.

## When each eye disappears
- **Her right / amber, as the far eye on the way out:** the cheek and nose-bridge contour starts clipping it at about f037 (~52°). It is 5 px at f045 and gone by f049–f051 (~70°).
- **Her left / green, as the near eye:** it narrows to the contour and is last seen at f069. It is gone by f073 (~105°, just past profile).
- **Amber, as the near eye on the way back:** a lash tick shows at f149, and the opening is visible from f153.
- **Green, as the far eye on the way back:** it reappears at the contour at f173, is clipped until about f201, and is clean from f205 (~30°).
- The far eye is hidden for about 14–16 frames on either side of each profile.

## Near-profile eye (video)
**Left profile, green eye, f061–f065:**
- Opening is 11–12 px wide between the lashes (19 px on canvas) and 9–10 px high.
- Iris is 6–8 px wide (9–12 px on canvas).
- The front corner of the opening sits 1–4 px behind the nose-bridge contour at the eye row (x ≈ 323).
- The iris sits at the FRONT of the opening, touching the front corner, with sclera visible behind it toward the ear. At f057 it is still at the front.

**Right profile, amber eye, f153–f161:**
- Opening is 10–16 px (16–25 px on canvas).
- The front corner is 1–2 px from the contour (x ≈ 435).
- The iris is centred to slightly front at f157–f161. The amber iris is faint and low-contrast, so position is ±1 px.

**Both profiles:** the winged lash line runs toward the back (ear side), and the eye is a narrow triangle.

## (1) Our profiles vs the video (scaled ×1.56)

| | video at profile (canvas px) | ours | verdict |
|---|---|---|---|
| left EyeL opening width | 17–19 (f061–f065) | 18 (612–629) | matches |
| left opening height | 14–16 | 16 | matches |
| left iris width | 9–12 | 6 | ours is narrow |
| left gap from nose-bridge contour to front corner | 2–6 | 16 (596 → 612) | ours is about 10 px too far back; matches video ~f053–f057 (≈75–80°) |
| right EyeR opening width | 19 (f157) | 24 (739–762) | ours is wide; matches f161–f163 (≈275°, i.e. 85° from front) |
| right iris width | 9–12 | 10 | matches |
| right gap from contour | 2–3 | 15 (762 → 777) | ours is about 12 px too far back |
| iris at front of opening | yes | yes, in both views (left 612, right 762 front edges) | matches |
| facing and eye identity | left = viewer-left, green; right = viewer-right, amber | same | matches |

Our two profiles are not mirror-consistent. The right eye is 33% wider (24 vs 18). The video's two profiles are the same width, about 12 px (19 on canvas). Both of ours sit about 10–12 canvas px further back from the nose bridge than the video profile.

## (2) EyeBallX sign in the profiles
Rule: `dx = round(X*(dxAtXplus1 if X>0 else -dxAtXminus1))`, so dxAtXminus1 is the dx at X = −1 and dxAtXplus1 is the dx at X = +1.

- **Front (apose):** −1 gives −3 (viewer-left, her right) and +1 gives +1. Correct.
- **Left view:** she faces screen-left and her LEFT side is toward the camera. So +1 (her left) means toward the camera, which moves the iris back from the front corner toward the eye centre: +x.
  - Current values: X = −1 gives +1 and X = +1 gives 0. **This is reversed.**
  - The comment in `eyes/work/export.py` line 354 ("her right (-1) = toward camera") is also wrong for this view.
- **Right view:** she faces screen-right and her RIGHT side is toward the camera. −1 means toward the camera, which moves the iris toward the eye centre: −x.
  - Current values: X = −1 gives −2 and X = +1 gives 0. Correct.

**Fix (not applied):** `eyes/work/export.py` line 355, which swaps the two dx limits:
```
        e='EyeL'; lim=dict(dxAtXminus1=-min(0,eyeinfo[e]['room_px']['left']),dxAtXplus1=min(1,max(0,eyeinfo[e]['room_px']['right']-2)),dyAtYminus1=-1,dyAtYplus1=1)
```
After the fix, left gives X = +1 → +1 px (toward the eye centre / camera) and X = −1 → 0 (front corner anchored).

## (3) Eye width vs frame
Widths are in video px, with canvas ×1.56 in brackets. Full rows are in `width_vs_frame.csv`.

| frame | yaw | her R (amber) | her L (green) |
|---|---|---|---|
| f001 | 0° | 22.5 (35) | 22 (34) |
| f017 | ~22° | 22.5 | 22 |
| f029 | ~41° | 17 | 21 |
| f037 | ~52° | 11, clipped | 20 |
| f045 | ~64° | 5, sliver | 16 |
| f049 | ~70° | gone | 15 |
| f057 | ~80° | – | 13.5 (lash) / 9 (bright) |
| f061–f065 | ~90° | – | 11–12 (lash) |
| f069 | ~99° | – | 7, at contour |
| f073 | – | – | gone |
| f153 | ~265° | 10 | – |
| f157 | ~270° | 12 | – |
| f161 | ~275° | 16 | – |
| f165 | ~281° | 18 | – |
| f173 | ~291° | 21 | 2–3, reappears |
| f181 | ~301° | 23 | 7, clipped |
| f193 | ~316° | 23 | 14, tight |
| f205 | ~330° | ~23 | 18, clean |
| f229 | 360° | 22.5 | 22 |

**Centre offsets:** each eye's centre relative to the head silhouette centre at the eye row, as a fraction of head width. Front is ±0.21. The near eye moves to −0.41…−0.49 at the left profile and +0.44…+0.45 at the right profile. The near eye's width stays at about 20–22 px until about 55° and then drops fast.

## Three-quarter frames with both eyes unclipped (reference/measurement only)
| target yaw | way out | way back |
|---|---|---|
| ~30° | f020–f024: both full width, amber clear of the contour | f205–f209: green gap 8–12 px |
| ~45° | f030–f032: amber is 15–17 px but only about 2 px from the contour (tight) | f193–f197: green gap 2–3 px (tight) |
| ~60° | none; amber is clipped from f037 | none; green is clipped until about f201 |

In this video, no frame shows both eyes clean at 60°.

## Caveats
- Eyes are about 22 px wide in the video. Widths are ±1–2 px.
- "Bright" widths count white plus iris pixels. "Lash" widths are read visually between the lash corners. The profile sclera is shaded, so the two differ by 3–5 px.
- The amber iris is close to skin in HSV, so amber positions are visual reads. Green positions are automated.
- The rotation is eased, so yaw values are approximate.

## Files
- `notes.md`
- `width_vs_frame.csv`
- `turn_eyes_sheet.png`: eye band at key frames
- `compare_profiles.png`: video f001/f063/f157 vs ours at ×1.56, with the eye row marked
- `eye_profile_zoom.png`: 8× zoom of the video profile eyes vs ours downscaled and aligned to the contour
- `zoom.py`: gridded zoom helper
- `tmp/`: scratch images
