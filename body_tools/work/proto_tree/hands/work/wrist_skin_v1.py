"""apose wrist check with the declared v1.4 body skin in the real rig/index.html.
Arm cases (both sides at once): Shoulder +-25, Elbow +-25, combined +-25; x hand rest/Fist/Point/Peace.
Per hand: seam band = +-4 px across the world wrist line (inside the arm): count cleared (alpha<250), light (> skin+60)
and bluish pixels vs the same count at rest; drift = body-only render in the forearm end band (3..8 px above the wrist)
compared with the rest body band moved rigidly by the forearm bone matrix (px differing > 40)."""
import asyncio,threading,http.server,functools,json,base64,io,sys
import numpy as np
from PIL import Image,ImageDraw
from playwright.async_api import async_playwright
from defs import D
ROOT='/workspace/shadowveil'; V=sys.argv[1] if len(sys.argv)>1 else 'apose'; PORT=int(sys.argv[2]) if len(sys.argv)>2 else 9141
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT)); threading.Thread(target=srv.serve_forever,daemon=True).start()
FING=['Thumb','Index','Middle','Ring','Pinky']
HANDS={'rest':[0]*5,'Fist':[1]*5,'Point':[1,0,1,1,1],'Peace':[1,0,0,1,1]}
ARMS=[('rest',{})]+[(f'{n}{"+" if s>0 else "-"}25',{k:s for k in ks}) for n,ks in (('Shoulder',['ShoulderL','ShoulderR']),('Elbow',['ElbowL','ElbowR']),('Sh+El',['ShoulderL','ShoulderR','ElbowL','ElbowR'])) for s in (1,-1)]
JS='''(vals)=>{for(const k in v)if(/^(Hand|Shoulder|Elbow|Wrist)/.test(k))v[k]=0;for(const k in vals)v[k]=vals[k];
 const mk=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c};
 const c=mk();const g=guard(c.getContext('2d'));render(g,false);
 const hs=R.hands;R.hands=null;const cb=mk();const gb=guard(cb.getContext('2d'));render(gb,false);R.hands=hs;
 const BM=useSkin()?chain(R.skin.bones,bodyAngle,null,p=>p.parent):chain(R.body.parts,bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]);
 return {full:c.toDataURL('image/png'),body:cb.toDataURL('image/png'),L:BM.forearm_L,R:BM.forearm_R,skin:useSkin()}}'''
