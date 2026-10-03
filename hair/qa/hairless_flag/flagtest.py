# Is ?hairless=1 working on the current live index.html? Render full + all-hair-hidden frames, live vs hairless; read-only, 8780.
import sys,json,base64,io,hashlib,urllib.request,numpy as np
sys.path.insert(0,'/workspace/.pwenv/lib/python3.13/site-packages')
from playwright.sync_api import sync_playwright
from PIL import Image
B='http://127.0.0.1:8780'; R='/workspace/shadowveil'; OUT=R+'/hair/qa/hairless_flag'
srv=hashlib.md5(urllib.request.urlopen(B+'/rig/index.html').read()).hexdigest(); disk=hashlib.md5(open(R+'/rig/index.html','rb').read()).hexdigest(); assert srv==disk
JS=r"""()=>{document.getElementById('auto').checked=false;pauseManual();for(const k in P)v[k]=P[k][2];const ids=(R.hair||[]).map(p=>'hair:'+p.id);
 const shot=(hide)=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));LP.hidden.clear();LP.solo.clear();for(const h of hide)LP.hidden.add(h);LP.active=true;
  try{hairDrive=null;render(g,true)}finally{LP.active=false;LP.hidden.clear()}return c.toDataURL('image/png')};
 return {on:window.RigHairless?RigHairless.on:null,full:shot([]),nohair:shot(ids)}}"""
dec=lambda u:np.array(Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA')).astype(int)
res={'index_md5':srv}
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-gpu','--force-color-profile=srgb','--disable-dev-shm-usage'])
    for v in sys.argv[1].split(','):
        hm=np.array(Image.open(f'{R}/hair/handoff_hairless/{v}_hair_rest_mask.png'))>0
        fr={}
        for tag,q in (('live',''),('hairless','&hairless=1&hlhandcut=0')):
            pg=br.new_page(viewport={'width':900,'height':700}); urls=[]
            pg.on('request',lambda r,urls=urls:urls.append(r.url.split('8780',1)[-1]))
            pg.goto(f'{B}/rig/index.html?view={v}&quality=linear&hair=A{q}',wait_until='domcontentloaded',timeout=180000)
            pg.wait_for_function('typeof R!=="undefined"&&R&&!R.loading',timeout=180000); pg.wait_for_timeout(1500)
            r=pg.evaluate(JS); pg.close(); fr[tag]=(dec(r['full']),dec(r['nohair']))
            Image.fromarray(fr[tag][1].astype(np.uint8)).save(f'{OUT}/{v}_{tag}_nohair.png')
            res[f'{v}_{tag}']=dict(on=r['on'],body_urls=sorted(set(u.split('?')[0] for u in urls if 'base_body' in u)))
        dark=lambda x:((x[...,3]>0)&(x[...,:3].max(-1)<90))
        lf,ln=fr['live']; hf,hn=fr['hairless']
        res[v]=dict(hair_mask_px=int(hm.sum()),full_live_vs_hairless_diff=int((lf!=hf).any(-1).sum()),
            nohair_dark_in_hairmask_live=int((dark(ln)&hm).sum()),nohair_dark_in_hairmask_hairless=int((dark(hn)&hm).sum()),
            nohair_live_vs_hairless_diff=int((ln!=hn).any(-1).sum()))
        print(v,res[f'{v}_live'],res[f'{v}_hairless'],res[v],flush=True)
    br.close()
json.dump(res,open(f'{OUT}/flagtest_{srv[:8]}.json','w'),indent=1)
