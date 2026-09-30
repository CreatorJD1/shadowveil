# Old (v1 render) vs new (re-render with the wisp underfill) tpose idle frames, head-compensated wisp region (wisp mask dilated 2 px,
# same definition as hair/qa/idle_battle/tools/alpha_seams.py). Frames are read one at a time.
import sys,json,os
sys.path.insert(0,'/workspace/shadowveil/hair/qa/idle_battle/tools')
from common import *
OLD=f'{P}/rig/previews/idle/frames/tpose'; NEW=f'{P}/hair/qa/wisp_fix/render/tpose_idle'
s=View('tpose'); x0,y0,w,h=s.x0,s.y0,s.w,s.h
wm=np.array(Image.open(f'{P}/hair/tpose_eye_crossing_wisp_mask.png').convert('L'))[y0:y0+h,x0:x0+w]>0
wisp=cv2.dilate(wm.astype(np.uint8),disk(2))>0
fill=np.array(Image.open(f'{P}/hair/qa/wisp_fix/work/fill_mask_tpose.png'))[y0:y0+h,x0:x0+w]>0
fillreg=cv2.dilate(fill.astype(np.uint8),disk(3))>0
FO=json.load(open(f'{OLD}/meta.json'))['frames']; FN=json.load(open(f'{NEW}/meta.json'))['frames']
rest=np.array(Image.open(f'{NEW}/rest.png'))
restO=np.array(Image.open(f'{OLD}/rest.png'))
rows=[]
def stats(img,HmR,restA):
    a=img[...,3].astype(int)
    rw=warp(restA,HmR,w,h,True)==255; Wd=warp(wisp.astype(np.uint8),HmR,w,h,True)>0
    reg=Wd&rw; hole=(a<255)&reg
    rgb=img[...,:3].astype(float); al=a[...,None]/255.
    comp=rgb*al+np.array([0,0,255.])*(1-al)
    blue=reg&(comp[...,2]>comp[...,0]+40)&(comp[...,2]>comp[...,1]+40)
    return int(hole.sum()),int(a[reg].min()) if reg.any() else 255,int(blue.sum()),int((reg&(a==0)).sum())
for i in range(min(len(FO),len(FN))):
    ang=(FN[i]['bones'].get('head') or FN[i]['bones'].get('torso'))[2]; angO=(FO[i]['bones'].get('head') or FO[i]['bones'].get('torso'))[2]
    HmR=s.roi_M(rotAt(PIV[0],PIV[1],ang))
    o=np.array(Image.open(f'{OLD}/frames/f{i:04d}.png'))[y0:y0+h,x0:x0+w]
    n=np.array(Image.open(f'{NEW}/frames/f{i:04d}.png'))[y0:y0+h,x0:x0+w]
    so=stats(o,HmR,restO[y0:y0+h,x0:x0+w,3]); sn=stats(n,HmR,rest[y0:y0+h,x0:x0+w,3])
    Fr=warp(fillreg.astype(np.uint8),HmR,w,h,True)>0
    d=(o.astype(int)!=n.astype(int)).any(-1)
    rows.append(dict(frame=i,t=FN[i]['t'],head_deg=ang,head_deg_old=angO,soft=abs(ang)>=0.01,
        old=dict(alpha_lt255=so[0],minA=so[1],blue=so[2],alpha0=so[3]),new=dict(alpha_lt255=sn[0],minA=sn[1],blue=sn[2],alpha0=sn[3]),
        diff_px_outside_fill_region=int((d&~Fr).sum()),diff_px_inside=int((d&Fr).sum())))
json.dump(rows,open(f'{P}/hair/qa/wisp_fix/data_tpose_idle_wisp.json','w'),indent=0)
def mx(k,side): i=max(range(len(rows)),key=lambda j:rows[j][side][k]); return rows[i][side][k],i
print('frames',len(rows),'soft',sum(r['soft'] for r in rows))
for side in ('old','new'):
    print(side,'max alpha<255',mx('alpha_lt255',side),'frames>0',sum(r[side]['alpha_lt255']>0 for r in rows),'min alpha',min(r[side]['minA'] for r in rows),
          'max blue',mx('blue',side),'max alpha0',mx('alpha0',side))
print('max head-angle mismatch old/new',max(abs(r['head_deg']-r['head_deg_old']) for r in rows))
print('max diff outside fill region',max(r['diff_px_outside_fill_region'] for r in rows))
for f in (20,60,67): print(f,rows[f])
