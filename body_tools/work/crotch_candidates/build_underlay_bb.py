#!/usr/bin/env python3
"""Skin underlay (contract v1.5 section 9) for views/<view>/: flat fill under the limbs, carried by its own mesh.
    python3 body_tools/build_underlay.py <view> --skin <skin.json in/out> [--image base_body_underlay.png] [--depth 34] [--cell 2]
- torso behind each upper arm: upperArm_* pixels within --depth px of the torso region -> torso's flat skin colour, bone torso
- pelvis behind each thigh: thigh_* pixels within --depth px of the pelvis region -> flat colour of the nearest pelvis/torso
  pixel class (her flat panty colour or flat skin colour), bone pelvis
Every fill pixel lies where the main skin at rest is alpha 255 with >=1 px margin from any alpha<255 pixel, so the
footprint is fully hidden (check_underlay rule). Flat colours only; no outline, no shading. 100% weight per vertex.
Writes views/<view>/<image> and adds/replaces the "underlay" block in the given skin.json (atomic writes)."""
import json, os, sys, argparse, numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = '/workspace/shadowveil'  # Base Body copy of rig/work/crotch_weights/build_underlay_copy.py: writes the image next to this script (body_tools/work/crotch_candidates), never into views/
OUTD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f'{ROOT}/rig/skin_tools'); import skinlib
ap = argparse.ArgumentParser(); ap.add_argument('view'); ap.add_argument('--skin', required=True)
ap.add_argument('--image', default='base_body_underlay.png'); ap.add_argument('--depth', type=float, default=34)
ap.add_argument('--cell', type=int, default=2); ap.add_argument('--margin', type=int, default=1)
ap.add_argument('--bgk', type=float, default=None)  # keep fill only where dist(host) + bgk < dist(background at rest): stays on the host side, away from the limb's free outline
ap.add_argument('--pairs', default=None)  # e.g. 'upperArm_L:torso,forearm_L:pelvis+thigh_L' (default: upperArm_*:torso, thigh_*:pelvis)
ap.add_argument('--crotch', type=float, default=0)  # drop thigh fill within this |x - pelvis pivot x| (crotch gap opens there)
ap.add_argument('--depth-parts', type=float, default=None)  # from-parts: only within this distance inside the limb's edge
ap.add_argument('--grow', type=int, default=3)  # from-parts: grow the limb footprint into the host by this many px (host-drawn there, so hidden; closes hairline cracks at blended edges)
ap.add_argument('--flat-pairs', default=None)  # extra flat-colour pairs (limb:host) on top of --from-parts (depth/bgk apply)
ap.add_argument('--flat-skin-only', action='store_true')  # flat pairs use the host's flat skin colour only (no cloth)
ap.add_argument('--flat-override', action='store_true')  # flat pairs replace part fill (static host fill where the main mesh is blended)
ap.add_argument('--no-flatten', action='store_true')  # from-parts: keep the parts' pixels as they are (default: flatten, see below)
ap.add_argument('--flat-tol', type=float, default=12.0)  # flatten: RGB distance to the flat skin / garment colour still counted as that fill
ap.add_argument('--peel', type=int, default=1)  # flatten: stroke pixels on the outer edge are dropped this many times (1 = the edge stroke pixel only)
ap.add_argument('--peel-keep', default=None)  # a:b:r[,..] keep (fill instead of peel) edge strokes within r px of the a/b part boundary
ap.add_argument('--parts-bg', default=None)  # limb:host:K[,..] from-parts pairs: keep fill only > K px from the rest background (pulls the fill inside the limb's free outline, so a swung limb never exposes it as an unlined silhouette edge)
ap.add_argument('--host-edge-line', default=None)  # host:x0:x1:y0:y1:w[:fill][,..] restore her outline on the host part's real outer edge inside the box: the host's
# alpha-255 pixels within w px of its own edge become the line colour (alpha 255), and host pixels within fill px (default 6) of that edge are filled
# flat skin if the underlay left them empty. Only where hidden at rest (same 'ok' mask). Applied after flatten, so rebuilds keep it.
ap.add_argument('--edge-line-rgb', default='13,11,29')
ap.add_argument('--host-strip', default=None)  # host:limb:w:y0:y1[:solid][,..] (solid = closed, hole-filled band, all cells host, small other-bone islands next to it re-hosted) static strip along the limb/hip seam: pixels within w/2 px of the seam between the limb's cut part and the other body parts (both sides), rows y0..y1, hidden at rest, flat skin/garment, 100% host (e.g. pelvis) - covers the split-seam crack when the hip rotates under a still limb
ap.add_argument('--from-parts', action='store_true')  # fill = the host cut parts' own painted pixels under the limb (profiles), not flat colours
A = ap.parse_args()
vd = f'{ROOT}/views/{A.view}'
j, V, T, L = skinlib.load(A.skin); W, H = j['size']
main = np.array(Image.open(f"{vd}/{j['image']}").convert('RGBA'))
lm, _ = skinlib.coverage(V, T, L, W, H)
ul_layer = int(L.min()) - 1   # integer in the body band, below every main group
rig = json.load(open(f'{vd}/body/rig.json')); by = {p['id']: p for p in rig['parts']}
bix = {b['name']: i for i, b in enumerate(j['bones'])}
def own(pid):
    p = by[pid]; return np.array(Image.open(f"{vd}/body/{p['file']}").convert('RGBA'))[..., 3] > 0 if p.get('file') else np.zeros((H, W), bool)
