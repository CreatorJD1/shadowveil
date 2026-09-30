import json, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from seg import segment_hand, load, SRC, lum
from defs import D
KEY_COLOR=(0,0,255)          # the one chroma-key constant (#0000FF)
ROOT='/workspace/shadowveil'
WORK=f'{ROOT}/hands'
W,Hh=1365,1739
CHAIN={'thumb':'Thumb','index':'Index','middle':'Middle','ring':'Ring','pinky':'Pinky'}
SEG2N={'metacarpal':1,'proximal':1,'middle':2,'distal':3}
def pname(side,lab):
    if lab=='palm': return f'{side}_palm'
    f,s=lab.split('_'); n=SEG2N[s]
    if f=='thumb': n={'metacarpal':1,'proximal':2,'distal':3}[s]
    return f'{side}_{CHAIN[f]}{n}'
ORDER=['palm']+[f'{c}{i}' for c in ['Pinky','Ring','Middle','Index','Thumb'] for i in (1,2,3)]

def hand_colors(sub,mask):
    rgb=sub[...,:3]; L=lum(rgb); op=sub[...,3]==255
    sk=rgb[mask&op&(L>112)&(L<145)]; ln=rgb[mask&op&(L<45)]
    return np.median(sk,0), np.median(ln,0)

LW=1.0
def paint(F,C,S,Lc,LW=1.0):
    """flat skin on F, outline (line colour) on F pixels within ~1.6px of anything outside C."""
    out=np.zeros(F.shape+(4,),np.float32)
    dt=ndi.distance_transform_edt(np.pad(C,3,constant_values=False))[3:-3,3:-3]
    out[F,:3]=S; out[F,3]=255
    e=F&(dt<=LW); out[e,:3]=Lc
    e2=F&(dt>LW)&(dt<=LW+0.8); out[e2,:3]=0.5*S+0.5*Lc
    return out

def build_hand(v,side,H):
    R=segment_hand(v,H)
    x0,y0,x1,y1=H['box']; a=load(v); sub=a[y0:y1,x0:x1]
    mask=R['mask']; labels=R['labels']; op=(sub[...,3]==255)&mask
    S,Lc=hand_colors(sub,mask)
    parts={}  # name -> dict(img, vis mask)
    for lab in set(labels[mask]):
        n=pname(side,lab); m=(labels==lab)
        img=np.zeros(sub.shape,np.float32); img[m]=sub[m]
        parts[n]=dict(img=img,vis=m.copy(),lab=lab)
    chains={f:[np.array(p,float)-np.array([x0,y0]) for p in ch] for f,ch in R['chains'].items()}
    yy,xx=np.mgrid[0:mask.shape[0],0:mask.shape[1]]
    info={}
    def region(f): 
        return np.isin(labels,[l for l in set(labels[mask]) if l.startswith(f+'_')])
    for f,ch in chains.items():
        C=CHAIN[f]; fr=region(f)
        piv=[]
        for j in range(3):
            if j==0: d=ch[1]-ch[0]
            else:
                d1=ch[j]-ch[j-1]; d2=ch[j+1]-ch[j]; d=d1/np.linalg.norm(d1)+d2/np.linalg.norm(d2)
            d=d/np.linalg.norm(d); nrm=np.array([-d[1],d[0]])
            p=ch[j]+d*1.5; ts=[]
            for sgn in (1,-1):
                t=0
                while t<25:
                    q=p+sgn*nrm*(t+0.5); qi=(int(round(q[1])),int(round(q[0])))
                    if not(0<=qi[0]<fr.shape[0] and 0<=qi[1]<fr.shape[1]) or not fr[qi]: break
                    t+=0.5
                ts.append(t)
            r=(ts[0]+ts[1])/2; shift=(ts[0]-ts[1])/2
            c=ch[j]+nrm*shift if abs(shift)<3 else ch[j]
            piv.append((c,max(r,1.5),d))
        if f=='thumb':
            # move Thumb1 pivot to where the CMC cut meets the outer contour, so the base corner never swings out (wrist notch)
            c,r,d=piv[0]; nrm=np.array([-d[1],d[0]])
            pm=parts[f'{side}_palm']['vis']; pc=np.array([xx[pm].mean(),yy[pm].mean()])
            if (pc-c)@nrm>0: nrm=-nrm
            t=0.0
            while t<40:
                q=c+nrm*(t+0.5); qi=(int(round(q[1])),int(round(q[0])))
                if not(0<=qi[0]<mask.shape[0] and 0<=qi[1]<mask.shape[1]) or not op[qi]: break
                t+=0.5
            piv[0]=(c+nrm*max(t-2.0,0),r,d)
        info[f]=piv
        # hidden fills: parent end caps at joints 1,2 ; palm cap at joint 0
        for j in range(3):
            c,r,d=piv[j]
            child=f'{side}_{C}{j+1}'
            parent=f'{side}_palm' if j==0 else f'{side}_{C}{j}'
            if child not in parts or parent not in parts: continue
            cm=parts[child]['vis']&op
            rr=r+0.75 if j else r*1.15+0.75
            disk=((xx-c[0])**2+(yy-c[1])**2)<=rr**2
            if f=='thumb' and j==0:
                F=cm                            # palm gets the whole thumb-base area as clean fill
            else:
                F=disk&cm
            Cn=(parts[parent]['vis']|F) if not (f=='thumb' and j==0) else mask
            pt=paint(F,Cn,S,Lc,LW=2.2 if (f=='thumb' and j==0) else 1.0)
            img=parts[parent]['img']; img[F]=pt[F]
    return dict(R=R,parts=parts,info=info,S=S,Lc=Lc,box=H['box'],op=op,mask=mask,labels=labels,sub=sub,chains=chains)

def tpose_extras(B,side):
    """T-pose: hand seen edge-on; index in front, middle is the sliver above; ring & pinky fully behind.
    Give Middle a hidden extension under Index, and Ring/Pinky hidden stacked copies under both."""
    parts=B['parts']; op=B['op']; S,Lc=B['S'],B['Lc']
    band={k:(parts[f'{side}_Index{k}']['vis']|parts[f'{side}_Middle{k}']['vis'])&op for k in (1,2,3)}
    allband=band[1]|band[2]|band[3]|parts[f'{side}_palm']['vis']
    # middle extension
    ext={k:parts[f'{side}_Index{k}']['vis']&op for k in (1,2,3)}
    for k in (1,2,3):
        F=ext[k]; pt=paint(F,allband,S,Lc); parts[f'{side}_Middle{k}']['img'][F]=pt[F]
    # ring/pinky: same band, shortened at the tip
    ch=B['chains']['index']; tip=ch[3]; d=(ch[3]-ch[0]); d/=np.linalg.norm(d)
    yy,xx=np.mgrid[0:op.shape[0],0:op.shape[1]]; ax=(xx-tip[0])*d[0]+(yy-tip[1])*d[1]
    for name,short in (('Ring',4),('Pinky',10)):
        keep=ax<-short
        Fs={k:band[k]&keep for k in (1,2,3)}
        Call=Fs[1]|Fs[2]|Fs[3]|parts[f'{side}_palm']['vis']
        for k in (1,2,3):
            img=np.zeros(B['sub'].shape,np.float32); pt=paint(Fs[k],Call,S,Lc); img[Fs[k]]=pt[Fs[k]]
            parts[f'{side}_{name}{k}']=dict(img=img,vis=np.zeros_like(op),lab=f'{name.lower()}_{k}',hidden=True)
        # pivots same as index chain
        B['info'][name.lower()]=B['info']['index']
    return B
