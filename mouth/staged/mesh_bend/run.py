#!/usr/bin/env python3
"""Job A driver: iterate configs over Open x Form grid for apose + tpose, measure, write results.json.
Usage: run.py iterate   -> runs every config in ITERATIONS, appends summaries to iterations.json
       run.py final N   -> renders/sheets/results for iteration N's config"""
import json, os, sys, time, copy
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bend import *
from measure import *

VIEWS = ['apose', 'tpose']
ITERATIONS = [
    ('it1 naive: coarse 6x4 grid, rigid lips, no pins/pad, flaps inside parts, interior unclipped, parabola open',
     dict(mesh='grid', sx=6, sy=4, bands=False, pins=False, pad=0, flaps='in_parts', clip_ext=None, minfill=0.25,
          open_profile='parabola', press=False, corner_dx=True, interior_tuck=0.0, interior_xover=0.0,
          clamp_always=False, interior_fit=False, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it2 + interior clipped to the lip gap, flaps split to own layers under the bodies',
     dict(mesh='grid', sx=6, sy=4, bands=False, pins=False, pad=0, flaps='own_layers', clip_ext=1.0, minfill=0.25,
          open_profile='parabola', press=False, corner_dx=True, interior_tuck=0.0, interior_xover=0.0,
          clamp_always=False, interior_fit=True, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it3 + pins on the vacated side + 3 px base.png skin pad',
     dict(mesh='grid', sx=6, sy=4, bands=False, pins=True, pad=3, flaps='own_layers', clip_ext=1.0, minfill=0.25,
          open_profile='parabola', press=False, corner_dx=True, interior_tuck=0.0, interior_xover=0.0,
          clamp_always=False, interior_fit=True, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it4 feature-aligned triangle strips (every 2nd column) + rigid line bands with compressible fill (her AA/AA_half lip thinning) + M/smile press',
     dict(mesh='strip', sx=2, sy=2, bands=True, pins=True, pad=3, flaps='own_layers', clip_ext=1.0, minfill=0.25,
          open_profile='parabola', press=True, corner_dx=True, interior_tuck=0.0, interior_xover=0.0,
          clamp_always=False, interior_fit=True, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it5 + interior tucked 1.5 px under both lips and 2 px past the corners, her cavity profile for the open hinge',
     dict(mesh='strip', sx=2, sy=2, bands=True, pins=True, pad=3, flaps='own_layers', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=False, interior_fit=True, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it6 + thin-column fix: when a column has no compressible fill the edge band moves with the seam band',
     dict(mesh='strip', sx=2, sy=2, bands=True, pins=True, pad=3, flaps='own_layers', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it7 strips at every column (sx=1)',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, pad_split='nearest', interior_extrap=False, interior_fill=False)),
    ('it8 flaps overlap their owner by 2 px and run along every column (incl. skin pad); pad split at the seam row; interior pad columns extrapolated (no fold)',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, interior_fill=False)),
    ('it9 rigid line band widened to the line\'s dark AA and corner branch (L<50); smile widening spread linearly instead of at the corner tips',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', interior_fill=False)),
    ('it10 pixel-snapped rigid bands: seam band, lip-edge bands and column shifts move by whole pixels; fill/skin take the fractions',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap='xy', interior_fill=False)),
    ('it11 snap vertical only (whole-pixel dy per column); horizontal stays continuous because snapping an inward (M) squeeze folds columns',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap='y', interior_fill=False)),
    ('it12 staged interior notches (1-2 px per column, her AA.png pixels the cavity classifier skipped) closed from AA.png',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=1.0, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap='y')),
    ('it13 interior clip tightened to 0.5 px past each lip edge (snapped bands make the edges whole-pixel)',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=0.5, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap='y')),
    ('it14 control run: it13 without pixel snapping (continuous sub-pixel bands), to show what a runtime without snapping gets',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=0.5, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap=None)),
    ('it15 it13 + the min-fill clamp excess spread along x (min/max filter then box, k=3) so each lip-edge band moves as one piece: removes the per-column comb on the upper-lip top edge at open',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=0.5, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap='y', xsmooth=3)),
    ('it16 it15 with a narrower spread (k=1): keeps the comb fix but gives back silhouette IoU lost by k=3 lifting whole edge runs',
     dict(mesh='strip', sx=1, sy=2, bands=True, pins=True, pad=3, flaps='own_layers_overlap', clip_ext=0.5, minfill=0.25,
          open_profile='her', press=True, corner_dx=True, interior_tuck=1.5, interior_xover=2.0,
          clamp_always=True, interior_fit=True, t_band=50, dx_profile='linear', snap='y', xsmooth=1)),
]
FINAL = 15   # index of the config used for the deliverables (it16)

_views = {}; _calib = {}; _her = {}
def view_for(v, cfg):
    return get_view(v, cfg.get('pad', PAD), cfg.get('t_band', 43), cfg.get('pad_split', 'seam_row'), cfg.get('interior_fill', True))
def get_view(v, pad, t_band=43, pad_split='seam_row', interior_fill=True):
    k = (v, pad, t_band, pad_split, interior_fill)
    if k not in _views: _views[k] = View(v, pad=pad, t_band=t_band, pad_split=pad_split, interior_fill=interior_fill)
    return _views[k]

def get_calib(v):
    if v in _calib: return _calib[v]
    p = f'{HERE}/calib.json'
    allc = json.load(open(p)) if os.path.exists(p) else {}
    if v not in allc or 'AA' not in allc[v] or 'edges' not in allc[v]:
        allc[v] = calibrate(get_view(v, PAD))
        json.dump(allc, open(p, 'w'), indent=1, default=float)
    _calib[v] = allc[v]
    return allc[v]

def run_cfg(cfg, keep=False):
    out = {}
    for v in VIEWS:
        V = view_for(v, cfg); C = get_calib(v)
        if v not in _her: _her[v] = her_crops(V)
        rest = render_cell(V, C, cfg, 0, 0)
        cells = {}
        for o in OPENS:
            for f in FORMS:
                cell = rest if (o == 0 and f == 0) else render_cell(V, C, cfg, o, f)
                m, comp = measure_cell(V, cell, rest, _her[v], o, f)
                if keep: m['_cell'] = cell; m['_comp'] = comp
                cells[(o, f)] = m
        out[v] = cells
    return out

def summarise(res):
    S = {}
    for v, cells in res.items():
        ms = list(cells.values())
        s = {}
        s['rest_px'] = cells[(0, 0)]['diff_vs_base_px']
        s['seam_ink_dev_median'] = round(float(np.median([m['seam']['ink_dev_median'] for m in ms])), 3)
        s['seam_ink_dev_max'] = round(float(max(m['seam']['ink_dev_max'] for m in ms)), 3)
        s['seam_darkrun_dev_max'] = int(max(m['seam']['darkrun_dev_max'] for m in ms))
        s['seam_break_cols_total'] = int(sum(len(m['seam']['break_cols']) for m in ms))
        s['seam_component_mismatch_cells'] = int(sum(m['seam']['components'] != m['seam']['components_rest'] for m in ms))
        s['outline_dev_median'] = round(float(np.median([m['outline']['dev_median'] for m in ms])), 3)
        s['outline_dev_max'] = round(float(max(m['outline']['dev_max'] for m in ms)), 3)
        s['outline_breaks_total'] = int(sum(len(m['outline']['break_cols']) for m in ms))
        s['holes_max_px'] = int(max(m['holes']['base_lip_showing_px'] for m in ms))
        s['holes_strict_max_px'] = int(max(m['holes']['base_lip_showing_strict_px'] for m in ms))
        s['max_seethrough'] = round(float(max(m['holes']['max_seethrough'] for m in ms)), 3)
        s['inner_holes_max_px'] = int(max(m['holes']['inner_hole_px'] for m in ms))
        s['interior_spill_max_px'] = int(max(m['interior']['spill_px'] for m in ms))
        s['interior_outside_hull_max_px'] = int(max(m['interior']['outside_lip_hull_px'] for m in ms))
        s['blue_spill_max_px'] = int(max(m['blue_spill_px'] for m in ms))
        s['flipped_tris_max'] = int(max(sum(m['flipped_tris'].values()) for m in ms))
        s['iou_sil'] = {m['her']: m['iou_sil'] for m in ms if 'her' in m}
        s['iou_opening'] = {m['her']: m['iou_opening'] for m in ms if 'her' in m and m['iou_opening'] is not None}
        s['pass'] = dict(rest=s['rest_px'] == 0,
                         line_width=s['seam_ink_dev_max'] <= 1.0 and s['outline_dev_max'] <= 1.0,
                         no_breaks=s['seam_break_cols_total'] == 0 and s['outline_breaks_total'] == 0 and s['seam_component_mismatch_cells'] == 0,
                         no_holes=s['holes_max_px'] == 0 and s['inner_holes_max_px'] == 0,
                         no_interior_spill=s['interior_spill_max_px'] == 0,
                         no_blue=s['blue_spill_max_px'] == 0)
        S[v] = s
    return S

def jsonable(cells):
    return {f'o{o}_f{f}': {k: v for k, v in m.items() if not k.startswith('_')} for (o, f), m in cells.items()}

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'iterate'
    if mode == 'iterate':
        which = [int(a) for a in sys.argv[2:]] or range(len(ITERATIONS))
        p = f'{HERE}/iterations.json'
        hist = json.load(open(p)) if os.path.exists(p) else {}
        for i in which:
            label, cfg = ITERATIONS[i]
            t = time.time()
            res = run_cfg(cfg)
            S = summarise(res)
            hist[str(i + 1)] = dict(label=label, cfg=cfg, summary=S, seconds=round(time.time() - t, 1),
                                    cells={v: jsonable(c) for v, c in res.items()})
            json.dump(hist, open(p, 'w'), indent=1, default=float)
            print(f'== {label}  ({time.time() - t:.0f}s)')
            for v, s in S.items():
                print(' ', v, json.dumps({k: s[k] for k in s if k not in ('iou_sil', 'iou_opening')}))
                print('    iou_sil', s['iou_sil'], 'iou_open', s['iou_opening'])
            sys.stdout.flush()
