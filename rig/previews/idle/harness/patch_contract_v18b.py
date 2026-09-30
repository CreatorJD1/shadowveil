# contract v1.8 part 2: HeadTilt/HeadNod and the hair inertia input (applied to the output of patch_contract_v18.py)
import sys
src,dst=sys.argv[1],sys.argv[2];s=open(src).read()
def R(old,new):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'anchor {n}x: {old[:80]!r}')
    s=s.replace(old,new)
R("Hair: switchable spring presets `default` (unchanged) / `A` / `B`, and every chained segment is clamped to its own limit after chaining.",
  "New head params `HeadTilt` (roll, ±8°) and `HeadNod` (pitch, ±6°) on the body's head part, pivoting at the neck seam, with a renderer-side neck gate so the seam stays closed (section 3). Hair: switchable spring presets `default` (unchanged) / `A` / `B`, every chained segment is clamped to its own limit after chaining, and the springs now also get the head's acceleration (root motion, lean and head params) as an inertia input (section 7).")
R("| `RootX`, `RootY` | -40 to 40 px (+x right, +y down; applied in whole px) | 0 | renderer / clip player (v1.8) |",
  "| `RootX`, `RootY` | -40 to 40 px (+x right, +y down; applied in whole px) | 0 | renderer / clip player (v1.8) |\n"
  "| `HeadTilt` | -1 to 1 (±8° roll about the neck seam; + = clockwise on screen) | 0 | Base Body (v1.8) |\n"
  "| `HeadNod` | -1 to 1 (±6° pitch; + = chin down / forward) | 0 | Base Body (v1.8) |")
R("\nNothing else may be animated. A new parameter needs a version bump of this contract.",
  "\n**Head (v1.8).** `HeadTilt` and `HeadNod` move the body's head part (cut part `head`, or the skin's `headBone`) about the neck seam centre, which the renderer finds at load: the centroid of the head-mesh vertices that touch torso vertices (apose 681,364; tpose 673,356; left 693,378; right 678,379; back 682,350), or the head part's pivot for cut parts. "
  "Everything that already rides the head moves with it as one block: eyes (400–403, 410–413 and the eye band 450–499), mouth (500, 510–519, 550–599), hair_back 100, the bun (101/650), hair_front 600, strand roots 601–619 with their chained children, and the hair bands 110–199 and 660–699. "
  "In the front and back views `HeadTilt` is a rotation of ±8°, and `HeadNod` is a vertical offset of ±4 px (+ = down) with no in-plane rotation, because an in-plane rotation there would read as a tilt. In the profiles `HeadNod` is a real ±6° rotation toward the facing side (left view counter-clockwise, right view clockwise for +1), and `HeadTilt` is not drawn (a roll is about the viewing direction's normal and has no clean in-plane equivalent). "
  "**Neck gate:** with a skin mesh the head vertices within 36 px of the seam blend from the torso transform (at the seam) to the head transform (36 px up, smoothstep). The weights are the renderer's own copy; `skin.json` is untouched. At `HeadTilt = HeadNod = 0` the head transform equals the torso transform, so the blend changes nothing (rest and all v1.7 poses render exactly as before). Measured at ±1 of each param alone: 0 px of alpha loss at the seam in all five views. With cut parts (skin off) there is no gate, and the head is a rigid rotation. The eyes and mouth sit at least 60 px from the seam, so they stay rigid with the head. `headPose()` reads the new head angle, so the hair springs react to it.\n\n"
  "Nothing else may be animated. A new parameter needs a version bump of this contract.")
R("  - **Chained limit (v1.8):**",
  "  - **Inertia input (v1.8):** the springs get the head's acceleration, taken from the head position of `headPose()` (which includes `RootX`/`RootY`, the lean and the head params) and low-passed over 0.05 s. The chain roots' targets get an offset: vertical `-a_y / 1500 px/s²` (the head accelerating up makes the hair drop), and horizontal `0.5 · a_x / 1500 px/s²` (the hanging tips lag). Each offset is clamped to ±1, and so is the total target, so the limits hold with every preset and with the chained clamp. At rest nothing changes. Vertical travel stays small because it is bounded by the hair's own `swayY × swayYMaxPx` (3 px).\n"
  "  - **Chained limit (v1.8):**")
R("So small rotations no longer flip parts between pixel-exact and smoothed drawing.","So small rotations no longer flip parts between pixel-exact and smoothed drawing. A single-frame sharpness pulse remains with `linear` whenever a joint passes very close to 0° (resampling is exact only there): measured on the apose idle torso/face, 8 steps over 1.5% and 3 pulse reversals in 5 s. `2x supersampled` (`quality=ss2`, URL `quality=`) removes it (0 steps, 0 reversals, 0 spikes; mean sharpness 0.96 of rest), so exports and previews should use `ss2`. Rest is always drawn 1:1 in every mode.")
open(dst,'w').write(s);print('ok')
