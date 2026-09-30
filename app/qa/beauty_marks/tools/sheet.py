import json, sys, random
from PIL import Image, ImageDraw
sys.path.insert(0, '.'); import bm
res = {json.loads(l)['path']: json.loads(l) for l in open('results.jsonl')}
def face_crop(path, f, W=260):
    rgb, s = bm.load(path, maxside=100000)
    im = Image.fromarray(rgb)
    pts = [f[k] for k in ('green', 'amber', 'eye') if k in f]
    d = f['d']; xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    box = (int(min(xs)-0.75*d), int(min(ys)-0.45*d), int(max(xs)+0.75*d), int(max(ys)+0.9*d))
    c = im.crop(box); sc = W / c.width
    return c.resize((W, max(1, int(c.height*sc))), Image.LANCZOS)
def make(items, out, cols=6, W=260):
    tiles = []
    for it in items:
        r = res[it['path']]
        for fi, f in enumerate(r['faces'][:3]):
            try: t = face_crop(it['path'], f, W)
            except Exception as e: continue
            g = f.get('green_side'); a = f.get('amber_side')
            lab = f"{'/'.join(it['path'].split('/')[-2:])[-38:]}\nG(her L)={len(g['blobs']) if g else '-'} A(her R)={len(a['blobs']) if a else '-'} {f['mode'][:8]} d={f['d']:.0f}"
            tiles.append((t, lab))
    H = max([t.height for t, _ in tiles] + [10]); rows = (len(tiles)+cols-1)//cols
    sh = Image.new('RGB', (cols*(W+6), rows*(H+34)), (30, 30, 30)); dr = ImageDraw.Draw(sh)
    for i, (t, lab) in enumerate(tiles):
        x, y = (i % cols)*(W+6), (i//cols)*(H+34)
        sh.paste(t, (x, y+30)); dr.text((x+2, y+1), lab, fill=(255, 230, 0))
    sh.save(out, quality=88); return len(tiles)
if __name__ == '__main__':
    cls = json.load(open('classified.json'))
    sel = [c for c in cls if c['consistent'] == sys.argv[1] and (len(sys.argv) < 4 or c['confidence'] == sys.argv[3])]
    random.seed(1); random.shuffle(sel)
    print(make(sel[:24], sys.argv[2]))
