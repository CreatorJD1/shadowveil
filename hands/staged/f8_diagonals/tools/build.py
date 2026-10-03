# F8 step 3: build staged parts for the 4 diagonal angles.  build.py <outroot> [interp order]
# Frame-scale label map -> frame parts (exact partition of the keyed/re-matted cut).  View scale: the WHOLE hand is resampled once
# (premultiplied, map_coordinates, view_fit base = s*frame + d, px centres at +0.5), then each view px is owned by exactly one part
# (label of the nearest frame px), so the parts rebuild the resampled hand exactly too.
import json,os,sys,numpy as np
from PIL import Image
from scipy import ndimage as nd
OUT=sys.argv[1];ORD=int(sys.argv[2]) if len(sys.argv)>2 else 3;CAP=float(sys.argv[3]) if len(sys.argv)>3 else 0;CAPP=float(sys.argv[4]) if len(sys.argv)>4 else 0
DC=json.load(open('../turn_check/diag_check.json'));SEG=json.load(open('seg.json'))
W,H=1365,1739;NEAR={'45':'L','135':'L','225':'R','315':'R'};SIGN={'+v':1,'-v':-1}
FING=['Pinky','Ring','Middle','Index','Thumb']   # back-to-front like the painted apose rig
CURL={'finger':(90,95,15),'thumb':(5,60,25)}
if os.environ.get('CURLF'): CURL['finger']=tuple(map(float,os.environ['CURLF'].split(',')))
if os.environ.get('CURLT'): CURL['thumb']=tuple(map(float,os.environ['CURLT'].split(',')))       # in-plane fold (tpose-style magnitudes; thumb from apose), sign set per hand below
JR={'1':7.5,'2':6.5,'3':5.5}
def blue(a): a=a.astype(int); return a[...,2]-np.maximum(a[...,0],a[...,1])>25
def resample(rgba,s,dx,dy):
    pm=rgba.astype(float)/255.;pm[...,:3]*=pm[...,3:4]
    Y,X=np.mgrid[:H,:W].astype(float);fx=(X+.5-dx)/s-.5;fy=(Y+.5-dy)/s-.5
    o=np.stack([nd.map_coordinates(pm[...,k],[fy,fx],order=ORD,mode='constant',cval=0) for k in range(4)],-1)
    a=np.clip(o[...,3],0,1);rgb=np.where(a[...,None]>1e-6,np.clip(o[...,:3]/np.maximum(a[...,None],1e-6),0,1),0)
    out=np.concatenate([rgb,a[...,None]],-1);out=np.round(out*255).astype(np.uint8);out[out[...,3]==0]=0
    # colour clamp to her own px range: no channel combination outside the hand's own colours can appear as a blue cast
    return out,fx,fy
