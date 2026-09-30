"""Locate the Joint test's wrist holes (enclosed transparent px within 8 px of the posed seam) using index.html's own
cutSeam/stampMask/palmExt, and classify each against our palm and its 3 px forearm overlap."""
import asyncio,threading,http.server,functools,json,sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from playwright.async_api import async_playwright
ROOT='/workspace/shadowveil'; V=sys.argv[1]; SIDE=sys.argv[2]; PORT=int(sys.argv[3]); DEGS=[float(x) for x in (sys.argv[4] if len(sys.argv)>4 else '25,-25').split(',')]
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT)); threading.Thread(target=srv.serve_forever,daemon=True).start()
JS='''([s,deg,extra])=>{const saved={};for(const k in P)saved[k]=v[k];const bmE=document.getElementById('bodymode'),ulE=document.getElementById('underlay'),sQ=QUAL,sB=bmE.value,sU=ulE.checked;
 const out=[];try{for(const k in P)v[k]=P[k][2];for(const k in extra)v[k]=extra[k];
 const cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=guard(cv.getContext('2d'));render(g,true);const restCv=document.createElement('canvas');restCv.width=W;restCv.height=H;restCv.getContext('2d').drawImage(cv,0,0);
 const restA=partAlpha(restCv);const palm=R.hands.parts.find(p=>p.parentExternal&&p.id[0]===s&&p.file);const mx=+(palm.maxWristDeg??R.hands.wristMaxDeg??25);const x=Math.max(-1,Math.min(1,deg/mx));const fa=palmParent(palm);
 const cutBy=R.body?Object.fromEntries(R.body.parts.map(p=>[p.id,p])):{};
 const pts=cutSeam(partAlpha(R.im['hands:'+palm.id]),cutBy[fa]?partAlpha(R.im['body:'+fa]):restA,restA);
 const bodies=[];if(R.body)bodies.push('cut');if(R.skin){bodies.push('skin');if(R.skin.underlay&&R.skin.underlay.ok)bodies.push('skin+underlay')}
 for(const b of bodies)for(const q of ['nearest','linear','ss2']){bmE.value=b==='cut'?'cut':'skin';ulE.checked=b==='skin+underlay';QUAL=q;v['Wrist'+s]=x;renderFinal(g,false);
  const M=palmExt(palm,R._BM||{},false);const posed=pts.map(([px,py])=>[M[0]*px+M[2]*py+M[4],M[1]*px+M[3]*py+M[5]]);v['Wrist'+s]=0;
  let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const [px,py] of pts.concat(posed)){x0=Math.min(x0,px);y0=Math.min(y0,py);x1=Math.max(x1,px);y1=Math.max(y1,py)}
  const bx0=Math.max(0,Math.floor(x0-20)),by0=Math.max(0,Math.floor(y0-20)),bx1=Math.min(W,Math.ceil(x1+20)),by1=Math.min(H,Math.ceil(y1+20));const w=bx1-bx0,h=by1-by0;
  const res={};for(const [nm,c,pp] of [['posed',cv,posed],['rest',restCv,pts]]){const Wd={x0:bx0,y0:by0,w,h,d:c.getContext('2d').getImageData(bx0,by0,w,h).data};const band8=stampMask(Wd,pp,8);const N=w*h,d=Wd.d;
   const op=new Uint8Array(N);for(let i=0;i<N;i++)op[i]=d[i*4+3]>=128?1:0;const seen=new Uint8Array(N),st=[];for(let xx=0;xx<w;xx++)st.push(xx,(h-1)*w+xx);for(let y=0;y<h;y++)st.push(y*w,y*w+w-1);
   while(st.length){const i=st.pop();if(seen[i]||op[i])continue;seen[i]=1;const xx=i%w;if(xx>0)st.push(i-1);if(xx<w-1)st.push(i+1);if(i>=w)st.push(i-w);if(i<N-w)st.push(i+w)}
   const cl=morph(morph(op,w,h,3,true),w,h,3,false);const H_=[],T_=[];for(let i=0;i<N;i++){if(!band8[i])continue;const X=bx0+i%w,Y=by0+((i/w)|0);if(!op[i]&&!seen[i])H_.push([X,Y,d[i*4+3]]);if(cl[i]&&!op[i])T_.push([X,Y,d[i*4+3]])}
   res[nm]={holes:H_,tears:T_}}
  out.push({mode:b+'/'+q,x,M,box:[bx0,by0,bx1,by1],seam:pts.length,...res,png:cv.toDataURL('image/png')})}
 }finally{QUAL=sQ;bmE.value=sB;ulE.checked=sU;for(const k in P)v[k]=saved[k];v['Wrist'+s]=0}return out}'''
def dec(u):
    import base64,io; return np.array(Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA'))
async def main():
    palm=np.array(Image.open(f'{ROOT}/views/{V}/hands/{SIDE}_palm.png').convert('RGBA'))[...,3]
    fore=np.array(Image.open(f'{ROOT}/views/{V}/body/forearm_{SIDE}.png').convert('RGBA'))[...,3]
    base=np.array(Image.open(f'{ROOT}/views/{V}/base.png').convert('RGBA'))[...,3]
    near3=ndi.binary_dilation(palm>0,iterations=3)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage'])
        pg=await b.new_page(); await pg.goto(f'http://127.0.0.1:{PORT}/rig/index.html?view={V}')
        await pg.wait_for_function('typeof R!=="undefined"&&R&&R.im&&R.im.base',timeout=90000); await pg.wait_for_timeout(4000)
        for deg in DEGS:
            for r in await pg.evaluate(JS,[SIDE,deg,{}]):
                M=np.array([[r['M'][0],r['M'][2],r['M'][4]],[r['M'][1],r['M'][3],r['M'][5]],[0,0,1]]); inv=np.linalg.inv(M)
                def cls(pts):
                    o=[]
                    for X,Y,a in pts:
                        u,vv=(inv@[X+0.5,Y+0.5,1])[:2]; u,vv=int(np.floor(u)),int(np.floor(vv))
                        o.append(dict(world=(X,Y),alpha=a,palm_src=(u,vv),palm_a=int(palm[vv,u]),palm_within3=bool(near3[vv,u]),forearm_rest_a=int(fore[Y,X]),base_a=int(base[Y,X])))
                    return o
                ph,rh=cls(r['posed']['holes']),cls(r['rest']['holes'])
                print(f"deg {deg:+} {r['mode']:22} holes {len(ph)} (rest {len(rh)}) tears {len(r['posed']['tears'])} (rest {len(r['rest']['tears'])}) box {r['box']}",flush=True)
                for h in ph: print('    HOLE',h,flush=True)
                for h in rh: print('    RESTHOLE',h,flush=True)
                if ph:
                    im=dec(r['png']); x0,y0,x1,y1=r['box']; X,Y=ph[0]['world']
                    bg=Image.new('RGBA',(1365,1739),'magenta'); bg.alpha_composite(Image.fromarray(im))
                    bg.crop((X-20,Y-20,X+20,Y+20)).resize((320,320),Image.NEAREST).save(f'/tmp/hole_{V}_{SIDE}_{deg:+}_{r["mode"].replace("/","_")}.png')
        await b.close()
asyncio.run(main())
