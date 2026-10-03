# (B) ?armsub=1: forearm sub-rotation at turn handoffs (staged)

Coder, Sat Oct 3 2026, PT. Live in rig/index.html md5 562c32a7 (02:38 PT), behind the flag only.

## API
- `window.RigArmSub.applyHandoff(view)`, then `RigArmSub.easeTo(0, ms)` (the same pattern as RigHeadGroup), plus `set` / `get` / `reset`.
- The sub angle is added to the forearm's posed angle in the render chain (`bodyAngleAS`). Calibration uses of `bodyAngle` are untouched.
- Applies only when POSED, so never at rest.
- Hands ride the forearm matrix, so each palm stays on its wristPivot (the rest distance, which the rig already checks at ≤2 px).
- Table: `rig/partmesh/staged/armsub.json`.

## Measurement
- `measure_arm.py` → `handoff_arm_offsets.json`: edge-NCC of forearm + hand, turn frame vs live, relative to the torso offset. Confidence is low (ncc 0.12–0.25).
- `ik.py` → `armsub_fit.json`.

| handoff | wanted wrist move (rel. torso) | forearm-only deg (table) | residual after | 2-bone (upperArm + forearm) deg | residual |
|---|---|---|---|---|---|
| left f062, L | (+5, −37) | +0.4 | 37.3 px | −15.9 / +30.0 | 14.6 px |
| back f109, L | (−34, −5) | +7.4 | 20.1 px | +5.4 / −1.8 | 18.2 px |
| back f109, R | (+30, −9) | −7.5 | 14.5 px | −5.4 / +1.9 | 12.5 px |
| right f160, R | (+5, −17) | −1.8 | 16.4 px | +14.5 / −29.4 | 0.1 px |

**Conclusion.**
- In the profiles, the frame's hand sits higher (shorter, foreshortened arm). A forearm rotation cannot produce that. Only the back gets a real reduction, about 40%.
- Fixing the profiles needs an elbow bend about 30° (looks wrong) or a scale/foreshortening term. Base Body / the user should decide.

## Checks (`as_check.js` on a served copy, 8792)
- `&armsub=1`: rest 0 px in all 5 views, 0 page errors.
- Posed px changed by the sub: back 51809, left 13881, right 19368; apose/tpose 0 (no entry).
- After `easeTo(0)`: 0 px vs off.
- Default 30/30 identical vs 00892ccb (`default_same.txt`).
- The posed palm↔wristPivot distance was not read back (BM is not reachable from page scope). It holds by construction, because the hands use the forearm's matrix.
