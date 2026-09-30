# Shadowveil eyes (Base Eyes), contract v1.1
Parts: views/<view>/eyes/{EyeR,EyeL}_{white,iris,lid_0..7,lash}.png (8 lid frames, recorded as top-level "lidFrames": 8 plus "lidFrameFiles" per eye in rig.json). They are full canvas 1365x1739, binary alpha except lid_1..7 edges, keyed off #0000FF, and each has a *_chroma.png copy alongside. There is also a rig.json per view.
Views: apose, tpose (cut from its own base; not reused from apose), left (EyeL only), right (EyeR only). back has no eyes.
Renderer: tools/render_eyes.py <view> EyeLOpen=.. EyeROpen=.. EyeBallX=.. EyeBallY=.. [-o out.png] [--base base_body.png]
  It uses drawImage semantics only. Per eye it draws the white, then the iris source-atop on an offscreen layer, then the nearest lid frame (round((1-Open)*(lidFrames-1)) = round((1-Open)*7)), then the lash.
Rebuild: work/export.py (it cuts the parts from views/<view>/base.png). Checks: work/verify.py writes verification.json, rest_diff_*.png and preview_*.png.


## Third pass (2026-09-29)
- 8 lid frames (lid_0 exact drawing, lid_7 closed); each frame covers k/7 of the opening area.
- Closed frame: long crease strokes toward nose/brow are replaced by copies of her nearest plain skin; brows, moles and the eyeshadow boundary are kept.
- Lid skin is the median of her skin in a 1-3 px ring around the lid, with a 1 px half-alpha feather; enclosed dark specks are covered.
- Profiles: forward lashes live in lid_0 exactly and ride down with the lid on lid_1..7 (her pixels shifted, root tapered, short bridge to the lid edge). The front iris-edge column is anchored in the white, so no sclera patch opens.
