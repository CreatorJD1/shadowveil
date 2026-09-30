import cv2,numpy as np,json,sys
R='/workspace/shadowveil/rig/previews/idle/frames/'
# usage: sheet.py out.png scale name:view:x0:y0:x1:y1:f1,f2,... [more rows]
out=sys.argv[1]; S=int(sys.argv[2]); rows=[]
def comp(p):
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED); a=im[...,3:4]/255.
    bg=np.full_like(im[...,:3],(255,0,0)); return (im[...,:3]*a+bg*(1-a)).astype(np.uint8)
for spec in sys.argv[3:]:
    name,view,x0,y0,x1,y1,fl=spec.split(':'); x0,y0,x1,y1=map(int,(x0,y0,x1,y1))
    tiles=[]
    items=[('rest',R+f'{name}/rest.png')]+[(f'f{int(f):04d}',R+f'{name}/frames/f{int(f):04d}.png') for f in fl.split(',')]
    for lab,p in items:
        c=cv2.resize(comp(p)[y0:y1,x0:x1],None,fx=S,fy=S,interpolation=cv2.INTER_NEAREST)
        hdr=np.zeros((16,c.shape[1],3),np.uint8); cv2.putText(hdr,lab,(2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1)
        tiles.append(np.vstack([hdr,c])); tiles.append(np.zeros((c.shape[0]+16,3,3),np.uint8))
    import os; C=int(os.environ.get('COLS','99'))*2
    chunks=[tiles[j:j+C] for j in range(0,len(tiles),C)]
    wmax=max(sum(t.shape[1] for t in ch) for ch in chunks)
    row=np.vstack([np.pad(np.hstack(ch),((0,0),(0,wmax-sum(t.shape[1] for t in ch)),(0,0))) for ch in chunks]); hdr=np.zeros((16,row.shape[1],3),np.uint8); cv2.putText(hdr,name,(2,12),cv2.FONT_HERSHEY_SIMPLEX,0.42,(255,255,255),1)
    rows.append(np.vstack([hdr,row]))
W=max(r.shape[1] for r in rows); rows=[np.pad(r,((0,4),(0,W-r.shape[1]),(0,0))) for r in rows]
cv2.imwrite(out,np.vstack(rows)); print(np.vstack(rows).shape)
