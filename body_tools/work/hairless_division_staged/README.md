# Base Body — hairless A-pose + Live2D piece division (STAGED, nothing live changed)
Fri Oct 2 2026, ~9:20 PM PT. Scripts: make_hairless.py, divide.py, sheets.py, jointtest.py (bilinear|nearest). Outputs in apose/.
Run order: python3 make_hairless.py apose && python3 divide.py && python3 sheets.py && python3 jointtest.py bilinear && python3 jointtest.py nearest

- hairless_apose.png: base.png with hair mask (hair_mask_used.png) replaced: flat skin (186,129,85) inside head region, 1 px line (13,11,29) on the cranium curve
  (cranium.json, GUESSED half-ellipse c=(682,212) a=75 b=98, crown y=114), ear_line_fill.json reused (45 px), alpha 0 elsewhere. Changed outside mask: 0. All locks: 0.
- pieces/*.png (14, full canvas) + parts.json (layer order, pivot, parent, flaps). Rest recomposite diff: 0 px (hand px from Base Hands' layer).
- Flaps: limbs = disk cap about the rig pivot reaching the outline at the seam, hidden under the covering piece's opaque px; hips also under torso, medial sweep-clipped;
  waist = band under pelvis; neck = flaps under torso and head. Outline only on flap edges exposed within ±25°.
- wrist_line_L/R.json + .png for Base Hands; hand_mask.png.
- Known open items: strand ink drawn over both ears kept (Hair hasn't claimed it); see the Oct 2 ~9:25 PM PT rerun below for what is left in the eye/brow lock;
  lateral hip ledge (~6 px outline step at hip ±25) needs mesh skinning or a different hip seam; 1-3 see-through px at hip/shoulder corners (bilinear).

## Rerun with Base Eyes' new eye/brow lock (Fri Oct 2 2026, ~9:25 PM PT)
- Previous outputs backed up untouched in apose_prev_lock/ (old lock run: 20,793 removed, 5,947 skin + 290 cranium line).
- Lock: eyes/handoff_hairless/apose_eye_brow_lock.png (now eyes + brows only, 4,810 px; was 11,693). make_hairless.py already read this path; the file was replaced by Base Eyes.
- make_hairless.py changes: EAR_TOP=216 (first row where the ears leave the skull outline). Own face-oval lock now starts at EAR_TOP (it used to cover the forehead too);
  cranium.json fringe rule limited to rows < EAR_TOP so the ear/side-head junction is unchanged vs the previous run. New forehead/temple cleanup step:
  zone = head region rows < EAR_TOP minus eye/brow lock (holes filled), mouth, hand, nose, beauty marks, minus the 1 px head-outline ring (cranium line / her outline kept).
  Cleared to flat skin (186,129,85): non-skin components (|rgb-skin|>20) touching the hair mask (<=4 px) + their 1 px halo (>8); then the remaining
  skin-noise px (|rgb-skin| 1..20) of the zone are flattened as well (her noise halo along the old hairline read as a ghost line next to the flat fill),
  except within 4 px of kept art (inner brow tips / nose-bridge shading, 30 px, far from hair) and within 2 px of the eye/brow lock. Only the two sampled colours are written.
  Masks: apose/forehead_clean_zone.png, apose/forehead_clean_mask.png. cranium.json unchanged (the ghost line was not on it).
- Result: hair mask 21,032 px (fringe 227, residual 828); flat skin from the hair mask 6,183 + cranium line 290 + ear line 45; cleared to alpha 0 14,529;
  forehead clean 3,898 px (577 strand/rim px incl. halo + 3,321 skin-noise px), all outside the hair mask. Changed outside hair mask + forehead clean: 0.
  Locks changed: eye_brow 0, mouth 0, hand 0, nose 0, beauty 0, face oval 0. Rows >= 216 identical to the previous run.
- divide/sheets/jointtest rerun: rest recomposite 0 px vs hairless_apose.png (outside hand mask; hand px from Base Hands' layer); joint test ±25 bilinear + nearest:
  0 enclosed holes at every joint (json identical to the previous run).
- Sheets: before apose_prev_lock/sheet_hairless_vs_original.png, after apose/sheet_hairless_vs_original.png; zoom apose/forehead_zoom_before_after.png
  (original | before | after); temple lock overlays apose/temple_L_lock_overlay_after.png, apose/temple_R_lock_overlay_after.png (cyan = lock).
- Left over: strand ink above/through the outer brows sits INSIDE the new eye/brow lock and is kept (lock wins): her-right temple ~48 dark px x 618-637 y 187-199
  (plus the diagonal strand crossing the brow toward the eye), her-left temple ~31 dark px x 730-745 y 188-199, plus ~190 light/noisy rim px inside the lock;
  needs Base Eyes to trim the lock there (or OK to edit inside it).
- Ear strand ink (left alone, Hair hasn't claimed it), rows 216-264: image-left ear x 595-618 (main stroke x 612-618 y 216-260, x 599-610 y 223-250);
  image-right ear x 746-768 (main band x 746-754 y 216-264 between face and ear, x 755-768 y 216-254 on the ear). ~200 px each side.

## Rerun with Base Eyes' trimmed lock v3 (Fri Oct 2 2026, ~9:35 PM PT)
- Backup of the previous outputs: apose_prev_lock_v2/. Lock: eyes/handoff_hairless/apose_eye_brow_lock.png now 4,497 px (v2 kept as apose_eye_brow_lock_v2.png):
  366 px freed above both outer brows (x 618-744, y 183-202); 53 px added = the two former lock holes (skin between brow and lid, x 724-740 / 635-639, y 208-213).
- make_hairless.py tweaks (pre-tweak script copy at /workspace/tmpsv/make_hairless_v3a.py, scratch): strand components count as hair-connected within NEAR=12 px of the
  hair mask (was 4; freed strand ink sits 5-12 px away; inner brow tips / nose bridge are >=30 px away and stay); the 2 px no-flatten band next to the lock now
  protects only darker-than-skin px (possible brow antialias); the light hairline-rim px there are flattened. Brow line itself is inside the lock and untouched.
- Result: hair mask 21,103 px (fringe 298, residual 828); flat skin from hair mask 6,254 + cranium line 290 + ear line 45; alpha 0 14,529; forehead/temple clean 4,309 px
  (862 strand/rim + halo, 3,447 skin noise), all outside the hair mask. vs v2 output: 482 px changed, all to (186,129,85), all in x 618-744 y 183-214.
  Changed outside hair mask + clean: 0. Inside locks: eye_brow 0 (v3 lock), mouth 0, hand 0, nose 0, beauty 0, face oval 0. cranium.json unchanged.
- divide/sheets/jointtest rerun: rest 0 px outside hand mask (0 with hand px from hairless; hand px come from Base Hands' layer); joint ±25 bilinear+nearest
  0 enclosed (json identical to v2).
- Zooms: apose/temple_zoom_before_after.png (original | before v2 | after v3 | after + lock), apose/forehead_zoom_before_after.png (original | first-lock run | now).
- Left over (inside the v3 lock, untouched): diagonal strand across her right brow (kept on purpose) incl. its 3 dark px exiting above the brow at x 633-635 y 199;
  her left temple: a 2 px-wide lock sliver at x 744-745 y 191-199 still holds a short strand stub (3 dark px + light px). Ear strand ink unchanged (see above).

## Hair hand-offs pass (Fri Oct 2 2026, ~9:55 PM PT), lock v4 (4,489 px; v3 kept as apose_eye_brow_lock_v3.png)
- Backup: apose_prev_lock_v3/ (+ make_hairless_v3.py.bak). make_hairless.py now also reads
  hair/staged/ear_strands/apose/for_base_body/ear_strand_px.json and hair/staged/brow_strand/apose/variant_above_only/for_eyes_body/brow_strand_px.json
  (24 px; NOT the 35 px list in the parent folder: the 11 below-brow px and 18 crossing px stay body/lock).
- Eye-corner crescents (L 90 + R 151): 207 -> flat skin (186,129,85); 34 sit inside the eye/brow lock (L 12 x617-618 y216-225, R 22 x746-747 y214-224) and are kept
  as drawn (lock wins; covered by hair_front at rest) -> Eyes should drop them from the lock. None touch the head outline ring; the face/jaw contour below stays.
- Flyaways (L 3 + R 32 = 35): alpha 0 in hairless_apose.png and in every piece (incl. the painted px at x759-762 y258-264). Curved inner-ear lines kept.
- Brow strand above-only: 24 -> flat skin (16 were already flat, 8 freed by the v4 lock at y199-200 x631-635). 0 in lock.
- Own face-oval / beauty-mark boxes exclude the hand-off px (20 crescent px fell inside the beauty box; moles untouched, checked by eye).
- Report: hair mask 21,104; changed outside hair mask + forehead clean + hand-off px 0; all locks 0 px. Rest recomposite 0 px (outside hand mask; 0 with hand px from hairless);
  joint ±25 bilinear+nearest 0 enclosed (identical to v3). Zoom: apose/ear_brow_zoom_before_after.png (both ears/eye corners + right brow; cyan lock, yellow hand-off px).
- Live patch (STAGED, live untouched): apose/live_patch_staged/base_body.png, base_body_skin.png (+ live_patch_report.json): 242 px changed each
  (35 flyaway -> alpha 0, 207 crescent -> skin; 34 locked crescent px left). Scratch rest_check (rig/rest_check.py in /tmp overlay, no symlinked outputs):
  live 0 px all views; Hair staged (speck_fix + ear_strands + brow variant_above_only) + live base_body: apose 35 px (the flyaways); + patched base_body: 0 px all five views.
- Later (T-pose, not done): crescent ink beside both outer eye corners still in base_body, x615-624 y192-248 (232 px) and x743-748 y192-242 (176 px)
  (hair/staged/ear_strands/work/other_views.json; also a 115 px blob x639-666 y196-207 and 169 px x624-660 y212-221 listed there).

## Lock v5 (Fri Oct 2 2026, ~10:02 PM PT): 34 eye-corner px released
- Backup apose_prev_lock_v4/. Lock now 4,455 px (v4 saved by Eyes as apose_eye_brow_lock_v4.png); removed exactly the 34 crescent px (x617-618 y216-225, x746-747 y214-224).
- Rerun: hairless_apose.png differs from v4 at exactly those 34 px, all -> (186,129,85,255). Crescents 241/241 flat skin; flyaways 35 alpha 0; brow 24 flat skin.
  All locks 0 px; changed outside hair mask + clean + hand-off px 0. Face/jaw line below the crescents unchanged.
- live_patch_staged/ rebuilt with the new script make_live_patch.py: base_body.png / base_body_skin.png 276 px vs live each (35 alpha 0, 241 skin); vs v4 +34 px.
- Rest 0 px (outside hand mask; 0 with hand px from hairless); crescent px flat skin in rebuilt pieces 241/241; joint ±25 bilinear+nearest 0 enclosed (identical to v4).
  Scratch rest_check (Hair staged speck_fix + ear_strands + brow variant_above_only + patched base_body): 0 px in all five views. ear_brow_zoom_before_after.png regenerated.
- Small leftover not in Hair's list: 6 dark px x752-754 y224-228 at the image-right ear top (stays; for Hair to classify).

## Speck fix body side, all five views (Fri Oct 2 2026, ~10:55 PM PT) — STAGED
- Hair's speck_fix PIXELS.md confirms: clear the 413 speck px to alpha 0 in base_body.png and base_body_skin.png (no skin under them).
- make_live_patch.py (rerunnable, `python3 make_live_patch.py [view...]`) now writes <view>/live_patch_staged/{base_body,base_body_skin}.png for all five views
  (+ live_patch_report.json): apose = ear hand-off (35 flyaway alpha 0, 241 crescent -> skin) + 58 specks alpha 0 = 334 px per file;
  tpose 54, left 68, right 23, back 210 px per file. right: round2_staged/base_body_skin.png (== live) + specks -> round2_staged/with_specks/base_body_skin.png
  (== right/live_patch_staged/base_body_skin.png). 0 px inside eye/mouth/hand locks in every file.
- apose hairless: all 58 speck px lie outside the head region and are already alpha 0 in hairless_apose.png and every piece -> no change; pieces/joint test unchanged.
- Rest (scratch copied trees, tools/build_full_tree.sh; no symlinks): rig/rest_check.py copy: apose 1034 (exactly Hands' F7 palm flaps, live order palm above forearm;
  0 with live palms), tpose/left/right/back 0; round2 right 0. Page rest check (rig/index.html copy, tools/page_rest.py, quality=linear, ?hairless=1 = hands under
  forearms + hand_mask cut): 0 px in all five views (round2 right 0). Without ?hairless: apose 1034. Control with live body: apose 35, tpose 23, left 48, right 10, back 120.
  Underlay (rest_check + check_underlay.py): ok in all views (round2 right ok, 35385 px footprint).

## A-pose base_body_skin hand cut (Fri Oct 2 2026, ~11:05 PM PT) — STAGED
- make_live_patch.py: for apose and tpose, base_body_skin.png is cut to rgba 0 inside <view>/hand_mask.png (same cut as the pieces; hands under forearms).
  apose: 2,206 opaque skin px cut (hand_mask 17,588 px); base_body.png not cut. tpose: 1,369 opaque skin px cut (hand_mask 8,603 px = hands/tpose_hand_erase_mask.png).
  0 px changed inside eye/brow and mouth locks (both views). Page rest (?hairless=1, rig/index.html copy with its in-memory hairlessHandCut disabled): 0 px all five views.
  Note: the page rest check is 0 with the uncut skin too (hand px of the skin equal base.png at rest), so it can't reproduce Coder's 1,749; the cut was confirmed by px count.

## Skin colour (186,129,85) -> (186,129,86) (Fri Oct 2 2026, ~11:20-11:30 PM PT) — STAGED
- (186,129,85) never occurs in views/apose/base.png; her flat skin is (186,129,86). All fill is now (186,129,86): make_hairless.py (FILL / view_config fill_rgb;
  detection still uses the sampled reference (186,129,85) so masks are unchanged), make_live_patch.py crescents, divide.py flaps (via hairless_report skin_rgb).
- Regenerated apose: hairless/pieces/live_patch equal the old files with 85->86 exactly (0 other px). Everything else recoloured in place by tools/recolour_skin85.py.
  Per-file counts: recolour_skin85_report.json (6,282,883 px total incl. sheets, zooms and apose_prev_lock* backups).
- Kept as drawn: (186,129,85) px that are HER art in views/<v>/base*.png: tpose 467 (base_body/base_body_skin/hairless; spread over the pieces), left 9, right 2, back 3.
  No other (186,129,85) left anywhere under hairless_division_staged/.

## T-pose hairless + 14 pieces (Fri Oct 2 2026, finished ~11:30 PM PT) — STAGED in tpose/
- Source: tpose/live_patch_staged/base_body.png (speck-cleared). Same hair sources as A-pose (live parts + speck_fix/lineart_fix staged parts, specks, residual, fringe).
  Per-view geometry in tpose/view_config.json (make_hairless.py reads it; A-pose output byte-identical without it). Own cranium fit tpose/cranium.json
  (ellipse cx681 cy207 a72 b93 -> crown y114, 1 px outline; ear/jaw junctions (613,242),(748,249)). Ear boxes keep the image-right ear (x753-767 y215-261,
  split from the face by a transparent gap) as body; ear_fill_polys fill the ear concha + ear/head gap only hair covered (290 px). Ear inner lines kept.
  ear_line_fill.json tpose px floating off the ear dropped (14 px, would be specks without hair); 21 kept.
- Hair mask 20,885 px (visible parts 19,437 + specks 54 + residual 1,179 + fringe 215); forehead clean 4,355 px (2,860 skin-noise flatten);
  changed outside hair mask + clean = 0. Locks (exact files): hands/tpose_hand_erase_mask.png 8,603 px -> 0 changed; mouth/handoff_hairless/tpose_mouth_lock.png
  2,373 -> 0; eyes/handoff_hairless/tpose_eye_brow_lock.png 3,425 -> 0 (incl. x741 y209-211 lash/brow); nose, beauty marks, face oval 0.
- Unclaimed eye-corner ink (Hair other_views.json x615-624 y192-248, x743-748 y192-242): no staged T-pose hair part holds it -> kept_boxes, left as drawn (0 non-hair px changed).
- Hair rest mask (hair/handoff_hairless/tpose_hair_rest_mask.png, 19,551 px): 19,459 inside our hair mask; 92 outside (39 cranium-filled, 53 kept: ear rims
  y209-215 and the unclaimed eye-corner ink); 1,426 hair-mask px outside the rest mask (residual/fringe/specks).
- divide.py tpose: 14 pieces, same layers as apose (feet201 shins203 thighs205 forearms220 upper arms222 neck239 torso240 head242 pelvis250), toes in feet,
  hands under forearms (parts.json note). Pivots from views/tpose/body/rig.json + NEW neck (681.5,354), head (681.5,309). Jaw polyline 2-3 px below her jaw line.
  Rebuild 0 px vs hairless (outside hand mask; 0 with hand px). Wrist lines L (1177,386)-(1177,417) pivot (1177,400), R (188,385)-(188,417) pivot (188,400).
- Joint ±25 (jointtest.py <mode> tpose): her T-pose art has 2,698 interior px at alpha 239-254 (faint seams, same at rest) -> counted below alpha 239:
  bilinear 0 enclosed all joints; nearest 0 except 1 alpha-0 px at hip_R +25 (649,851): her alpha 247-251 seam px under the pelvis can't take a flap without
  changing the rest image.
- Rest: scratch tree rig/rest_check.py copy tpose 0 (apose 852 = Hands' F7 palm flaps at the wrists, 0 with live palms; others 0); page ?hairless=1 0 in all five.
- Sheets: tpose/sheet_hairless_vs_original.png, sheet_parts_exploded(.png,_inplace.png), sheet_joint_test_25_*.png, forehead_temple_ear_zoom_before_after.png.
- Scripts now take the view: make_hairless.py <view>, divide.py <view>, sheets.py <view>, jointtest.py <mode> <view> (A-pose outputs byte-identical).

## Left, right, back hairless + pieces (Sat Oct 3 2026, ~00:15 AM PT) — STAGED in left/, right/, back/
Same pipeline as T-pose: `make_hairless.py <view>`, `divide.py <view>`, `sheets.py <view>`, `jointtest.py <mode> <view>`; per-view `view_config.json`,
`cranium.json` (own Catmull-Rom skull fit; no ellipse), `divide_config.json` (jaw/nape cut, NEW neck/head pivots, layers from the live rig, hip caps).
- Source <view>/live_patch_staged/base_body.png (speck-cleared). Locks: exact files eyes/handoff_hairless/{left,right}_eye_brow_lock.png,
  mouth/handoff_hairless/{left,right}_mouth_lock.png, hands/<view>_hand_erase_mask.png (back: hand only, no face locks); own locks: ear boxes, nose, face line.
- Fill tone: (186,129,86) is NOT her tone in these views (base.png: left 8 px, right 0, back 8). Fill = her most common flat skin in views/<view>/base.png:
  left (185,122,78) 25,186 px; right (183,120,76) 23,766 px; back (183,122,77) 24,234 px (Hands' (180,120,77): 233 px). Set by view_config fill_rgb.
  Line (13,11,29). (186,129,85) only her native px (left 9, right 2, back 3).
- Hair mask / clean / fill (px): left 29,370 / 1,819 / 20,188 skin + 476 cranium line; right 30,538 / 1,871 / 20,248 + 465; back 32,310 / 0 / 24,296 + 308.
  Changed outside hair mask + clean = 0 in all three; every lock 0 px; nose/moles/face profile line/ears unchanged. Rest mask px left dark: 4 / 1 / 12 (AA edge px).
- Kept as drawn (Hair other_views.json ink, 0 px cut into a staged part in any view -> kept_ink_mask.png): left 642, right 652, back 504 px
  (Hair's uncut outline ink floating round the skull + faint lines; see hairless_report.json kept_ink_other_views). Also kept (not in any hair part or rest mask):
  left/right faint strand ghost lines on cheek/temple (inside the Eyes lock / face), back nape wisp lines x~650-720 y~277-300 (her neck art).
- back: body_tools/ear_line_fill.json back px (30, the haired-rig lobe/jaw outline) NOT applied (would hang below the lobes once the hair is gone).
- make_hairless.py: new optional keys skin_sample_band, ear_line_fill (apose/tpose byte-identical). divide.py: new optional extra_flaps (apose/tpose identical).
- divide: left 9 pieces, right 9, back 14 (toes in feet). Rebuild 0 px (outside hand mask; 0 with hand px) in all three.
  Pivots NEW: left neck (691.5,376) head (690.5,287); right neck (677.5,377.5) head (681.5,294.5); back neck (681.5,349) head (681.5,300); rest from views/<v>/body/rig.json.
  Profile: torso flap under the upper arm (shoulder), extra hip cap = torso flap under the thigh, r110 (hipcap_L/R); hand over the thigh -> flat under-hand skin on
  the thigh (left 8,988, right 9,390 px). Neck/nape cut is art-based only, NOT against head-group offsets (waits on Coder).
- Wrist lines: left L (703,850.7)-(656,852.2) pivot (678,852); right R (705,855.3)-(676,856.3) pivot (676,857); back L (323.9,744.1)-(293.5,715.4) pivot (308,730),
  R (1069.5,715.4)-(1039.1,744.1) pivot (1055,730). Profile hands lie over the thigh: hand layer must be above the thigh (242) and under the forearm (250).
- Joint ±25 (floor = min interior alpha of her art: left 233, right 237, back 232): 0 enclosed below floor, bilinear and nearest, all joints, except back nearest hip_L -25:
  1 alpha-0 px (537,785): her alpha 241-251 seam inside the hip outline under the pelvis can't take a flap without changing the rest image (same case as tpose hip_R).
  Other enclosed px are her own faint seams (alpha >=233), present at rest.
- make_live_patch.py: hand cut now for every view with pieces; hand px a piece fills are not cut. left 0 / right 0 (all 8,988 / 9,390 hand px are thigh fill),
  back 2,257 opaque px cut (hand mask 16,726). right round2_staged/with_specks/base_body_skin.png == right/live_patch_staged/base_body_skin.png. Eye/mouth locks 0.
- Rest: scratch tree (tools/build_full_tree.sh) rig/rest_check.py copy: left 0, right 0, back 0 (tpose 0; apose 852 = Hands' F7 palm flaps); underlay ok all views.
  Page ?hairless=1, quality=linear, port 8772, served rig/index.html md5 == shadowveil's (db5cf270...; live file was unparsable 00:06-00:27 PT, run after the fix):
  0 px in all five views. (Hair's newer staged tone_fix/hairfront_holes files are not in build_full_tree.sh: those fell back to live.) Server killed.
- Byte-exact locks (00:35 PT): make_hairless keep_alpha0_rgb (l/r/b) keeps her bytes on px transparent in source and output (earlier 21 alpha-0 px per profile
  mouth lock had RGB zeroed). Now eye/mouth/hand locks 0 px byte for byte; changed outside hair mask + clean 0. divide compares alpha-0 as transparent (rebuild 0).
- Sheets per view: sheet_hairless_vs_original.png, sheet_parts_exploded(.png,_inplace.png), sheet_joint_test_25_{bilinear,nearest}.png,
  left/right forehead_temple_ear_zoom_before_after.png, back head_ears_nape_zoom_before_after.png.

## Head-group handoff neck check (Sat Oct 3 2026, ~01:05 AM PT) — STAGED
- Offsets from rig/partmesh/staged/headgroup.json (read only; index.html md5 db5cf270...): apose (0,-9) stretch; left (0,+11), back (+2,+11), right (+3,+5) overlap.
  Backups: <view>/pieces_pre_headgroup/, parts_pre_headgroup.json. parts.json gets "headgroup_handoff". Tools: tools/neck_apose.py, sim.py, expo.py, restchk.py, sheet.py, page_hg.py.
- apose: neck.png extended under the head (138 px changed, all hidden under opaque head at rest): outlines continued straight at x647/x715 in (13,11,29),
  flat skin (186,129,86) between, 12 rows above the jaw/chin per column (9 + 2 margin + 1); 123 hidden old-flap px outside the lines removed (they made the
  jagged sloping outline at the stretch). At -9: 0 enclosed holes, 0 neck px outside her silhouette, outlines continuous 1 px at x647/x715 (before: a break + 2-4 px steps).
- left/back/right: no neck change needed: 0 neck px newly visible (right 1 px (643,286) = her nape outline px at the head/neck junction, inside her silhouette),
  0 px outside her silhouette, 0 new enclosed holes below her alpha floor (new enclosed px are her faint head-edge seams, alpha >= 239).
- All views: rebuild 0, rest vs previous pieces 0, eye/mouth/hand locks 0. Page (copied tree, port 8772, md5 checked, quality=linear, ?hairless=1&headgroup=1,
  RigHeadGroup.applyHandoff(view)): no new see-through at the neck in any view; apose's 18 alpha-0 enclosed px (incl. (603-605,304-306)) are her own hair-strand
  gaps beside the jaw (base.png (602-604,312-314) and (605-608,271-276), x<616, outside the neck; body pieces empty there), moved with the head -> not filled.
  Page rest ?hairless=1&headgroup=1: 0 px in all five views. Note: the page draws the live skinned body, not these pieces.
- Sheets: <view>/sheet_headgroup_neck_before_after.png (rest | before | after at the offset).

## Hair ear_strands masks on left/right/back hairless bodies (Sat Oct 3 2026, ~03:20 AM PT) — STAGED
- Masks: hair/staged/ear_strands/<view>/for_base_body/<view>_body_{skin,clear}_mask.png. skin -> flat skin (left 185,122,78 / right 183,120,76 / back 183,122,77);
  clear -> rgba 0. Backups before any change: <view>/pre_hair_ear_masks/ (hairless, pieces, live_patch_staged, parts.json, hairless_report.json).
- Changed: left hairless 621 (68 skin + 553 alpha0), head 618, neck 3; right hairless 640 (64 + 576), head 637, neck 4 (2 skin + 2 alpha0); back hairless 437 (45 + 392), head 437.
  0 px outside the masks, 0 wrong values, 0 off-palette, eye/mouth/hand-erase/F11 wrist-flap overlap 0. Pieces rebuild == hairless (0 px outside hand mask).
- live_patch_staged/ NOT changed: with the masks applied, page ?hairless=1 rest = 621 / 640 / 437 px (the page still maps the pre-ear_strands hair_front).
  With Hair's ear_strands hair_front in place too it is 0 / 0 / 0, so apply to live_patch together with Hair's hair_front going in. Details + scripts: hair_ear_masks_check/.
- Sheets: <view>/sheet_hair_ear_masks_before_after.png.
