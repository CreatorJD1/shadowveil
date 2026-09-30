import json, os, sys, numpy as np
from PIL import Image
from build import *
VIEWS=['apose','tpose','left','right','back']
# per-joint curl magnitudes (deg) at curl=1. Palm-side views fold the finger back over the palm (tips tucked in);
# back-of-hand views fold mid+tip back onto the proximal segment (fingers read as tucked under); tpose is a true side-view fist.
CURL={'apose':(165,165,150),'tpose':(90,100,70),'left':(15,170,170),'right':(15,170,170),'back':(15,170,170)}
THUMBCURL={'apose':(5,60,25),'tpose':(5,20,25),'left':(5,35,30),'right':(5,35,30),'back':(5,35,30)}
def sim_tip(pts,angs,sgn):
    # pts: joints j0,j1,j2,tip (canvas); rotate chain with cumulative angles, return all points
    P=[np.array(p,float) for p in pts]; out=[P[0]]; cum=0; cur=P[0]
    for k in range(3):
        cum+=sgn*angs[k]; t=np.deg2rad(cum); R=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]])
        cur=cur+R@(P[k+1]-P[k]); out.append(cur)
    return out
def pick_sign(pts,angs,target):
    best=None
    for s in (1,-1):
        Q=sim_tip(pts,angs,s); score=np.linalg.norm(Q[-1]-target)+0.5*np.mean([np.linalg.norm(q-target) for q in Q[1:]])
        if best is None or score<best[0]: best=(score,s)
    return best[1]
SPREADDEG={'Index':12,'Ring':8,'Pinky':16}
LAYERBASE={'front':300,'far':100}   # contract v1.2 hand band 300-399: R 300-315, L 320-335; far profile hand kept hidden   # body/base.png assumed between (e.g. 200)

def rot_sign(d,t):
    # canvas rotate(+θ) moves a point at direction d by (-d_y, d_x)
    return 1 if (-d[1]*t[0]+d[0]*t[1])>=0 else -1

def full(img,box):
    x0,y0,x1,y1=box; F=np.zeros((Hh,W,4),np.uint8); F[y0:y1,x0:x1]=np.clip(np.round(img),0,255).astype(np.uint8); return F

def keyed_from_chroma(chroma, ref):
    """Keyer used for verification: recover alpha of a pixel composited over KEY_COLOR.
    p = a*c + (1-a)*K ; exact recovery needs the fg colour, so we verify against ref instead."""
    K=np.array(KEY_COLOR,float)
    return None

