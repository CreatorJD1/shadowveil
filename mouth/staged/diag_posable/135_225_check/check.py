# 135 (f087) / 225 (f131): are any of her lip / lip-corner px visible? Read-only. Tests the face/head region of each frame
# for px matching HER lip tones from the f033/f191 cuts (RGB dist <= 12) and for the lip-vs-skin colour rule used by lipcut.
import sys, json, os; sys.dont_write_bytecode = True
sys.path.insert(0, '/workspace/shadowveil/mouth/staged/diag_posable/tools')
from common import *
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from scipy.ndimage import label as cc
import lipcut
tones = []
for t in ('045', '315'):
    rgb, skin, soft, comp = cut_frame(t); tones.append(rgb[soft >= .5].astype(int))
tones = np.unique(np.concatenate(tones), axis=0); tree = cKDTree(tones)
ref = {}
for t in ('045', '315'):
    rgb = frame_rgb(t); x0, y0, x1, y1 = DIAG[t]['search']; ref[t] = lipcut.skin_ref(rgb, (x0, y0, x1, y1))
skin_ref = np.mean(list(ref.values()), 0)
out = {}
for ang, fr in (('135', 87), ('225', 131)):
    im = np.asarray(Image.open(f'{ROOT}/reference/apose_turn/frames/f{fr:03d}.png').convert('RGB')).astype(int)
    # head region: rows 60..300 (head top y62 raw .. below the chin), all columns that are not key blue
    y0, y1 = 60, 300; reg = im[y0:y1]
    notblue = ~(reg[..., 2] > reg[..., 0] + 40)
    d, _ = tree.query(reg.reshape(-1, 3)); d = d.reshape(reg.shape[:2])
    tone = (d <= 12) & notblue
    # lip-vs-skin rule (lipcut ramp, coverage >= .5), restricted to px that are also lip-tone matches and reddish (R>G+25)
    redd = (reg[..., 0] > reg[..., 1] + 25) & (reg[..., 0] > 60)
    cand = tone & redd
    lab, n = cc(cand, structure=np.ones((3, 3)))
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        comps.append(dict(px=int(len(ys)), bbox=[int(xs.min()), int(ys.min() + y0), int(xs.max()), int(ys.max() + y0)]))
    comps.sort(key=lambda c: -c['px'])
    # skin visible in the head region (her face skin tone, dist <= 30 from the diagonal face skin)
    skin = (np.sqrt(((reg - skin_ref) ** 2).sum(-1)) <= 30) & notblue
    sy, sx = np.nonzero(skin)
    out[ang] = dict(frame=f'f{fr:03d}', head_rows=[y0, y1], lip_tone_px=int(tone.sum()), lip_tone_reddish_px=int(cand.sum()),
                    components=comps[:10], face_skin_px=int(skin.sum()),
                    face_skin_bbox=[int(sx.min()), int(sy.min() + y0), int(sx.max()), int(sy.max() + y0)] if len(sx) else None)
    # crops: head region x4 with candidate px marked magenta, and the skin px marked
    xs_ = np.nonzero(notblue.any(0))[0]; cx0, cx1 = max(0, xs_.min() - 10), min(im.shape[1], xs_.max() + 10) if len(xs_) else (0, 768)
    crop = im[y0:y1, cx0:cx1].astype(np.uint8); mk = crop.copy(); mk[cand[:, cx0:cx1]] = (255, 0, 255)
    z = lambda a: np.kron(a, np.ones((4, 4, 1), np.uint8))
    Image.fromarray(np.concatenate([z(crop), np.full((z(crop).shape[0], 8, 3), 255, np.uint8), z(mk)], 1)).save(f'crop_{ang}_f{fr:03d}.png')
    print(ang, json.dumps(out[ang]))
json.dump(out, open('check.json', 'w'), indent=1)
