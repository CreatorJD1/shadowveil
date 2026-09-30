# Base Hands — Shadowveil (contract v1)
Deliverables: /workspace/shadowveil/views/<view>/hands/{rig.json, <H>_palm.png, <H>_<Finger>{1,2,3}.png}
Views: apose, tpose, left, right, back. All PNGs full canvas 1365x1739, x=y=0, keyed RGBA.
Erase masks: /workspace/shadowveil/hands/<view>_hand_erase_mask.png (255 = hand pixel to remove from base; stops at wrist crease).
Work files: chroma/<view>/*.png (parts on #0000FF), previews/, contact_sheet.png, work/ (scripts: defs.py, seg.py, handmask.py, build.py, deliver.py, render.py, check.py, previews.py).
Key colour constant: KEY_COLOR in work/build.py.
Visible pixels are exact copies of base.png; only hidden fill (joint caps, palm fill under finger/thumb bases, T-pose ring/pinky/middle stand-ins) is new flat skin + outline.
Rest check: base.png with mask erased + parts = base.png, 0 px different, all views.
