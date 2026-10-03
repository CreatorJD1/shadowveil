import sys; sys.path.insert(0,'.'); from posekit import *
for ang in ('045','315'):
    C = ctx(ang); pj, img = load_set(ORIG+'/'+ang); dt = ndi.distance_transform_edt(C['fg'])
    own = {k: (img[k][...,3]>0) & (np.abs(img[k][...,:3].astype(int)-C['F']).max(2)==0) & C['fg'] & ~C['TM'] for k in img}
    st4 = ndi.generate_binary_structure(2,1)
    for jn, j in pj['joints'].items():
        if 'pivot' not in j or 'joint_radius_px' not in j: continue
        p = j['pivot']; ch = j['flap_on']; par = j['under']; 
        if jn=='head_neck': ch,par='neck','head'
        seam = own[ch] & ndi.binary_dilation(own[par], st4)
        ys,xs = np.nonzero(seam)
        # seam direction & centre
        print(ang, jn, 'pivot', p, 'inscribed r', round(float(dt[int(p[1]),int(p[0])]),1), 'seam', len(xs), 'seam x', xs.min() if len(xs) else None, xs.max() if len(xs) else None, 'y', ys.min() if len(ys) else None, ys.max() if len(ys) else None, 'seam mid', (round(xs.mean(),1), round(ys.mean(),1)) if len(xs) else None, 'r', j['joint_radius_px'])
