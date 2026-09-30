# Three-quarter candidates (measure-only; plain copies of Coder's frames, not upscaled, cut or skinned)
Source: /workspace/shadowveil/reference/apose_turn/frames/fNNN.png. Angles: best estimate [folded range]; see ../report.md for the method.
Joint positions (rig scale, ±3-frame neighbours included): candidates.json → joints_rig_viewerLeft_viewerRight.
All eight: 1 connected component (no tears), about 1 px anti-aliased edge (aa band 1.05–1.26 mixed px per edge px, same at f001), no motion blur visible,
flat cel colour with light soft shading (skin dark fraction 3.5–5.9% vs 2.7% on our apose base and 3.2% on our left base).

| frame | target | best ° [range] | raw H vs f001 | foot vs f001 (rig px) | note |
|---|---|---|---|---|---|
| f023 | 30 | 29.9 [22.7–37.1] | +0.57% | +9 | Best 30°. Both arms and legs separate cleanly; the far elbow is still visible. |
| f033 | 45 | 43.9 [37.1–50.6] | +0.76% | +16 | Best 45°. Arms separate, crotch gap closing (hip x not measurable from f036 on). f034 has a slightly softer edge (aa 1.26). |
| f041 | 60 | 63.9 [58.9–68.9] | +0.95% | +16 | Usable. Far elbow is hidden behind the torso (elbow_vl '–'). f040 (55.8°) is the alternative. |
| f085 | 135 | 134.2 [125–143] | −0.76% | −25 | Back three-quarter. The ankle row is merged from f082 back; the figure is about 1–2% smaller in the back half. |
| f129 | 225 | 220.2 [212–228] | −1.14% | −31 | Mirror of 135. Largest foot drift before normalization; f130/f131 have softer edges (aa 1.39–1.42), so avoid those. |
| f183 | 300 | 297.6 [293–303] | +0.76% | +12.5 | Mirror of 60. The far elbow is hidden at f180. |
| f191 | 315 | 314.2 [308–320] | +0.76% | +12.5 | Mirror of 45. Clean. |
| f203 | 330 | 329.3 [323–336] | +0.76% | +12.5 | Mirror of 30. Clean. |
Visual read: the frames look slightly less turned than the best estimate (e.g. f023 looks about 20–25°), which is closer to the lower (leg) cue.
