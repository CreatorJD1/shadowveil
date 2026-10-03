from common import *
from PIL import Image, ImageDraw
OUT = f'{ROOT}/mouth/staged/diag_posable'
d = json.load(open(f'{OUT}/build_log.json'))
names = ['rest', 'M', 'smile', 'OH_half', 'AA_half', 'EE_half', 'OH', 'AA', 'EE']
def tile(img, z, lab):
    t = np.kron(img, np.ones((z, z, 1), np.uint8)); im = Image.fromarray(np.concatenate([np.full((16, t.shape[1], 3), 255, np.uint8), t], 0))
    ImageDraw.Draw(im).text((2, 2), lab, fill=(0, 0, 0)); return np.asarray(im)
def row(ts):
    h = max(t.shape[0] for t in ts); out = []
    for t in ts: out += [np.pad(t, ((0, h - t.shape[0]), (0, 0), (0, 0)), constant_values=255), np.full((h, 6, 3), 255, np.uint8)]
    return np.concatenate(out, 1)
rows = []
for tag in ('045', '315'):
    fr = np.asarray(Image.open(f"{ROOT}/reference/apose_turn/frames/f{DIAG[tag]['frame']:03d}.png").convert('RGB'))
    fv = np.clip(np.round(to_view(fr.astype(float), tag)), 0, 255).astype(np.uint8)
    x0, y0, x1, y1 = d[tag]['_tones']['frame_box']; x0 += 6; x1 -= 6; y0 += 8; y1 -= 12
    vx0, vy0, vx1, vy1 = d[tag]['_tones']['view_box']; vx0 += 10; vx1 -= 10; vy0 += 12; vy1 -= 18
    for sc, bg, (a, b, c, e), z, sub in (('frame', fr, (x0, y0, x1, y1), 9, 'frame_scale/'), ('view', fv, (vx0, vy0, vx1, vy1), 6, '')):
        ts = []
        for n in names:
            p = np.asarray(Image.open(f'{OUT}/{tag}/{sub}{n}.png'))
            comp = np.where(p[..., 3:4] == 255, p[..., :3], bg)[b:e, a:c]
            lab = f'{tag} {sc} {n}' + (' (HER lips)' if n == 'rest' else ' FRONT bent, flag off')
            ts.append(tile(comp, z, lab))
        rows.append(row(ts))
    # chroma row (frame scale, key convention)
    ts = [tile(np.asarray(Image.open(f'{OUT}/{tag}/frame_scale/chroma/{n}_chroma.png'))[y0:y1, x0:x1], 9, f'{tag} chroma {n}') for n in names]
    rows.append(row(ts))
W_ = max(r.shape[1] for r in rows)
rows = [np.pad(r, ((0, 8), (0, W_ - r.shape[1]), (0, 0)), constant_values=255) for r in rows]
ban = Image.fromarray(np.full((22, W_, 3), 255, np.uint8)); ImageDraw.Draw(ban).text((4, 4), 'STAGED diag_posable: rest = HER f033/f191 lips (0 px). Other shapes = FRONT apose art bent onto her diagonal lips, behind ?diagmouth=1 (off by default), each needs its own OK line.', fill=(180, 0, 0))
Image.fromarray(np.concatenate([np.asarray(ban)] + rows, 0)).save(f'{OUT}/sheet.png')
print('sheet', W_)
