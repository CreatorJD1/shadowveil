import sys; sys.path.insert(0,'.'); from posekit import *
ang, which, jn, th, R, z = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
d = ORIG + '/' + ang if which == 'old' else FIX + '/' + ang
pj, img = load_set(d)
owner = np.full((H, W), '', object)
for k in pj['layerOrder_backToFront']: owner[img[k][..., 3] > 0] = k
for k in img:
    fl = (img[k][..., 3] > 0) & (owner != k); im = img[k].copy(); im[fl, :3] = (im[fl, :3] * 0.6 + np.array([255, 0, 160]) * 0.4).astype(np.uint8); img[k] = im
c = pj['joints'][jn]['pivot']; comp = pose(ang, pj, img, jn, th)
a = comp[..., 3:] / 255.; t = (comp[..., :3] * a + np.array([150, 230, 150]) * (1 - a)).clip(0, 255).astype(np.uint8)
x0, y0 = int(c[0]) - R, int(c[1]) - R; t = t[y0:y0 + 2 * R, x0:x0 + 2 * R]
im = Image.fromarray(t).resize((2 * R * z, 2 * R * z), Image.NEAREST)
from PIL import ImageDraw; D = ImageDraw.Draw(im); D.ellipse([R * z - 4, R * z - 4, R * z + 4, R * z + 4], outline=(255, 0, 0))
im.save(f'{FIX}/tools/_z_{ang}_{which}_{jn}_{th}.png')
