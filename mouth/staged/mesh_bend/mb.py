#!/usr/bin/env python3
"""Mesh-bend engine for the staged Shadowveil mouth prototype (NOT live).
Grid / triangle mesh per part, forward-mapped vertices, inverse affine per triangle,
bilinear sampling of PREMULTIPLIED RGBA (so no key colour / black fringe can bleed in).
Every output pixel is an interpolation of her own pixels (no painting)."""
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label, binary_fill_holes

ROOT = '/workspace/shadowveil'
W, H = 1365, 1739
BLUE = np.array([0, 0, 255], float)

def load_rgba(p):
    return np.array(Image.open(p).convert('RGBA'))

def premul(a):
    a = a.astype(np.float64)
    out = a.copy()
    out[..., :3] = a[..., :3] * a[..., 3:4] / 255.0
    return out

def unpremul_u8(p):
    a = p[..., 3:4]
    rgb = np.where(a > 0, p[..., :3] * 255.0 / np.maximum(a, 1e-9), 0)
    out = np.concatenate([rgb, a], -1)
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)

def over(dst, src):
    """premultiplied float over"""
    return src + dst * (1 - src[..., 3:4] / 255.0)

def lum(a):
    a = a.astype(np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]

def hexc(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], float)

# ---------------------------------------------------------------- bilinear sampler
def bilinear(P, sx, sy):
    """P premultiplied float (H,W,4); sx, sy pixel-space coords (pixel centres at i+0.5). Outside = transparent."""
    fx = sx - 0.5; fy = sy - 0.5
    # snap near-integer coordinates (identity at rest -> exact copy)
    rx = np.rint(fx); ry = np.rint(fy)
    fx = np.where(np.abs(fx - rx) < 1e-6, rx, fx); fy = np.where(np.abs(fy - ry) < 1e-6, ry, fy)
    x0 = np.floor(fx).astype(int); y0 = np.floor(fy).astype(int)
    tx = (fx - x0)[..., None]; ty = (fy - y0)[..., None]
    h, w = P.shape[:2]
    def g(yy, xx):
        ok = (xx >= 0) & (xx < w) & (yy >= 0) & (yy < h)
        v = P[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)]
        return v * ok[..., None]
    return (g(y0, x0) * (1 - tx) * (1 - ty) + g(y0, x0 + 1) * tx * (1 - ty)
            + g(y0 + 1, x0) * (1 - tx) * ty + g(y0 + 1, x0 + 1) * tx * ty)

# ---------------------------------------------------------------- grid mesh
class Grid:
    """Regular grid mesh in source px coords (pixel boundaries), two triangles per cell."""
    def __init__(self, x0, y0, x1, y1, sx, sy):
        self.xs = np.arange(x0, x1 + 1e-9, sx, dtype=float)
        if self.xs[-1] < x1: self.xs = np.append(self.xs, x1)
        self.ys = np.arange(y0, y1 + 1e-9, sy, dtype=float)
        if self.ys[-1] < y1: self.ys = np.append(self.ys, y1)
        X, Y = np.meshgrid(self.xs, self.ys)
        self.src = np.stack([X, Y], -1)       # (ny, nx, 2)
        self.dst = self.src.copy()
        self.sx, self.sy = sx, sy

    def tris(self):
        ny, nx = self.src.shape[:2]
        for j in range(ny - 1):
            for i in range(nx - 1):
                a, b, c, d = (j, i), (j, i + 1), (j + 1, i), (j + 1, i + 1)
                yield (a, b, d); yield (a, d, c)

    def n_tris(self):
        ny, nx = self.src.shape[:2]; return 2 * (ny - 1) * (nx - 1)

    def flipped(self):
        """count triangles whose signed area changes sign / collapses"""
        bad = 0
        for t in self.tris():
            S = np.array([self.src[k] for k in t]); D = np.array([self.dst[k] for k in t])
            sa = np.cross(S[1] - S[0], S[2] - S[0]); da = np.cross(D[1] - D[0], D[2] - D[0])
            if sa * da <= 1e-9: bad += 1
        return bad

    def forward(self, pts):
        """map source points (N,2) through the piecewise-linear mesh"""
        pts = np.asarray(pts, float); out = pts.copy()
        for n, (x, y) in enumerate(pts):
            i = int(np.clip(np.searchsorted(self.xs, x, 'right') - 1, 0, len(self.xs) - 2))
            j = int(np.clip(np.searchsorted(self.ys, y, 'right') - 1, 0, len(self.ys) - 2))
            u = (x - self.xs[i]) / (self.xs[i + 1] - self.xs[i]); v = (y - self.ys[j]) / (self.ys[j + 1] - self.ys[j])
            A, B, C, D = self.dst[j, i], self.dst[j, i + 1], self.dst[j + 1, i], self.dst[j + 1, i + 1]
            if u >= v:   # tri (a,b,d)
                out[n] = A + u * (B - A) + v * (D - B)
            else:        # tri (a,d,c)
                out[n] = A + v * (C - A) + u * (D - C)
        return out

