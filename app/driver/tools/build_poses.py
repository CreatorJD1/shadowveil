#!/usr/bin/env python3
"""Write app/driver/poses.json from the rest spec, the beauty-mark audit (eyeballed turn stills) and align.json."""
import json, pathlib
ROOT = pathlib.Path('/workspace/shadowveil'); GB = ROOT / 'reference/grok_build'
rest = json.loads((GB / 'public/clean-room/layers/rotation/rest.json').read_text())
eyerig = json.loads((GB / 'public/clean-room/eyes/rig.json').read_text())
ov = json.loads((ROOT / 'app/qa/beauty_marks/tools/overrides.json').read_text())
cls = {c['path']: c for c in json.loads((ROOT / 'app/qa/beauty_marks/tools/classified.json').read_text())}
al = json.loads((ROOT / 'app/driver/align.json').read_text())
A = lambda kind, a: next((x for x in al if x['kind'] == kind and x['angle'] == a), None)
ok = lambda r, n=0.95: r and r['ncc'] >= n and r['mad'] <= 8
U = lambda p: '../../' + p
stills = []
for a in range(0, 360, 45):
    p = f'reference/grok_build/public/clean-room/layers/rotation/turn-{a:03d}.png'
    o = ov[str(ROOT / p)]; c = cls.get(str(ROOT / p), {})
    visible = o['consistent'] != 'n/a'
    st = dict(angle=a, src=U(p), consistent=o['consistent'] in ('true', 'n/a'), marks_visible=visible,
              audit=o['consistent'], note=o['note'], detector=c.get('positions', ''), overlays={})
    e = A('eyes', a)
    if e is None: st['overlays']['eyes'] = dict(use=False, why='no eye still for this angle; the turnaround still keeps its own eyes')
    elif ok(e): st['overlays']['eyes'] = dict(use=True, src=U(e['src']), x=e['x'], y=e['y'], scale=e['scale'], ncc=e['ncc'], key='blue', why=f"aligned by template match (NCC {e['ncc']}, scale {e['scale']} = the crop is a 2x enlargement)")
    else: st['overlays']['eyes'] = dict(use=False, src=U(e['src']), ncc=e['ncc'], why='could not be aligned cleanly; left off')
    hs = []
    for side in 'LR':
        h = A('hand' + side, a)
        if h is None: continue
        hs.append(dict(side=side, use=bool(ok(h, 0.9)), src=U(h['src']), x=h['x'], y=h['y'], scale=h['scale'], ncc=h['ncc'], mad=h['mad'],
                       why=('aligned (NCC %.3f)' % h['ncc']) if ok(h, 0.9) else 'match too weak; left off'))
    st['overlays']['hands'] = hs or [dict(use=False, why='no hand still for this angle; the turnaround still keeps its own hands')]
    hq = A('hands', a)
    if hq: st['overlays']['hands_strip'] = dict(use=False, src=U(hq['src']), ncc=hq['ncc'], why=f"hands-{a:03d}.jpg is a resampled QA strip (best NCC {hq['ncc']} at scale {hq['scale']}); not aligned cleanly, shown in the side panel only")
    hr = A('hair', a)
    st['overlays']['hair'] = dict(use=False, src=U(f'reference/grok_build/public/clean-room/layers/hair/hair-{a:03d}.png'), ncc=hr and hr['ncc'],
                                  why='hair-NNN.png is a separate 1344x1472 drawing, not registered to the rotation canvas (best NCC %.2f); the still\'s own hair is the rest-spec hair. Shown in the side panel.' % (hr['ncc'] if hr else 0))
    stills.append(st)
out = dict(
    generated_by='app/driver/tools/build_poses.py', canvas=rest['canvas'], headY=rest['headY'], footY=rest['footY'],
    rest=rest, eyes_rule=eyerig['doNotMirror'], gaze=eyerig['gaze'], mirror=False,
    canonical_marks='turn-000: 1 mark under her right (amber) eye, 2 under her left (green) eye = viewer-right cheek in front views (plus a faint 1-2 px speck).',
    policy=dict(rule='Only blend between stills that are both consistent. consistent = marks match turn-000, or marks are not visible (face turned away, expected).',
                skip='default: blend directly between the nearest consistent stills on either side of the angle',
                hold='alternative: hold the last consistent still (in the direction of travel) until the next consistent one is reached',
                targets='inconsistent stills are never pose targets'),
    talk=dict(clips=[U('reference/grok_build/public/clean-room/videos/talk-%s.mp4' % k) for k in ('speak', 'ask', 'laugh')],
              qa={k: [U(f'reference/grok_build/artifacts/turn/qa/{k}-{t}.jpg') for t in ('0.4', '1.8', '3.2', '5.0')] for k in ('speak', 'ask', 'laugh')},
              front_window_deg=10, note='Talk clips are 768x1168 arms-down plates (not the A-pose, figure 1136 px tall vs 1641 on the rest canvas). Upscaling is not allowed by the rest spec (upscale:false), so they play 1:1 in the talk panel beside the stage, only while the head is at the front (|angle| <= 10°), keyed and with the Clean room white-flash skip.'),
    hair=dict(spec=rest['hair'], hide='Hair toggle uses the Clean room skin-fill mask (applyPartMask with hair off): hair pixels inside the skull ellipse take the mean face-skin colour sampled from the same still, the rest are made transparent. Authored-pixel masking, nothing drawn.'),
    stills=stills)
(ROOT / 'app/driver/poses.json').write_text(json.dumps(out, indent=1))
for s in stills: print(s['angle'], s['consistent'], s['audit'], s['overlays']['eyes']['use'], [h['use'] for h in s['overlays']['hands']])
