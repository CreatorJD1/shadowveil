// live skin.json vs rig/work/weight_bleed_fix/<view>_skin_fix.json in the browser rig: rest vs base, posed FR PNGs
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const PORT=process.env.PORT||8793,OUT='/workspace/shadowveil/rig/work/weight_bleed_fix/br';fs.mkdirSync(OUT,{recursive:true});
const POSES=s=>({rest:{},[`Shoulder${s}+1`]:{[`Shoulder${s}`]:1},[`Shoulder${s}-1`]:{[`Shoulder${s}`]:-1},[`Elbow${s}+1`]:{[`Elbow${s}`]:1},[`Elbow${s}-1`]:{[`Elbow${s}`]:-1},
 [`Sh${s}+1_El${s}+1`]:{[`Shoulder${s}`]:1,[`Elbow${s}`]:1},[`Sh${s}-1_El${s}-1`]:{[`Shoulder${s}`]:-1,[`Elbow${s}`]:-1},[`Hip${s}+1`]:{[`Hip${s}`]:1},[`Hip${s}-1`]:{[`Hip${s}`]:-1},'BodyLean+1':{BodyLean:1},'BodyLean-1':{BodyLean:-1}});
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1800000});const res={};
for(const v of ['left','right']){const s=v==='left'?'L':'R';for(const tag of (process.env.TAGS||'live,fix').split(',')){const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
 const sk=tag==='live'?'':`&skin=../../../rig/work/weight_bleed_fix/${v}_skin_${tag}.json`;
 await pg.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}${sk}`,{waitUntil:'domcontentloaded',timeout:600000});await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:600000});await new Promise(r=>setTimeout(r,1200));
 const r=await pg.evaluate(async(PS)=>{document.getElementById('auto').checked=false;pauseManual();const out={};
  document.getElementById('check').click();out._rest=document.getElementById('status').textContent.split('\n')[0];out._skin=R.skin&&R.skin.src;out._ul=R.skin&&R.skin.underlay&&R.skin.underlay.ok;
  for(const n in PS){for(const k in P)set(k,P[k][2]);for(const k in PS[n])set(k,PS[n][k]);draw();out[n]=FR.toDataURL('image/png')}return out},POSES(s));
 res[`${v}_${tag}`]={rest:r._rest,skin:r._skin,underlayOk:r._ul,errs};for(const n in r)if(!n.startsWith('_'))fs.writeFileSync(`${OUT}/${v}_${tag}__${n}.png`,Buffer.from(r[n].split(',')[1],'base64'));await pg.close();console.error(v,tag)}}
fs.writeFileSync(`${OUT}/summary_${(process.env.TAGS||'live,fix').replace(/,/g,'_')}.json`,JSON.stringify(res,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
