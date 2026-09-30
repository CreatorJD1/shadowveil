#!/usr/bin/env python3
"""Beauty-mark detector (read-only on art). Finds her irises by colour (amber = her right eye,
green = her left eye), builds a cheek window under each eye scaled by eye distance, and counts
small, round, isolated dark blobs inside skin. Canonical (turn-000): amber side 1, green side 2."""
import cv2, numpy as np, sys, json
from PIL import Image

def load(path, maxside=2600):
    im = Image.open(path)
    im.draft('RGB', (maxside, maxside)) if im.format == 'JPEG' else None
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (128,128,128,255)); bg.alpha_composite(im); im = bg
    im = im.convert('RGB')
    s = 1.0
    if max(im.size) > maxside:
        s = maxside / max(im.size); im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    return np.asarray(im), s

def comps(mask, minarea):
    n, lab, st, cen = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    return [(st[i], cen[i]) for i in range(1, n) if st[i][4] >= minarea]

def find_eyes(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    H, S, V = hsv[...,0].astype(int), hsv[...,1].astype(int), hsv[...,2].astype(int)
    k = np.ones((2,2), np.uint8)
    green = cv2.morphologyEx(((H>=38)&(H<=90)&(S>=80)&(V>=70)).astype(np.uint8), cv2.MORPH_OPEN, k)
    amber = cv2.morphologyEx(((H>=8)&(H<=30)&(S>=140)&(V>=165)).astype(np.uint8), cv2.MORPH_OPEN, k)
    white = ((S < 45) & (V > 200)).astype(np.uint8)
    lum = rgb.mean(2)
    def cands(mask, lo, hi):
        out = []
        for st, c in comps(mask, 8):
            x, y, w, h, a = st
            if w > 6*h or h > 3*w: continue
            fill = a / (w*h)
            if fill < 0.35: continue
            r = max(2.0, np.sqrt(a/np.pi))
            x0, y0 = int(max(0, c[0]-3*r)), int(max(0, c[1]-1.8*r)); x1, y1 = int(c[0]+3*r)+1, int(c[1]+1.8*r)+1
            wh = white[y0:y1, x0:x1].sum()
            dk = (lum[y0:y1, x0:x1] < 60).sum()
            if wh < 0.15*a or dk < 0.1*a: continue   # needs sclera + lash/pupil around it
            pup = (lum[y:y+h, x:x+w] < 75).sum()
            above = lum[int(max(0, c[1]-2.2*r)):int(max(0, c[1]-0.6*r))+1, int(max(0, c[0]-1.5*r)):int(c[0]+1.5*r)+1]
            lash = (above < 60).sum() if above.size else 0
            strong = pup >= 0.04*a and lash >= 0.15*a and fill >= 0.5
            sub = ((white[y0:y1, x0:x1] > 0) | (mask[y0:y1, x0:x1] > 0)).astype(np.uint8)
            sub = cv2.dilate(sub, np.ones((3,3), np.uint8))
            nn, ll, ss, _ = cv2.connectedComponentsWithStats(sub, 8)
            ci = ll[min(ll.shape[0]-1, int(c[1])-y0), min(ll.shape[1]-1, int(c[0])-x0)]
            ew = int(ss[ci][2]) if ci > 0 else int(w)
            out.append(dict(c=(float(c[0]), float(c[1])), r=float(r), a=int(a), h=int(h), w=int(w), ew=ew, strong=bool(strong)))
        return out
    return cands(green, 8, 1e9), cands(amber, 8, 1e9)

def pairs(g, a):
    cand = []
    for gi, G in enumerate(g):
        for ai, A in enumerate(a):
            ratio = G['a']/A['a']
            if not (0.3 < ratio < 3.3): continue
            if not (G['strong'] or A['strong']): continue
            dx, dy = G['c'][0]-A['c'][0], G['c'][1]-A['c'][1]
            d = np.hypot(dx, dy); rr = (G['r']+A['r'])/2
            if not (4.5*rr < d < 14*rr): continue
            if abs(dy) > 0.45*d: continue
            score = abs(np.log(ratio)) + abs(d/rr - 8.8)/4 + abs(dy)/d
            cand.append((score, gi, ai, d))
    cand.sort(); used_g, used_a, out = set(), set(), []
    for sc, gi, ai, d in cand:
        if gi in used_g or ai in used_a: continue
        used_g.add(gi); used_a.add(ai); out.append((sc, g[gi], a[ai], d))
    return out, used_g, used_a

def cheek_blobs(rgb, eye, other_dir, d, side_sign_out, win=(-0.55, 0.28, 0.16, 0.66)):
    """eye: (x,y); other_dir: unit vector from this eye toward the other eye (image space);
    returns blobs in the cheek window below the eye."""
    u = np.array(other_dir); n = np.array([-u[1], u[0]])
    if n[1] < 0: n = -n
    e = np.array(eye)
    # window in face coords: a outward..inward, b downward
    A0, A1, B0, B1 = win
    corners = [e + a*u*d + b*n*d for a in (A0, A1) for b in (B0, B1)]
    xs = [c[0] for c in corners]; ys = [c[1] for c in corners]
    pad = int(0.15*d)+2
    x0, y0 = int(max(0, min(xs)-pad)), int(max(0, min(ys)-pad))
    x1, y1 = int(min(rgb.shape[1], max(xs)+pad)), int(min(rgb.shape[0], max(ys)+pad))
    if x1-x0 < 4 or y1-y0 < 4: return None
    crop = rgb[y0:y1, x0:x1].astype(np.float32)
    lum = crop.mean(2)
    hsv = cv2.cvtColor(crop.astype(np.uint8), cv2.COLOR_RGB2HSV)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    rel = np.stack([xx-e[0], yy-e[1]], -1) / d
    fa = rel @ u; fb = rel @ n
    inwin = (fa >= A0) & (fa <= A1) & (fb >= B0) & (fb <= B1)
    skin = inwin & (hsv[...,0] <= 25) & (hsv[...,1] >= 50) & (lum > 70)
    if skin.sum() < 0.25*inwin.sum(): return dict(skin_frac=float(skin.sum()/max(1,inwin.sum())), blobs=[], window=(x0,y0,x1,y1))
    med = float(np.median(lum[skin]))
    dark = (lum < 0.62*med).astype(np.uint8)
    n_, lab, st, cen = cv2.connectedComponentsWithStats(dark, 8)
    sc = d/67.0
    blobs = []
    # skin mask dilated: blob must be surrounded by skin
    for i in range(1, n_):
        x, y, w, h, a = st[i]
        cx, cy = cen[i]
        if not inwin[int(round(cy)) if int(round(cy))<inwin.shape[0] else -1, int(round(cx)) if int(round(cx))<inwin.shape[1] else -1]: continue
        if x == 0 or y == 0 or x+w >= dark.shape[1] or y+h >= dark.shape[0]: continue
        if max(w, h) > max(3, 0.11*d): continue
        if a < max(3, 2.0*sc*sc): continue
        if max(w,h) > 2.6*max(1,min(w,h)): continue
        ring = cv2.dilate((lab==i).astype(np.uint8), np.ones((5,5),np.uint8)) - cv2.dilate((lab==i).astype(np.uint8), np.ones((3,3),np.uint8))
        rs = ring.astype(bool)
        if rs.sum() == 0: continue
        skinring = (skin[rs]).mean()
        if skinring < 0.6: continue
        if lum[lab==i].mean()/med > 0.47: continue
        blobs.append(dict(x=float(cx+x0), y=float(cy+y0), area=int(a), a=float((np.array([cx+x0,cy+y0])-e)@u/d), b=float((np.array([cx+x0,cy+y0])-e)@n/d),
                          contrast=float(lum[lab==i].mean()/med), skinring=float(skinring)))
    return dict(skin_frac=float(skin.sum()/max(1,inwin.sum())), med=med, blobs=blobs, window=(x0,y0,x1,y1))

def analyse(path):
    rgb, s = load(path)
    g, a = find_eyes(rgb)
    res = dict(path=path, scale=s, n_green=len(g), n_amber=len(a), faces=[])
    P, ug, ua = pairs(g, a)
    for _, G, A, d in P[:40]:
        uG = np.array(A['c'])-np.array(G['c']); uG /= np.linalg.norm(uG)
        f = dict(mode='pair', d=float(d/s), green=[c/s for c in G['c']], amber=[c/s for c in A['c']],
                 mirrored=bool(A['c'][0] > G['c'][0] and abs(uG[0]) > 0.7))
        f['green_side'] = cheek_blobs(rgb, G['c'], tuple(uG), d, 1)
        f['amber_side'] = cheek_blobs(rgb, A['c'], tuple(-uG), d, 1)
        res['faces'].append(f)
    singles = [('green', c) for i, c in enumerate(g) if i not in ug] + [('amber', c) for i, c in enumerate(a) if i not in ua]
    singles = [t for t in singles if t[1]['strong']] if not P else []
    singles.sort(key=lambda t: -t[1]['a'])
    singles = singles[:4]
    paired = [np.array(c['c']) for _, G, A, _d in P[:40] for c in (G, A)]
    pd = [d for _, G, A, d in P[:40]]
    for side, E in singles[:20]:
        if any(np.linalg.norm(np.array(E['c'])-pc) < 1.2*pd[i//2] for i, pc in enumerate(paired)): continue
        d = max(8.8*E['r'], 4.4*E['h'], 2.4*E['ew'])
        cb = cheek_blobs(rgb, E['c'], (1.0, 0.0), d, 1, win=(-0.6, 0.6, 0.14, 0.7))
        if not cb or cb.get('skin_frac', 0) < 0.6: continue
        f = dict(mode='single-'+side, d=float(d/s), eye=[c/s for c in E['c']])
        f[side+'_side'] = cb
        res['faces'].append(f)
    for f in res['faces']:
        for k in ('green_side', 'amber_side'):
            if f.get(k):
                for b in f[k]['blobs']: b['x'] /= s; b['y'] /= s
                f[k]['window'] = [v/s for v in f[k]['window']]
    return res, rgb

if __name__ == '__main__':
    for p in sys.argv[1:]:
        r, _ = analyse(p)
        print(p.split('/')[-1], len(r['faces']))
        for f in r['faces']:
            def sm(side):
                if not side: return '-'
                return f"{len(side['blobs'])} " + ' '.join(f"({b['a']:+.2f},{b['b']:.2f},A{b['area']})" for b in side['blobs'])
            print('   ', f['mode'], 'd=%.0f' % f['d'], 'G:', sm(f.get('green_side')), '| A:', sm(f.get('amber_side')))
