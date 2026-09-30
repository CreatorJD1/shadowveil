import json,sys,os,numpy as np,cv2
VD='/workspace/shadowveil/reference/grok_build/public/clean-room/videos'
def frames(c):
    cap=cv2.VideoCapture(f'{VD}/{c}.mp4'); out=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        out.append(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
    return out
def fg(im): return ~((im[...,2]>140)&(im[...,0]<90)&(im[...,1]<90))
def track(c,F=None):
    J=json.load(open(f'/workspace/gb/mp2_{c}.json')); n=J['n']
    if os.path.exists(f'/workspace/gb/mp_{c}.json'):
        J1=json.load(open(f'/workspace/gb/mp_{c}.json'))
        for i in range(n):
            for h in J1['frames'][i]:
                a=np.array(h['img'])
                if a[:,1].mean()<float(os.environ.get('YMAX','0.70'))*J['H'] and all(np.linalg.norm(a.mean(0)-np.array(o['img']).mean(0))>35 for o in J['frames'][i]): J['frames'][i].append(h)
    if F is None: F=frames(c)
    T={'A':[None]*n,'B':[None]*n}
    for i,hs in enumerate(J['frames']):
        m=fg(F[i]); cx=np.nonzero(m)[1].mean()
        for h in hs:
            a=np.array(h['img']); side='A' if a[:,0].mean()<cx else 'B'
            if T[side][i] is None or h['score']>T[side][i]['score']: T[side][i]=dict(h,center=a.mean(0).tolist(),size=float(max(np.ptp(a[:,0]),np.ptp(a[:,1]))))
    out={}
    for s in 'AB':
        idx=[i for i in range(n) if T[s][i]]; 
        if not idx: out[s]=None; continue
        cs=np.array([T[s][i]['center'] for i in idx]); xs=np.interp(range(n),idx,cs[:,0]); ys=np.interp(range(n),idx,cs[:,1])
        # median filter to kill single-frame jumps
        from scipy.ndimage import median_filter
        xs=median_filter(xs,5); ys=median_filter(ys,5)
        out[s]=dict(det=idx,x=xs.tolist(),y=ys.tolist(),raw=T[s])
    return out,F
if __name__=='__main__':
    from PIL import Image,ImageDraw
    clips=sys.argv[1].split(','); step=int(sys.argv[2]); outp=sys.argv[3]
    rows=[]
    for c in clips:
        tr,F=track(c)
        for s in 'AB':
            t=tr[s]; r=Image.new('RGB',(40+ (len(range(0,len(F),step)))*72,76),'white'); d=ImageDraw.Draw(r); d.text((1,2),c[:7],fill='black'); d.text((1,14),'img'+('L' if s=='A' else 'R'),fill='black')
            if t is None: d.text((1,30),'none',fill='red'); rows.append(r); continue
            d.text((1,26),f'{len(t["det"])}det',fill='black')
            for k,i in enumerate(range(0,len(F),step)):
                x,y=t['x'][i],t['y'][i]; S=45
                cr=Image.fromarray(F[i]).crop((int(x-S),int(y-S),int(x+S),int(y+S))).resize((70,70))
                r.paste(cr,(40+k*72,2)); d.text((40+k*72,62),str(i),fill='red' if t['raw'][i] else 'gray')
            rows.append(r)
    o=Image.new('RGB',(max(r.width for r in rows),76*len(rows)),'white')
    for k,r in enumerate(rows): o.paste(r,(0,76*k))
    o.save(outp)
