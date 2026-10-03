import sys,json
sys.path.insert(0,'/workspace/.pwenv/lib/python3.13/site-packages')
from playwright.sync_api import sync_playwright
port=sys.argv[1]; extra=sys.argv[2] if len(sys.argv)>2 else ''
JS="""()=>{const A=restPixels();const b=document.createElement('canvas');b.width=W;b.height=H;const gb=b.getContext('2d');gb.drawImage(R.im.base,0,0);
const B=gb.getImageData(0,0,W,H).data;let n=0;for(let i=0;i<A.length;i+=4){if(A[i+3]===0&&B[i+3]===0)continue;if(A[i]!==B[i]||A[i+1]!==B[i+1]||A[i+2]!==B[i+2]||A[i+3]!==B[i+3])n++}
return {diff:n,qual:QUAL,hairless:window.RigHairless?RigHairless.on:null,missing:window.RigHairless?RigHairless.missing:null,warn:(R.warn||[]).slice(0,10),body:document.getElementById('bodymode')?document.getElementById('bodymode').value:null}}"""
out={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-gpu','--force-color-profile=srgb'])
    for v in ['apose','tpose','left','right','back']:
        pg=b.new_page(viewport={'width':1000,'height':800})
        pg.goto(f'http://127.0.0.1:{port}/rig/index.html?view={v}&quality=linear{extra}',wait_until='load')
        pg.wait_for_function("typeof R!=='undefined'&&R&&R.im&&R.im.base&&!R.loading",timeout=120000); pg.wait_for_timeout(2500)
        out[v]=pg.evaluate(JS); pg.close()
    b.close()
print(json.dumps(out))
