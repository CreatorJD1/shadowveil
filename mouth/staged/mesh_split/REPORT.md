# Mouth staged jobs (Base Mouth), 2026-10-02 PT. STAGED: nothing is live

## 1. Mouth lock masks for Base Body's hairless/divided base
`mouth/handoff_hairless/<view>_mouth_lock.png` (1365x1739, L mode, 255 = locked, 0 = free) and a `.json` per view, plus `mouth_lock_summary.json`.
Locked = the union of the opaque pixels of every mouth shape (each inside its partsBBox) plus the rest lips of base.png (base pixels under rest.png alpha; rest.png matches base byte for byte there), dilated by 4 px (Chebyshev, 9x9 square). Body must keep base RGBA byte-identical wherever the mask is 255.

| view | bbox x0,y0,x1,y1 (inclusive) | locked px |
|---|---|---|
| apose | 647,266,714,310 | 2407 |
| tpose | 648,257,715,301 | 2373 |
| left  | 583,248,623,299 | 1512 |
| right | 749,251,790,301 | 1466 |

Generator: `mouth/handoff_hairless/make_lock_masks.py`

## 2. Upper/lower lip + interior split (apose, tpose)
`mouth/staged/mesh_split/<view>/{upper_lip,lower_lip,interior}.png`, `parts.json`, `sheet.png` (8x, #0000FF). Generator: `mouth/staged/mesh_split/make_mesh_split.py`.
- Draw order: interior < lower_lip < upper_lip. upper+lower over base.png changes **0 px** (apose and tpose). With the reverse order it changes 96 px (apose) / 90 px (tpose).
- Seam: in each column, take the darkest rest-lip pixel within anchor.y-6..+3 and extend it to its contiguous run with luminance < 43. The whole dark run goes to upper_lip. The corner columns that have no dark pixel copy the nearest seam column's split.
- Lower flap: 2 px tall, hidden. It extends the lower lip's top-row colour upward in each column and sits fully under upper's opaque pixels.
- Upper flap: 2 px tall, coincident rather than hidden. It's a byte copy of the lower-lip pixels it overlaps. With only two layers in one draw order, both flaps can't be hidden at once. For a true tuck-under in a mesh rig, make the upper flap its own drawable placed below lower_lip.
- Interior: the cavity of AA.png (inner dark, a teeth strip only 2 rows tall, and the tongue) at AA geometry. Hide it at MouthOpen=0. In apose, 5 interior px fall outside the rest lips.
