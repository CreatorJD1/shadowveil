# F12 diagonal wrist flaps (frame scale) + gap/hole check.  f12.py <out root> <RAD> <LW> [ERO]
import sys,json,os,glob,numpy as np
sys.path.insert(0,'/workspace/shadowveil/body_tools/work/diag_body/tools')
from common import frame,fg_mask,ANG,ROOT
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize
from collections import Counter
OUT,RAD,LW=sys.argv[1],float(sys.argv[2]),int(sys.argv[3]);os.makedirs(OUT,exist_ok=True)
K8=np.ones((3,3),bool)
BENDS={'bend+1':25,'bend-1':-25,'anger+0.14':3.5,'jump-0.2':-5,'jump+0.2969':7.42,'run-0.12':-3,'run+0.12':3}
def key(c): c=c.astype(int);return c[...,2]-np.maximum(c[...,0],c[...,1])>25
def over(d,s):
    a=s[...,3:4];oa=a+d[...,3:4]*(1-a);return np.concatenate([np.where(oa>0,(s[...,:3]*a+d[...,:3]*d[...,3:4]*(1-a))/np.maximum(oa,1e-9),0),oa],-1)
def rot(im,deg,c):
    if deg==0: return im
    t=np.radians(deg);yy,xx=np.mgrid[:im.shape[0],:im.shape[1]].astype(float);x=xx+.5-c[0];y=yy+.5-c[1]
    sx=np.cos(t)*x+np.sin(t)*y+c[0]-.5;sy=-np.sin(t)*x+np.cos(t)*y+c[1]-.5
    pm=np.concatenate([im[...,:3]*im[...,3:4],im[...,3:4]],-1);o=np.stack([nd.map_coordinates(pm[...,k],[sy,sx],order=1,mode='constant') for k in range(4)],-1)
    return np.concatenate([np.where(o[...,3:4]>0,o[...,:3]/np.maximum(o[...,3:4],1e-9),0),o[...,3:4]],-1)
def disk(r): y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def lw_mean(c):
    op=c[...,3]>=.5;lum=(c[...,:3]*255)@[.299,.587,.114];L=op&(lum<95);sk=skeletonize(L);w=2*nd.distance_transform_edt(L)[sk];return float(w.mean()) if len(w) else None
