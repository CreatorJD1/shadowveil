import json,numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
from locate import fg
from arm2 import arms2,wrist2,geoball
from handgeo import handgeo
R='/workspace/shadowveil/views'; FR='/workspace/shadowveil/reference/apose_turn/frames'
def hands(m):
    ys,xs=np.nonzero(m); top=ys.min(); H=ys.max()-top+1; cx=np.median(xs); out={}
    comps=[]
    for fr in (0.30,0.40):
        for c in arms2(m,top,H,fr):
            if c['area']>40000*(H/1056)**2: continue
            if all(np.hypot(c['tip'][0]-q['tip'][0],c['tip'][1]-q['tip'][1])>15 for q in comps): comps.append(c)
    for c in comps:
        gb=geoball(m,c['tip'],int(170*H/1056)); c=dict(c,mask=gb); w=wrist2(c,H); g=handgeo(w['hand'],w['wrist'],w['axis'])
        side='imgR' if np.mean(np.nonzero(gb)[1])>cx else 'imgL'
        hy,hx=np.nonzero(w['hand'])
        out[side]=dict(wrist=w['wrist'],axis=w['axis'],tip=max(g['tip_pts'],key=lambda p:(np.array(p)-w['wrist'])@np.array(w['axis'])) if g['tip_pts'] else None,L=g['L'],palm=g['palm_len'],pw=g['palm_w'],tips=g['tips'],centroid=[float(hx.mean()),float(hy.mean())],mask=w['hand'])
    return out,H
if __name__=='__main__':
    J=json.load(open('handoff_bboxfit.json'))
    res={}
    for f,v in (('f001','apose'),('f109','back')):
        rec=J[f]; A=np.float32([[rec['scale'],0,rec['tx']],[0,rec['scale'],rec['ty']]])
        fr=np.array(Image.open(f'{FR}/{f}.png').convert('RGB')); fm=fg(fr); lab,n=ndi.label(fm); fm=lab==(np.argmax(ndi.sum(fm,lab,range(1,n+1)))+1)
        fmw=cv2.warpAffine(fm.astype(np.uint8),A,(1365,1739),flags=cv2.INTER_LINEAR)>0
        vm=np.array(Image.open(f'{R}/{v}/base.png').convert('RGBA'))[...,3]>127
        HF,hf=hands(fmw); HV,hv=hands(vm)
        for side in ('imgL','imgR'):
            a,b=HF[side],HV[side]
            her={'apose':{'imgL':'R','imgR':'L'},'back':{'imgL':'L','imgR':'R'}}[v][side]
            d=lambda p,q:[round(p[0]-q[0],1),round(p[1]-q[1],1)]
            iou=float((a['mask']&b['mask']).sum()/(a['mask']|b['mask']).sum())
            sh=np.round(np.array(b['wrist'])-np.array(a['wrist'])).astype(int); am=np.roll(np.roll(a['mask'],sh[1],0),sh[0],1)
            iou_w=float((am&b['mask']).sum()/(am|b['mask']).sum())
            ang=np.degrees(np.arctan2(a['axis'][1],a['axis'][0])-np.arctan2(b['axis'][1],b['axis'][0]))
            r=dict(her=her,wrist_off=d(a['wrist'],b['wrist']),tip_off=d(a['tip'],b['tip']),centroid_off=d(a['centroid'],b['centroid']),L_frame=a['L'],L_view=b['L'],L_ratio=a['L']/b['L'],palm_frame=a['palm'],palm_view=b['palm'],pw_frame=a['pw'],pw_view=b['pw'],tips=(a['tips'],b['tips']),axis_rot_deg=float(ang),IoU_fit=iou,IoU_wrist_aligned=iou_w,view_wrist=b['wrist'],view_tip=b['tip'])
            res[f'{f}_{v}_{her}']=r; print(f,v,her,{k:(round(x,3) if isinstance(x,float) else x) for k,x in r.items() if k not in('view_wrist','view_tip')})
            # crop: view silhouette vs fitted frame silhouette
            x0,y0=[int(min(a['centroid'][i],b['centroid'][i]))-110 for i in (0,1)]; x0=max(0,x0); y0=max(0,y0)
            img=np.zeros((220,220,3),np.uint8); A_=a['mask'][y0:y0+220,x0:x0+220]; B_=b['mask'][y0:y0+220,x0:x0+220]
            img[A_&B_]=(200,200,200); img[B_&~A_]=(255,60,60); img[A_&~B_]=(60,160,255)
            Image.fromarray(img).resize((440,440),Image.NEAREST).save(f'_s/sil_{f}_{her}.png')
    json.dump(res,open('handoff_sil.json','w'),indent=1,default=float)
