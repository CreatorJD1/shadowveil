"""Render the live rig/index.html (Body parts + wristPivot palms + hand frames) for all views: rest, Fist, Point, Peace, curl 0.5."""
import asyncio,threading,http.server,functools,json,base64,io
from PIL import Image,ImageDraw
from playwright.async_api import async_playwright
ROOT='/workspace/shadowveil'; PORT=8899
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT)); threading.Thread(target=srv.serve_forever,daemon=True).start()
FING=['Thumb','Index','Middle','Ring','Pinky']
POSES=[('rest',None),('Fist',[1]*5),('Point',[1,0,1,1,1]),('Peace',[1,0,0,1,1]),('curl 0.5',[.5]*5)]
JS='''(vals)=>{for(const k in v)if(k.startsWith('Hand'))v[k]=0;for(const k in vals)v[k]=vals[k];const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));try{render(g,false)}catch(e){window.__err=String(e)}return c.toDataURL('image/png')}'''
async def main():
    rows=[]; info={}
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        for V in ['apose','tpose','left','right','back']:
            pg=await b.new_page()
            await pg.goto(f'http://127.0.0.1:{PORT}/rig/index.html?view={V}#check')
            await pg.wait_for_function('typeof R!=="undefined"&&R&&R.im&&R.im.base',timeout=60000); await pg.wait_for_timeout(3000)
            st=await pg.eval_on_selector('#status','e=>e.textContent'); warn=await pg.evaluate('R.warn')
            info[V]={'status':st.split('\n')[0],'frames':await pg.evaluate('Object.keys(R.frames).length'),'body':await pg.evaluate('!!R.body'),'warn':warn}
            rig=json.load(open(f'{ROOT}/views/{V}/hands/rig.json'))
            boxes=[(h,(d['box'][0]-45,d['box'][1]-45,d['box'][2]+45,d['box'][3]+45)) for h,d in rig['hands'].items() if d.get('visible')]
            cells=[]
            for name,vals in POSES:
                vv={} if vals is None else {f'Hand{h}{f}':x for h in 'LR' for f,x in zip(FING,vals)}
                im=Image.open(io.BytesIO(base64.b64decode((await pg.evaluate(JS,vv)).split(',')[1]))).convert('RGBA')
                bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im)
                for h,bx in boxes:
                    c=bg.crop(bx).convert('RGB'); c=c.resize((c.width*3,c.height*3),Image.NEAREST); ImageDraw.Draw(c).rectangle([0,0,170,14],fill='white'); ImageDraw.Draw(c).text((3,2),f'{V} {h} {name}',fill='black'); cells.append((name,h,c))
            await pg.close()
            nh=len(boxes); cw=max(c.width for *_,c in cells); ch=max(c.height for *_,c in cells)
            sh=Image.new('RGB',(nh*(cw+6)+6,len(POSES)*(ch+6)+30),(215,215,215)); ImageDraw.Draw(sh).text((6,8),f"{V}: {info[V]['status']} | frames {info[V]['frames']} | body rig {'on' if info[V]['body'] else 'off'}",fill='black')
            for i,(name,h,c) in enumerate(cells): sh.paste(c,(6+(i%nh)*(cw+6),30+(i//nh)*(ch+6)))
            sh.save(f'{ROOT}/hands/previews/check_{V}.png'); rows.append(sh)
        await b.close()
    s=0.5; rs=[r.resize((int(r.width*s),int(r.height*s))) for r in rows]
    al=Image.new('RGB',(sum(r.width for r in rs)+6*len(rs)+6,max(r.height for r in rs)+12),(180,180,180)); x=6
    for r in rs: al.paste(r,(x,6)); x+=r.width+6
    al.save(f'{ROOT}/hands/previews/check_all.png'); print(json.dumps(info,indent=1))
asyncio.run(main())
