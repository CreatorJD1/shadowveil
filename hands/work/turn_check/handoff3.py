import json,numpy as np,cv2
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
from locate import fg
from handoff2 import hands   # same silhouette hand measurement on both sides
R='/workspace/shadowveil/views'; FR='/workspace/shadowveil/reference/apose_turn/frames'
MAP=json.load(open('/workspace/shadowveil/body_tools/work/apose_turn/angle_map.json'))['handoff']
# manual landmarks for profile frames, read on a 10 px grid in bbox-fit coords, converted to frame px here
BB={'f062':(1.5432330827067668,100.7011278195489,-46.421052631578945),'f160':(1.549056603773585,94.90754716981132,-49.84528301886792)}
MAN={'f062':dict(frame_tip=(655,862),frame_thumb=(648,757),frame_width_y=780,frame_front_back=(648,678),view_tip=(660,998),view_thumb=(637,954),view_front_back=(634,702)),
     'f160':dict(frame_tip=(700,863),frame_thumb=(706,757),frame_width_y=790,frame_front_back=(673,700),view_tip=(684,998),view_thumb=(720,953),view_front_back=(651,720))}
res={}
def outline(m): return m&~ndi.binary_erosion(m,iterations=2)
for v,f in (('apose','f001'),('left','f062'),('right','f160'),('back','f109')):
    m=MAP[v]; s,tx,ty=m['scale'],m['dx'],m['dy']; A=np.float32([[s,0,tx],[0,s,ty]])
    fr=np.array(Image.open(f'{FR}/{f}.png').convert('RGB')); frw=cv2.warpAffine(fr,A,(1365,1739),flags=cv2.INTER_CUBIC,borderValue=(0,0,255))
    base=np.array(Image.open(f'{R}/{v}/base.png').convert('RGBA')); bv=base[...,:3].copy(); bv[base[...,3]==0]=0
    r=json.load(open(f'{R}/{v}/hands/rig.json')); P={p['id']:p for p in r['parts']}
    rec=dict(frame=f,map=dict(scale=s,dx=tx,dy=ty),hands={})
    if f in ('f001','f109'):
        fm=fg(fr); lab,n=ndi.label(fm); fm=lab==(np.argmax(ndi.sum(fm,lab,range(1,n+1)))+1)
        fmw=cv2.warpAffine(fm.astype(np.uint8),A,(1365,1739),flags=cv2.INTER_LINEAR)>0
        HF,_=hands(fmw); HV,_=hands(base[...,3]>127)
        for side in ('imgL','imgR'):
            a,b=HF[side],HV[side]; her={'apose':{'imgL':'R','imgR':'L'},'back':{'imgL':'L','imgR':'R'}}[v][side]
            d=lambda p,q:[round(float(p[0]-q[0]),1),round(float(p[1]-q[1]),1)]
            sh=np.round(np.array(b['wrist'])-np.array(a['wrist'])).astype(int); am=np.roll(np.roll(a['mask'],sh[1],0),sh[0],1)
            rec['hands'][her]=dict(method='silhouette (wrist cut + fingertip + centroid), same code both sides',wrist_dxdy=d(a['wrist'],b['wrist']),tip_dxdy=d(a['tip'],b['tip']),centroid_dxdy=d(a['centroid'],b['centroid']),
                L_frame=round(a['L'],1),L_view=round(b['L'],1),scale_ratio=round(a['L']/b['L'],3),palm_w_ratio=round(a['pw']/b['pw'],3) if a['pw'] and b['pw'] else None,
                axis_rot_deg=round(float(np.degrees(np.arctan2(a['axis'][1],a['axis'][0])-np.arctan2(b['axis'][1],b['axis'][0]))),1),
                IoU_mapped=round(float((a['mask']&b['mask']).sum()/(a['mask']|b['mask']).sum()),3),IoU_wrist_aligned=round(float((am&b['mask']).sum()/(am|b['mask']).sum()),3))
            # crop
            ys,xs=np.nonzero(a['mask']|b['mask']); Q=(max(0,xs.min()-25),max(0,ys.min()-25),min(1365,xs.max()+25),min(1739,ys.max()+25))
            ov=frw.copy(); ov[outline(b['mask'])]=(255,255,0)
            strip=np.concatenate([bv[Q[1]:Q[3],Q[0]:Q[2]],frw[Q[1]:Q[3],Q[0]:Q[2]],ov[Q[1]:Q[3],Q[0]:Q[2]]],1)
            im=Image.fromarray(strip).resize((strip.shape[1]*2,strip.shape[0]*2),Image.LANCZOS); dr=ImageDraw.Draw(im)
            h=rec['hands'][her]; dr.text((4,4),f"{v} view her {her} | {f} mapped | overlay (yellow = view hand outline)  wrist d{h['wrist_dxdy']} tip d{h['tip_dxdy']} scale {h['scale_ratio']}",fill='white')
            im.save(f'handoff_{f}_{v}_{her}.png')
    else:
        so,txo,tyo=BB[f]; M=MAN[f]
        conv=lambda p:(round(s*(p[0]-txo)/so+tx,1),round(s*(p[1]-tyo)/so+ty,1))
        ft,fth=conv(M['frame_tip']),conv(M['frame_thumb']); fw=abs(conv((M['frame_front_back'][1],0))[0]-conv((M['frame_front_back'][0],0))[0])
        vt,vth=M['view_tip'],M['view_thumb']; vw=M['view_front_back'][1]-M['view_front_back'][0]
        sd='L' if v=='left' else 'R'
        rec['hands'][sd]=dict(method='manual landmarks on 10 px grid (hand not separable from hip silhouette); +-2 px reading',frame_tip=ft,view_tip=vt,tip_dxdy=[round(ft[0]-vt[0],1),round(ft[1]-vt[1],1)],frame_thumb=fth,view_thumb=vth,thumb_dxdy=[round(fth[0]-vth[0],1),round(fth[1]-vth[1],1)],
            tip_to_thumb_frame=round(ft[1]-fth[1],1),tip_to_thumb_view=vt[1]-vth[1],front_back_width_frame=round(fw,1),front_back_width_view=vw,width_ratio=round(fw/vw,3),pivot=[P[sd+'_palm']['pivotX'],P[sd+'_palm']['pivotY']])
        acc=np.zeros((1739,1365),bool)
        for p in r['parts']:
            if p['id'].startswith(sd+'_') and p.get('file'): acc|=np.array(Image.open(f"{R}/{v}/hands/{p['file']}").convert('RGBA'))[...,3]>127
        Q=(560,680,820,1030); ov=frw.copy(); ov[outline(acc)]=(255,255,0)
        strip=np.concatenate([bv[Q[1]:Q[3],Q[0]:Q[2]],frw[Q[1]:Q[3],Q[0]:Q[2]],ov[Q[1]:Q[3],Q[0]:Q[2]]],1)
        im=Image.fromarray(strip).resize((strip.shape[1]*2,strip.shape[0]*2),Image.LANCZOS); dr=ImageDraw.Draw(im); W=Q[2]-Q[0]
        for k in (1,2):
            for pt,col in ((ft,(0,255,0)),(fth,(0,255,0))): x=(pt[0]-Q[0]+k*W)*2; y=(pt[1]-Q[1])*2; dr.ellipse((x-5,y-5,x+5,y+5),outline=col,width=2)
        for pt in (vt,vth): x=(pt[0]-Q[0])*2; y=(pt[1]-Q[1])*2; dr.ellipse((x-5,y-5,x+5,y+5),outline=(255,0,0),width=2)
        h=rec['hands'][sd]; dr.text((4,4),f"{v} view her {sd} (red=tip/thumb) | {f} mapped (green) | overlay yellow=view hand outline   tip d{h['tip_dxdy']} thumb d{h['thumb_dxdy']}",fill='white')
        im.save(f'handoff_{f}_{v}_{sd}.png')
    res[f]=rec; print(f,v,json.dumps(rec['hands']))
json.dump(res,open('handoff.json','w'),indent=1)