# owner = topmost cut part (same segmentation as build_skin.py)
owner = np.full((H, W), '', object); top = np.full((H, W), -1e9)
for p in rig['parts']:
    if not p.get('file'): continue
    m = own(p['id']) & (p['layer'] > top); owner[m] = p['id']; top[m] = p['layer']
solid = main[..., 3] == 255
ok = solid & ~ndi.binary_dilation(~solid, iterations=max(1, A.margin)) & (lm > ul_layer)   # >= 1 px (default) inside any alpha<255 / transparent pixel   # 1 px margin inside alpha<255 / transparent
rgb = main[..., :3].astype(int)
dbg = ndi.distance_transform_edt(main[..., 3] > 0)   # distance to transparent background at rest
skin_px = solid & (rgb[..., 0] > 140) & (rgb[..., 0] - rgb[..., 2] > 60)
cloth_px = solid & (np.abs(rgb[..., 0] - 55) < 12) & (np.abs(rgb[..., 1] - 53) < 12) & (np.abs(rgb[..., 2] - 56) < 12)
def mode(mask):
    if not mask.any(): return np.array([185, 128, 85])
    c, n = np.unique(rgb[mask], axis=0, return_counts=True); return c[n.argmax()]
img = np.zeros((H, W, 4), np.uint8); bone = np.full((H, W), -1, np.int32); rep = {}
if A.pairs: PAIRS = [(x.split(':')[0], x.split(':')[1].split('+'), int(x.split(':')[2]) if len(x.split(':')) > 2 else A.grow) for x in A.pairs.split(',')]
else: PAIRS = [(f'{l}_{s}', [h], A.grow) for s in 'LR' for l, h in (('upperArm', 'torso'), ('thigh', 'pelvis'))]
PAIRS = [(l, h, g, False) for l, h, g in PAIRS]
if A.flat_pairs: PAIRS += [(x.split(':')[0], x.split(':')[1].split('+'), 0, True) for x in A.flat_pairs.split(',')]
for limb, hl, grow, flatp in PAIRS:
    if limb not in by or not by[limb].get('file'): continue
    if A.from_parts and not flatp:
        # topmost listed host whose cut part is alpha-255 there; its own pixel colour; weighted to that host
        for host in sorted([h for h in hl if by.get(h, {}).get('file')], key=lambda h: by[h]['layer']):
            him = np.array(Image.open(f"{vd}/body/{by[host]['file']}").convert('RGBA'))
            region = (ndi.binary_dilation(owner == limb, iterations=grow) if grow > 0 else (owner == limb)) & ok & (him[..., 3] == 255)
            if A.depth_parts: region &= ndi.distance_transform_edt(owner == limb) <= A.depth_parts
            for kk in (A.parts_bg or '').split(','):
                if kk and kk.split(':')[0] == limb and kk.split(':')[1] in (host, '*'): region &= dbg > float(kk.split(':')[2])
            img[region] = him[region]; bone[region] = bix[host]
            rep[limb + ':' + host] = {'host': host, 'px': int(region.sum()), 'from': by[host]['file']}
        continue
    hosts_all = np.isin(owner, hl)
    _, (jy, jx) = ndi.distance_transform_edt(~hosts_all, return_indices=True); near_host = owner[jy, jx]
    for host in hl:
        hosts_col = (host, 'torso') if host == 'pelvis' else (host,)
        hm = owner == host
        d = ndi.distance_transform_edt(~hm)
        region = (owner == limb) & (d <= A.depth) & ok & (near_host == host)
        if A.bgk is not None: region &= d + A.bgk < dbg
        if limb.startswith('thigh') and A.crotch > 0: region &= np.abs(np.arange(W) + 0.5 - by['pelvis']['pivotX'])[None, :] >= A.crotch
        # colour: flat class (skin / cloth) of the nearest host pixel
        hostm = np.isin(owner, hosts_col) & (skin_px | cloth_px)
        _, (iy, ix) = ndi.distance_transform_edt(~hostm, return_indices=True)
        is_cloth = cloth_px[iy, ix]
        cs, cc = mode(np.isin(owner, hosts_col) & skin_px), mode(np.isin(owner, hosts_col) & cloth_px)
        if flatp and A.flat_skin_only: is_cloth = np.zeros_like(is_cloth)
        col = np.where(is_cloth[..., None], cc, cs)
        if flatp and not A.flat_override: region &= bone < 0   # only where the parts' own fill left nothing
        img[region, :3] = col[region]; img[region, 3] = 255; bone[region] = bix[host]
        rep[limb + ':' + host] = {'host': host, 'px': int(region.sum()), 'skinRGB': cs.tolist(), 'clothRGB': cc.tolist(), 'clothPx': int((region & is_cloth).sum())}
