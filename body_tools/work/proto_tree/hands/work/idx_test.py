"""Run the real rig/index.html headless (system Chrome) with the hands dir optionally redirected to a staging dir.
Reports load warnings, frame segment count, joint gaps from index.html's own handChain, and pixel agreement with rigrender2."""
import sys,json,asyncio,threading,http.server,functools,os,base64,io
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright
ROOT='/workspace/shadowveil'; VIEW=sys.argv[1]; STAGE=sys.argv[2] if len(sys.argv)>2 else None
PORT=int(os.environ.get('PORT',8765+hash(VIEW)%100))
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory=ROOT)
class Q(H.func):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT)); threading.Thread(target=srv.serve_forever,daemon=True).start()
PRE={'Fist':[1,1,1,1,1],'Point':[1,0,1,1,1],'Peace':[1,0,0,1,1],'Half':[.5,.5,.5,.5,.5]}
FING=['Thumb','Index','Middle','Ring','Pinky']
JS_JOINTS='''(vals)=>{for(const k in vals)v[k]=vals[k];
 const parts=R.hands.parts;const M=handChain(parts,handAngle(R.hands),p=>I,false);const by={};for(const p of parts)by[p.id]=p;const out=[];
 const ap=(m,x,y)=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];
 for(const p of parts){if(!p.parent||!by[p.parent]||!/\\d$/.test(p.id)||!p.file)continue;const q=by[p.parent];const f=frameOf(p,false),pf=frameOf(q,false);
  const piv=(f&&f.pivot)||[p.pivotX,p.pivotY];const cp=(pf&&pf.childPivot)||piv;const a=ap(M[q.id],cp[0],cp[1]),b=ap(M[p.id],piv[0],piv[1]);out.push([p.id,Math.hypot(a[0]-b[0],a[1]-b[1])])}
 const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));let err=null;try{render(g,false)}catch(e){err=String(e)}return {j:out,png:c.toDataURL('image/png'),err}}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        pg=await b.new_page(); logs=[]
        pg.on('console',lambda m:logs.append(m.type+': '+m.text)); pg.on('response',lambda r: print('404:',r.url) if r.status==404 else None)
        if STAGE:
            async def rt(route):
                fn=route.request.url.split('/views/'+VIEW+'/hands/')[1].split('?')[0]
                path=os.path.join(STAGE,fn)
                if os.path.exists(path): await route.fulfill(path=path)
                else: await route.fulfill(status=404,body='')
            await pg.route(f'**/views/{VIEW}/hands/**',rt)
        await pg.goto(f'http://127.0.0.1:{PORT}/rig/index.html?view={VIEW}#check')
        await pg.wait_for_function('typeof R!=="undefined"&&R&&R.im&&R.im.base',timeout=60000)
        await pg.wait_for_timeout(2500)
        st=await pg.eval_on_selector('#status','e=>e.textContent')
        print('STATUS:',st.replace('\n',' | '))
        print('frames segments:',await pg.evaluate('Object.keys(R.frames).length'))
        hw=[w for w in await pg.evaluate('R.warn') if any(s in w for s in ['_palm','Thumb','Index','Middle','Ring','Pinky','hands'])]
        print('hand warnings:',hw)
        print('console warn/err:',[l for l in logs if l.startswith(('warning','error'))][:10])
        worst=0; res=[]
        for name,vals in PRE.items():
            for c in [0,.25,.5,.75,1]:
                vv={f'Hand{h}{f}':x*c for h in 'LR' for f,x in zip(FING,vals)}
                r=await pg.evaluate(JS_JOINTS,vv); g=max(x[1] for x in r['j']) if r['j'] else 0; worst=max(worst,g)
                res.append((name,c,round(g,4)))
                if r.get('err'): print('RENDER ERROR (not hands):',r['err'],flush=True) if c==0 and name=='Fist' else None
                if name=='Fist' and c in (.5,1): Image.open(io.BytesIO(base64.b64decode(r['png'].split(',')[1]))).save(f'/tmp/idx_{VIEW}_{name}_{c}.png')
        print('joint gaps (index.html handChain), worst px:',round(worst,4)); print(res)
        await b.close()
asyncio.run(main())
