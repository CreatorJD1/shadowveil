# Step 5 (F7) A-pose wrist flap check on Base Body's staged pieces (read-only use of body_tools/work/hairless_division_staged/apose).
# wrist_sim.py <hands dir overlay or ''> <out.json> [order: under|over]
# Rest: body pieces back-to-front with each hand side composited UNDER the forearm pieces (Body's note: forearm draws above the hand),
# compared with hairless_'+V+'.png (exact, no resampling).  Bend: each hand side (all apose hand parts at curl 0) rotated rigidly about the
# palm pivot by wrist*25 deg (palmExt, wristMaxDeg default 25), premultiplied bilinear, forearm static; metrics in a 46 px box round the pivot,
# new vs rest: enclosed holes, tears (closing r3), partial alpha (A<255 inside 4 px erosion); lineart: breaks (edge px without line px within 1 px,
# runs>=2, line = A>=128 & lum<95), mean line width (2*EDT on skeleton) in the box.
import sys,json,os,numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize
V,OV,OUT=sys.argv[1],sys.argv[2],sys.argv[3];ORDER='under'
B='/workspace/shadowveil/body_tools/work/hairless_division_staged/'+V+'/';H='/workspace/shadowveil/views/'+V+'/hands/'
P=json.load(open(B+'parts.json'));rig=json.load(open(H+'rig.json'));parts=sorted([p for p in rig['parts'] if p.get('file') and not p.get('hidden_never')],key=lambda p:p['layer'])
def rgba(f): return np.array(Image.open(f).convert('RGBA')).astype(np.float64)/255.
def over(dst,src):  # straight-alpha over, float
    a=src[...,3:4];oa=a+dst[...,3:4]*(1-a);rgb=np.where(oa>0,(src[...,:3]*a+dst[...,:3]*dst[...,3:4]*(1-a))/np.maximum(oa,1e-9),0);return np.concatenate([rgb,oa],-1)
def hand(S):
    c=None
    for p in parts:
        if not p['id'].startswith(S+'_'): continue
        f=(OV+'/'+p['file']) if OV and os.path.exists(OV+'/'+p['file']) else H+p['file'];im=rgba(f);c=im if c is None else over(c,im)
    return c
SIDES=[x for x in 'LR' if os.path.exists(B+f'wrist_line_{x}.json')];piv={S:tuple(json.load(open(B+f'wrist_line_{S}.json'))['pivot']) for S in SIDES};HS={S:hand(S) for S in SIDES}
def rot(im,deg,c):
    if deg==0: return im
    t=np.radians(deg);yy,xx=np.mgrid[:im.shape[0],:im.shape[1]].astype(float);x=xx+.5-c[0];y=yy+.5-c[1]
    sx=np.cos(t)*x+np.sin(t)*y+c[0]-.5;sy=-np.sin(t)*x+np.cos(t)*y+c[1]-.5
    pm=np.concatenate([im[...,:3]*im[...,3:4],im[...,3:4]],-1);o=np.stack([nd.map_coordinates(pm[...,k],[sy,sx],order=1,mode='constant') for k in range(4)],-1)
    return np.concatenate([np.where(o[...,3:4]>0,o[...,:3]/np.maximum(o[...,3:4],1e-9),0),o[...,3:4]],-1)
def hands_on(out,degL,degR):
    for S in SIDES: out=over(out,rot(HS[S],degL if S=='L' else degR,piv[S]))
    return out
def scene(degL,degR,crop=None):
    out=np.zeros(HS[SIDES[0]].shape);hands_done=False
    for pid in P['layerOrder_backToFront']:
        if pid.startswith('forearm') and not hands_done and ORDER=='under':
            out=hands_on(out,degL,degR);hands_done=True
        out=over(out,rgba(B+f'pieces/{pid}.png'))
    if not hands_done: out=hands_on(out,degL,degR)
    return np.round(out*255).astype(np.uint8)
def disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def metrics(im,S,R0=None):
    cx,cy=map(int,piv[S]);b=46;c=im[cy-b:cy+b,cx-b:cx+b];A=c[...,3].astype(int);op=A>=128
    lab,n=nd.label(~op);brd=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])));e=np.isin(lab,[k for k in range(1,n+1) if k not in brd])
    t=nd.binary_closing(op,structure=disk(3),border_value=0)&~op&~e;s=nd.binary_erosion(op,structure=disk(4),border_value=0)&(A<255)
    lum=c[...,:3].astype(float)@[0.299,0.587,0.114];L=op&(lum<95);edge=op&~nd.binary_erosion(op,border_value=1)
    unc=edge&~nd.binary_dilation(L,structure=np.ones((3,3)));lb,_=nd.label(unc,structure=np.ones((3,3)));sz=np.bincount(lb.ravel());runs=np.isin(lb,np.nonzero(sz>=2)[0][1:]) if len(sz)>1 else unc&False
    sk=skeletonize(L);w=2*nd.distance_transform_edt(L)[sk]
    return dict(holes=int(e.sum()),tears=int(t.sum()),partial=int(s.sum()),breaks=int(runs.sum()),width=round(float(w.mean()),3) if len(w) else None),(e,t,s,runs)
res={'order':ORDER,'overlay':OV}
rest=scene(0,0);ref=np.array(Image.open(B+'hairless_'+V+'.png').convert('RGBA'))
d=(rest.astype(int)!=ref.astype(int)).any(2);res['rest_diff_px']=int(d.sum());hm=np.array(Image.open('/workspace/shadowveil/hands/'+V+'_hand_erase_mask.png').convert('L'))>0
res['rest_diff_in_hand_mask']=int((d&hm).sum());res['rest_diff_outside']=int((d&~hm).sum())
Image.fromarray(rest).save(OUT.replace('.json','_rest.png'))
WR={'bend+1':1,'bend-1':-1,'anger+0.14':0.14,'jump-0.2':-0.2,'jump+0.2969':0.2969,'run-0.12':-0.12,'run+0.12':0.12}
res['live_vs_ref_in_hand_mask_note']='hairless ref has hands erased; compare rest against live run'
for S in SIDES:
    m0,_=metrics(rest,S);res[f'{S} rest']=m0
    for k,x in WR.items():
        deg=x*25;im=scene(deg if S=='L' else 0,deg if S=='R' else 0);m,_=metrics(im,S)
        m['new_holes']=m['holes']-m0['holes'];m['new_tears']=m['tears']-m0['tears'];m['new_partial']=m['partial']-m0['partial'];m['new_breaks']=m['breaks']-m0['breaks']
        m['dw']=None if m['width'] is None or m0['width'] is None else round(m['width']-m0['width'],3);m['deg']=deg;res[f'{S} {k}']=m
        if k in ('bend+1','bend-1'): Image.fromarray(im[int(piv[S][1])-46:int(piv[S][1])+46,int(piv[S][0])-46:int(piv[S][0])+46]).save(OUT.replace('.json',f'_{S}_{k}.png'))
        print(S,k,m)
print('rest diff px',res['rest_diff_px'],'in hand mask',res['rest_diff_in_hand_mask'],'outside',res['rest_diff_outside'])
json.dump(res,open(OUT,'w'),indent=1)
