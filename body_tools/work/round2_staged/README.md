# Round 2 (right view) staged candidate c3 — NOT live (Oct 2, 2026, 10:35 PM PT)
Needs the user's OK to go live. Nothing under views/ or rig/ was written.

## Files
- skin.json: same main mesh/weights as live (build_skin.py right --sigma-shoulder 12 --sigma-hip-outer 24 --hip-outer-ramp 20 50 --torso-arm-clamp 520:4); new underlay block (image base_body_underlay.png).
- base_body_underlay.png: new underlay image. base_body_skin.png: unchanged copy of live.
- rig.json: no change needed ("skin": "skin.json").
- build_underlay.proposed.py + build_underlay.patch.diff: adds host-strip modes `keep` / `solidkeep` (strip colours come from the host parts' own hidden fill, not from the main image, which shows the limb there at rest).
- Underlay change: --host-strip pelvis:forearm_R:24:700:870:solidkeep,torso:upperArm_R:24:585:640:keep,torso:forearm_R:24:600:640:keep
  (was pelvis:forearm_R:8:710:858). That is a static torso strip 12 px either side of the arm/torso seam at the armpit, plus a solid 24 px pelvis strip at the forearm/hip seam.

## Numbers (renders from a copy of rig at git HEAD 6d5b239; base = live files)
See hole_numbers.json. Armpit hole (arm_settle f160–176) and hip cracks (weight_shift f150–215):
- linear: armpit 553 → 0 (peak 59 @f169 → 0); hip 1520 → 0 (f173–190: 639 → 0; peak 55 @f197 → 0, up to 6 cracks → 0)
- ss2:    armpit 493 → 0 (peak 57 @f170 → 0); hip 912 → 0 (f173–190: 442 → 0; peak 41 @f194 → 0)
- Full clips (linear): no new holes. Leftovers are already in base: 13 px @arm_settle f157 (hand area x748–751), 1 px @weight_shift f57 (base: 5 px).
## Checks (checks/)
- rest_check.py: 0 px in all five views; page Rest check 0 px with quality=linear and with quality=ss2.
- check_skin_rules: head 0 bad triangles, forearm end 0 bad vertices, wrist pivot same. check_underlay: ok (35385 px footprint, 0 touching).
- jointTest 25° / 12.5° (page_linear.json / page_ss2.json): identical to live. Outline mean vs rest, skin+underlay/linear: shoulder +0.49/+0.28 px, hip −0.14/+0.07, elbow/knee/ankle 0.
  ss2 shoulder_R at 12.5° is +1.25 px, the same as live (comes from the ss2 path, not this change).
- outline_check (armpit/hip ROI in the idle renders): same widths, ends, components and kinks as base.
- before_after_sheet.png: columns base linear | staged linear | base ss2 | staged ss2.
