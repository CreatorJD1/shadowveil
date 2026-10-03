# No-mirror check for hair (Base Hair, 1:45 AM PT, Oct 3 2026)

**Result: PASS. No live or staged hair part was made by flipping or mirroring, and the rig flips no hair.**

## 1. Scripts and logs under `hair/` (grep for fliplr/flipud/FLIP_LEFT_RIGHT/ImageOps.mirror/ImageOps.flip/cv2.flip/scaleX/scale(-1/[:, ::-1]/mirror)
- **0 image flips** in any hair script.
- Every hit is something else:
  - `out[::-1]` / `anc(e)[::-1]`: chain list reversal (validate_hair.py, unclamp.py, handoff_hairless/build.py).
  - `[:, ::-1]` on `np.nonzero` output: a (y,x)→(x,y) coordinate swap, not an image flip.
  - "Python mirror of rig/index.html": the renderer re-implementation (tools/render.py, earfill_lib.py, qa docs).
  - `make_hair_actions.py`: "mirrored roll" means the BodyLean sign seen from behind, a parameter value, not pixels.
  - `qa/export_check` "Mirror: f191": the symmetric-angle frame, which is a separately drawn frame (see 3).

## 2. Rig
- `rig/index.html` has no scaleX, scale(-1), flipH or mirror on hair. The only hit is a comment about hands that says "never mirrored".
- No `rig.json` (live or staged) has a scaleX/flip/mirror key.

## 3. Pixel checks
- **Part vs flipped part** (`check.py`, `pairs.json`):
  - Coverage: 153 parts, i.e. every views/*/hair/*.png plus hair/staged/**/hair/*.png (diagonals, diagonals_v2, ear_strands, merged, speck_fix, lineart_fix, tone_fix, hairfront_holes, brow_strand).
  - Each part was flipped and compared with every part, itself included. Each pair with a bbox within 3 px was tested over all offsets, 400 pairs in total.
  - A mirrored copy would score IoU ≈ 1 **and** exact RGBA ≈ 1. No pair does.
  - The high-IoU pairs are near-symmetric shapes:
    - diagonal buns, IoU 0.95–1.0 but exact 1–2%;
    - back hair_back vs itself, IoU 0.94 with exact 31%, which is flat-colour coincidence.
  - The pairs with exact = 1.0 overlap on only a few px (IoU ≤ 0.02).
  - Parts with different bbox sizes cannot be flipped copies.
- **Whole sets, flipped and best-shifted** (`diagonal_pairs.json`):

  | Pair | IoU | Exact RGBA on overlap |
  |---|---|---|
  | 045 vs flipped 315 | 0.787 | 0.2% |
  | 135 vs flipped 225 | 0.894 | 1.1% |
  | diagonals_v2 | same values | same values |
  | live left vs flipped live right | 0.881 | 0.3% |

  These are different drawings.
- **Source turn frames** (her own frames, used by the diagonals):

  | Frames | Exact match in the head zone after flip and best shift |
  |---|---|
  | f033 vs flipped f191 | 1.4% |
  | f087 vs flipped f131 | 2.4% |
  | f025 vs flipped f200 | 1.6% |

  Each angle is a separately drawn frame, not a mirror.
- Sub-offset sets (Job 3) are render-time translations only. ear_strands/merged are exact same-position copies from each view's own base.png.
