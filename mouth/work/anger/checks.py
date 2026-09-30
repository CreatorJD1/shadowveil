import json,sys; import numpy as np; from PIL import Image; from scipy import ndimage as ndi
ROOT='/workspace/shadowveil'
def comp(v,n):
    b=Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA'); b.alpha_composite(Image.open(f'{ROOT}/views/{v}/mouth/{n}.png').convert('RGBA')); return np.array(b).astype(float)
def runs(L,x,y0,y1,thr):
    col=L[y0:y1,x]<thr; lab,n=ndi.label(col); return [int((lab==i).sum()) for i in range(1,n+1)]
out={}
for v in ['apose','tpose']:
    R=json.load(open('build_report.json'))[v]; ax=int(round(R['transform']['dstCentre'][0])); sy=int(R['restSeamY'])
    rest=comp(v,'rest'); ang=comp(v,'anger'); k=np.array(Image.open(f'{ROOT}/views/{v}/mouth/anger.png')); ra=np.array(Image.open(f'{ROOT}/views/{v}/mouth/rest.png'))[...,3]
    base=np.array(Image.open(f'{ROOT}/views/{v}/base.png').convert('RGBA')).astype(float)
    Lr=rest[...,:3]@[.299,.587,.114]; La=ang[...,:3]@[.299,.587,.114]; Lbase=base[...,:3]@[.299,.587,.114]
    D=np.load(f'tmp/D_{v}.npy')
    skinL=np.median(Lbase[sy+20:sy+24,ax-5:ax+5])
    seamR=[max(runs(Lr,x,sy-4,sy+5,36) or [0]) for x in range(ax-20,ax+21) if abs(x-ax)>3]
    seamA=[max(runs(La,x,sy-6,sy+6,14) or [0]) for x in range(ax-20,ax+21) if abs(x-ax)>3]
    # anger outer outline: dark (<14) run at the top and bottom boundary of the anger lips
    ys,xs=np.nonzero((k[...,3]==255)&(np.abs((k[...,:3].astype(float)-base[...,:3]).sum(-1))>0)&((k[...,:3].astype(float)@[.299,.587,.114])<100))
    top=[];bot=[]
    for x in range(ax-15,ax+16):
        c=np.nonzero((La[:,x]<100)&(k[:,x,3]==255))[0]; c=c[(c>sy-20)&(c<sy+20)]
        if len(c)==0: continue
        t0,b0=c.min(),c.max(); top.append(int((La[t0:t0+4,x]<14).sum())); bot.append(int((La[b0-3:b0+1,x]<14).sum()))
    # breaks: the anger line (<14) must be one connected component along the seam across the mouth
    bb=R['restDrawnBBox']; seamline=(La<14); seamline[:sy-6]=False; seamline[sy+6:]=False; seamline[:,:bb[0]-3]=False; seamline[:,bb[2]+4:]=False; lab,n=ndi.label(seamline,structure=np.ones((3,3)))
    big=np.argmax(ndi.sum(seamline,lab,range(1,n+1)))+1; yy,xx=np.nonzero(lab==big)
    # rest line visible through? : pixels of base lips (D) not fully covered, or rest-region px under partial anger alpha that are darker than skin
    showthru=int((D&(k[...,3]<255)).sum()); partial=(ra>0)&(k[...,3]<255)&(Lbase<skinL-10)
    a=k[...,3]; vis=a>0
    lipbox=np.nonzero(a==255); aa=k[lipbox][:,:3]
    out[v]=dict(seamLineRunPx=dict(rest_median=float(np.median(seamR)),rest_range=[min(seamR),max(seamR)],anger_median=float(np.median(seamA)),anger_range=[min(seamA),max(seamA)]),
        angerOuterLine=dict(top_median=float(np.median(top)),bottom_median=float(np.median(bot))),
        angerSeamLineSpanX=[int(xx.min()),int(xx.max())],angerSeamComponents=int(n),angerSeamMainComponentPx=int((lab==big).sum()),angerSeamColumnsWithoutLine=[int(x) for x in range(bb[0]+2,bb[2]-1) if not seamline[:,x].any()],restSeamColumnsWithoutLine=[int(x) for x in range(bb[0]+2,bb[2]-1) if not (Lr[sy-4:sy+5,x]<36).any()],
        restLipPxNotFullyCovered=showthru,restRegionDarkPxUnderPartialAlpha=int(partial.sum()),
        partBBox=[int(np.nonzero(vis)[1].min()),int(np.nonzero(vis)[0].min()),int(np.nonzero(vis)[1].max()),int(np.nonzero(vis)[0].max())],
        opaquePx=int((a==255).sum()),semiPx=int(((a>0)&(a<255)).sum()),rgbAtAlpha0Max=int(k[a==0,:3].max()),
        blueSpillPx=int((vis&(k[...,2]>np.maximum(k[...,0],k[...,1]))).sum()),pureBluePx=int((vis&(k[...,0]<40)&(k[...,1]<40)&(k[...,2]>200)).sum()),
        uniqueColours=int(len(np.unique(k[vis][:,:3],axis=0))),
        lipColours=dict(anger_line_median=[int(c) for c in np.median(ang[(La<10)&(k[...,3]==255)][:,:3],0)],anger_fill_median=[int(c) for c in np.median(ang[(La>15)&(La<60)&(k[...,3]==255)&(np.abs(ang[...,2]-ang[...,0])<25)][:,:3],0)]))
    # geometry of anger lips on the face
    lm=(k[...,3]==255)&(La<100)&(np.abs(ang[...,:3]-base[...,:3]).sum(-1)>30); yl,xl=np.nonzero(lm)
    out[v]['angerLipBBox']=[int(xl.min()),int(yl.min()),int(xl.max()),int(yl.max())]
    out[v]['angerW']=int(xl.max()-xl.min()+1); out[v]['angerH']=int(yl.max()-yl.min()+1)
    out[v]['restW_H']=[R['restDrawnBBox'][2]-R['restDrawnBBox'][0]+1,R['restDrawnBBox'][3]-R['restDrawnBBox'][1]+1]
    # nostril bottom (dark px between nose and mouth, above the lips)
    reg=(Lbase<skinL-35); reg[:sy-30]=False; reg[sy-14:]=False; reg[:, :ax-12]=False; reg[:, ax+13:]=False; ny=np.nonzero(reg)[0]
    out[v]['nostrilBottomY']=int(ny.max()) if len(ny) else None
    out[v]['gapNostrilToLipTop']=dict(rest=int(R['restDrawnBBox'][1]-ny.max()-1),anger=int(yl.min()-ny.max()-1)) if len(ny) else None
print(json.dumps(out,indent=1)); json.dump(out,open('checks.json','w'),indent=1)
