# Lossless check of the renderer's RGBA frames (rig/previews/idle/frames/<name>/frames): interior alpha<255 (rest=255) in the head region.
# On the video these pixels blend with grey #808080; in a #0000FF keyed render they show key blue.
import json,sys
from common import *
names=sys.argv[1:] or available_names()
res={}
for n in names:
    v='apose' if n.startswith('apose') else n.rsplit('_',1)[-1] if n.startswith('keys') else n
    s=View(v); x0,y0,w,h=s.x0,s.y0,s.w,s.h
    er=s.erase.astype(np.uint8); eredge=(cv2.dilate(er,disk(2))>0)&~(cv2.erode(er,disk(2))>0)
    hairu=cv2.dilate(s.hair_union.astype(np.uint8),disk(3))>0
    wp=f'{P}/hair/{v}_eye_crossing_wisp_mask.png'
    wisp=(cv2.dilate((np.array(Image.open(wp).convert('L'))[y0:y0+h,x0:x0+w]>0).astype(np.uint8),disk(2))>0) if os.path.exists(wp) else np.zeros((h,w),bool)
    F=json.load(open(f'{IDLE}/frames/{n}/meta.json'))['frames']
    rest=np.array(Image.open(f'{IDLE}/frames/{n}/rest.png'))[y0:y0+h,x0:x0+w,3]
    rows=[]
    for i in range(len(F)):
        a=np.array(Image.open(f'{IDLE}/frames/{n}/frames/f{i:04d}.png'))[y0:y0+h,x0:x0+w,3]
        ang=(F[i]['bones'].get('head') or F[i]['bones'].get('torso'))[2]; HmR=s.roi_M(rotAt(PIV[0],PIV[1],ang))
        ww=lambda m:warp(m.astype(np.uint8),HmR,w,h,True)>0
        # rest silhouette follows the head
        rw=warp(rest,HmR,w,h,True)==255
        S=ww(s.sil); hole=(a<255)&rw&S; full=(a==0)&rw&S; E=ww(eredge); Wd=ww(wisp); Hu=ww(hairu)
        r=dict(frame=i,t=F[i]['t'],axis=abs(ang)<0.01,head=int(hole.sum()),hair_cut=int((hole&E&~Wd).sum()),wisp=int((hole&Wd).sum()),
               hair_other=int((hole&Hu&~E&~Wd).sum()),nonhair=int((hole&~Hu).sum()),minA=int(a[hole].min()) if hole.any() else 255,full=int(full.sum()),full_hair=int((full&(E|Wd|Hu)).sum()),
               wispA=int(a[hole&Wd].min()) if (hole&Wd).any() else 255, cutA=int(a[hole&E].min()) if (hole&E).any() else 255)
        rows.append(r)
    ax=np.array([r['axis'] for r in rows])
    def st(k): 
        x=np.array([r[k] for r in rows]); i=int(x.argmax()); return dict(frames=int((x>0).sum()),max=int(x.max()),max_frame=i,max_t=rows[i]['t'],in_axis_frames=int((x[ax]>0).sum()))
    res[n]=dict(view=v,soft_frames=int((~ax).sum()),head=st('head'),hair_cut=st('hair_cut'),wisp=st('wisp'),hair_other=st('hair_other'),nonhair=st('nonhair'),full=st('full'),full_hair=st('full_hair'),
                min_alpha_wisp=min(r['wispA'] for r in rows),min_alpha_cut=min(r['cutA'] for r in rows),rows=rows)
    print(n,{k:(res[n][k]['frames'],res[n][k]['max'],res[n][k]['max_frame'],res[n][k]['in_axis_frames']) for k in ('head','hair_cut','wisp','hair_other','nonhair','full','full_hair')},'minA wisp/cut',res[n]['min_alpha_wisp'],res[n]['min_alpha_cut'],flush=True)
    json.dump(res[n],open(f'{OUT}/data/alpha_{n}.json','w'))
