import sys; sys.path.insert(0,'.'); from posekit import *
ang, which, joint = sys.argv[1], sys.argv[2], sys.argv[3]; tint = len(sys.argv) > 4
d = ORIG + '/' + ang if which == 'old' else FIX + '/' + ang
pj, img = load_set(d); band, c, r = band_of(pj, joint, 15)
if tint:
    owner = np.full((H, W), '', object)
    for k in pj['layerOrder_backToFront']: owner[img[k][..., 3] > 0] = k
    for k in img:
        fl = (img[k][..., 3] > 0) & (owner != k); im = img[k].copy(); im[fl, :3] = (im[fl, :3] * 0.5 + np.array([255, 0, 160]) * 0.5).astype(np.uint8); img[k] = im
R = int(r + 30); x0, y0 = max(int(c[0]) - R, 0), max(int(c[1]) - R, 0)
tiles = []
for th in (-25, 0, 25):
    comp = pose(ang, pj, img, joint, th); m, v = metrics(comp, band)
    a = comp[..., 3:] / 255.; t = (comp[..., :3] * a + np.array([150, 230, 150]) * (1 - a))
    t[v['notch']] = [80, 80, 255]; t[v['holes']] = [255, 0, 0]
    t = t[y0:y0 + 2 * R, x0:x0 + 2 * R].clip(0, 255).astype(np.uint8)
    z = max(2, 600 // t.shape[1])
    tiles.append(Image.fromarray(t).resize((t.shape[1] * z, t.shape[0] * z), Image.NEAREST)); print(th, m)
w = sum(t.width for t in tiles); o = Image.new('RGB', (w, max(t.height for t in tiles)), 'white'); x = 0
for t in tiles: o.paste(t, (x, 0)); x += t.width
o.save(f'{FIX}/tools/_look_{ang}_{which}_{joint}.png')
