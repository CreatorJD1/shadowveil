# pass 1: per-frame silhouette metrics + head crops (read-only on the video)
import subprocess, numpy as np, json
V='/workspace/shadowveil/reference/grok_build/public/clean-room/videos/apose-turn.mp4'
W,H=768,1168
p=subprocess.Popen(['ffmpeg','-v','error','-i',V,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
rows=[]; crops=[]
i=0
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    a=np.frombuffer(b,np.uint8).reshape(H,W,3).astype(np.int16)
    blue=(a[...,2]>a[...,0]+60)&(a[...,2]>a[...,1]+60)
    fg=~blue
    ys,xs=np.nonzero(fg)
    top=int(ys.min()); bot=int(ys.max())
    # arm span: widest row between y=200 and 600
    rw=fg[200:600].sum(1); cols=[np.nonzero(fg[y])[0] for y in range(200,600)]
    span=max((c.max()-c.min()+1) if len(c) else 0 for c in cols)
    # torso width at y=450 (waist) contiguous run around body centre
    head=fg[top:top+200]; hx=np.nonzero(head.any(0))[0]
    # head centre x: centroid of fg in rows top+60..top+140 (face level, below the bun)
    fy0=top+60; fr=fg[fy0:fy0+80]; hcx=float(np.nonzero(fr)[1].mean())
    rows.append(dict(frame=i,top=top,bottom=bot,span=int(span),headCx=hcx))
    x0=int(round(hcx))-110; x0=max(0,min(W-220,x0))
    crops.append(a[top:top+240,x0:x0+220].astype(np.uint8)); rows[-1]['cropX0']=x0; rows[-1]['cropY0']=top
    i+=1
p.wait()
json.dump(rows,open('tmp/pass1.json','w'))
np.save('tmp/headcrops.npy',np.stack(crops))
print(i, [ (r['frame'],r['span']) for r in rows[::10]])