def main():
    allrig={}
    stats={}
    for v in VIEWS:
        a=load(v).astype(np.uint8)
        outdir=f'{ROOT}/views/{v}/hands'; os.makedirs(outdir,exist_ok=True)
        chdir=f'{WORK}/chroma/{v}'; os.makedirs(chdir,exist_ok=True)
        rig=dict(contract='v1',owner='Base Hands',view=v,canvas=[W,Hh],keyColor='#0000FF',
                 coordinateSpace='view pixels, origin top-left; every part PNG is full-canvas (x=y=0)',
                 curlSign='maxCurlDeg is signed: canvas rotate() convention, + = clockwise on screen (y down)',
                 parts=[],spread={},hands={})
        sides=list(D[v])
        allsides=['L','R']
        for side in allsides:
            if side not in D[v]:
                # far hand in a profile: fully occluded behind the body
                lb=LAYERBASE['far']+(0 if side=='R' else 20)
                for i,pn in enumerate(ORDER):
                    par=None
                    if pn!='palm':
                        k=int(pn[-1]); par=f'{side}_palm' if k==1 else f'{side}_{pn[:-1]}{k-1}'
                    rig['parts'].append(dict(id=f'{side}_{pn}',file=None,**({'parentExternal':f'forearm_{side}'} if pn=='palm' else {}),x=0,y=0,pivotX=None,pivotY=None,parent=par,
                        layer=210+(0 if pn=='palm' else 1+['Pinky','Ring','Middle','Index','Thumb'].index(pn[:-1])),maxCurlDeg=0,hidden=True,
                        note='far hand, fully occluded by the body in this profile; nothing drawn'))
                rig['hands'][side]=dict(visible=False,layerGroup='behind body')
                continue
            H=D[v][side]; B=build_hand(v,side,H)
            if v=='tpose': B=tpose_extras(B,side)
            box=B['box']; x0,y0=box[0],box[1]; info=B['info']
            wr=np.array(H['wrist'],float); palm_piv=wr.mean(0)
            lb=LAYERBASE['front']+(0 if side=='R' else 20)
            tmcp=info['thumb'][1][0]
            imcp=info['index'][0][0]
            pmv=B['parts'][f'{side}_palm']['vis']; yy_,xx_=np.nonzero(pmv); palmc=np.array([xx_.mean()+x0,yy_.mean()+y0])
            fsign={}
            for f in ['thumb','index','middle','ring','pinky']:
                pts=[info[f][k][0]+np.array([x0,y0]) for k in range(3)]+[np.array(B['chains'].get(f,B['chains']['index'])[3])+np.array([x0,y0])]
                angs=THUMBCURL[v] if f=='thumb' else CURL[v]
                if v=='tpose' and f!='thumb':
                    c_,r_,d_=info[f][0]; fsign[f]=rot_sign(d_,tmcp-c_)
                else: fsign[f]=pick_sign(pts,angs,palmc)
            for i,pn in enumerate(ORDER):
                pid=f'{side}_{pn}'; P=B['parts'].get(pid)
                ent=dict(id=pid,file=None,x=0,y=0)
                if pn=='palm':
                    ent.update(pivotX=round(float(palm_piv[0]),1),pivotY=round(float(palm_piv[1]),1),parent=None,parentExternal=f'forearm_{side}',layer=lb+i,maxCurlDeg=0,
                               note='wrist-crease pivot; palm draws above the forearm')
                else:
                    fing=pn[:-1]; k=int(pn[-1]); f=fing.lower()
                    c,r,d=info[f][k-1]
                    par=f'{side}_palm' if k==1 else f'{side}_{fing}{k-1}'
                    mag=(THUMBCURL[v] if f=='thumb' else CURL[v])[k-1]
                    sgn=fsign[f]
                    ent.update(pivotX=round(float(c[0]+x0),1),pivotY=round(float(c[1]+y0),1),parent=par,layer=lb+i,
                               maxCurlDeg=sgn*mag,jointRadiusPx=round(float(r),1))
                    if P is not None and P.get('hidden'): ent['hidden']=True
                if P is not None:
                    fn=f'{pid}.png'; ent['file']=fn
                    F=full(P['img'],box)
                    Image.fromarray(F,'RGBA').save(f'{outdir}/{fn}')
                    ch=np.zeros((Hh,W,3),np.float32); ch[:]=KEY_COLOR
                    al=F[...,3:].astype(np.float32)/255
                    ch=F[...,:3]*al+ch*(1-al)
                    Image.fromarray(np.round(ch).astype(np.uint8),'RGB').save(f'{chdir}/{fn}')
                else:
                    ent['hidden']=True; ent['note']='not visible in this view'
                rig['parts'].append(ent)
            # spread
            sp={}
            for fing in ['Index','Ring','Pinky']:
                c,r,d=info[fing.lower()][0]
                t=(tmcp-c) if fing=='Index' else (c-info['middle'][0][0])
                sp[fing]=dict(part=f'{side}_{fing}1',pivotX=round(float(c[0]+x0),1),pivotY=round(float(c[1]+y0),1),
                              maxSpreadDeg=rot_sign(d,t)*SPREADDEG[fing])
            rig['spread'][f'Hand{side}Spread']=dict(range=[0,1],default=0,fingers=sp,
                note='rotation added at the finger 1 pivot; Middle does not move')
            c,r,d=info['thumb'][0]
            sg=-rot_sign(d,imcp-c)
            rig['spread'][f'Hand{side}ThumbSpread']=dict(range=[-1,1],default=0,part=f'{side}_Thumb1',
                pivotX=round(float(c[0]+x0),1),pivotY=round(float(c[1]+y0),1),degAtPlus1=sg*20,degAtMinus1=-sg*15,
                note='+1 swings the thumb out away from the index, -1 across the palm')
            rig['hands'][side]=dict(visible=True,box=list(map(int,box)),skinRGB=[int(x) for x in B['S']],lineRGB=[int(x) for x in B['Lc']],
                layerGroup='in front of body')
            stats[(v,side)]=dict(S=B['S'].tolist(),L=B['Lc'].tolist())
        rig['spreadNote']='ThumbSpread: rotation = value*degAtPlus1 for value>=0, |value|*degAtMinus1 for value<0 (degAtMinus1 is the signed rotation at -1).'
        if v=='tpose': rig['hiddenNote']='Ring/Pinky are fully behind Index/Middle at rest (edge-on hand). Their files are clean flat stand-ins that sit entirely under opaque Index/Middle pixels, so drawing them keeps rest pixel-identical; draw them so a curled Index/Middle does not reveal empty space.'
        json.dump(rig,open(f'{outdir}/rig.json','w'),indent=1)
        allrig[v]=rig
    json.dump(allrig,open(f'{WORK}/rig_all_views.json','w'),indent=1)
    print(stats)
main()
