from seg import *
import os
OUT='/workspace/shadowveil/views/{}/hair'; EM='/workspace/shadowveil/hair/{}_hair_erase_mask.png'
BUN_FRONT={'apose':False,'tpose':False,'left':True,'right':True,'back':True}
ST={'apose':{'deg':10},'tpose':{'deg':10},'left':{'deg':10},'right':{'deg':10},'back':{'deg':10}}
def comp(mask,st=np.ones((3,3))): return ndi.label(mask,structure=st)
def FORB(v):
    import glob
    f_=np.zeros((1739,1365),bool)
    for f in glob.glob(f'/workspace/shadowveil/views/{v}/eyes/Eye*_*.png')+glob.glob(f'/workspace/shadowveil/views/{v}/mouth/*.png'):
        if 'chroma' in f: continue
        import time
        for t in range(10):
            try: f_|=np.array(Image.open(f).convert('RGBA'))[...,3]>0; break
            except Exception: time.sleep(2)
        else: raise RuntimeError('unreadable '+f)
    return ndi.binary_dilation(f_,iterations=2)
def build(v):
    M=masks(v); im=M['im']; a=M['a']; H,W=a.shape
    r,g,b=im[...,0],im[...,1],im[...,2]
    lum=(r*299+g*587+b*114)//1000; sat=im[...,:3].max(-1)-im[...,:3].min(-1)
    skin=(a>200)&(sat>=45)&(lum>=80)&~M['hair']
    nearskin=dilation(skin,disk(1))
    hair,thick,thin=M['hair'],M['thick'],M['thin']
    bun=thick&M['bunreg']
    # keep only the main connected bun blob(s) touching the ellipse centre area
    cap=thick&~bun
    # strand grouping
    g_,k=ndi.label(dilation(thin,disk(4)))
    groups=[]
    for i in range(1,k+1):
        m=thin&(g_==i)
        if m.sum()>=1: groups.append(m)
    cx,cy,ax,ay=CFG[v]['bun']
    bunwide=dilation(M['bunreg'],disk(10))
    bunadd=np.zeros_like(bun); strands=[]; small=[]
    for m in groups:
        ys,xs=np.where(m)
        # bun wisps: mostly inside the widened bun ellipse
        if (m&bunwide).sum()>0.6*m.sum() and ys.mean()<cy+ay: bunadd|=m; continue
        if m.sum()<60: small.append(m); continue
        strands.append(m)
    # tiny fragments: join the nearest strand within 6px, else stay fixed in base
    for m in small:
        d=dilation(m,disk(6)); hit=[j for j,s in enumerate(strands) if (s&d).any()]
        if hit: strands[hit[0]]|=m
    bun=bun|bunadd
    # ---- v2: fold leftover hair fragments, then 3px dilation of every swaying part ----
    ycut=CFG[v]['ycut']
    pskin=(a>200)&(lum>=60)&(sat>=35)&(r>g)&(g>b)        # broad skin (classifies lineart)
    sskin=(a>0)&(lum>=100)&(sat>=40)&(r>g)&(g>b)         # clear skin (dilation never enters)
    ns=dilation(pskin,disk(2))
    forb=FORB(v)
    parts=cap|bun|np.any(strands,0)
    grey=(a>0)&(sat<30)&(lum<215)&~sskin
    L=(hair|grey)&~parts&~M['face']&~forb; L[ycut:]=False
    lab,k=ndi.label(L,structure=np.ones((3,3)))
    fr=ndi.mean(ns,lab,range(1,k+1)); com=ndi.center_of_mass(L,lab,range(1,k+1))
    dpart=ndi.distance_transform_edt(~parts)
    sets=[('bun',bun)]+[('s%d'%j,s) for j,s in enumerate(strands)]+[('cap',cap)]
    dists=[ndi.distance_transform_edt(~m) for _,m in sets]
    protect=np.zeros_like(hair); folded={}
    for i in range(k):
        m=lab==i+1; cy_,cx_=com[i]
        inc=any(x0<=cx_<x1 and y0<=cy_<y1 for x0,x1,y0,y1 in CFG[v].get('incl',[]))
        if not inc and (fr[i]>=0.5 or dpart[m].min()>10): protect|=m; continue
        dd=[d[m].min() for d in dists]; j=int(np.argmin(dd))
        nm,_=sets[j]; folded[nm]=folded.get(nm,0)+int(m.sum())
        if nm=='bun': bun=bun|m
        elif nm=='cap': cap=cap|m
        else: strands[int(nm[1:])]=strands[int(nm[1:])]|m
    allow=~sskin&~M['face']&~protect&~forb&~cap&(a>0)
    allow[ycut+40:]=False
    sw=[bun]+strands
    for _ in range(3):
        taken=cap|np.any(sw,0)
        new=[]
        for m in sw:
            g1=dilation(m,disk(1))&allow&~taken
            new.append(m|g1); taken|=g1
        sw=new
    bun,strands=sw[0],sw[1:]
    M['protect']=protect; M['folded']=folded; M['sskin']=sskin
    # order strands left->right, then top
    strands.sort(key=lambda s:(np.where(s)[1].mean()))
    M['cap2']=cap
    return M,cap,bun,strands,skin
