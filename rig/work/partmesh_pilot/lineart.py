# Lineart continuity/width QA on hand-only composites. lineart.py <renderdir> <view> <rig.json> <out.json>
# line = opaque (A>=128) & luminance<LUM. Joints = world position of every finger/thumb segment pivot (frame pivot if set).
# per joint zone (r=JR): width = mean 2*EDT on the line skeleton; breaks = silhouette-edge px with no line px within 1 px (runs>=2 px);
# comps = line components touching the zone; sharp = contour vertices whose turn angle > SHARP deg (k=4 px chords), clustered.
# every metric is compared with the same joint at rest. Also mean line width per finger (px where that finger's layers are opaque).
import sys,json,numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize
from skimage.measure import find_contours
from pivot_qa_lib import comp_dir
D,view,RIG,OUT=sys.argv[1:5];LUM=95;JR=10;SHARP=75
rig=json.load(open(RIG));by={p['id']:p for p in rig['parts']}
meta=json.load(open(D+'/meta.json'));C={c['name']:c for c in meta['cases']}
FING=['Thumb','Index','Middle','Ring','Pinky']
def line_mask(im):
    lum=0.299*im[...,0]+0.587*im[...,1]+0.114*im[...,2];return (im[...,3]>=128)&(lum<LUM)
def joints(cn,S):
    J={}
    for f in FING:
        for s in (1,2,3):
            pid=f'{S}_{f}{s}';p=by.get(pid);c=C[cn]['parts'].get(pid)
            if not p or not c: continue
            fr=p.get('frames') or [];fi=c['frame'];e=fr[fi] if fi is not None and fi<len(fr) else None
            piv=(e.get('pivot') if isinstance(e,dict) else None) or [p['pivotX'],p['pivotY']]
            a,b,cc,d,ee,ff=c['M'];J[pid]=(a*piv[0]+cc*piv[1]+ee,b*piv[0]+d*piv[1]+ff)
    return J
def owner_map(cn,S):
    ps=sorted([k for k in C[cn]['parts'] if k.startswith(S+'_')],key=lambda k:C[cn]['parts'][k]['layer']);O=None
    for i,p in enumerate(ps):
        a=np.array(Image.open(f'{D}/{cn}_layers/{p}.png'))[...,3]>=128
        if O is None: O=np.full(a.shape,-1,int)
        O[a]=i
    fam=[(p[2:].rstrip('123') if p[-1] in '123' else p[2:]) for p in ps]
    return O,fam
def sharp_pts(op,own=None):
    pts=[]
    for ct in find_contours(op.astype(float),0.5):
        n=len(ct)
        if n<12: continue
        k=4;P=ct[:, ::-1]
        v1=P[(np.arange(n)-k)%n]-P;v2=P[(np.arange(n)+k)%n]-P
        cos=(v1*v2).sum(1)/(np.linalg.norm(v1,axis=1)*np.linalg.norm(v2,axis=1)+1e-9);ang=np.degrees(np.arccos(np.clip(cos,-1,1)))  # 180 = straight
        idx=np.nonzero(180-ang>SHARP)[0]
        # cluster consecutive indices, keep the sharpest of each
        if len(idx):
            groups=np.split(idx,np.nonzero(np.diff(idx)>2)[0]+1)
            for g in groups:
                i=g[np.argmin(ang[g])]
                if own is not None:  # keep only corners whose two chord ends sit on the same finger (intra-finger kink, not a crotch between fingers)
                    O,fam,idx_near=own;fs=[]
                    for q in (P[(i-k)%n],P[(i+k)%n]):
                        y,x=int(round(q[1])),int(round(q[0]));y=min(max(y,0),O.shape[0]-1);x=min(max(x,0),O.shape[1]-1)
                        yy,xx=idx_near[0][y,x],idx_near[1][y,x];fs.append(fam[O[yy,xx]] if O[yy,xx]>=0 else None)
                    if fs[0]!=fs[1] or fs[0] is None: continue
                pts.append((P[i][0],P[i][1],180-ang[i]))
    return pts
