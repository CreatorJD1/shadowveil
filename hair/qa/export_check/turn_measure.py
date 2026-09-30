"""Task 5: measure the shared apose-turn frames (reference/apose_turn/frames/fNNN.png, 24 fps). One frame at a time. Measure only."""
import numpy as np, json
from PIL import Image
F='/workspace/shadowveil/reference/apose_turn/frames'; OUT='/workspace/shadowveil/hair/qa/export_check'
rows=[]
for i in range(1,242):
    im=np.array(Image.open(f'{F}/f{i:03d}.png').convert('RGB')).astype(np.int16)
    r,g,b=im[...,0],im[...,1],im[...,2]
    bg=(b>140)&(r<90)&(g<90)&(b-np.maximum(r,g)>90); fg=~bg
    ys,xs=np.nonzero(fg); top,bot=ys.min(),ys.max(); Hf=bot-top
    hair=fg&(np.maximum(np.maximum(r,g),b)<75)
    skin=fg&(r>95)&(r-b>25)&(r>=g)
    def width(y0,y1,m=fg):
        w=[];c=[]
        for y in range(y0,y1):
            xx=np.nonzero(m[y])[0]
            if len(xx): w.append(xx.max()-xx.min()); c.append((xx.max()+xx.min())/2)
        return (np.median(w) if w else 0, np.median(c) if c else 0)
    hip=width(top+int(.52*Hf),top+int(.56*Hf)); waist=width(top+int(.40*Hf),top+int(.42*Hf))
    # head: rows top..top+0.2Hf
    H0=top; H1=top+int(0.20*Hf)
    hm=hair[H0:H1]; sm=skin[H0:H1]
    hy,hx=np.nonzero(hm)
    # row widths of hair silhouette (hair+skin) to find bun notch
    head=(hm|sm)
    wr=np.array([ (lambda xx:(xx.max()-xx.min()+1) if len(xx) else 0)(np.nonzero(head[y])[0]) for y in range(head.shape[0])])
    skull_w=np.percentile(wr[wr>0],95)
    # bun: rows from top while width < 0.62*skull_w (narrow top blob) -> bun visible top part
    k=0
    while k<len(wr) and wr[k]<0.62*skull_w: k+=1
    bun_rows=k
    # notch: after the bun, first local min of width (bun waist) if exists before skull
    by,bx=np.nonzero(head[:max(k,1)])
    bun_cx=float(bx.mean()) if len(bx) else float('nan')
    # skull centre: rows k..k+60
    sy,sx=np.nonzero(head[k:k+70]); skull_cx=float(sx.mean()) if len(sx) else float('nan')
    # face skin fraction in head rows k+40..k+140 (face visibility) & skin centroid
    band=slice(k+30,min(head.shape[0],k+150)); sk=sm[band]; hr=hm[band]
    skin_frac=float(sk.sum()/max((sk|hr).sum(),1)); sky,skx=np.nonzero(sk); skin_cx=float(skx.mean()) if len(skx) else float('nan')
    # hair lowest point (hanging length): lowest hair pixel within head/neck column region top..0.30Hf, x within skull +-0.8w
    reg=hair[H0:top+int(0.32*Hf)]; ry,rx=np.nonzero(reg)
    sel=np.abs(rx-skull_cx)<0.75*skull_w; low=int(ry[sel].max()) if sel.any() else 0
    rows.append(dict(f=i,top=int(top),figH=int(Hf),hipW=float(hip[0]),waistW=float(waist[0]),skullW=float(skull_w),bun_rows=int(bun_rows),
        bun_dx=round((bun_cx-skull_cx)/skull_w,3),skin_frac=round(skin_frac,3),skin_dx=round((skin_cx-skull_cx)/skull_w,3) if len(skx) else None,
        hair_low=round(low/Hf,3),hair_area=int(hm.sum()),skin_area=int(sm.sum())))
    if i%40==1: print(rows[-1],flush=True)
json.dump(rows,open(OUT+'/turn_measure.json','w'),indent=0)
