# diag_posable: posable 45° (f033) and 315° (f191) mouths (STAGED, Base Mouth, Sat Oct 3 2026 ~03:40 PT)

- Rig md5 was **562c32a7** at the start and at the end. qa_gates.py md5 6a5427ae.
- Nothing in rig/, views/, diagonals/ or diagonals_snap/ was changed.
- Following Coder's decision, **frame_scale/ is primary**: full-canvas 768×1168 PNGs in her frame's px, the same format Eyes used. View scale (1365×1739) is secondary.

## Layout (per angle `045/`, `315/`)
- `rig.json`: params, grid, selection (copied from live apose), and the lip-seam anchor in frame and view coords. Parts have parent `head` (head group), layer 500 and chroma key #0000FF.
  - Every non-rest part has `requiresFlag: "diagmouth"`, `defaultOn: false`, an `okLine` and a front-art note. **With the flag off, the mouth always shows rest.** The flag name is a proposal; Coder picks the real one.
- `frame_scale/{rest,M,smile,OH_half,AA_half,EE_half,OH,AA,EE}.png` (primary) and `frame_scale/chroma/<s>_chroma.png`.
- `<s>.png` at view scale and `chroma/<s>_chroma.png`. The chroma files are the part over pure #0000FF in RGB, the same convention as the live `mouth/<view>/<s>_chroma.png`.
- Anchors (lip-seam centre):

| angle | frame coords | view coords |
|---|---|---|
| 045 | (356.5, 212.24) | (634.30, 272.08) |
| 315 | (409.5, 212.53) | (737.02, 275.62) |

- `135_225_NONE.md` and `135_225_check/`: no mouth at 135 or 225 (see below).
- Also here: `sheet.png` (contact sheet), `summary.json`, `gate.json`, `build_log.json`, and the scripts in `tools/` (build.py, gate.py, rigjson.py, sheet.py).

## Rest = HER lips
- The rest is her closed lips cut from f033/f191 with lipcut's detector. Alpha is hard, and every RGB value is her own frame px.
- Frame scale: 189 px (045) and 177 px (315). View scale: 439 / 425 px, the bilinear pixel-centre resample of her frame (lipcut's `to_view`), masked with a hard alpha.

| rest gate | 045 | 315 |
|---|---|---|
| rest over her frame vs f033/f191 (frame) | **0 px** | **0 px** |
| rest over view resample vs view resample | **0 px** | **0 px** |
| opaque on key blue (B>max(R,G)+20) / outside her silhouette (frame) | **0 / 0** | **0 / 0** |

## Shapes (FRONT art bent; flag off by default; each needs its own OK line)
- Each shape is the Job A front mesh-bend cell at the named (Open, Form) from `views/apose/mouth/rig.json`, warped with diag.py's G map.
- Both scales are **rendered natively** at their own resolution (frame 8× supersampling, view 4×). Neither is a resample of the other, so the frame-scale lines are cut at frame resolution, not downsampled.
- Processing:
  - Alpha is hard (0 or 255).
  - Lines are a 1 px skeleton in her diagonal seam tone (045 (39,4,0), 315 (36,8,0)). Gaps of 3 px or less are bridged.
  - Lip px are snapped to her diagonal lip-body tones (175 / 164 tones).
  - Interior px are snapped to #3F2319, #9C5A4A and #EFE4DA.
  - A flat skin pad (her local skin tone) is used only where it has to hide her closed lips and their pale rim. Everywhere else the part is transparent, so her frame shows.
  - Everything is clipped to her face silhouette with the loose key rule.
- Lines: in all 16 shapes at both scales there is **1 component** (no breaks) and **0 2×2 blocks** (1 px wide). Frame lines are 17-26 px, view lines 31-41 px.

## Gates (qa_gates.py `file_report` imported read-only, diagonal palette, tol 2), 36 files
| set | off-palette | chroma | soft edge | colours not in her frame or interior | opaque on key blue / outside silhouette |
|---|---|---|---|---|---|
| frame_scale, 18 files | **0** | **0** | **0** | **0** | **0 / 0** |
| view shapes, 16 files | **0** | **0** | **0** | **0** | **0** (view face mask) |
| view rest 045 | **21** | 0 | 0 | 387 px | 0 |
| view rest 315 | 0 | 0 | 0 | 373 px | 0 |

## Needs a decision
1. **View-scale rest conflicts with itself.** "0 px vs the view resample" forces the resample's bilinear blends into the part. That leaves 21 off-palette px in 045 (0 in 315), plus 387 / 373 px whose colours are blends that exist nowhere in her frame.
   - The frame-scale rest is fully clean.
   - Recommendation: the rig draws `frame_scale/` parts under the same transform it uses for her frame. Rest then matches in any browser, and the view files stay as reference only.
2. **The open shapes are front art, not her diagonal drawing.** They are tiny at frame scale (about 25×10 px), so the lower lip reads mostly as interior. Each one needs its own OK line before the flag is turned on.
3. The flag name `diagmouth` is a placeholder.

## 135 (f087) / 225 (f131): no mouth parts, by design
- **No lip corner is visible at either angle**, so no parts were made.
- In the x10 crops of the cheek-profile edge at mouth height (y 190-240) the jaw contour is smooth and outlined, with no lip notch or lip fill.
- A tone-only scan does flag px: about 80 / 86 px in the profile band, and about 1311 / 1381 px across the whole head region. The marked crops show these are her neck/jaw shading and outline, which share the dark lip tones. They are not lips.
- Files: `135_225_check/check.json`, `crop_*.png`, `jaw_edge_*_marked.png`.