log={}
for ang,NS in NEAR.items():
    if os.environ.get('CURLMAP'): CURL.update({k:tuple(v) for k,v in json.loads(os.environ['CURLMAP']).get(ang,{}).items()})
    od=f'{OUT}/{ang}';os.makedirs(od+'/frame_scale',exist_ok=True);parts=[];rec={}
    for S in 'RL':
        key=f'{ang}_{S}';z=np.load(f'cut/{key}.npz');s,dx,dy=float(z['scale']),float(z['dx']),float(z['dy'])
        rgb=z['rgb'];al=z['alpha'];m=al>0;hand=np.zeros(m.shape+(4,),np.uint8);hand[...,:3]=rgb;hand[...,3]=al;hand[~m]=0
        V=lambda p:[round(s*(p[0]+.5)+dx,2),round(s*(p[1]+.5)+dy,2)]
        if S==NS: lab=np.load(f'cut/{key}_lab.npy');piv=SEG[key]['piv']
        else: lab=np.where(m,'palm','');piv={'palm':z['w'].tolist()}
        # frame scale parts + exact rebuild
        ids=['palm']+([f+n for f in FING for n in '123'] if S==NS else [])
        reb=np.zeros_like(hand)
        for pid in ids:
            p=hand.copy();p[lab!=pid]=0;Image.fromarray(p).save(f'{od}/frame_scale/{S}_{pid}.png');reb[lab==pid]=p[lab==pid]
        # view scale
        hv,fx,fy=resample(hand,s,dx,dy)
        lab_m=np.where(m,lab,'');idx=nd.distance_transform_edt(lab_m=='',return_distances=False,return_indices=True)
        ny,nx=idx[0],idx[1];fyi=np.clip(np.round(fy).astype(int),0,m.shape[0]-1);fxi=np.clip(np.round(fx).astype(int),0,m.shape[1]-1)
        labv=lab_m[ny[fyi,fxi],nx[fyi,fxi]];labv[hv[...,3]==0]=''
        rebv=np.zeros_like(hv);tsign=SIGN[DC[key]['thumb_side']]
        u=z['u'];v=z['v']
        PI={}
        for pid in ids: p=hv.copy();p[labv!=pid]=0;PI[pid]=p
        # joint caps (her own px only): opaque px of the PARENT within CAP*jointRadius of the child's pivot are copied into the child
        # (child draws above -> identical opaque px at rest), and opaque px of the CHILD within CAPP*jointRadius go into the parent
        # (parent draws below the child -> hidden at rest).  Only alpha-255 px, so the rest composite does not change.
        capn={}
        if S==NS and (CAP>0 or CAPP>0):
            Y,X=np.mgrid[:H,:W]
            for pid in ids:
                if pid=='palm': continue
                f,n=pid[:-1],pid[-1];par='palm' if n=='1' else f'{f}{int(n)-1}';pv=V(piv[pid]);r=JR[n]*s/1.0
                d=np.hypot(X+.5-pv[0],Y+.5-pv[1])
                if CAP>0:
                    mk=(labv==par)&(hv[...,3]==255)&(d<=CAP*r);PI[pid][mk]=hv[mk];capn[pid]=int(mk.sum())
                if CAPP>0:
                    mk=(labv==pid)&(hv[...,3]==255)&(d<=CAPP*r);PI[par][mk]=hv[mk];capn[par+'<'+pid]=int(mk.sum())
        FIRST={}
        for i,pid in enumerate(ids):
            p=PI[pid];fn=f'{S}_{pid}.png';Image.fromarray(p).save(f'{od}/{fn}')
            e=dict(id=f'{S}_{pid}',file=fn,x=0,y=0)
            if pid=='palm':
                e.update(pivotX=V(piv['palm'])[0],pivotY=V(piv['palm'])[1],parent=None,parentExternal=f'forearm_{S}',layer=(300 if S=='R' else 320),maxCurlDeg=0,
                         note=('wrist-cut pivot (diag_check red line); hand draws UNDER the forearm' if S==NS else 'far-side foreshortened hand: whole-hand sprite, palm pivot only; draws UNDER the forearm'))
            else:
                f,n=pid[:-1],pid[-1];pv=V(piv[pid]);par=f'{S}_palm' if n=='1' else f'{S}_{f}{int(n)-1}'
                # curl sign: fingers fold toward the thumb (palm) side, thumb folds across toward the fingers; canvas rotate(+) = clockwise
                a,b=np.array(piv[f+'1']),np.array(piv[f+'_tip']);d=(b-a)/np.linalg.norm(b-a);tgt=v*tsign*(-1 if f=='Thumb' else 1)
                cw=np.array([-d[1],d[0]]);sg=1 if cw@tgt>0 else -1;mag=CURL['thumb' if f=='Thumb' else 'finger'][int(n)-1]
                e.update(pivotX=pv[0],pivotY=pv[1],parent=par,layer=(300 if S=='R' else 320)+1+i,maxCurlDeg=sg*mag,jointRadiusPx=JR[n])
            parts.append(e)
        # checks: view rebuild = straight-alpha over of all part PNGs in layer order (as the renderer draws them)
        acc=np.zeros((H,W,4))
        for pid in ids:
            a=PI[pid].astype(float)/255;al=a[...,3:4];oa=al+acc[...,3:4]*(1-al);acc=np.concatenate([np.where(oa>0,(a[...,:3]*al+acc[...,:3]*acc[...,3:4]*(1-al))/np.maximum(oa,1e-9),0),oa],-1)
        rebv=np.round(acc*255).astype(np.uint8)
        d0=int((np.abs(reb.astype(int)-hand.astype(int)).max(-1)>0).sum());d1=int((np.abs(rebv.astype(int)-hv.astype(int)).max(-1)>0).sum())
        raw=z['orig'];chg=int(((np.abs(hand[...,:3].astype(int)-raw.astype(int)).max(-1)>0)&m).sum())
        A=hv[...,3];partial=int(((A>0)&(A<255)).sum());op=A>=128;edge=int((op&~nd.binary_erosion(op)).sum())
        rec[S]=dict(kind='near' if S==NS else 'far',parts=len(ids),frame_rebuild_px=d0,view_rebuild_px=d1,blue_frame=int((blue(hand)&m).sum()),blue_view=int((blue(hv)&(A>0)).sum()),
                    her_px_changed_by_rematte=chg,frame_px=int(m.sum()),view_px=int((A>0).sum()),edge_soft_band_px=round(partial/max(edge,1),2),scale=s,
                    lineless_outline=round(1-DC[key]['outline_cov'],3),caps=capn,pivots_view={k:V(p) for k,p in piv.items()})
        print(ang,S,{k:v for k,v in rec[S].items() if k!='pivots_view'})
    rig=dict(contract='v1',owner='Base Hands',view=f'diag{ang}',staged=True,source=f"reference/apose_turn/frames/{DC[f'{ang}_R']['frame']}.png",canvas=[W,H],
             coordinateSpace='view pixels (view_fit of diagonals.json: base = scale*frame + (dx,dy)), every part PNG full-canvas',
             curlSign='maxCurlDeg signed, canvas rotate() convention (+ = clockwise, y down); no frames: the curl is an in-plane fold carried by rotation only',
             drawOrder='both hands draw UNDER Base Body\'s diagonal forearms, which end on the diag_check wrist cut',parts=parts)
    json.dump(rig,open(f'{od}/rig.json','w'),indent=1);log[ang]=rec
json.dump(log,open(f'{OUT}/build_log.json','w'),indent=1)
