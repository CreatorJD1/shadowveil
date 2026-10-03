# Spot-1 re-check, handtrim underlay (right view), Oct 3 2026 02:05-02:40 PT. Result: FAIL (not stageable)
Renders: rig/index.html md5 00892ccb (served == live, checked before each batch), no ?hairless flag. Ports 8772 (staged) / 8774 (live), copied trees, killed afterwards.
Holes (round2 method, idle clips): armpit f160-176 linear 553->0, ss2 493->0; hip weight_shift linear 1520->0, ss2 912->0.
Rest: 0 px diff (linear, ss2). Rest line vs reference/right.png in armpit/hip ROI: 0 px offset, same width.
Pose extremes +/-25 deg (ShoulderR/ElbowR/HipR/KneeR/twists, single + pairs, 69 poses):
 - HipR -25: hip crack only partly closed (live 76 -> 33 px linear, 68 -> 31 ss2).
 - Visible shape change (new opaque px outside live silhouette, unlined): 23 poses, 628 px linear / 646 ss2.
   ShoulderR -25: 55 px tab x630-637 y625-701 (also every arm_settle frame). HipR -25: 25-27 px x635-638 y809-819.
 - Dark underlay px visible outside her line: linear 0; ss2 34 px in 17 poses + 64 px in arm_settle (x636-639 y712-723).
Locks: hand_erase 0, f7/f10 0, f11 right R_palm 10 px (4 flap-only) at x659-660 y853-857 -> FAIL. Line-art 132.
Palette: 0 off-palette (183,120,76 / 48,46,49 / 11,11,28). Note: 113 live-equal px at x632-639 y643-699 were snapped 13,11,29 -> 11,11,28 at 01:55 by another agent (pre_linetone_snap/), so 971 px now differ from live, not 858.
Sheet: recheck_sheet_00892ccb.png (master | live | staged | diff).
