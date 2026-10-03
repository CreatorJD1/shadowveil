// body under the hair: rest frame with R.hair=[] (hair parts not drawn), plain vs ?hairless=1; px in the hair footprint that still look like hair (dark, non-skin)
const pp=require('/workspace/jt/node_modules/puppeteer-core');(async()=>{const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',protocolTimeout:1800000,args:['--no-sandbox','--disable-dev-shm-usage']});const out={};const PORT=process.env.PORT||8795;
async function grab(v,q){const p=await b.newPage();await p.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}${q}`,{waitUntil:'domcontentloaded',timeout:1500000});
 await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:1500000,polling:2000});await new Promise(r=>setTimeout(r,1000));
 const r=await p.evaluate(()=>{document.getElementById('auto').checked=false;document.getElementById('rest').click();draw();const full=Array.from(FR.getContext('2d').getImageData(0,0,W,H).data);const hs=R.hair;R.hair=[];draw();const nh=Array.from(FR.getContext('2d').getImageData(0,0,W,H).data);R.hair=hs;draw();return{full,nh}});
 const c=await p.screenshot({encoding:'base64'}).catch(()=>null);await p.close();return r}
for(const v of (process.argv[2]||'apose').split(',')){const a=await grab(v,'&quality=linear'),h=await grab(v,'&hairless=1&quality=linear');
 let d=0,dark_plain=0,dark_hl=0;for(let i=0;i<a.nh.length;i+=4){if(a.nh[i]!==h.nh[i]||a.nh[i+1]!==h.nh[i+1]||a.nh[i+2]!==h.nh[i+2]||a.nh[i+3]!==h.nh[i+3])d++;
  const y=Math.floor(i/4/1365);if(y<420){if(a.nh[i+3]>0&&a.nh[i]<70&&a.nh[i+1]<60)dark_plain++;if(h.nh[i+3]>0&&h.nh[i]<70&&h.nh[i+1]<60)dark_hl++}}
 out[v]={hairHidden_px_plain_vs_hairless:d,darkHairLike_px_above_y420:{plain:dark_plain,hairless:dark_hl}};console.error(v,JSON.stringify(out[v]))}
console.log(JSON.stringify(out));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