def despill(im,part,hairmask):
    r,g,b=im[...,0],im[...,1],im[...,2]
    fr=part&(b>r+25)&(b>g+25)
    out=im.copy(); good=hairmask&~((b>r+25)&(b>g+25))
    ys,xs=np.where(fr)
    med=np.median(im[good][:,:3],axis=0)
    for y,x in zip(ys,xs):
        for rad in (1,2,3,5,8):
            y0,y1,x0,x1=max(0,y-rad),y+rad+1,max(0,x-rad),x+rad+1
            nb=good[y0:y1,x0:x1]
            if nb.sum()>=2: c=np.median(im[y0:y1,x0:x1][nb][:,:3],axis=0); break
        else: c=med
        c=np.clip(c,0,255); c[2]=min(c[2],max(c[0],c[1])+20)
        out[y,x,:3]=c
    return out,fr
def pivot_root(m,thick):
    att=m&dilation(thick,disk(3))
    if att.any():
        l,k=ndi.label(att,structure=np.ones((3,3)))
        # topmost attachment component = root
        best=min(range(1,k+1),key=lambda i:np.where(l==i)[0].min())
        ys,xs=np.where(l==best); return float(round(xs.mean(),1)),float(round(ys.mean(),1))
    dt,ind=ndi.distance_transform_edt(~thick,return_indices=True)
    ys,xs=np.where(m); j=np.argmin(dt[ys,xs]); return float(xs[j]),float(ys[j])