def zone_stats(im,J,fingerA,own=None):
    A=im[...,3];op=A>=128;L=line_mask(im);sk=skeletonize(L);dt=nd.distance_transform_edt(L)
    edge=op&~nd.binary_erosion(op,border_value=0);cov=nd.binary_dilation(L,structure=np.ones((3,3)))
    unc=edge&~cov;lab,_=nd.label(unc,structure=np.ones((3,3)));sz=np.bincount(lab.ravel());runs=np.isin(lab,np.nonzero(sz>=2)[0][1:]) if len(sz)>1 else unc&False
    if own is not None:
        O,fam=own;_,idx=nd.distance_transform_edt(O<0,return_indices=True);own=(O,fam,idx)
    SP=sharp_pts(op,own);JS=7;yy,xx=np.mgrid[:A.shape[0],:A.shape[1]];out={}
    llab,_=nd.label(L,structure=np.ones((3,3)))
    for pid,(x,y) in J.items():
        Z=(xx-x)**2+(yy-y)**2<=JR*JR;w=2*dt[sk&Z]
        out[pid]=dict(width=float(w.mean()) if len(w) else None,breaks=int((runs&Z).sum()),comps=int(len(set(np.unique(llab[Z]))-{0})),
                      sharp=sum(1 for px,py,t in SP if (px-x)**2+(py-y)**2<=JS*JS),sharp_max=max([t for px,py,t in SP if (px-x)**2+(py-y)**2<=JS*JS],default=0))
    fw={}
    for f,FA in fingerA.items():
        w=2*dt[sk&FA];fw[f]=float(w.mean()) if len(w) else None
    return out,fw
def fingerA(cn,S):
    r={}
    for f in FING:
        m=None
        for s in (1,2,3):
            fn=f'{D}/{cn}_layers/{S}_{f}{s}.png'
            try: a=np.array(Image.open(fn))[...,3]>=128
            except FileNotFoundError: continue
            m=a if m is None else m|a
        if m is not None: r[f]=nd.binary_dilation(m,iterations=1)
    return r
res={}
for S in 'LR':
    if not any(k.startswith(S+'_') for k in C['rest']['parts']): continue
    Jr=joints('rest',S);zr,fr=zone_stats(comp_dir(D,'rest',S),Jr,fingerA('rest',S),owner_map('rest',S))
    for cn in [c for c in C if c!='rest']:
        z,fw=zone_stats(comp_dir(D,cn,S),joints(cn,S),fingerA(cn,S),owner_map(cn,S))
        rows={}
        for pid in z:
            a,b=z[pid],zr.get(pid)
            if not b: continue
            rows[pid]=dict(dw=None if a['width'] is None or b['width'] is None else round(a['width']-b['width'],2),
                           new_breaks=a['breaks']-b['breaks'],new_comps=a['comps']-b['comps'],new_sharp=a['sharp']-b['sharp'],sharp_max=round(a['sharp_max'],1))
        fdw={f:(None if fw.get(f) is None or fr.get(f) is None else round(fw[f]-fr[f],2)) for f in fr}
        res[f'{S} {cn}']=dict(joints=rows,finger_dw=fdw)
json.dump(dict(rest={S:None for S in 'LR'},cases=res),open(OUT,'w'))
# summary
FAILW=1.0
for k,r in res.items():
    J=r['joints'];bw=[(p,v['dw']) for p,v in J.items() if v['dw'] is not None and abs(v['dw'])>FAILW]
    br=[(p,v['new_breaks']) for p,v in J.items() if v['new_breaks']>=2];sh=[(p,v['new_sharp']) for p,v in J.items() if v['new_sharp']>0]
    fw=[(f,d) for f,d in r['finger_dw'].items() if d is not None and abs(d)>FAILW]
    print(view,k,'| width>1:',bw or '-','| fingerW>1:',fw or '-','| breaks:',br or '-','| new sharp:',sh or '-')