res={'bends_deg':BENDS,'radius':RAD,'line_px':LW}
for ang in ['045','315']:
    a8=ANG[ang]['hands'];F=frame(ang);fg,_=fg_mask(F);WC=json.load(open(f'{ROOT}/body_tools/work/diag_body/{ang}/wrist_cuts.json'))
    fs=f'{ROOT}/hands/staged/f8_diagonals/{a8}/frame_scale';rig=json.load(open(f'{ROOT}/hands/staged/f8_diagonals/{a8}/rig.json'))
    HS={};Hm={}
    for S in 'LR':
        ps=sorted([p for p in rig['parts'] if p['id'].startswith(S+'_')],key=lambda p:p['layer']);c=None
        for p in ps:
            im=np.array(Image.open(f"{fs}/{S}_{p['id'][2:]}.png").convert('RGBA')).astype(float)/255;c=im if c is None else over(c,im)
        HS[S]=c;Hm[S]=c[...,3]>0
    Hall=Hm['L']|Hm['R'];body=np.zeros(F.shape[:2]+(4,));body[...,:3]=F/255.;body[...,3]=(fg&~Hall)
    def scene(S,deg,flap=None):
        out=np.zeros_like(body)
        for T in 'LR':
            h=HS[T] if (T!=S or flap is None) else over(flap,HS[T])
            out=over(out,rot(h,deg if T==S else 0,piv[T]))
        return over(out,body)
    piv={S:tuple(WC['wrists'][S]['f8_palm_pivot_frame']) for S in 'LR'}
    os.makedirs(f'{OUT}/{a8}',exist_ok=True)
    for S in 'LR':
        W=WC['wrists'][S];(x0,y0),(x1,y1)=W['boundary_line_fit'];px,py=piv[S];yy,xx=np.mgrid[:1168,:768]
        t=np.array([x1-x0,y1-y0]);t/=np.linalg.norm(t);n=np.array([-t[1],t[0]]);d=(xx+.5-x0)*n[0]+(yy+.5-y0)*n[1]
        if d[Hm[S]&(np.hypot(xx-px,yy-py)<15)].mean()>0: d=-d   # d>0 = forearm side
        near=np.hypot(xx+.5-px,yy+.5-py)<=30
        arm=fg&~Hall&(d>0)&near
        # her palette for this side: frame px of her hand_S and forearm_S near the wrist, non-key
        zone=(Hm[S]|arm)&near&fg&~key(F);cols=F[zone];lum=cols@[.299,.587,.114]
        pal=set(map(tuple,F[(Hm[S]|(fg&~Hall&(d>0)))&fg&~key(F)&(np.hypot(xx-px,yy-py)<60)].tolist()))
        SKIN=Counter(map(tuple,cols[lum>110].tolist())).most_common(1)[0][0];LINE=Counter(map(tuple,cols[lum<60].tolist())).most_common(1)[0][0]
        flap=(d>0)&(np.hypot(xx+.5-px,yy+.5-py)<=RAD)&(fg&~Hall)&~Hm[S]
        lab,_=nd.label(flap|Hm[S],structure=K8);keep=np.unique(lab[Hm[S]]);flap&=np.isin(lab,keep[keep>0])
        outside=~(flap|Hm[S]|(fg&~Hall));ln=flap&nd.binary_dilation(outside,structure=K8,iterations=LW)
        fl=np.zeros(F.shape[:2]+(4,),np.uint8);fl[flap,:3]=SKIN;fl[ln,:3]=LINE;fl[flap,3]=255
        Image.fromarray(fl).save(f'{OUT}/{a8}/{S}_wristflap.png');flf=fl.astype(float)/255
        cols_used=set(map(tuple,fl[flap][:,:3].tolist()))
        r=dict(skin=list(SKIN),line=list(LINE),flap_px=int(flap.sum()),line_px=int(ln.sum()),off_palette=int(sum(c not in pal for c in cols_used)),chroma=int(key(fl[flap][:,:3]).sum()),
               flap_px_not_under_opaque_forearm=int((flap&~(fg&~Hall)).sum()))
        # line width of her forearm outline near the wrist (rest) for reference
        r0=scene(S,0);r0f=scene(S,0,flf);r['rest_px_change_with_flap']=int((np.round(r0*255)!=np.round(r0f*255)).any(-1).sum())
        Fr=np.concatenate([F/255.,fg[...,None].astype(float)],-1);r['rest_composite_vs_her_frame_px']=int(((np.round(r0*255).astype(int)!=np.round(Fr*255).astype(int)).any(-1)&fg).sum())
        tt=(xx+.5-x0)*t[0]+(yy+.5-y0)*t[1];tl=np.hypot(x1-x0,y1-y0)
        zoneW=(np.abs(d)<=6)&(tt>=2)&(tt<=tl-2)     # wrist interior: 6 px either side of Body's boundary line, inside the cut by 2 px
        zoneE=(np.abs(d)<=6)&(((tt>=-3)&(tt<2))|((tt>tl-2)&(tt<=tl+3)))   # the two outline ends of the seam
        def gap(c,c0):
            op=c[...,3]>=.5;lb,nn=nd.label(~op);brd=set(np.unique(np.concatenate([lb[0],lb[-1],lb[:,0],lb[:,-1]])));enc=np.isin(lb,[k for k in range(1,nn+1) if k not in brd])
            g=(nd.binary_closing(op,structure=disk(5),border_value=0)&~op)|enc
            op0=c0[...,3]>=.5;g0=(nd.binary_closing(op0,structure=disk(5),border_value=0)&~op0)
            return int((g&zoneW&~g0).sum()),int((enc&(zoneW|zoneE)).sum()),int((g&zoneE&~g0).sum())
        def breaks(c):
            op=c[...,3]>=.5;lum=(c[...,:3]*255)@[.299,.587,.114];L=op&(lum<95);edge=op&~nd.binary_erosion(op,border_value=1)
            unc=edge&~nd.binary_dilation(L,structure=K8)&nd.binary_dilation(zoneW|zoneE,iterations=3);lb,_=nd.label(unc,structure=K8);sz=np.bincount(lb.ravel())
            return int(np.isin(lb,np.nonzero(sz>=2)[0][1:]).sum()) if len(sz)>1 else 0
        w0=lw_mean(r0[int(py)-30:int(py)+30,int(px)-30:int(px)+30])
        r['rest_line_width']=round(w0,3);r['rest_breaks']=breaks(r0)
        for k,deg in BENDS.items():
            c=scene(S,deg);cf=scene(S,deg,flf)
            g,h,e=gap(c,r0);gf,hf,ef=gap(cf,r0)
            wn=lw_mean(c[int(py)-30:int(py)+30,int(px)-30:int(px)+30]);wf=lw_mean(cf[int(py)-30:int(py)+30,int(px)-30:int(px)+30])
            r[k]=dict(deg=deg,gap_no_flap=g,holes_no_flap=h,gap_flap=gf,holes_flap=hf,end_notch_no_flap=e,end_notch_flap=ef,breaks_no_flap=breaks(c),breaks_flap=breaks(cf),dw_no_flap=round(wn-w0,3),dw_flap=round(wf-w0,3))
            if k in('bend+1','bend-1'):
                for nm,im in (('noflap',c),('flap',cf)): Image.fromarray(np.round(im[int(py)-40:int(py)+40,int(px)-40:int(px)+40]*255).astype(np.uint8)).save(f'{OUT}/{a8}/crop_{S}_{k}_{nm}.png')
        res[f'{a8}_{S}']=r;print(a8,S,json.dumps(r),flush=True)
json.dump(res,open(f'{OUT}/check.json','w'),indent=1)