if __name__=='__main__':
    import sys
    allmeta={}
    for v in (sys.argv[1:] or VIEWS):
        M,cap,bun,strands,skin=build(v); im=M['im'].copy(); a=M['a']; H,W=a.shape
        import glob
        forb=np.zeros((H,W),bool)
        for f in glob.glob(f'/workspace/shadowveil/views/{v}/eyes/Eye*_*.png')+glob.glob(f'/workspace/shadowveil/views/{v}/mouth/*.png'):
            if 'chroma' not in f: forb|=np.array(Image.open(f).convert('RGBA'))[...,3]>0
        forb=ndi.binary_dilation(forb,iterations=2)
        nf=int(((cap|bun|np.any(strands,0))&forb).sum())
        forb2=ndi.binary_dilation(forb,iterations=3)  # extra sway margin for moving parts
        cap=cap&~forb; bun=bun&~forb2; strands=[s&~forb2 for s in strands]; strands=[s for s in strands if s.sum()>=30]
        if nf: print(v,'hair px removed from parts (inside eye/mouth parts +2px):',nf)
        od=OUT.format(v); os.makedirs(od,exist_ok=True)
        for f in os.listdir(od):
            if f.endswith('.png') or f=='rig.json': os.remove(os.path.join(od,f))
        # chroma-blue fringe (b>r+40 & b>g+40) can't go into a part (no-chroma rule) and can't be despilled
        # without breaking rest identity -> leave those pixels to base_body (not erased, not in any part)
        rr,gg,bb_=im[...,0],im[...,1],im[...,2]
        strict=(a>0)&(bb_>rr+40)&(bb_>gg+40)
        nstrict={'bun':int((bun&strict).sum()),'strands':int((np.any(strands,0)&strict).sum()),'cap':int((cap&strict).sum())}
        bun=bun&~strict; strands=[s&~strict for s in strands]; cap=cap&~strict
        print(v,'chroma-blue px left in base_body (excluded from parts):',nstrict)
        # Base Body skin-fills cleared pixels whose 25px neighbourhood is mostly skin; a soft-alpha part pixel there
        # would be stacked over opaque skin -> drop such pixels from the parts (they stay in base_body)
        sw0=bun|np.any(strands,0)
        hm_=np.array(Image.open(f'/workspace/shadowveil/hands/{v}_hand_erase_mask.png'))
        hm_=(hm_[...,-1] if hm_.ndim==3 else hm_)>127
        for _it in range(2):
            allm=hm_|(sw0&(a>0))
            bskin=~allm&(im[...,3]==255)&(im[...,0]>140)&(im[...,2]<120)&(im[...,0]-im[...,2]>60)
            op=ndi.uniform_filter((~allm).astype(float),25); sk=ndi.uniform_filter(bskin.astype(float),25)
            bfill=np.where(op>0,sk/np.maximum(op,1e-6),0)>0.5
            drop=sw0&(a>0)&(a<255)&bfill
            if not drop.any(): break
            print(v,'soft px dropped (Body skin-fills under them):',int(drop.sum()))
            bun=bun&~drop; strands=[s&~drop for s in strands]; sw0=sw0&~drop
        swaying=bun.copy()
        for s in strands: swaying|=s
        allhair=cap|swaying
        des=im.copy(); fr=np.zeros_like(allhair)  # no despill: parts are exact base.png copies
        medc=np.median(im[cap&(a==255)&~fr][:,:3],axis=0).astype(int)
        # hair_back: opaque cap pixels + median-colour fill under bun footprint and strand roots, only where base is opaque
        capfill=ndi.binary_fill_holes(dilation(cap,disk(2)))
        headarea=capfill|ndi.binary_fill_holes(bun|cap)
        fill=(bun|(dilation(swaying,disk(4))&capfill))&headarea&(a==255)&~forb
        def save(name,mask,src=des,const=None):
            o=np.zeros((H,W,4),np.uint8)
            if const is not None: o[mask,:3]=const; o[mask,3]=255
            else: o[mask]=src[mask].astype(np.uint8)
            Image.fromarray(o).save(f'{od}/{name}'); return o
        hb=np.zeros((H,W,4),np.uint8); hb[fill,:3]=medc; hb[fill,3]=255
        capop=cap&(a==255); hb[capop]=des[capop].astype(np.uint8)
        Image.fromarray(hb).save(f'{od}/hair_back.png')
        hfm=capop if v!='back' else np.zeros_like(cap)
        save('hair_front.png',hfm)
        save('bun.png',bun)
        rig=[dict(id='hair_back',file='hair_back.png',x=0,y=0,pivotX=0,pivotY=0,parent=None,layer=0,swayWeight=0,maxSwayDeg=0)]
        ys,xs=np.where(cap); cpx,cpy=float(round(xs.mean(),1)),float(round(ys.mean(),1))
        rig[0]['pivotX'],rig[0]['pivotY']=cpx,cpy
        rig.append(dict(id='hair_front',file='hair_front.png',x=0,y=0,pivotX=cpx,pivotY=cpy,parent=None,layer=900,swayWeight=0,maxSwayDeg=0))
        # bun pivot at its base: where bun meets cap
        base=bun&dilation(cap,disk(2))
        by,bx=np.where(base)
        # use the lowest part of the contact (bun base)
        sel=by>=np.percentile(by,50)
        bpx,bpy=float(round(bx[sel].mean(),1)),float(round(by[sel].mean(),1))
        rig.append(dict(id='bun',file='bun.png',x=0,y=0,pivotX=bpx,pivotY=bpy,parent='hair_front' if v!='back' else 'hair_back',layer=950 if BUN_FRONT[v] else 1,swayWeight=0.3,maxSwayDeg=4.0))
        for j,s in enumerate(strands):
            n=f'strand_{j+1:02d}'; save(n+'.png',s)
            px,py=pivot_root(s,cap|bun)
            par='bun' if (s&dilation(bun,disk(4))).any() and not (s&dilation(cap,disk(4))).any() else 'hair_front' if v!='back' else 'hair_back'
            rig.append(dict(id=n,file=n+'.png',x=0,y=0,pivotX=px,pivotY=py,parent=par,layer=901+j,swayWeight=1.0,maxSwayDeg=float(ST[v]['deg'])))
        json.dump(rig,open(f'{od}/rig.json','w'),indent=1)
        em=np.where(swaying&(a>0),255,0).astype(np.uint8)
        os.makedirs('/workspace/shadowveil/hair',exist_ok=True)
        Image.fromarray(em,'L').save(EM.format(v))
        np.save(f'meta_{v}.npy',dict(protect=M['protect'],fr=fr,allhair=allhair,cap=cap,bun=bun,strands=strands,fill=fill,face=M['face']),allow_pickle=True)
        print(v,'folded',M['folded'],'strands',len(strands),'bun px',int(bun.sum()),'cap px',int(cap.sum()),'despilled',int(fr.sum()),'fill',int(fill.sum()),'median',medc)