def dec(u): return np.array(Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA')).astype(int)
async def main():
    rig=json.load(open(f'{ROOT}/views/{V}/hands/rig.json'))
    SIDES=[s_ for s_ in 'LR' if next(q for q in rig['parts'] if q['id']==s_+'_palm').get('file')]
    FAR=[s_ for s_ in 'LR' if s_ not in SIDES]
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage'])
        pg=await b.new_page(); errs=[]; pg.on('console',lambda m: errs.append(m.text) if m.type in('error','warning') else None)
        await pg.goto(f'http://127.0.0.1:{PORT}/rig/index.html?view={V}#check')
        await pg.wait_for_function('typeof R!=="undefined"&&R&&R.im&&R.im.base',timeout=90000); await pg.wait_for_timeout(4000)
        st=await pg.eval_on_selector('#status','e=>e.textContent'); print('STATUS:',st.replace('\n',' | ')[:400])
        print('warn:',await pg.evaluate('R.warn'),'skin loaded:',await pg.evaluate('!!R.skin'),'useSkin:',await pg.evaluate('useSkin()'))
        rest=await pg.evaluate(JS,{}); rfull=dec(rest['full']); rbody=dec(rest['body'])
        def band(m,side):
            (x0,y0),(x1,y1)=D[V][side]['wrist']; A=np.array([x0,y0],float); B=np.array([x1,y1],float); t=B-A; Lw=np.linalg.norm(t); t/=Lw; n=np.array([-t[1],t[0]])
            if (np.array(D[V][side]['inside'])-A)@n>0: n=-n   # n -> forearm
            pts={}
            for s_lo,s_hi,key in ((-4,4,'seam'),(3,8,'fore')):
                P=[]
                for u in np.arange(1.5,Lw-1.5,0.5):
                    for s in np.arange(s_lo,s_hi+0.01,0.5):
                        q=A+t*u+n*s; P.append((q[0],q[1]))
                P=np.array(P); w=np.stack([m[0]*P[:,0]+m[2]*P[:,1]+m[4],m[1]*P[:,0]+m[3]*P[:,1]+m[5]],1)
                pts[key]=(np.unique(np.round(P).astype(int),axis=0),np.round(w).astype(int),np.round(P).astype(int))
            return pts
        I6=[1,0,0,1,0,0]
        def seam_count(img,side,m):
            S=np.array(rig['hands'][side]['skinRGB']); _,w,_=band(m,side)['seam']; w=np.unique(w,axis=0)
            px=img[w[:,1],w[:,0]]; cl=int((px[:,3]<250).sum()); li=int(((px[:,:3].sum(1)>S.sum()+60)&(px[:,3]>=250)).sum()); bl=int(((px[:,2]>px[:,0]+10)&(px[:,:3].sum(1)>150)).sum())
            return cl,li,bl
        from scipy import ndimage as ndi
        INT=ndi.binary_erosion(rfull[...,3]>=250,iterations=2)      # rest pixels well inside the silhouette
        def rigid(img,m):
            # rest image moved rigidly by m (what a perfectly rigid wrist would show), bilinear like the renderer
            inv=np.linalg.inv(np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]],[0,0,1]]))
            return np.array(Image.fromarray(img.astype(np.uint8)).convert('RGBa').transform((1365,1739),Image.AFFINE,tuple(inv[0])+tuple(inv[1]),resample=Image.BILINEAR).convert('RGBA')).astype(int)
        def check(full,body,side,m):
            bd=band(m,side); out={}
            for key,img,ref in (('seam',full,rfull),('fore',body,rbody)):
                _,w,src=bd[key]; ok=(w[:,0]>=0)&(w[:,0]<1365)&(w[:,1]>=0)&(w[:,1]<1739)&INT[src[:,1],src[:,0]]
                w=w[ok]; rr=rigid(ref,m)[w[:,1],w[:,0]]; px=img[w[:,1],w[:,0]]
                d=np.abs(px-rr).max(1)
                out[key]=(int(((px[:,3]<250)&(px[:,3]<rr[:,3]-16)).sum())   # cleared = more transparent than a rigid wrist would be
                            ,int((d>48).sum()),len(w),float(d.mean()))
                if key=='seam':
                    S=np.array(rig['hands'][side]['skinRGB'])
                    out['light']=int(((px[:,:3].sum(1)>S.sum()+60)&(rr[:,:3].sum(1)<=S.sum()+60)).sum()); out['blue']=int(((px[:,2]>px[:,0]+10)&(px[:,:3].sum(1)>150)).sum())
            return out
        base0={s:seam_count(rfull,s,I6) for s in SIDES}
        if FAR:
            fp=[q for q in rig['parts'] if q['id'][0] in FAR]
            print('far hand',FAR,'parts',len(fp),'with a file:',sum(1 for q in fp if q.get('file')),'hidden:',all(q.get('hidden') or not q.get('file') for q in fp),'layers',sorted({q['layer'] for q in fp}),flush=True)
        print('rest seam band (cleared, light, bluish):',base0)
        rows=[]; cells=[]; allpass=True
        for an,av in ARMS:
            for hn,hv in HANDS.items():
                vals=dict(av); vals.update({f'Hand{h}{f}':x for h in 'LR' for f,x in zip(FING,hv)})
                r=await pg.evaluate(JS,vals); full=dec(r['full']); body=dec(r['body'])
                res={}
                for side in SIDES:
                    m=r[side]; o=check(full,body,side,m)
                    cl,sdiff,sn,smean=o['seam']; _,fdiff,fn,fmean=o['fore']
                    passed=cl==0 and o['light']==0 and o['blue']==0 and sdiff<=max(3,sn//100) and fdiff<=max(3,fn//100)
                    allpass&=passed
                    res[side]=dict(cleared=cl,light=o['light'],blue=o['blue'],strip_vs_rigid=f'{sdiff}/{sn} (mean {smean:.1f})',forearm_vs_rigid=f'{fdiff}/{fn} (mean {fmean:.1f})',ok='PASS' if passed else 'FAIL')
                    _,w,_=band(m,side)['seam']
                    cx=int(np.mean(w[:,0])); cy=int(np.mean(w[:,1]))
                    bg=Image.new('RGBA',(1365,1739),'white'); bg.alpha_composite(Image.fromarray(full.astype(np.uint8)))
                    c=bg.crop((cx-24,cy-24,cx+24,cy+24)).convert('RGB').resize((192,192),Image.NEAREST); d=ImageDraw.Draw(c); d.rectangle([0,0,192,11],fill='white'); d.text((2,0),f'{side} {an} {hn} {res[side]["ok"]}',fill='black' if passed else 'red'); cells.append(c)
                print(an,hn,res,flush=True); rows.append((an,hn,res))
        await b.close()
    cols=8; o=Image.new('RGB',(cols*196+4,((len(cells)+cols-1)//cols)*196+24),(200,200,200)); ImageDraw.Draw(o).text((4,6),f'{V} wrist with declared body skin (real rig/index.html): {"ALL PASS" if allpass else "FAILURES"}; crops 4x at the world wrist',fill='black')
    for i,c in enumerate(cells): o.paste(c,(4+(i%cols)*196,24+(i//cols)*196))
    o.save(f'{ROOT}/hands/previews/wrist_skin_{V}.png'); print('ALLPASS',allpass); print('console:',errs[:5])
asyncio.run(main())
