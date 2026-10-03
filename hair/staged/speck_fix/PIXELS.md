# Speck fix: exact pixels added to the hair erase mask (STAGED, not applied)

For Base Body. These are the stray hair pixels still on `base_body.png` (and `base_body_skin.png`). The staged fix moves each one into its owning strand PNG as an exact `base.png` copy (RGBA), and adds it to `hair/<view>_hair_erase_mask.png`.

- Machine-readable list (x, y, owning strand, base.png RGBA): `hair/staged/speck_fix/for_base_body/speck_px.json`
- Mask of just these pixels, per view (255 = added): `hair/staged/speck_fix/for_base_body/<view>_speck_px_ADD.png`
- Full staged erase mask (live OR added): `hair/staged/speck_fix/hair/<view>_hair_erase_mask.png`
- Coordinates are 0-based `[x, y]` on the 1365×1739 canvas. At every one of these pixels, current `base_body.png` = `base_body_skin.png` = `base.png`.

**What Base Body needs to do before apply:** clear these pixels to alpha 0 in `base_body.png` and `base_body_skin.png`. The alpha<255 ones must end up exactly alpha 0 with no skin fill under them. If the body keeps them, the translucent ones composite twice and rest breaks by 201 px (tpose 23, left 48, right 10, back 120). `apply.sh` refuses to run until this is true.

| view | px | alpha 255 | alpha <255 |
|---|---|---|---|
| apose | 58 | 58 | 0 |
| tpose | 54 | 31 | 23 |
| left | 68 | 20 | 48 |
| right | 23 | 13 | 10 |
| back | 210 | 90 | 120 |
| total | 413 | | |

## apose (58 px)

**strand_01** (24 px, into `views/apose/hair/strand_01.png`):

(581,234) (580,235) (588,235) (589,235) (588,236) (588,237) (588,238) (587,242) (587,243) (586,244) (568,245) (569,245) (586,245) (586,246) (587,247) (567,248) (587,248) (587,249) (565,252) (588,254) (589,254) (592,260) (593,261) (594,262)

**strand_02** (4 px, into `views/apose/hair/strand_02.png`):

(591,116) (600,123) (596,124) (604,129)

**strand_03_tip** (13 px, into `views/apose/hair/strand_03_tip.png`):

(605,272) (608,274) (609,274) (608,275) (608,276) (607,281) (605,285) (598,288) (598,290) (596,293) (605,313) (604,316) (608,321)

**strand_05** (6 px, into `views/apose/hair/strand_05.png`):

(742,96) (742,97) (742,98) (742,99) (744,109) (745,110)

**strand_06_tip** (6 px, into `views/apose/hair/strand_06_tip.png`):

(754,282) (756,284) (752,321) (750,326) (751,327) (750,338)

**strand_07** (5 px, into `views/apose/hair/strand_07.png`):

(771,220) (771,221) (772,222) (779,226) (782,236)

## tpose (54 px)

**strand_01** (17 px, into `views/tpose/hair/strand_01.png`):

(589,219) (594,223) (582,227) (577,233) (592,233) (591,235) (575,236) (575,237) (591,237) (574,238) (591,238) (591,239) (591,240) (591,241) (592,245) (592,246) (594,250)

**strand_02** (8 px, into `views/tpose/hair/strand_02.png`):

(597,116) (597,117) (611,117) (598,118) (599,118) (598,119) (602,121) (606,127)

**strand_03** (10 px, into `views/tpose/hair/strand_03.png`):

(608,264) (607,267) (603,281) (605,284) (605,285) (605,286) (610,309) (611,310) (612,311) (616,319)

**strand_06** (9 px, into `views/tpose/hair/strand_06.png`):

(770,171) (770,177) (777,181) (778,183) (774,200) (772,203) (771,204) (776,222) (779,228)

**strand_06_tip** (10 px, into `views/tpose/hair/strand_06_tip.png`):

(749,263) (759,298) (759,299) (757,304) (756,305) (754,308) (750,316) (749,317) (749,318) (748,322)

## left (68 px)

**strand_01** (68 px, into `views/left/hair/strand_01.png`):

(586,142) (582,144) (581,145) (582,145) (583,145) (580,146) (579,147) (580,147) (587,147) (578,148) (579,148) (578,149) (577,150) (577,151) (576,152) (583,152) (588,152) (576,153) (587,153) (586,154) (585,155) (584,157) (583,159) (578,162) (575,163) (578,163) (577,164) (581,164) (576,165) (576,166) (577,169) (578,169) (578,170) (579,172) (580,176) (581,176) (580,177) (581,177) (580,178) (581,178) (581,179) (581,180) (582,182) (582,183) (582,184) (583,185) (583,186) (583,187) (583,188) (583,189) (583,190) (583,191) (583,192) (583,193) (582,194) (583,194) (583,195) (582,196) (583,196) (582,197) (583,197) (582,198) (582,199) (580,202) (581,202) (578,206) (579,206) (578,207)

