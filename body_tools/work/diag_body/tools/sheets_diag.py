"""sheet per angle: her frame | pieces coloured | parts exploded | rest recomposite diff, + the +-25 joint test tiles below."""
import sys; sys.path.insert(0, '.'); from common import *
from PIL import ImageDraw
from overview import seg_image
for ang in sys.argv[1:] or ['045', '315']:
    od = f'{OUT}/{ang}'; pj = json.load(open(f'{od}/parts.json')); F = frame(ang).astype(np.uint8)
    # exploded: each piece pushed away from the pelvis pivot by 18% of its centroid offset
    cx, cy = pj['pieces'][-1]['pivot'] if pj['pieces'][-1]['id'] == 'pelvis' else (384, 600)
    ex = Image.new('RGBA', (768, 1168), (235, 235, 235, 255))
    for k in pj['layerOrder_backToFront']:
        im = Image.open(f'{od}/pieces/{k}.png'); a = np.array(im)[..., 3] > 0; ys, xs = np.nonzero(a)
        dx, dy = int((xs.mean() - cx) * 0.22), int((ys.mean() - cy) * 0.12); ex.alpha_composite(im, (max(dx, -200), dy) if True else (0, 0))
    panels = [Image.fromarray(F), seg_image(ang), ex.convert('RGB'), Image.open(f'{od}/rest_recomposite_diff.png').convert('RGB')]
    ck = json.load(open(f'{od}/checks.json'))
    labels = [f"her frame {pj['frame']}", 'pieces (colour) + pivots', 'parts exploded (her px + hidden flaps)',
              f"rest diff: {ck['rest']['diff_px_vs_frame_on_body_px']} px (red), off-pal {ck['totals']['off_palette']}, chroma {ck['totals']['chroma']}"]
    jt = Image.open(f'{od}/joint_test_25.png').convert('RGB')
    sw = 384; sh_ = 584
    W = max(4 * sw, jt.width); sheet = Image.new('RGB', (W, sh_ + 30 + jt.height + 20), (255, 255, 255)); d = ImageDraw.Draw(sheet)
    for i, (p, l) in enumerate(zip(panels, labels)):
        sheet.paste(p.resize((sw, sh_), Image.LANCZOS), (i * sw, 22)); d.text((i * sw + 4, 4), l, fill=(0, 0, 0))
    d.text((4, sh_ + 28), f'joint test +-25 deg (nearest; red = hole, orange = 1 px crack). Diagonal {ang}, FRAME px. Staged, not live.', fill=(0, 0, 0))
    sheet.paste(jt, (0, sh_ + 46)); sheet.save(f'{od}/sheet_{ang}.png'); print(f'{od}/sheet_{ang}.png', sheet.size)
