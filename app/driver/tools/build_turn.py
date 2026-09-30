#!/usr/bin/env python3
"""Write app/driver/poses.json (v2): the authored A-pose turn (reference/apose_turn/f001-f241) mapped onto the
1365x1739 rest canvas. Uses body_tools/work/apose_turn/angle_map.json when it exists; otherwise a provisional
fit: exact head/foot-line fit (top -> y40, foot -> y1682, profiles y1681) and silhouette-centre match to the
rest view at the anchor frames, linearly interpolated in between. Read-only on all art."""
import json, csv, pathlib, numpy as np
from PIL import Image
ROOT = pathlib.Path('/workspace/shadowveil'); FR = ROOT / 'reference/apose_turn/frames'
BT = ROOT / 'body_tools/work/apose_turn'
AM = BT / 'angle_map.json'
table = {int(r['frame'][1:]): r for r in csv.DictReader(open(BT / 'turn_table.csv'))}
N = 241
LOOP_END = 232   # angle_map: f233-f241 are a slow settle back to ~f001; loop f001..f232 and wrap
def bbox_x(f):
    a = np.asarray(Image.open(FR / f'f{f:03d}.png').convert('RGB')).astype(int)
    body = (a[..., 2] - np.maximum(a[..., 0], a[..., 1])) <= 120
    xs = np.where(body.any(0))[0]; return (xs.min() + xs.max() + 1) / 2
def view_cx(v):
    bb = Image.open(ROOT / f'views/{v}/base.png').split()[-1].getbbox(); return (bb[0] + bb[2]) / 2
am = json.loads(AM.read_text()) if AM.exists() else None
# handoffs: from angle_map when present, else the provisional list the user gave
if am and isinstance(am.get('handoff'), dict):
    handoffs = sorted([dict(frame=int(v['frame']), view=k) for k, v in am['handoff'].items() if isinstance(v, dict) and 'frame' in v], key=lambda h: h['frame'])
elif am and am.get('handoffs'):
    handoffs = [dict(frame=int(str(h.get('frame', h.get('f'))).lstrip('f')), view=h['view']) for h in am['handoffs']]
else:
    handoffs = [dict(frame=1, view='apose'), dict(frame=62, view='left'), dict(frame=109, view='back'), dict(frame=160, view='right')]
bun = {'apose': 101, 'left': 650, 'right': 650, 'back': 650}
anch = {1: 'apose', 62: 'left', 109: 'back', 160: 'right', 233: 'apose'}
fit = {}
for f, v in anch.items():
    t = table[f]; top, foot = float(t['raw_top']), float(t['raw_foot']); ft = float(t['foot_target'])
    s = (ft - 40) / (foot - top); fit[f] = dict(scale=s, dy=40 - top * s, dx=view_cx(v) - bbox_x(f) * s)
if am and isinstance(am.get('handoff'), dict):   # Body's measured per-handoff fit wins over the provisional one
    for k, v in am['handoff'].items():
        if isinstance(v, dict) and 'scale' in v: fit[int(v['frame'])] = dict(scale=float(v['scale']), dx=float(v['dx']), dy=float(v['dy']))
    if 'apose' in am['handoff']: v = am['handoff']['apose']; fit[233] = dict(scale=float(v['scale']), dx=float(v['dx']), dy=float(v['dy']))
    FIT_SRC = 'angle_map.json handoff (per-view scale/offset, uniform), linear between handoffs'
else: FIT_SRC = None
ks = sorted(fit)
angles_anchor = {1: 0, 33: 45, 62: 90, 109: 180, 160: 270, 191: 315, 233: 360}
if am and isinstance(am.get('anchors'), dict):
    angles_anchor = {int(v): int(k) for k, v in am['anchors'].items()}
tab_angle = {}
if am and isinstance(am.get('table'), list):
    for r in am['table']: tab_angle.setdefault(int(r['frame']), []).append(float(r['angle']))
frames = []
for f in range(1, N + 1):
    i = max(k for k in ks if k <= f); j = min([k for k in ks if k >= f] or [ks[-1]]); w = 0 if i == j else (f - i) / (j - i)
    m = {k: fit[i][k] * (1 - w) + fit[j][k] * w for k in ('scale', 'dx', 'dy')}
    if f in angles_anchor: ang = angles_anchor[f]
    elif f in tab_angle: ang = sum(tab_angle[f]) / len(tab_angle[f])
    else: ang = float(table[f]['angle_best'])
    if f > 200 and ang < 30: ang += 360     # the last front frames are ~360
    if f > LOOP_END: ang = 360
    frames.append(dict(f=f, src=f'../../reference/apose_turn/frames/f{f:03d}.png', angle=round(ang, 1),
                       scale=round(m['scale'], 5), dx=round(m['dx'], 2), dy=round(m['dy'], 2)))