## right (23 px)

**strand_04** (23 px, into `views/right/hair/strand_04.png`):

(790,152) (788,156) (794,162) (797,162) (795,163) (796,166) (793,167) (793,168) (794,168) (780,169) (783,169) (783,170) (782,171) (796,173) (780,174) (796,174) (780,175) (782,175) (796,175) (780,176) (780,177) (795,179) (794,183)

## back (210 px)

**strand_01** (29 px, into `views/back/hair/strand_01.png`):

(593,205) (595,206) (593,208) (590,211) (590,212) (595,212) (593,213) (596,213) (591,215) (590,216) (589,217) (588,218) (587,219) (583,220) (586,220) (585,221) (582,222) (583,222) (584,222) (581,223) (582,223) (583,223) (582,224) (580,226) (579,227) (580,227) (579,228) (579,229) (578,232)

**strand_02** (73 px, into `views/back/hair/strand_02.png`):

(613,258) (607,260) (607,261) (607,262) (607,263) (606,264) (611,264) (606,265) (607,265) (606,266) (607,266) (605,269) (606,269) (609,269) (605,270) (606,270) (609,270) (604,271) (605,271) (604,272) (603,273) (603,274) (607,274) (602,275) (603,275) (602,276) (606,276) (601,278) (601,279) (602,280) (603,280) (600,281) (601,281) (602,281) (600,282) (601,282) (600,283) (601,283) (603,283) (602,284) (602,285) (599,289) (599,290) (601,290) (601,291) (601,292) (601,293) (599,294) (601,294) (601,295) (599,296) (601,296) (601,297) (601,298) (600,299) (601,299) (600,300) (600,301) (601,302) (602,303) (602,304) (603,304) (603,305) (603,306) (604,307) (604,308) (604,309) (605,310) (606,311) (607,311) (606,312) (607,313) (608,314)

**strand_04** (75 px, into `views/back/hair/strand_04.png`):

(755,252) (750,257) (750,258) (755,258) (751,259) (755,259) (756,259) (751,260) (756,260) (751,261) (757,265) (753,267) (753,268) (758,268) (755,272) (759,272) (756,274) (760,274) (760,275) (757,276) (758,278) (762,279) (759,281) (762,281) (760,283) (763,284) (763,285) (763,286) (764,286) (763,287) (764,287) (761,288) (763,288) (764,288) (761,289) (763,289) (764,289) (761,290) (764,290) (762,291) (764,291) (762,292) (764,292) (762,293) (764,293) (764,294) (761,297) (763,297) (761,298) (761,299) (762,301) (760,302) (761,302) (760,303) (759,304) (759,305) (760,305) (758,306) (759,306) (760,306) (758,307) (757,308) (758,308) (758,309) (755,311) (756,311) (755,312) (754,313) (755,313) (753,314) (754,314) (752,315) (753,315) (751,319) (752,319)

**strand_05** (33 px, into `views/back/hair/strand_05.png`):

(770,208) (773,208) (773,209) (772,211) (773,212) (767,213) (768,213) (769,213) (773,213) (775,215) (766,216) (772,216) (772,217) (773,217) (773,218) (779,220) (780,221) (778,222) (780,222) (781,222) (778,223) (780,223) (780,224) (782,224) (781,225) (782,225) (783,225) (783,226) (784,227) (785,228) (785,229) (786,230) (787,231)

## FINAL (Fri Oct 2 2026, 8:55 PM PT, checked with the current renderer at main 6d5b239)
The pixel list is **final at 413 px** (apose 58, tpose 54, left 68, right 23, back 210). It is unchanged from the list above.

The six faint clusters that split off at sway were re-checked with the current renderer:
- left strand_01: four clusters, around (576,151), (583,180), (586,193) and (572,200);
- back strand_04: around (756,309);
- back strand_05: around (782–786,224–228).

All the base.png px that connect them to their strand are already in the staged strand as exact copies. The only other base px within 3 px of the split pieces are at the left strand_01 root, where hair_front/hair_back own them. See `work/connect_probe.py` and `work/connect_probe.json`. So no px was added.

The split is the faint 1 px stroke dropping under the ink threshold after resampling. It happens even at s=0 posed (pure ss2 resampling, no rotation). Whether that counts as a defect is scored against the resampling baseline in `hair/qa/lineart/` (step 2).

Consistency check (`work/verify_final.py`): ALL CONSISTENT.
