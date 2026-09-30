import json,numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
V='/workspace/shadowveil/views/apose'; G='/workspace/shadowveil/reference/grok_build/public/clean-room'
r=json.load(open(f'{V}/hands/rig.json')); g={p['id']:p for p in json.load(open(f'{G}/rig/apose.json'))['parts']}
Hc,Wc=1739,1365; res={}
def edge(m): return m & ~ndi.binary_erosion(m)
def hd(a,b):
    ea,eb=edge(a),edge(b); da=ndi.distance_transform_edt(~eb); db=ndi.distance_transform_edt(~ea)
    d1=da[ea]; d2=db[eb]; allv=np.concatenate([d1,d2])
    return float(allv.max()),float(np.percentile(allv,95)),float(allv.mean()),float(d1.max()),float(d2.max())
sheet=[]
for ours,gid in (('L','r-hand'),('R','l-hand')):
    acc=np.zeros((Hc,Wc),bool)
    for p in r['parts']:
        if p['id'].startswith(ours+'_') and p.get('file'):
            acc|=np.array(Image.open(f"{V}/hands/{p['file']}").convert('RGBA'))[...,3]>127
    P={p['id']:p for p in r['parts']}; op=np.array([P[ours+'_palm']['pivotX'],P[ours+'_palm']['pivotY']])
    gp=g[gid]; ga=np.array(Image.open(f'{G}/rig/{gid}.png').convert('RGBA'))[...,3]>127
    for mode,off in (('pivot-aligned',op-np.array(gp['pivot'],float)),('as-placed (same canvas)',np.zeros(2))):
        gm=np.zeros((Hc,Wc),bool); ox=int(round(gp['x']+off[0])); oy=int(round(gp['y']+off[1]))
        # half-pixel pivot (706.5): shift by rounding; record residual
        gm[oy:oy+ga.shape[0],ox:ox+ga.shape[1]]=ga
        inter=(acc&gm).sum(); uni=(acc|gm).sum(); H=hd(acc,gm)
        res[f'ours_{ours}_vs_{gid}_{mode}']=dict(offset=[float(off[0]),float(off[1])],placed_at=[ox,oy],rounding_residual=[float(gp['x']+off[0]-ox),float(gp['y']+off[1]-oy)],iou=float(inter/uni),ours_px=int(acc.sum()),grok_px=int(gm.sum()),only_ours=int((acc&~gm).sum()),only_grok=int((gm&~acc).sum()),edge_max=H[0],edge_p95=H[1],edge_mean=H[2],max_ours_to_grok=H[3],max_grok_to_ours=H[4])
        if mode=='pivot-aligned':
            ys,xs=np.nonzero(acc|gm); b=(xs.min()-6,ys.min()-6,xs.max()+7,ys.max()+7)
            img=np.zeros((b[3]-b[1],b[2]-b[0],3),np.uint8); a_=acc[b[1]:b[3],b[0]:b[2]]; g_=gm[b[1]:b[3],b[0]:b[2]]
            img[a_&g_]=(200,200,200); img[a_&~g_]=(255,60,60); img[g_&~a_]=(60,160,255)
            y,x=op[1]-b[1],op[0]-b[0]; cv2.circle(img,(int(x),int(y)),3,(0,255,0),-1)
            # locate the max offset point
            ea,eb=edge(acc),edge(gm); da=ndi.distance_transform_edt(~eb); db=ndi.distance_transform_edt(~ea)
            yy,xx=np.unravel_index(np.argmax(np.where(ea,da,0)),da.shape); cv2.circle(img,(int(xx-b[0]),int(yy-b[1])),5,(255,255,0),1)
            yy2,xx2=np.unravel_index(np.argmax(np.where(eb,db,0)),db.shape); cv2.circle(img,(int(xx2-b[0]),int(yy2-b[1])),5,(255,0,255),1)
            res[f'ours_{ours}_vs_{gid}_{mode}']['max_pt_ours']=[int(xx),int(yy)]; res[f'ours_{ours}_vs_{gid}_{mode}']['max_pt_grok']=[int(xx2),int(yy2)]
            sheet.append(Image.fromarray(img).resize((img.shape[1]*3,img.shape[0]*3),Image.NEAREST))
json.dump(res,open('outline_match.json','w'),indent=1)
for k,v in res.items(): print(k,{a:(round(b,3) if isinstance(b,float) else b) for a,b in v.items()})
W=Image.new('RGB',(sum(s.width for s in sheet)+10,max(s.height for s in sheet)),'black'); x=0
for s in sheet: W.paste(s,(x,0)); x+=s.width+10
W.save('outline_overlay.png')