source = 'provisional'
if am:   # angle_map wins for angle / scale / offset wherever it gives them
    source = 'angle_map.json anchors/angles + ' + (FIT_SRC or 'provisional scale/offset fit (no handoff fit in angle_map yet)')
    rows = am.get('frames') if isinstance(am.get('frames'), list) else (am.get('map') or [])
    byf = {int(str(r.get('frame', r.get('f'))).lstrip('f')): r for r in rows if isinstance(r, dict)}
    for fr in frames:
        r = byf.get(fr['f'])
        if not r: continue
        for k_src, k in (('angle', 'angle'), ('scale', 'scale'), ('dx', 'dx'), ('dy', 'dy'), ('offsetX', 'dx'), ('offsetY', 'dy')):
            if k_src in r: fr[k] = r[k_src]
        if 'offset' in r and isinstance(r['offset'], (list, tuple)): fr['dx'], fr['dy'] = r['offset'][:2]
# beauty-mark audit per frame (info only; the authored animation is never cut)
audit = {}
for r in csv.DictReader(open(ROOT / 'app/qa/beauty_marks/all_stills.csv')):
    if '/reference/apose_turn/frames/' in r['path']:
        audit[int(r['path'][-7:-4])] = dict(consistent=r['consistent'], confidence=r['confidence'], positions=r['positions'])
for fr in frames: fr['marks'] = audit.get(fr['f'], dict(consistent='n/a'))
out = dict(
    version=2, generated_by='app/driver/tools/build_turn.py', canvas=[1365, 1739], headY=40, footY=1682, fit_source=source,
    fit_note='per frame: rest = frame * scale + (dx, dy). Provisional fit: at f001/f062/f109/f160/f241 the head top maps to y40 and the foot line to y1682 (y1681 profiles), and the silhouette centre to the rest view silhouette centre; linear in between. Replaced by body_tools/work/apose_turn/angle_map.json when it exists (rerun this script).',
    anchors=[dict(frame=f, angle=a) for f, a in angles_anchor.items()],
    handoffs=[dict(h, bun_z=bun.get(h['view'])) for h in handoffs],
    no_hold=[57, 164], no_hold_note='f057 and f164: a hand blends into the hip; the driver never rests or holds there (scrub release is nudged one frame).',
    loop_end=LOOP_END, loop_note='angle_map: f233-f241 settle back to ~f001, so the turn plays f001..f232 and wraps to f001.',
    targets=sorted(set([1, 33, 62, 109, 160, 191] + [f for f in angles_anchor if f <= LOOP_END and f not in (57, 164)]) - {130, 131} | ({132} if 131 in angles_anchor else set())),
    target_note='225° maps to f131 (soft edges per angle_map); f132 is used as the 225° target.',
    hidden_during_turn=dict(eyes='400-413', mouth='500, 510-519, 550-599', hands='300-335, 210-215, 340-379, 216-218', hair='100, 101, 650, 600-619 (+clips), 102, 690-699, 660-689',
        how='During the turn the stage shows only the authored turn frame (eyes, mouth, hands and hair are baked in). The live rig (rig/index.html?view=..., read-only, embedded) is not composited at all, so every live layer above is hidden; its auto (blink / talk) stays off, so eye open 1, gaze 0, mouth open/form 0, fingers/spread/wrist 0 and the hair springs are at rest. Live parts return only at the handoff frames, crossfaded on the matched scale/offset.'),
    despill='Hair-edge despill of the key blue: in a 3 px band next to keyed-out pixels, blue is clamped to max(red, green) + 8 (colour correction of existing pixels only).',
    mirror=False,
    talk=dict(clips=['../../reference/grok_build/public/clean-room/videos/talk-%s.mp4' % k for k in ('speak', 'ask', 'laugh')],
              qa={k: ['../../reference/grok_build/artifacts/turn/qa/%s-%s.jpg' % (k, t) for t in ('0.4', '1.8', '3.2', '5.0')] for k in ('speak', 'ask', 'laugh')},
              note='Front only (resting at f001). 768x1168 plates played 1:1 in the talk panel with the Clean room key and white-flash skip.'),
    removed='The generated turnaround stills clean-room/layers/rotation/turn-000..315.png are no longer used by the driver (user: wrong feet/knees, head backward 135-225).',
    frames=frames)
(ROOT / 'app/driver/poses.json').write_text(json.dumps(out, indent=0))
print(source, [(f, {k: round(v, 3) for k, v in fit[f].items()}) for f in ks])