# flatten (from-parts): the cut parts' fill carries her line art (outline strokes + AA) and slight tonal variation.
# Keep only two flat colours: her flat skin and her flat garment colour (bra/briefs), both the modal colours of base.png
# on the torso/pelvis (+thigh for skin). Stroke pixels on the underlay's outer edge are dropped (--peel passes) and every
# remaining stroke pixel takes the class of the nearest flat pixel, so the boundary is flat fill only.
flat_rep = None
if A.from_parts and not A.no_flatten:
    base = np.array(Image.open(f'{vd}/base.png').convert('RGBA')).astype(int); brgb = base[..., :3]; bsol = base[..., 3] == 255
    def part_mask(ids): return np.any([own(i) for i in ids if i in by], axis=0)
    def modal(m):
        c, n = np.unique(brgb[m], axis=0, return_counts=True); return c[n.argmax()]
    body_ids = ['torso', 'pelvis'] + [k for k in by if k.startswith('thigh')]
    b_skin = bsol & part_mask(body_ids) & (brgb[..., 0] > 140) & (brgb[..., 0] - brgb[..., 2] > 60)
    b_cloth = bsol & part_mask(['torso', 'pelvis']) & (np.abs(brgb[..., 0] - brgb[..., 2]) < 15) & (brgb.max(-1) > 40) & (brgb.max(-1) < 90)
    S, G = modal(b_skin), modal(b_cloth)
    m = bone >= 0; rgb = img[..., :3].astype(int)
    dS = np.sqrt(((rgb - S) ** 2).sum(-1)); dG = np.sqrt(((rgb - G) ** 2).sum(-1))
    is_s = m & (dS <= A.flat_tol) & (dS <= dG); is_g = m & (dG <= A.flat_tol) & (dG < dS); stroke = m & ~is_s & ~is_g
    n_stroke = int(stroke.sum()); n_edge0 = int((stroke & ~ndi.binary_erosion(m)).sum()); peeled = 0
    keep = np.zeros((H, W), bool)   # --peel-keep a:b:r -> never peel within r px of the a/b cut-part boundary (e.g. the hip seam, where the
    for kk in (A.peel_keep or '').split(','):   # edge fill closes the crotch/buttock gap); those edge strokes are filled flat instead
        if kk:
            pa, pb, rr = kk.split(':'); ma, mb = own(pa), own(pb)
            keep |= (ndi.distance_transform_edt(~ma) <= float(rr)) & (ndi.distance_transform_edt(~mb) <= float(rr))
    for _ in range(A.peel):   # peel stroke pixels off the outer edge (A.peel passes); the rest are filled flat, so the edge is flat fill
        e = stroke & m & ~ndi.binary_erosion(m) & ~keep
        if not e.any(): break
        m &= ~e; stroke &= ~e; peeled += int(e.sum())
    flatpx = m & ~stroke
    _, (iy, ix) = ndi.distance_transform_edt(~flatpx, return_indices=True)
    cls_g = is_g[iy, ix]   # class of the nearest flat pixel (own class for flat pixels)
    bone[~m] = -1; img[~m] = 0
    img[m & ~cls_g, :3] = S; img[m & cls_g, :3] = G; img[m, 3] = 255
    flat_rep = {'skinRGB': S.tolist(), 'garmentRGB': G.tolist(), 'strokePx': n_stroke, 'strokeOnEdgeBefore': n_edge0, 'peeledFromEdge': peeled,
                'filledInterior': n_stroke - peeled, 'skinPx': int((m & ~cls_g).sum()), 'garmentPx': int((m & cls_g).sum())}
