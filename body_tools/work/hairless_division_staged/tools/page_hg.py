import sys,json,base64,numpy as np
sys.path.insert(0,'/workspace/.pwenv/lib/python3.13/site-packages')
from playwright.sync_api import sync_playwright
port=sys.argv[1]
JS="""async (view)=>{const grab=()=>{draw();const g=FR.getContext('2d');const d=g.getImageData(0,0,W,H).data;let s='';const CH=0x8000;for(let i=0;i<d.length;i+=CH)s+=String.fromCharCode.apply(null,d.subarray(i,i+CH));return btoa(s)};
 RigHeadGroup.reset();const rest=grab();const h=await RigHeadGroup.applyHandoff(view);const hg=RigHeadGroup.get();const off=grab();
 const A=restPixels();const b=document.createElement('canvas');b.width=W;b.height=H;const gb=b.getContext('2d');gb.drawImage(R.im.base,0,0);const B=gb.getImageData(0,0,W,H).data;let n=0;
 for(let i=0;i<A.length;i+=4){if(A[i+3]===0&&B[i+3]===0)continue;if(A[i]!==B[i]||A[i+1]!==B[i+1]||A[i+2]!==B[i+2]||A[i+3]!==B[i+3])n++}
 RigHeadGroup.reset();return {W,H,rest,off,h,hg:{dx:hg.dx,dy:hg.dy,w:hg.w},restDiffWhileOffsetSet:n,qual:QUAL,hairless:RigHeadGroup&&window.RigHairless.on,hgon:RigHeadGroup.on}}"""
out={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-gpu','--force-color-profile=srgb'])
    for v in ['apose','left','back','right']:
        pg=b.new_page(viewport={'width':1000,'height':800})
        pg.goto(f'http://127.0.0.1:{port}/rig/index.html?view={v}&quality=linear&hairless=1&headgroup=1',wait_until='load')
        pg.wait_for_function("typeof R!=='undefined'&&R&&R.im&&R.im.base&&!R.loading",timeout=120000); pg.wait_for_timeout(2500)
        r=pg.evaluate(JS,v); pg.close()
        for k in ('rest','off'):
            a=np.frombuffer(base64.b64decode(r[k]),np.uint8).reshape(r['H'],r['W'],4); np.save(f'/workspace/tmpsv/hg/page_{v}_{k}.npy',a); r[k]=None
        out[v]=r
    b.close()
print(json.dumps(out))