class Mesh:
    """Generic triangle mesh: src (N,2), dst (N,2), tris (M,3)."""
    def __init__(self, src, dst, tris):
        self.src = np.asarray(src, float); self.dst = np.asarray(dst, float); self.tris_ = np.asarray(tris, int)
    def n_tris(self): return len(self.tris_)
    def flipped(self):
        S = self.src[self.tris_]; D = self.dst[self.tris_]
        cr = lambda a, b: a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
        sa = cr(S[:, 1] - S[:, 0], S[:, 2] - S[:, 0]); da = cr(D[:, 1] - D[:, 0], D[:, 2] - D[:, 0])
        ok = np.abs(sa) > 1e-6
        return int(((sa * da <= 0) & ok).sum())
    def forward(self, pts):
        pts = np.asarray(pts, float); out = np.full_like(pts, np.nan)
        S = self.src[self.tris_]; D = self.dst[self.tris_]
        v0 = S[:, 1] - S[:, 0]; v1 = S[:, 2] - S[:, 0]
        den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
        good = np.abs(den) > 1e-9
        for n, p in enumerate(pts):
            w = p - S[:, 0]
            l1 = np.where(good, (w[:, 0] * v1[:, 1] - w[:, 1] * v1[:, 0]) / np.where(good, den, 1), -1)
            l2 = np.where(good, (v0[:, 0] * w[:, 1] - v0[:, 1] * w[:, 0]) / np.where(good, den, 1), -1)
            ins = np.nonzero((l1 >= -1e-7) & (l2 >= -1e-7) & (l1 + l2 <= 1 + 1e-7))[0]
            if len(ins):
                k = ins[0]
                out[n] = D[k, 0] + l1[k] * (D[k, 1] - D[k, 0]) + l2[k] * (D[k, 2] - D[k, 0])
        return out

def grid_mesh(g):
    ny, nx = g.src.shape[:2]
    idx = lambda j, i: j * nx + i
    tris = []
    for (a, b, c) in g.tris():
        tris.append([idx(*a), idx(*b), idx(*c)])
    return Mesh(g.src.reshape(-1, 2), g.dst.reshape(-1, 2), tris)

def render(P, mesh, off=(0, 0)):
    """Warp premultiplied image P (a crop whose top-left is canvas px `off`) through mesh (canvas coords).
    Returns premultiplied float of the same crop size."""
    ox, oy = off
    out = np.zeros_like(P)
    done = np.zeros(P.shape[:2], bool)
    for t in mesh.tris_:
        S = mesh.src[t] - [ox, oy]; D = mesh.dst[t] - [ox, oy]
        M = np.array([[D[1, 0] - D[0, 0], D[2, 0] - D[0, 0]], [D[1, 1] - D[0, 1], D[2, 1] - D[0, 1]]])
        det = np.linalg.det(M)
        if abs(det) < 1e-12: continue
        Minv = np.linalg.inv(M)
        bx0 = int(np.floor(D[:, 0].min() - 0.5)); bx1 = int(np.ceil(D[:, 0].max() + 0.5))
        by0 = int(np.floor(D[:, 1].min() - 0.5)); by1 = int(np.ceil(D[:, 1].max() + 0.5))
        bx0, by0 = max(bx0, 0), max(by0, 0); bx1, by1 = min(bx1, P.shape[1] - 1), min(by1, P.shape[0] - 1)
        if bx1 < bx0 or by1 < by0: continue
        yy, xx = np.mgrid[by0:by1 + 1, bx0:bx1 + 1]
        px = xx + 0.5 - D[0, 0]; py = yy + 0.5 - D[0, 1]
        l1 = Minv[0, 0] * px + Minv[0, 1] * py; l2 = Minv[1, 0] * px + Minv[1, 1] * py
        eps = 1e-9
        inside = (l1 >= -eps) & (l2 >= -eps) & (l1 + l2 <= 1 + eps) & ~done[yy, xx]
        if not inside.any(): continue
        sx = S[0, 0] + l1 * (S[1, 0] - S[0, 0]) + l2 * (S[2, 0] - S[0, 0])
        sy = S[0, 1] + l1 * (S[1, 1] - S[0, 1]) + l2 * (S[2, 1] - S[0, 1])
        Y, X = yy[inside], xx[inside]
        out[Y, X] = bilinear(P, sx[inside], sy[inside])
        done[Y, X] = True
    return out

# ---------------------------------------------------------------- palette / classes
def palette(view):
    rj = json.load(open(f'{ROOT}/views/{view}/mouth/rig.json'))
    C = rj['colors']
    return rj, {k: hexc(C[k]) for k in ['skin', 'upper', 'lower', 'line', 'hl', 'inner', 'teeth', 'tongue']}

def nearest_class(rgb, pal):
    names = list(pal); Pm = np.stack([pal[k] for k in names])
    d = ((rgb[..., None, :3].astype(float) - Pm) ** 2).sum(-1)
    return np.array(names)[d.argmin(-1)], d.min(-1)

def mouth_sil(rgb, pal):
    """silhouette = pixels whose nearest palette colour is not skin"""
    cls, _ = nearest_class(rgb, pal)
    return cls != 'skin'

def cavity_mask(shape_rgba, pal):
    """make_mesh_split's cavity rule on any open shape"""
    names = list(pal); near, _ = nearest_class(shape_rgba, pal)
    cand = (shape_rgba[..., 3] == 255) & np.isin(near, ['inner', 'teeth', 'tongue', 'hl'])
    lab, n = label(cand, structure=np.ones((3, 3)))
    if n == 0: return np.zeros(cand.shape, bool)
    sizes = [(lab == i).sum() for i in range(1, n + 1)]
    cav = lab == (1 + int(np.argmax(sizes)))
    return binary_fill_holes(cav) & (shape_rgba[..., 3] == 255)

def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0

def onto(base_u8, stack_pm):
    """composite a premultiplied stack onto a uint8 straight-alpha background; untouched where stack alpha == 0"""
    b = premul(base_u8)
    o = over(b, stack_pm)
    out = unpremul_u8(o)
    keep = stack_pm[..., 3] <= 1e-9
    out[keep] = base_u8[keep]
    return out
