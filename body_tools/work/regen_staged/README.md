# Targeted regen — staged, NOT live (Oct 3, 2026, ~1:30 AM PT)
No AI pixels were applied. None of the four spots turned out to be a broken texture px that a tight-mask regen can fix with rest = 0.
Lock overlaps for every mask: lock_overlaps.json (eye, mouth, hair rest/sway, hands/<v>_hand_erase_mask, wrist flaps f7/f10 L/R palms; f11 doesn't exist; line art = base.png px with alpha>128 and max rgb<70).
- spot1_right_hip_armpit: round2_staged c3 underlay touches 7 px of hands/right_hand_erase_mask (x707-710, y865-867). base_body_underlay_handtrim.png puts those 7 back to live (858 changed px, hand 0, wrist 0). NOT re-rendered. Line-art overlap is 132 (hidden host-strip copies at her line px locations).
- spot2: crotch notch = mesh/weights (thigh edges with no line open a flat-topped gap at hipR+25 / hipL-25 / splay). See spot2_crotch_notch_sheet.png. Not texture.
- spot3: turn-handoff gaps are proportion/pose mismatches (apose_turn/report.md). Not a tight mask.
- spot4_seam_holes: tpose source px (673,832) is her line px, so it is rejected. The back candidate (551,756) on thigh_L is flat skin (183,122,77): 1 px, all locks 0, but rest changes 1 px (alpha 247->255).
