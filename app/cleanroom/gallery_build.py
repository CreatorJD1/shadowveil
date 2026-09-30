#!/usr/bin/env python3
"""Build app/cleanroom/gallery.json: every file under reference/grok_build/public/clean-room/ and
reference/grok_build/artifacts/ assigned to one gallery group (read-only on the clone).
The gallery page (gallery.html) lazy-loads and paginates each group."""
import json, pathlib, re, os
ROOT = pathlib.Path('/workspace/shadowveil')
GB = ROOT / 'reference/grok_build'
files = sorted(str(p.relative_to(GB)) for base in ('public/clean-room', 'artifacts') for p in (GB / base).rglob('*') if p.is_file())
GROUPS = [  # (id, title, note, regex on path relative to grok_build) — first match wins
 ('turnaround', 'Turnaround', 'layers/rotation turn-000..315 (8 x 45°, 1365x1739, rest.json head y=40 / feet y=1681), base views, turnaround sheets, frames and QA',
  r'layers/rotation/|^public/clean-room/[^/]+\.(png|jpg)$|turnaround|turn-sheet|artifacts/turn/(heads/|qa-heads|qa-backs|angle-contact|rot-samples|fig\d|back\.|left\.|right\.|profile-|apose-rot)'),
 ('eyes', 'Eyes', 'eye parts + rig.json (doNotMirror: amber = her right, green = her left), per-angle eye stills 000/045/090/270/315, face crops, eye QA, per-clip eye layers',
  r'clean-room/eyes/|artifacts/turn/fix/(eyes|face)-|artifacts/turn/face-|artifacts/eyes/|artifacts/turn/[^/]*eye|layers/stack/.*/eyes\.png$|artifacts/turn/(qa-faces|qa-look|wave-iris|chk-)'),
 ('hands', 'Hands', 'hand stills 000/045/315 (L/R lock crops), hands-000/045/180/315, qa-hands.jpg, rig hands, source hand cuts',
  r'hand'),
 ('mouth', 'Mouth / talk', 'talk-speak / talk-ask / talk-laugh + talk clip, QA frames at 0.4/1.8/3.2/5.0 s, talk stills and sheets',
  r'talk|artifacts/turn/qa/|mouth|tongue'),
 ('hair', 'Hair', 'hair angles 000..315 (png+jpg) and hair QA; the hair rest spec is in layers/rotation/rest.json ("High bun, short strands, no wind")',
  r'layers/hair/|artifacts/turn/(hair|bangs|h2-|m-hair|only-hair|off-hair|play-nohair)'),
 ('videos', 'Videos (loops / actions)', 'all other clean-room videos', r'^public/clean-room/videos/'),
 ('hires', 'Hires stills', 'public/clean-room/hires', r'^public/clean-room/hires/'),
 ('sheets', 'Sheets', 'public/clean-room/sheets (composites)', r'^public/clean-room/sheets/'),
 ('frames', 'Frames', 'public/clean-room/frames', r'^public/clean-room/frames/'),
 ('layers', 'Layer cuts', 'layers/anim held frames, layers/stack and layers/hierarchy per-clip / per-still cuts', r'^public/clean-room/layers/'),
 ('rig', 'Rig parts', 'public/clean-room/rig', r'^public/clean-room/rig/'),
 ('imagine_images', 'Imagine images', 'artifacts/imagine_images', r'^artifacts/imagine_images/'),
 ('imagine_videos', 'Imagine videos', 'artifacts/imagine_videos', r'^artifacts/imagine_videos/'),
 ('artifacts', 'Artifacts QA', 'artifacts/** QA frames and checks (turn, qa3..8, vqa, lookqa, drift-audit, crops, tone, root)', r'^artifacts/'),
 ('data', 'Data & pages', 'json specs, html pages, zip', r'.'),
]
out = {g[0]: dict(id=g[0], title=g[1], note=g[2], items=[]) for g in GROUPS}
kindof = lambda f: 'video' if f.endswith('.mp4') else 'image' if re.search(r'\.(png|jpe?g|webp|gif)$', f, re.I) else 'data'
for f in files:
    k = kindof(f)
    gid = next(g[0] for g in GROUPS if re.search(g[3], f, re.I))
    if k == 'data' and gid not in ('data',):
        gid = 'data' if not f.endswith('rest.json') and not f.endswith('eyes/rig.json') else gid
    out[gid]['items'].append(dict(p=f, k=k, b=os.path.getsize(GB / f)))
res = dict(base='../../reference/grok_build/', total=len(files), groups=[out[g[0]] for g in GROUPS])
(ROOT / 'app/cleanroom/gallery.json').write_text(json.dumps(res, separators=(',', ':')))
for g in res['groups']: print(g['id'], len(g['items']))
print('total', len(files))