edge_rep = []
for spec in (A.host_edge_line or '').split(','):
    if not spec: continue
    f = spec.split(':'); host = f[0]; x0, x1, y0, y1 = map(int, f[1:5]); w = float(f[5]); fill = float(f[6]) if len(f) > 6 else 6.0
    hm = np.array(Image.open(f"{vd}/body/{by[host]['file']}").convert('RGBA'))[..., 3] == 255
    box = np.zeros((H, W), bool); box[y0:y1 + 1, x0:x1 + 1] = True
    dh = ndi.distance_transform_edt(hm)   # distance to the host's own edge
    sk = np.array(flat_rep['skinRGB'] if flat_rep else mode(np.isin(owner, [host]) & skin_px))
    fbox = np.zeros((H, W), bool); fbox[y0:y1 + 1, max(0, x0 - int(fill)):x1 + int(fill) + 1] = True   # gap fill may run past the line box in x (no slit between line and fill)
    newf = fbox & hm & ok & (dh <= fill) & (bone < 0)
    img[newf, :3] = sk; img[newf, 3] = 255; bone[newf] = bix[host]
    line = box & hm & ok & (dh <= w) & (bone >= 0)
    img[line, :3] = [int(c) for c in A.edge_line_rgb.split(',')]; img[line, 3] = 255
    tap = np.zeros((H, W), bool)
    if len(f) > 7 and f[7]:   # taper t/top/bot/ext: t px of line just outside the line ends (first `top` rows, last `bot` rows + `ext` rows past the end), hidden-at-rest px only
        t_, tr, br, ex = [int(v) for v in f[7].split('/')]
        rows = np.zeros((H, W), bool); rows[y0:y0 + tr, :] = True; rows[y1 - br + 1:y1 + ex + 1, :] = True
        grow = line.copy()
        for _ in range(t_): grow |= ndi.binary_dilation(grow, np.ones((3, 3), bool)) & rows
        tap = grow & ~line & rows & ok & (bone < 0)
        img[tap, :3] = [int(c) for c in A.edge_line_rgb.split(',')]; img[tap, 3] = 255; bone[tap] = bix[host]
    ys_, xs_ = np.nonzero(line | tap)
    edge_rep.append({'host': host, 'box': [x0, x1, y0, y1], 'w': w, 'filledPx': int(newf.sum()), 'linePx': int(line.sum()), 'taperPx': int(tap.sum()),
                     'lineX': [int(xs_.min()), int(xs_.max())] if len(xs_) else None, 'lineY': [int(ys_.min()), int(ys_.max())] if len(ys_) else None, 'rgb': A.edge_line_rgb})
