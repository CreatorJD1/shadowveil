# Job 3 (Oct 2 2026): rig rest renders with the staged head group (?headgroup=1) moved by the EYE-fit handoff offsets, served by Hair's
# (hairless=1: Body's hair-free body + the final staged hair, so hiding hair items exposes the whole visible hair mass; the live
# base_body still carries a baked hair copy, which hides most hair from a hide-diff.)
# scratch server 127.0.0.1:8780 rooted at /workspace/shadowveil (index.html md5 checked). Read-only. Per view saves masks (npz):
#   full      alpha of the full rest frame
#   hair      px where the frame changes when ALL hair items are hidden (visible hair, incl. hair_back where it shows)
#   bun       px where the frame changes when only the bun is hidden
import sys,json,base64,io,hashlib,urllib.request,numpy as np
sys.path.insert(0,'/workspace/.pwenv/lib/python3.13/site-packages')
from playwright.sync_api import sync_playwright
from PIL import Image
PORT=8795; BASE=f'http://127.0.0.1:{PORT}'; R='/workspace/shadowveil'; OUT=R+'/rig/work/hgsubhair/m'
HG={'apose':(0,-9),'left':(0,11),'back':(2,11),'right':(3,5)}
srv=hashlib.md5(urllib.request.urlopen(BASE+'/rig/index.html').read()).hexdigest(); disk=hashlib.md5(open(R+'/rig/index.html','rb').read()).hexdigest()
assert srv==disk,(srv,disk); print('index.html md5',srv,'== disk')
JS=r"""async([vw,mode])=>{document.getElementById('auto').checked=false;pauseManual();for(const k in P)v[k]=P[k][2];
 await RigHeadGroup.applyHandoff(vw);const S0=RigHeadGroup.get().sub||{};if(mode==='off')RigHeadGroup.set({sub:S0.mouth?{mouth:S0.mouth}:{}});const hg=RigHeadGroup.get();
 const facem=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));const ids=['sys:eyes','sys:mouth'];const sh=new Set(LP.solo);LP.solo.clear();for(const h of ids)LP.solo.add(h);LP.active=true;try{hairDrive=null;render(g,false)}finally{LP.active=false;LP.solo.clear();for(const h of sh)LP.solo.add(h)}return c.toDataURL('image/png')};
 const shot=(hide,solo=[])=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));
   const sh=new Set(LP.hidden),so=new Set(LP.solo);LP.hidden.clear();LP.solo.clear();for(const h of hide)LP.hidden.add(h);for(const h of solo)LP.solo.add(h);LP.active=true;
   try{hairDrive=null;render(g,false)}finally{LP.active=false;LP.hidden.clear();LP.solo.clear();for(const h of sh)LP.hidden.add(h);for(const h of so)LP.solo.add(h)}
   return c.toDataURL('image/png')};
 const ids=(R.hair||[]).map(p=>'hair:'+p.id);
 return {hg,ids,face:facem(),full:shot([]),nohair:shot(ids),nobun:shot(['hair:bun']),solohair:shot([],ids),solobun:shot([],['hair:bun'])}}"""
dec=lambda u:np.array(Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA')).astype(np.int16)
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-gpu','--force-color-profile=srgb','--disable-dev-shm-usage'])
    for v in HG:
      for mode in ('off','on'):
        pg=b.new_page(viewport={'width':1000,'height':800})
        pg.goto(f'{BASE}/rig/index.html?view={v}&quality=linear&headgroup=1&hairless=1&hlhandcut=0',wait_until='domcontentloaded',timeout=180000)
        pg.wait_for_function('typeof R!=="undefined"&&R&&!R.loading&&window.RigHeadGroup',timeout=180000); pg.wait_for_timeout(1500)
        r=pg.evaluate(JS,[v,mode]); pg.close()
        F,N,B,SH,SB=dec(r['full']),dec(r['nohair']),dec(r['nobun']),dec(r['solohair']),dec(r['solobun'])
        # visible hair = hair drawn alone (solo, preview path) AND the full frame shows that same pixel (so hair under an opaque,
        # different body px is not counted; Body's base_body still carries identical hair copies, so a hide-diff alone misses them)
        hair=(SH[...,3]>127)&(np.abs(F[...,:3]-SH[...,:3]).max(-1)<=8); bun=(SB[...,3]>127)&(np.abs(F[...,:3]-SB[...,:3]).max(-1)<=8)
        Image.fromarray(F.astype(np.uint8)).save(f'{OUT}/{v}_{mode}_full.png');Image.fromarray(dec(r['face']).astype(np.uint8)).save(f'{OUT}/{v}_{mode}_face.png')
        np.savez_compressed(f'{OUT}/{v}_{mode}_masks.npz',full=F[...,3]>127,hair=hair,bun=bun,solo_hair=SH[...,3]>127)
        json.dump({'view':v,'headgroup':r['hg'],'hair_ids':r['ids'],'index_md5':srv,'port':PORT},open(f'{OUT}/{v}_{mode}_render.json','w'),indent=1)
        print(v,mode,r['hg'],'hair px',int(hair.sum()),'bun px',int(bun.sum()),flush=True)
    b.close()
