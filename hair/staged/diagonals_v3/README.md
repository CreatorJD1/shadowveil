# diagonals_v3 (Base Hair, 2026-10-03 ~03:30 PT) — copy of diagonals_v2 (v2 kept unchanged)
Why: Eyes' part outlines include lid skin, so the v2 cut (white+lash+lid_0..7+iris±4, dilated 1) over-carved.
v3 (work/build_v3.py, build_v3.json):
- Eye OPENING = union of Eyes' staged white + iris (pupil is inside iris) + lash parts (eyes/staged/diagonals/<ang>/), viewFit-mapped,
  no dilation, no gaze shift, no lid parts → <ang>/eye_opening_view.png (045: 763 px, 315: 670 px). Hair inside it → alpha 0.
- Px v2 cut outside the opening are restored only where her source turn frame (f033 / f191) draws hair (blue key, <ang>/src_hair_key_view.png),
  snapped (hard alpha) to the live hair-art palette. Px over lid skin that she draws as skin stay out.
- Iris-tone removal: strong green anywhere + iris-part colours within 6 px of the opening (only the 4 px in 315 strand_06, all green).
- Off-palette anywhere: 0 (qa_gates).
Per file (v2 cut → restored over lid / still removed in opening / not restored: src skin / not restored: iris tone):
- 045 hair_front     53 → 9 / 37 / 7 / 0
- 045 strand_03_tip 117 → 7 / 67 / 43 / 0
- 315 strand_06     217 → 39 / 118 / 56 / 4
- all other files identical to v2.
Source check: her frames draw hair over 0 px of Eyes' white/iris at both angles; hair overlaps only Eyes' LASH part (045: 45 px at x587–595 y201–218;
315: 42 px at x772–780 y210–223, the outer-corner lash under strand_06). So at 315 strand_06 does NOT cross the eye white/iris in her
frame — it lies over the outer lash corner only; the 76 other strand_06 px removed inside the opening were v1 cut errors over the white/iris.
QA: qa_gates copy hair/qa/qa_gates_runs/qa_gates_diagv3.py → diagonals 0 off-palette / 0 chroma / 0 soft (34 files); hair over opening 0 at 045/315.
Sheet: eye_crops_v1_v2_v3_source.png (source | v1 | v2 | v3; outline rows: magenta = opening, cyan = restored).
Known (inherited from v2, not from the eye cut): hard alpha 128 leaves ~22% of the mapped hair mask uncovered (045 6378/29512, 315 6819/30729 px)
where v1 alpha was < 128 — the grey patches in the sheet.
