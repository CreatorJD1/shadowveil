"""Real rig/index.html: swing shoulder+elbow +-25 deg, count seam pixels along the wrist (light or bluish vs local skin).
Optional arg 'before' serves the pre-fix palms from backup_wrist/."""
import asyncio,threading,http.server,functools,json,base64,io,sys,os
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright
from defs import D
ROOT='/workspace/shadowveil'; PORT=int(sys.argv[2]) if len(sys.argv)>2 else 8931; BEFORE=len(sys.argv)>1 and sys.argv[1]=='before'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT)); threading.Thread(target=srv.serve_forever,daemon=True).start()
JS='''([vals,mode])=>{const e=document.getElementById('bodymode');if(e&&mode)e.value=mode;for(const k in vals)v[k]=vals[k];const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));render(g,false);
 // world wrist line = palm matrix applied to palm pivot
 return c.toDataURL('image/png')}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        for V in ['apose','tpose','left','right','back']:
            pg=await b.new_page()
            if BEFORE:
                async def rt(route,V=V):
                    fn=route.request.url.split('/hands/')[1].split('?')[0]; pth=f'{ROOT}/hands/work/backup_wrist/{V}/{fn}'
                    await (route.fulfill(path=pth) if os.path.exists(pth) else route.continue_())
                await pg.route(f'**/views/{V}/hands/*_palm.png*',rt)
            await pg.goto(f'http://127.0.0.1:{PORT}/rig/index.html?view={V}')
            await pg.wait_for_function('typeof R!=="undefined"&&R&&R.im&&R.im.base',timeout=60000); await pg.wait_for_timeout(2500)
            modes=await pg.evaluate("(()=>{const e=document.getElementById('bodymode');return e?[...e.options].map(o=>o.value):['']})()")
            rig=json.load(open(f'{ROOT}/views/{V}/hands/rig.json'))
            res=[]
            for mode in modes[:1]:
                for sgn in (0,1,-1):
                    vals={'ShoulderL':sgn,'ShoulderR':sgn,'ElbowL':sgn,'ElbowR':sgn}
                    im=np.array(Image.open(io.BytesIO(base64.b64decode((await pg.evaluate(JS,[vals,mode])).split(',')[1]))).convert('RGBA')).astype(int)
                    M=await pg.evaluate('''(()=>{const r={};const BM=chain(R.body.parts,bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]);for(const k of ['forearm_L','forearm_R'])r[k]=BM[k];return r})()''')
                    tot=0
                    for side,dd in D[V].items():
                        pp=next(q for q in rig['parts'] if q['id']==side+'_palm')
                        if not pp.get('file'): continue
                        m=M[pp.get('parentExternal') or 'forearm_'+side]
                        S=np.array(rig['hands'][side]['skinRGB'])
                        (x0,y0),(x1,y1)=dd['wrist']
                        xm=(x0+x1)/2; ym=(y0+y1)/2; cx=m[0]*xm+m[2]*ym+m[4]; cy=m[1]*xm+m[3]*ym+m[5]
                        for tt in np.linspace(0.1,0.9,40):
                            x=x0+(x1-x0)*tt; y=y0+(y1-y0)*tt; wx=m[0]*x+m[2]*y+m[4]; wy=m[1]*x+m[3]*y+m[5]
                            for dx in range(-3,4):
                                for dy in range(-3,4):
                                    px=im[int(round(wy+dy)),int(round(wx+dx))]
                                    if px[3]<250 or (px[:3].sum()>S.sum()+60) or (px[2]>px[0]+15 and px[:3].sum()>200): tot+=1
                        Image.fromarray(im[int(cy)-30:int(cy)+30,int(cx)-40:int(cx)+40].astype(np.uint8)).resize((320,240),Image.NEAREST).save(f'/tmp/wr_{"B" if BEFORE else "A"}_{V}_{mode}_{sgn}_{side}.png')
                    res.append((mode or 'default',sgn*25,tot))
            print(V,'BEFORE' if BEFORE else 'AFTER',res,flush=True); await pg.close()
        await b.close()
asyncio.run(main())
