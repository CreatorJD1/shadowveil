// Headless capture of rig FR canvas at rest, live and headgroup=1 (Base Eyes, read-only).
const pp=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');const path=require('path');
const OUT=path.resolve(__dirname,'../caps');const BASE='http://127.0.0.1:8781/rig/'; // scratch server rooted at /workspace/shadowveil (was 8765 = tmpsv_tree, invalid)
(async()=>{
 const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--disable-gpu','--window-size=1600,1000']});
 const pid=b.process().pid;console.log('chrome pid',pid);const meta={pid,base:BASE,server_root:'/workspace/shadowveil',server_port:8781};
 try{for(const vw of ['apose','left','right'])for(const hg of [0,1]){
  const url=`${BASE}?view=${vw}&quality=linear${hg?'&headgroup=1':''}`;const p=await b.newPage();const logs=[];
  p.on('console',m=>logs.push(m.text()));p.on('pageerror',e=>logs.push('ERR '+e.message));
  await p.setViewport({width:1600,height:1000});await p.goto(url,{waitUntil:'load',timeout:120000});
  await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading&&typeof FR!=="undefined"&&FR',{timeout:120000,polling:250});
  await new Promise(r=>setTimeout(r,1500));
  let h=null;if(hg)h=await p.evaluate(async v=>{const x=await RigHeadGroup.applyHandoff(v);return{x,cur:RigHeadGroup.get(),on:RigHeadGroup.on}},vw);
  await p.evaluate(async()=>{RigManual();for(const k in P)set(k,P[k][2]);draw();await new Promise(r=>setTimeout(r,400));draw();await new Promise(r=>setTimeout(r,200));draw()});
  const pv=await p.evaluate(()=>{const o={};for(const k in P)if(/Eye|Brow|Head|Angle/i.test(k))o[k]=P[k][2];return o});
  const d=await p.evaluate(()=>FR.toDataURL('image/png'));const tag=(hg?'hg':'live')+'_'+vw;
  fs.writeFileSync(`${OUT}/${tag}_rest.png`,Buffer.from(d.split(',')[1],'base64'));
  meta[tag]={url,hg:h,params:pv,logs:logs.slice(0,15)};console.log('done',tag,JSON.stringify(h));await p.close()}}
 finally{fs.writeFileSync(path.join(OUT,'meta.json'),JSON.stringify(meta,null,1));await b.close()}
})().catch(e=>{console.error(e);process.exit(1)});