strip_rep = []
for spec in (A.host_strip or '').split(','):
    if not spec: continue
    f_ = spec.split(':'); host, limb, w_, y0_, y1_ = f_[:5]; smode = f_[5] if len(f_) > 5 else ''; w_ = float(w_); y0_, y1_ = int(y0_), int(y1_)
    lm_ = owner == limb; other = (owner != '') & ~lm_ & (owner != 'head')
    rows = np.zeros((H, W), bool); rows[y0_:y1_ + 1] = True
    if smode == 'solid':   # clean band: closed + hole-filled, every cell host-owned, no interleaving with other underlay bones (1 px cells crack when a neighbour rotates)
        band = ((ndi.distance_transform_edt(~lm_) <= w_ / 2) & (owner != '') & (owner != 'head') | lm_ & (ndi.distance_transform_edt(lm_) <= w_ / 2)) & rows
        band = ndi.binary_fill_holes(ndi.binary_closing(band, np.ones((3, 3), bool), iterations=2)) & rows & ok
        lab_, n_ = ndi.label((bone >= 0) & (bone != bix[host]) & ~band & rows)   # leftover islands of other bones hugging the band -> host (clean split)
        if n_:
            sz = ndi.sum(np.ones_like(lab_), lab_, range(1, n_ + 1)); touch = ndi.maximum(ndi.binary_dilation(band, iterations=1).astype(int), lab_, range(1, n_ + 1))
            band |= np.isin(lab_, [i + 1 for i in range(n_) if sz[i] <= 60 and touch[i]])
        reg = band
    else:
        near = (ndi.distance_transform_edt(~lm_) <= w_ / 2) & other | (ndi.distance_transform_edt(~other) <= w_ / 2) & lm_
        reg = near & rows & ok
    if flat_rep: S_, G_ = np.array(flat_rep['skinRGB']), np.array(flat_rep['garmentRGB'])
    else: S_, G_ = mode(skin_px), mode(cloth_px)
    mr = main[..., :3].astype(int); isg = np.sqrt(((mr - G_) ** 2).sum(-1)) < np.sqrt(((mr - S_) ** 2).sum(-1))
    prev = int((reg & (bone >= 0)).sum())
    img[reg, :3] = np.where(isg[reg][:, None], G_, S_); img[reg, 3] = 255; bone[reg] = bix[host]
    strip_rep.append({'host': host, 'limb': limb, 'mode': smode or 'seam', 'w': w_, 'rows': [y0_, y1_], 'px': int(reg.sum()), 'rehostedPx': prev, 'garmentPx': int((reg & isg).sum())})
# mesh: pixel-aligned cells, one bone per cell (mixed cells -> 1 px cells), 100% weights
C = A.cell; verts, vix, tris, wts = [], {}, [], []
def vid(x, y, b):
    k = (x, y, b)
    if k not in vix: vix[k] = len(verts); verts.append([x, y]); wts.append([[int(b), 1.0]])
    return vix[k]
def quad(x, y, s, b):
    a, bb, c, d = vid(x, y, b), vid(x + s, y, b), vid(x + s, y + s, b), vid(x, y + s, b); tris.extend([[a, bb, c], [a, c, d]])
ys, xs = np.nonzero(bone >= 0)
for cx, cy in sorted({(int(x) // C, int(y) // C) for x, y in zip(xs, ys)}):
    blk = bone[cy * C:(cy + 1) * C, cx * C:(cx + 1) * C]; ks = set(blk[blk >= 0].tolist())
    if len(ks) == 1 and (blk >= 0).all(): quad(cx * C, cy * C, C, ks.pop())
    else:
        for dy in range(blk.shape[0]):
            for dx in range(blk.shape[1]):
                if blk[dy, dx] >= 0: quad(cx * C + dx, cy * C + dy, 1, int(blk[dy, dx]))
assert '/body_tools/work/crotch_candidates/' in os.path.abspath(A.skin)  # Base Body copy: writes only here
tmp = f'{OUTD}/{A.image}.tmp'; Image.fromarray(img, 'RGBA').save(tmp, format='PNG'); os.replace(tmp, f'{OUTD}/{A.image}')
j['underlay'] = {'image': A.image, 'layer': ul_layer, 'vertices': verts, 'triangles': tris, 'weights': wts,
                 'note': 'Base Body flat fill under the limbs (body_tools/build_underlay.py): torso behind the upper arms, pelvis behind the thighs; own mesh, 100% host-bone weights; hidden at rest behind alpha-255 main skin' + ('; profile: the cut parts\' hidden fill flattened to her flat skin ' + str(flat_rep['skinRGB']) + ' and flat garment (bra/briefs) ' + str(flat_rep['garmentRGB']) + ', line-art strokes removed' if flat_rep else '') + ''.join('; static ' + s_['host'] + ' strip along the ' + s_['limb'] + ' seam rows ' + str(s_['rows']) + ' (' + str(s_['px']) + ' px, hidden at rest)' for s_ in strip_rep) + ''.join('; outline restored on the ' + e['host'] + ' real outer edge in box ' + str(e['box']) + ' (' + str(e['linePx']) + ' px, rgb ' + e['rgb'] + ', hidden at rest)' for e in edge_rep)}
json.dump(j, open(A.skin + '.tmp', 'w'), separators=(',', ':')); os.replace(A.skin + '.tmp', A.skin)
print(json.dumps({'image': f'views/{A.view}/{A.image}', 'skin': A.skin, 'layer': ul_layer, 'px': int((bone >= 0).sum()), 'vertices': len(verts), 'triangles': len(tris), 'parts': rep, 'flatten': flat_rep, 'edgeLine': edge_rep, 'hostStrip': strip_rep}))
