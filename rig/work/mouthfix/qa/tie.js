const pp=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--disable-dev-shm-usage']});const out={};
for(const v of ['apose','tpose','left','right'])for(const q of ['','&mouthfix=1']){const p=await b.newPage();await p.goto(`http://127.0.0.1:8795/rig/index.html?view=${v}${q}`,{waitUntil:'domcontentloaded',timeout:180000});
 await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading&&R.mouthShapes',{timeout:180000});
 out[v+(q||'')]=await p.evaluate(()=>{const S=R.mouthShapes,rest=S.find(s=>s.name==='rest');const r={fade:MOUTH_FADE_MS,ties:[],n:0,restWins:0};
  // every point exactly equidistant between rest and another shape (midpoints), plus (0.25,0)
  const pts=[[0.25,0]];for(const s of S)if(s!==rest)pts.push([(s.open+rest.open)/2,(s.form+rest.form)/2]);
  for(const [o,f] of pts){set('MouthOpen',o);set('MouthForm',f);const d=s=>Math.round(Math.hypot(s.open-o,s.form-f)*1e9);const dm=Math.min(...S.map(d));const tied=S.filter(s=>d(s)===dm).map(s=>s.name);
   if(tied.length>1&&tied.includes('rest')){r.n++;const pk=mouthPick().replace('mouth_','');if(pk==='rest')r.restWins++;r.ties.push([o,f,tied.join('/'),pk])}}
  for(const k in P)set(k,P[k][2]);return r});await p.close()}
console.log(JSON.stringify(out,null,0));await b.close()})();
