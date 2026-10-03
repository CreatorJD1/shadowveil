import sys; sys.path.insert(0,'.'); from common import *
from PIL import ImageDraw
COL = dict(head=(255,80,80), neck=(255,180,0), torso=(80,200,80), pelvis=(60,120,255), upper_arm_R=(200,0,200), forearm_R=(0,200,200), upper_arm_L=(255,120,200),
           forearm_L=(120,255,255), thigh_R=(150,100,40), shin_R=(255,255,0), foot_R=(255,0,0), thigh_L=(120,60,200), shin_L=(0,255,120), foot_L=(255,150,80))
def seg_image(ang, flaps=False):
    pj = json.load(open(f'{OUT}/{ang}/parts.json')); F = frame(ang).astype(float)
    o = F * 0.25 + 40
    for p in pj['pieces']:
        a = np.array(Image.open(f"{OUT}/{ang}/{p['file']}")); m = a[..., 3] > 0
        own = m & (np.abs(a[..., :3].astype(int) - F.astype(int)).sum(2) == 0)
        o[own] = 0.45 * F[own] + 0.55 * np.array(COL[p['id']])
    im = Image.fromarray(o.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for p in pj['pieces']:
        x, y = p['pivot']; d.ellipse([x-3, y-3, x+3, y+3], outline=(255,255,255)); d.text((x+4, y-5), p['id'], fill=(255,255,255))
    return im
if __name__ == '__main__':
    for a in sys.argv[1:]: seg_image(a).save(f'{OUT}/scratch/seg_{a}.png')
